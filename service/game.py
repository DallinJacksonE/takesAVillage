from constants import DEVELOPMENT_COSTS
import time
import uuid

# Core Models
from models.player import Player
from actions import ActionFactory
from dtos import ChatMessageDTO
from models.map import MapFactory
# Extracted Utilities
from utils.name_generator import get_random_name
from serializers.state_builder import build_player_state
from models.developments import Development
from dtos import DevelopmentDTO
from dataclasses import asdict
from systems.economy import EconomySystem
from systems.conflict import ConflictSystem
from systems.social import SocialSystem


class Game:
    # ==========================================
    # 1. INITIALIZATION & SETUP
    # ==========================================
    def __init__(self, game_id, host_id):
        self.id = game_id
        self.host_id = host_id
        self.status = 'WAITING'
        self.players = {}
        self.developments = {}
        self.map_data = []

        self.action_factory = ActionFactory(self.players)
        self.chat_messages = []  # The global chat array for the UI

        # Time and Phase state
        self.day = 1
        self.phase = 'WORK'
        self.phase_end_time = 0

    def add_player(self, session_id):
        if session_id not in self.players:
            name = get_random_name()
            self.players[session_id] = Player(session_id, name)

    def start_game(self):
        # Enforce the minimum player requirement
        if len(self.players) < 2:
            return False

        # 1. Generate the map tiles based on the final player count
        factory = MapFactory(len(self.players))

        # 2. Populate map_data by converting the MapTile objects into dictionaries
        # so your MapTileDTO.from_dict() can safely parse them later.
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
        self.phase_end_time = time.time() + 60

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
        player = self.players.get(user_id)
        if not player:
            return False

        action_command = data.get('action_command') or data.get('action')
        payload = data.get('payload', data)

        if player.finished_phase and action_command != 'FINISH_PHASE':
            return False

        # --- Branch A: System Actions (Routed to Systems) ---
        if action_command == 'BUILD_DEV':
            success = EconomySystem.build_development(self, player, payload)
            if success:
                return self.action_finish_phase(player)
            return False

        elif action_command == 'MAINTAIN_DEV':
            success = EconomySystem.maintain_development(self, player, payload)
            if success:
                return self.action_finish_phase(player)
            return False

        elif action_command == 'UPGRADE_DEV':
            success = EconomySystem.upgrade_development(self, player, payload)
            if success:
                return self.action_finish_phase(player)
            return False

        elif action_command == 'CONTEST_DEV':
            success = ConflictSystem.action_contest_development(
                self, player, payload)
            if success:
                return self.action_finish_phase(player)
            return False

        elif action_command == 'COMMIT_WORK':
            return self.action_commit_work(player, payload)

        elif action_command == 'START_FIRE':
            success = SocialSystem.start_fire(self, player)
            if success:
                return True
            return False

        elif action_command == 'FINISH_PHASE':
            return self.action_finish_phase(player)

        status, action_obj = self.action_factory.process_action(
            user_id, payload)

        if status not in ["ERROR", "ILLEGAL"]:

            # --- NEW: Real-time Contract Intercepts ---
            if status == "UPDATED_COMPLETED" and action_obj.type == "TRADE":
                # Instantly swap items so they can trade again this phase
                SocialSystem.execute_trade(self, action_obj)

            elif status == "UPDATED_ACCEPTED" and action_obj.type == "CAMPFIRE":
                # The target of the request is the host
                host = self.players.get(action_obj.target_id)
                if host:
                    SocialSystem.seat_guest(self, host, action_obj)
            # ------------------------------------------

            player.add_timeline_event(
                f"ACTION_{status}", {"action_id": action_obj.id, "type": action_obj.type})
            return True

        return False

    # ==========================================
    # 4. ACTION EXECUTORS
    # ==========================================

    def action_commit_work(self, player, payload):
        """Locks in the worker's choice and cleans up the action array."""
        work_action = payload.get('work_action')
        if not work_action:
            return False

        dev_data = work_action.get('development', {})
        dev_id = dev_data.get('id')
        live_dev = self.developments.get(dev_id)

        # If the development is under hold, no new work can be committed here.
        if live_dev and getattr(live_dev, 'is_contested', False):
            return False

        player.committed_action = work_action

        # Handle Accepted Job Offers (Cleanup)
        action_id = work_action.get('action_id')
        if action_id:
            # Mark chosen contract as COMPLETED
            chosen_action = self.action_factory.find_action(action_id)
            if chosen_action:
                chosen_action.status = 'COMPLETED'

            # Cancel other hoarded offers in the player's action list
            for act in list(player.actions.values()):
                if act.type == 'EMPLOYMENT' and act.status == 'ACCEPTED' and act.id != action_id:
                    act.status = 'CANCELED'

        return self.action_finish_phase(player)

    def action_finish_phase(self, player):
        player.finished_phase = True
        self.check_all_players_locked()
        return True

    # ==========================================
    # 5. PHASE RESOLUTIONS & EXPORT
    # ==========================================
    def resolve_work_phase(self):

        # 1. Resolve conflicts and stalemates FIRST
        ConflictSystem.resolve_contests(self)

        # 2. Generate yields for uncontested developments SECOND
        EconomySystem.resolve_work_phase(self)

    def resolve_trade_phase(self):
        for player in self.players.values():
            player.reset_phase()

    def resolve_night_phase(self):
        for player in self.players.values():
            player.consume_daily()
            player.reset_phase()
        for dev in self.developments.values():
            dev.degrade()

    def get_state_for_player(self, session_id):
        return build_player_state(self, session_id)
