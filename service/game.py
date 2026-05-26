import time
import uuid
import importlib
import copy
import random
# Core Models
from models.player import Player
from models.map import MapFactory
from models.chat_message import ChatMessage
# Extracted Utilities
from serializers.state_builder import build_player_state
from serializers.game_info_builder import add_player_hist, add_map_hist

from actions.contract_factory import ContractFactory
from actions.action_dispatcher import ActionDispatcher
from db import db
from serializers.snapshots import build_game_snapshot, build_player_snapshot
import json


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
        self.mountains_ratio = self.rules.MOUNTAINS_RATIO
        self.woods_ratio = self.rules.WOODS_RATIO
        self.farms_ratio = self.rules.FARMS_RATIO
        self.resource_costs = self.rules.RESOURCE_COSTS

        self.players = {}
        self.developments = {}
        self.map_data = {}
        self.contract_factory = ContractFactory(
            self.players, self.developments)
        self.chat_messages = []
        self.player_history = {}
        self.map_history = {}
        self.names = self.rules.AVAILABLE_NAMES.copy()

        # Time and Phase state
        self.day = 1
        self.phase = 'WORK'
        self.phase_end_time = 0

        # Histoty functions
        self.add_player_hist = add_player_hist
        self.add_map_hist = add_map_hist

    def add_player(self, session_id):
        if session_id not in self.players:
            name = random.choice(self.names)
            self.names.remove(name)
            self.players[session_id] = Player(
                session_id,
                name,
                copy.deepcopy(self.starting_inventory),
                self.rules.DEFAULT_SICKNESS)

    def start_game(self):
        # Determine game length
        self.game_length += random.randint(-4, 4)
        # Enforce the minimum player requirement
        if len(self.players) < 1:
            return False

        # 1. Generate the map tiles based on the final player count
        factory = MapFactory(len(self.players), self.farms_ratio,
                             self.woods_ratio, self.mountains_ratio)

        self.map_data = factory.map_tiles

        self.status = 'RUNNING'
        self.start_phase('WORK')
        return True

    # ==========================================
    # PHASE MANAGEMENT
    # ==========================================
    def check_timer(self):
        if time.time() >= self.phase_end_time:
            self.next_phase()
            return True
        return False

    def check_all_players_locked(self):
        active_players = [
            p for p in self.players.values()
            if p.health != "dead"
        ]

        if all(p.finished_phase for p in active_players):
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

        # -------------------------
        # GAME SNAPSHOT
        # -------------------------

        game_snapshot = build_game_snapshot(self)

        db.store_game_result(
            self.id,
            self.day,
            self.phase,
            json.dumps(game_snapshot)
        )

        # -------------------------
        # PLAYER SNAPSHOTS
        # -------------------------

        for player in self.players.values():

            db.store_player_snapshot(
                game_id=self.id,
                day_num=self.day,
                phase=self.phase,
                player=player
            )

        self.phase_end_time = time.time() + self.phase_length

        # ------------------------------------------------
        # Activate pending contests at START of WORK
        # ------------------------------------------------
        if phase_name == 'WORK':

            ActionDispatcher.start_day(self)

            for dev in self.developments.values():

                if (
                    getattr(dev, 'pending_contest', False)
                    and dev.pending_contest_day == self.day
                ):

                    dev.is_contested = True

                    # Initiator automatically participates
                    dev.contester_supporters = []
                    dev.pending_contest = False

                    owner = self.players.get(dev.owner)

                    if owner:
                        owner.add_timeline_event(
                            "CONTEST_STARTED",
                            {
                                "dev_id": dev.id,
                                "attacker": dev.contest_initiator_id
                            }
                        )

        for player in self.players.values():

            # Auto-finish inactive players
            if player.health == "dead":
                player.finished_phase = True
            else:
                player.finished_phase = False

            player.committed_action = None

    def get_time_remaining(self):
        return max(0, int(self.phase_end_time - time.time()))

    # ==========================================
    # SEPARATED INPUT ROUTING
    # ==========================================

    def handle_chat(self, user_id, data):
        content = data.get('content')
        # Default to global chat if no target
        to_id = data.get('to_id', 'GLOBAL')

        chat_msg = ChatMessage(
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
        # Any logical checks for player action handling should go in
        # ActionDispatcher.player_can_perform_action
        return ActionDispatcher.dispatch(self, user_id, data)

    # ==========================================
    # PHASE RESOLUTIONS & EXPORT
    # ==========================================
    def resolve_work_phase(self):
        ActionDispatcher.resolve_work_phase(self)

    def resolve_trade_phase(self):
        pass

    def resolve_night_phase(self):
        # End of day logical operations or checks should go in
        # ActionDispactcher.resolve_night
        ActionDispatcher.resolve_night(self)

    def is_game_over(self):
        all_dead = True
        for player in self.players.values():
            if player.health != "dead":
                all_dead = False
        return all_dead

    def get_state_for_player(self, session_id):
        return build_player_state(self, session_id)
