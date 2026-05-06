import time

# Core Models
from player import Player
from message import MessageFactory
from developments import Development

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
        self.message_factory = MessageFactory(self.players)

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
    # 2. PHASE MANAGEMENT (The Game Loop)
    # ==========================================
    def check_timer(self):
        if time.time() >= self.phase_end_time:
            self.next_phase()

    def check_all_players_locked(self):
        if all(p.finished_phase for p in self.players.values()):
            self.next_phase()

    def next_phase(self):
        # Resolve current phase before transitioning
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
        # Example: Set timer for 60 seconds from now
        self.phase_end_time = time.time() + 60

    def get_time_remaining(self):
        return max(0, int(self.phase_end_time - time.time()))

    # ==========================================
    # 3. INPUT ROUTING (Traffic Cops)
    # ==========================================
    def handle_user_action(self, user_id, action, payload):
        player = self.players.get(user_id)
        if not player:
            return False

        # Prevent actions if locked, unless the action is to finish the phase
        if player.finished_phase and action != 'FINISH_PHASE':
            return False

        if action == 'BUILD_DEV':
            return self.action_build_development(player, payload)

        elif action == 'COMMIT_WORK':
            return self.action_commit_work(player, payload)

        elif action == 'FINISH_PHASE':
            return self.action_finish_phase(player)

        return False

    def handle_message_action(self, user_id, data):
        # Passes the payload to the factory to update websocket states
        status, message = self.message_factory.process_message(user_id, data)
        return status, message

    # ==========================================
    # 4. ACTION EXECUTORS
    # ==========================================
    def action_build_development(self, player, payload):
        # Implementation for building a development
        pass

    def action_commit_work(self, player, payload):
        """Locks in the worker's chosen action and cleans up hoarded offers."""
        work_action = payload.get('work_action')
        if not work_action:
            return False

        # Lock in the worker's choice
        player.committed_action = work_action

        # Handle Accepted Job Offers (Cleanup)
        message_id = work_action.get('message_id')
        if message_id:
            # Mark chosen message as COMPLETED
            chosen_msg = self.message_factory.find_message(message_id)
            if chosen_msg:
                chosen_msg.status = 'COMPLETED'

            # Cancel other hoarded offers
            for msg in list(player.messages.values()):
                if msg.type == 'EMPLOYMENT' and msg.status == 'ACCEPTED' and msg.id != message_id:
                    msg.status = 'CANCELED'

        return self.action_finish_phase(player)

    def action_finish_phase(self, player):
        player.finished_phase = True
        self.check_all_players_locked()
        return True

    # ==========================================
    # 5. PHASE RESOLUTIONS (End-of-Day Math)
    # ==========================================
    def resolve_work_phase(self):
        """Generates resources for self-employed workers and resets phase state."""
        for player in self.players.values():
            ca = getattr(player, 'committed_action', None)

            if ca and isinstance(ca, dict):
                employer_id = ca.get('employer_id')
                wage = int(ca.get('wage', 0))
                wage_type = ca.get('wage_type', 'food')

                # Self-Employment: Generate resources from thin air
                if employer_id == player.session_id:
                    player.resources[wage_type] = player.resources.get(
                        wage_type, 0) + wage

            # Clear the committed action and reset phase states
            player.committed_action = None
            player.reset_phase()

    def resolve_trade_phase(self):
        # Implementation for resolving trades / updating ownership
        for player in self.players.values():
            player.reset_phase()

    def resolve_night_phase(self):
        # Implementation for consumption and sickness checks
        for player in self.players.values():
            player.consume_daily()
            player.reset_phase()

    # ==========================================
    # 6. STATE EXPORT
    # ==========================================
    def get_state_for_player(self, session_id):
        """Delegates to the external builder for DTO serialization."""
        return build_player_state(self, session_id)
