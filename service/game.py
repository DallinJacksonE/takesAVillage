import time
import uuid
import importlib
import copy
import random
import json
from models.player import Player
from models.map import MapFactory
from models.chat_message import ChatMessage
from serializers.state_builder import build_player_state
from serializers.game_info_builder import add_player_hist, add_map_hist
from actions.contract_factory import ContractFactory
from actions.action_dispatcher import ActionDispatcher
from db import db
from serializers.snapshots import build_game_snapshot, build_work_snapshot, build_night_snapshot, build_trade_snapshot
from models.chat import Chat
from logger import BackendLogger


class Game:
    def __init__(self, game_id, host_id, ruleset_name="default", bots=0,
                 training=False, training_session_id=None,
                 training_generation=None):
        self.id = game_id
        self.host_id = host_id
        self.status = 'WAITING'

        # Instantiate the specific Game Logger
        self.logger = BackendLogger("game", self.id)

        try:
            self.rules = importlib.import_module(f"constants.{ruleset_name}")
            self.logger.info(f"Loaded ruleset: {ruleset_name}")
        except ImportError as e:
            self.logger.warning(f"Ruleset '{ruleset_name}' not found: "
                                f"{e}. Falling back to default.")
            self.rules = importlib.import_module("constants.default")

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
            self.players, self.developments)
        self.chat_messages = []
        self.player_history = {}
        self.map_history = {}
        self.names = self.rules.AVAILABLE_NAMES.copy()
        self.chats = []
        self.host_connected = False
        self.bots_spawned = False

        self.day = 1
        self.phase = 'WORK'
        self.phase_end_time = 0

        self.add_player_hist = add_player_hist
        self.add_map_hist = add_map_hist

        self.bot_count = bots
        self.training = training
        self.training_session_id = training_session_id
        self.training_generation = training_generation

    def add_player(self, session_id):
        if session_id not in self.players:
            name = random.choice(self.names)
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
        self.game_length += random.randint(-4, 4)
        if len(self.players) < 1:
            return False

        factory = MapFactory(len(self.players), self.farms_ratio,
                             self.woods_ratio, self.mountains_ratio)
        self.map_data = factory.map_tiles

        if self.training:
            self.host_connected = True

        self.status = 'RUNNING'
        self.start_phase('WORK')
        return True

    def check_timer(self):
        if time.time() >= self.phase_end_time:
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
        if not self.training and self.phase == "NIGHT":
            game_snapshot = build_game_snapshot(self)
            db.store_game_snapshot(
                self.id, self.day, self.phase, json.dumps(game_snapshot))

        if not self.training:
            for player in self.players.values():
                if self.phase == "WORK":
                    snapshot = build_work_snapshot(player, self)
                    db.store_work_snapshot(snapshot)
                elif self.phase == "TRADE":
                    snapshot = build_trade_snapshot(player, self)
                    db.store_trade_snapshot(snapshot)
                    player.trade_history = []
                elif self.phase == "NIGHT":
                    snapshot = build_night_snapshot(player, self)
                    db.store_night_snapshot(snapshot)

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

        if phase_name == 'WORK':
            ActionDispatcher.start_day(self)
            for dev in self.developments.values():
                if getattr(dev, 'pending_contest', False) and dev.pending_contest_day == self.day:
                    dev.is_contested = True
                    dev.contester_supporters = []
                    dev.pending_contest = False
                    owner = self.players.get(dev.owner)
                    if owner:
                        owner.add_timeline_event(
                            "CONTEST_STARTED", {
                                "dev_id": dev.id, "attacker": dev.contest_initiator_id}
                        )

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
        return max(0, int(self.phase_end_time - time.time()))

    def handle_chat(self, user_id, data):
        content = data.get('content')
        to_id = data.get('to_id', 'GLOBAL')

        chat_msg = ChatMessage(str(uuid.uuid4()), user_id,
                               to_id, content, time.time())
        self.chat_messages.append(chat_msg)

        sender = self.players.get(user_id)
        if sender:
            sender.add_timeline_event("SENT_CHAT", chat_msg.__dict__)

        if to_id != 'GLOBAL':
            recipient = self.players.get(to_id)
            if recipient and recipient != sender:
                recipient.add_timeline_event(
                    "RECEIVED_CHAT", chat_msg.__dict__)

        return chat_msg

    def create_chat(self, creator_id, name, member_ids):
        all_members = list(set(member_ids + [creator_id]))
        chat = Chat(str(uuid.uuid4()), name, creator_id, all_members)
        self.chats.append(chat)
        return chat

    def handle_action(self, user_id, data):
        if self.status == "WAITING":
            return None
        if user_id is None:
            return
        return ActionDispatcher.dispatch(self, user_id, data)

    def resolve_work_phase(self):
        ActionDispatcher.resolve_work_phase(self)

    def resolve_trade_phase(self):
        pass

    def resolve_night_phase(self):
        ActionDispatcher.resolve_night(self)

    def is_game_over(self):
        return all(p.health == "dead" for p in self.players.values())

    def get_state_for_player(self, session_id):
        return build_player_state(self, session_id)

    def get_global_chat_history(self):
        return [msg.to_dict() for msg in self.chat_messages if msg.to_id == "GLOBAL"]

    def get_private_chat_history(self, player_id):
        return [
            msg.to_dict() for msg in self.chat_messages
            if (msg.to_id == player_id or msg.from_id == player_id or msg.to_id == "GLOBAL")
        ]

    def get_available_build_actions(self, player):
        actions = []
        for tile in self.map_data.values():
            if tile.development:
                continue
            build_cost = self.development_costs.get(
                tile.type, {}).get("build", {})
            affordable = all(player.resources.get(r, 0) >=
                             a for r, a in build_cost.items())
            if affordable:
                actions.append({"action_command": "BUILD_DEV",
                               "payload": {"tile_id": tile.id}})
        return actions

    def get_available_upgrade_actions(self, player): return []
    def get_available_maintenance_actions(self, player): return []
    def get_available_contest_actions(self, player): return []

    def get_available_actions(self, player):
        actions = []
        if self.phase == "WORK":
            if player.health == "SICK":
                return []
            actions.extend(self.get_available_build_actions(player))
            actions.extend(self.get_available_upgrade_actions(player))
            actions.extend(self.get_available_maintenance_actions(player))
            actions.extend(self.get_available_contest_actions(player))
            for job in player.available_work:
                actions.append(
                    {"action_command": "COMMIT_WORK", "payload": {"job": job}})
        return actions
