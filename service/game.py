import time
import uuid
import importlib
import copy
import random
# Core Models
from models.player import Player
from dtos import ChatMessageDTO
from models.map import MapFactory
# Extracted Utilities
from utils.name_generator import get_random_name
from serializers.state_builder import build_player_state
from serializers.game_info_builder import add_player_hist, add_map_hist

from actions.contract_factory import ContractFactory
from actions.action_dispatcher import ActionDispatcher


class Game:
    # ==========================================
    # INITIALIZATION & SETUP
    # ==========================================
    def __init__(self, game_id, host_id, ruleset_name="default"):
        self.id = game_id
        self.host_id = host_id
        self.status = 'WAITING'
        try:
            self.rules = importlib.import_module(f"constants.{ruleset_name}")
        except ImportError:
            print(f"Warning: Ruleset"
                  f" '{ruleset_name}' not found. Falling back to default.")
            self.rules = importlib.import_module("constants.default")

        # Constants for the game, can add new rulesets in constants folder
        self.development_costs = self.rules.DEVELOPMENT_COSTS
        self.campfire_cost = self.rules.CAMPFIRE_COST
        self.max_fire_seats = self.rules.MAX_FIRE_SEATS
        self.starting_inventory = self.rules.STARTING_INVENTORY
        self.phase_length = self.rules.PHASE_LENGTH
        self.game_length = self.rules.GAME_LENGTH

        self.players = {}
        self.developments = {}
        self.map_data = {}
        self.contract_factory = ContractFactory(self.players)
        self.chat_messages = []
        self.player_history = {}
        self.map_history = {}

        # Time and Phase state
        self.day = 1
        self.phase = 'WORK'
        self.phase_end_time = 0

    def add_player(self, session_id):
        if session_id not in self.players:
            name = get_random_name()
            self.players[session_id] = Player(
                session_id, name, copy.deepcopy(self.starting_inventory))

    def start_game(self):
        # Determine game length
        self.game_length += random.randint(-4, 4)
        # Enforce the minimum player requirement
        if len(self.players) < 1:
            return False

        # 1. Generate the map tiles based on the final player count
        factory = MapFactory(len(self.players))

        self.map_data = factory.map_tiles

        self.status = 'ACTIVE'
        self.start_phase('WORK')
        return True

    # ==========================================
    # 2. PHASE MANAGEMENT
    # ==========================================
    def check_timer(self):
        if time.time() >= self.phase_end_time:
            self.next_phase()
            return True
        return False

    def check_all_players_locked(self):
        if all(p.finished_phase for p in self.players.values()):
            self.next_phase()

    def next_phase(self):
        if self.phase == 'WORK':
            self.resolve_work_phase()
            self.start_phase('TRADE')
        elif self.phase == 'TRADE':
            self.resolve_trade_phase()
            self.start_phase('NIGHT')
        elif self.phase == 'NIGHT':
            self.resolve_night_phase()
            self.day += 1
            self.start_phase('WORK')
            

    def start_phase(self, phase_name):
        self.phase = phase_name
        self.phase_end_time = time.time() + self.phase_length

    def get_time_remaining(self):
        return max(0, int(self.phase_end_time - time.time()))

    # ==========================================
    # 3. SEPARATED INPUT ROUTING
    # ==========================================

    def handle_chat(self, user_id, data):
        content = data.get('content')
        # Default to global chat if no target
        to_id = data.get('to_id', 'GLOBAL')

        chat_msg = ChatMessageDTO(
            id=str(uuid.uuid4()),
            from_id=user_id,
            to_id=to_id,
            content=content,
            timestamp=time.time()
        )
        self.chat_messages.append(chat_msg)

        # Log for research timeline
        sender = self.players.get(user_id)
        if sender:
            sender.add_timeline_event("SENT_CHAT", chat_msg.__dict__)

        # Log for specific recipient if it was a DM
        if to_id != 'GLOBAL':
            recipient = self.players.get(to_id)
            if recipient and recipient != sender:
                recipient.add_timeline_event(
                    "RECEIVED_CHAT", chat_msg.__dict__)

        return True

    def handle_action(self, user_id, data):
        return ActionDispatcher.dispatch(self, user_id, data)

    def action_finish_phase(self, player):
        player.finished_phase = True
        self.check_all_players_locked()
        return True

    # ==========================================
    # 5. PHASE RESOLUTIONS & EXPORT
    # ==========================================
    def resolve_work_phase(self):
        ActionDispatcher.resolve_work_phase(self)

    def resolve_trade_phase(self):
        for player in self.players.values():
            player.reset_phase()

    def resolve_night_phase(self):
        if self.day >= self.game_length:
            self.status = 'ENDED'
            return
        for player in self.players.values():
            player.consume_daily()
            add_player_hist(self, player.session_id)
        add_map_hist(self)
            player.reset_phase()
        for dev in self.developments.values():
            dev.degrade()

    def get_state_for_player(self, session_id):
        return build_player_state(self, session_id)
