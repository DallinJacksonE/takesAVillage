import time
import uuid
import importlib
import copy
import random
from service.game.models.player import Player
from service.game.models.map import MapFactory
from service.game.models.chat_message import ChatMessage
from service.game.serializers.state import build_player_state
from service.game.serializers.game_history import add_player_hist, add_map_hist
from service.game.actions.contract_service import ContractFactory
from service.game.actions.dispatcher import ActionDispatcher
from service.game.actions.phase_resolution import PhaseResolver
from service.game.models.chat import Chat
from service.game.phases import Phase
from service.logging import BackendLogger


class Game:
    def __init__(self, game_id, host_id, ruleset_name="default", bots=0,
                 training=False, training_session_id=None,
                 training_generation=None, *, clock=time.time, rng=random,
                 logger=None, dispatcher=ActionDispatcher,
                 phase_resolver=PhaseResolver,
                 on_phase_completed=None):
        self.id = game_id
        self.host_id = host_id
        self.status = 'WAITING'
        self._clock = clock
        self._rng = rng
        self._dispatcher = dispatcher
        self._phase_resolver = phase_resolver
        self._on_phase_completed = on_phase_completed or (
            lambda _game, _phase: None)

        self.logger = logger or BackendLogger("game", self.id)

        try:
            self.rules = importlib.import_module(
                f"service.game.constants.{ruleset_name}")
            self.logger.info(f"Loaded ruleset: {ruleset_name}")
        except ImportError as e:
            self.logger.warning(f"Ruleset '{ruleset_name}' not found: "
                                f"{e}. Falling back to default.")
            self.rules = importlib.import_module(
                "service.game.constants.default")

        required_constants = [
            "DEVELOPMENT_COSTS", "CAMPFIRE_COST", "MAX_FIRE_SEATS",
            "STARTING_INVENTORY", "PHASE_LENGTH", "GAME_LENGTH",
            "MOUNTAINS_RATIO", "WOODS_RATIO", "FARMS_RATIO"
        ]
        for const in required_constants:
            if not hasattr(self.rules, const):
                raise AttributeError(
                    f"Ruleset {ruleset_name} missing required constant: {const}")

        self.development_costs = self.rules.DEVELOPMENT_COSTS
        self.campfire_cost = self.rules.CAMPFIRE_COST
        self.max_fire_seats = self.rules.MAX_FIRE_SEATS
        self.starting_inventory = self.rules.STARTING_INVENTORY
        self.phase_length = self.rules.PHASE_LENGTH
        self.game_length = self.rules.GAME_LENGTH
        self.mountains_ratio = self.rules.MOUNTAINS_RATIO
        self.woods_ratio = self.rules.WOODS_RATIO
        self.farms_ratio = self.rules.FARMS_RATIO

        self.logger.info(f"Ruleset '{ruleset_name}' | "
                         f"Phase: {self.phase_length}s | "
                         f"Game Length: {self.game_length} days")

        self.players = {}
        self.developments = {}
        self.map_data = {}
        self.contract_factory = ContractFactory(
            self.players, self.developments, self)
        self.chat_messages = []
        self.player_history = {}
        self.map_history = {}
        self.names = self.rules.AVAILABLE_NAMES.copy()
        self.chats = []
        self.host_connected = False
        self.bots_spawned = False

        self.day = 1
        self.phase = Phase.WORK.value
        self.phase_end_time = 0
        self.trade_count = 0
        self.contest_count = 0
        self.lie_count = {}

        self.add_player_hist = add_player_hist
        self.add_map_hist = add_map_hist

        self.bot_count = bots
        self.training = training
        self.training_session_id = training_session_id
        self.training_generation = training_generation
        if self.training:
            self.phase_length = 5

    def add_player(self, session_id):
        if session_id not in self.players:
            name = self._rng.choice(self.names)
            self.names.remove(name)
            self.players[session_id] = Player(
                session_id,
                name,
                copy.deepcopy(self.starting_inventory),
                self.rules.DEFAULT_SICKNESS)
            self.logger.info(
                f"Player {session_id[:8]} joined. "
                f"({len(self.players)}/{self.bot_count})"
            )
            if self.training and self.status == 'WAITING':
                if len(self.players) == self.bot_count:
                    self.logger.info("Training game auto-started")
                    self.start_game()

    def remove_player(self, session_id):
        if session_id in self.players:
            name = self.players[session_id].name
            if name not in self.names:
                self.names.append(name)
            del self.players[session_id]
            self.logger.info(
                f"Player {session_id[:8]} left the lobby. "
                f"({len(self.players)}/{self.bot_count})"
            )

    def start_game(self):
        if self.status != 'WAITING':
            return False
        if len(self.players) < 1:
            return False
        self.game_length += self._rng.randint(-4, 4)

        factory = MapFactory(len(self.players), self.farms_ratio,
                             self.woods_ratio, self.mountains_ratio)
        self.map_data = factory.map_tiles

        if self.training:
            self.host_connected = True

        self.status = 'RUNNING'
        self.start_phase(Phase.WORK)
        return True

    def check_timer(self):
        if self._clock() >= self.phase_end_time:
            self.next_phase()
            return True
        return False

    def check_all_players_locked(self):
        if self.status == "WAITING":
            return False
        active_players = [
            p for p in self.players.values() if p.health != "dead"]
        if not active_players:
            return False

        if all(p.finished_phase for p in active_players):
            self.next_phase()

    def next_phase(self):
        self._on_phase_completed(self, self.phase)

        if self.phase == 'WORK':
            self.resolve_work_phase()
            self.start_phase('TRADE')
        elif self.phase == 'TRADE':
            self._phase_resolver.resolve_trade(self)
            self.start_phase('NIGHT')
        elif self.phase == 'NIGHT':
            self.resolve_night_phase()
            if self.status == "ENDED":
                return
            self.day += 1
            self.start_phase('WORK')

    def start_phase(self, phase_name):
        phase_name = Phase.value_of(phase_name)
        self.phase = phase_name
        self.phase_end_time = self._clock() + self.phase_length

        if phase_name == 'WORK':
            self._phase_resolver.start_day(self)

        for player in self.players.values():
            if player.health == "dead":
                player.finished_phase = True
            else:
                player.finished_phase = False

            if phase_name == "TRADE":
                player.last_committed_action = player.committed_action
                player.committed_action = None
            else:
                player.committed_action = None

    def get_time_remaining(self):
        return max(0, int(self.phase_end_time - self._clock()))

    def handle_chat(self, user_id, data):
        content = data.get('content')
        to_id = data.get('to_id', 'GLOBAL')

        if user_id not in self.players or not isinstance(content, str):
            return None
        content = content.strip()
        if not content:
            return None
        group_chat = next(
            (chat for chat in self.chats if chat.id == to_id), None)
        if group_chat:
            if user_id not in group_chat.member_ids:
                return None
        elif to_id != 'GLOBAL' and to_id not in self.players:
            return None

        chat_msg = ChatMessage(
            str(uuid.uuid4()), user_id, to_id, content, self._clock())
        self.chat_messages.append(chat_msg)

        sender = self.players.get(user_id)
        if sender:
            sender.add_timeline_event("SENT_CHAT", chat_msg.__dict__)

        if group_chat:
            recipients = [
                self.players[member_id]
                for member_id in group_chat.member_ids
                if member_id != user_id
            ]
            for recipient in recipients:
                recipient.add_timeline_event(
                    "RECEIVED_CHAT", chat_msg.__dict__)
        elif to_id != 'GLOBAL':
            recipient = self.players.get(to_id)
            if recipient and recipient != sender:
                recipient.add_timeline_event(
                    "RECEIVED_CHAT", chat_msg.__dict__)

        return chat_msg

    def create_chat(self, creator_id, name, member_ids):
        if creator_id not in self.players or not isinstance(member_ids, list):
            return None
        all_members = list(dict.fromkeys(member_ids + [creator_id]))
        if any(member_id not in self.players for member_id in all_members):
            return None
        chat = Chat(str(uuid.uuid4()), name, creator_id, all_members)
        self.chats.append(chat)
        return chat

    def handle_action(self, user_id, data):
        if self.status == "WAITING":
            return None
        if user_id is None:
            return
        return self._dispatcher.dispatch(self, user_id, data)

    def resolve_work_phase(self):
        self._phase_resolver.resolve_work(self)

    def resolve_night_phase(self):
        self._phase_resolver.resolve_night(self)

    def is_game_over(self):
        return all(p.health == "dead" for p in self.players.values())

    def get_state_for_player(self, session_id):
        return build_player_state(self, session_id)

    def get_global_chat_history(self):
        return [msg.to_dict() for msg in self.chat_messages if msg.to_id == "GLOBAL"]

    def get_private_chat_history(self, player_id):
        group_ids = {
            chat.id for chat in self.chats if player_id in chat.member_ids
        }
        return [
            msg.to_dict() for msg in self.chat_messages
            if (msg.to_id == player_id
                or msg.from_id == player_id
                or msg.to_id == "GLOBAL"
                or msg.to_id in group_ids)
        ]
