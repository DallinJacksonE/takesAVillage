import time
import uuid

# Core Models
from player import Player
from actions import ActionFactory
from developments import Development
from dtos import ChatMessageDTO

# Extracted Utilities
from utils.name_generator import get_random_name
from serializers.state_builder import build_player_state


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
        self.status = 'ACTIVE'
        self.start_phase('WORK')

    # ==========================================
    # 2. PHASE MANAGEMENT
    # ==========================================
    def check_timer(self):
        if time.time() >= self.phase_end_time:
            self.next_phase()

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
        """Pure social chat pipeline. Bypasses game logic entirely."""
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
        """Unified game state pipeline for System Actions and Player Contracts."""
        player = self.players.get(user_id)
        if not player:
            return False

        action_command = data.get('action_command') or data.get('action')
        payload = data.get('payload', data)

        # Prevent actions if locked (unless they are trying to finish the phase)
        if player.finished_phase and action_command != 'FINISH_PHASE':
            return False

        # --- Branch A: Hardcoded System Actions ---
        if action_command == 'BUILD_DEV':
            return self.action_build_development(player, payload)
        elif action_command == 'COMMIT_WORK':
            return self.action_commit_work(player, payload)
        elif action_command == 'FINISH_PHASE':
            return self.action_finish_phase(player)

        # --- Branch B: Dynamic Contracts (Trade, Employment, Campfire) ---
        status, action_obj = self.action_factory.process_action(
            user_id, payload)

        if status != "ERROR" and status != "ILLEGAL":
            player.add_timeline_event(f"ACTION_{status}", {
                "action_id": action_obj.id,
                "type": action_obj.type
            })
            return True

        return False

    # ==========================================
    # 4. ACTION EXECUTORS
    # ==========================================
    def action_build_development(self, player, payload):
        pass

    def action_commit_work(self, player, payload):
        """Locks in the worker's choice and cleans up the action array."""
        work_action = payload.get('work_action')
        if not work_action:
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
        for player in self.players.values():
            ca = getattr(player, 'committed_action', None)

            if ca and isinstance(ca, dict):
                employer_id = ca.get('employer_id')
                wage = int(ca.get('wage', 0))
                wage_type = ca.get('wage_type', 'food')

                # Self-Employment Generation
                if employer_id == player.session_id:
                    player.resources[wage_type] = player.resources.get(
                        wage_type, 0) + wage

            player.committed_action = None
            player.reset_phase()

    def resolve_trade_phase(self):
        for player in self.players.values():
            player.reset_phase()

    def resolve_night_phase(self):
        for player in self.players.values():
            player.consume_daily()
            player.reset_phase()

    def get_state_for_player(self, session_id):
        return build_player_state(self, session_id)
