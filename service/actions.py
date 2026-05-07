import uuid
import copy
from datetime import datetime

# --- Core Action Models (Contracts) ---


class Action:
    """
    The unified Base Action. 
    Represents a contract between an initiator and a target (which can be the 'SYSTEM').
    """

    def __init__(self, initiator_id, target_id, action_type):
        self.id = str(uuid.uuid4())
        self.initiator_id = initiator_id
        self.target_id = target_id
        self.type = action_type
        # Status Lifecycle: PENDING -> ACCEPTED -> COMMITTED | DENIED | CANCELED | COMPLETED
        self.status = 'PENDING'
        self.created_at = datetime.now()

    def is_legal(self, _player) -> bool:
        return True


class EmploymentAction(Action):
    def __init__(self, initiator_id, target_id, dev_id, wage, wage_type, is_application=False):
        super().__init__(initiator_id, target_id, 'EMPLOYMENT')
        self.dev_id = dev_id
        self.wage = int(wage) if wage is not None else 0
        self.wage_type = wage_type
        self.is_application = is_application

    def is_legal(self, player):
        # The employer must own the development
        employer_id = self.target_id if self.is_application else self.initiator_id
        if player.session_id == employer_id:
            if str(self.dev_id) not in [str(d) for d in player.developments]:
                return False
        return True


class TradeAction(Action):
    def __init__(self, initiator_id, target_id, offer_items, request_items):
        super().__init__(initiator_id, target_id, 'TRADE')
        self.offer_items = offer_items or {}
        self.request_items = request_items or {}
        self.actual_offer_items = self.offer_items.copy()
        self.actual_request_items = self.request_items.copy()
        self.initiator_finalized = False
        self.target_finalized = False


class CampfireAction(Action):
    def __init__(self, initiator_id, target_id, is_request=False):
        super().__init__(initiator_id, target_id, 'CAMPFIRE')
        self.is_request = is_request

    def is_legal(self, player):
        # If it's an offer, the initiator must not be actively hosting another fire
        # (or whatever your specific host rules dictate)
        if not self.is_request and player.session_id == self.initiator_id:
            return not player.hosting_fire
        return True


class SystemAction(Action):
    """
    Contracts where the target is the Game Engine itself (MAINTENANCE, UPGRADE).
    """

    def __init__(self, initiator_id, action_type, dev_id, cost, cost_type):
        super().__init__(initiator_id, 'SYSTEM', action_type)
        self.dev_id = dev_id
        self.cost = cost
        self.cost_type = cost_type

# --- Factory ---


class ActionFactory:
    def __init__(self, players):
        self.players = players

    def process_action(self, user_id, data):
        """Unified entry point for drafting or updating a contract."""
        action_id = data.get('id') or data.get('actionId')

        if action_id and self.find_action(action_id):
            return self._update_action(user_id, action_id, data)
        else:
            return self._create_action(data)

    def _create_action(self, action_data):
        try:
            new_action = self.build_action_from_data(action_data)
        except ValueError as e:
            print(f"Error creating action: {e}")
            return "ERROR", None

        self._add_action_to_players(new_action)
        return "CREATED", new_action

    def build_action_from_data(self, data):
        action_type = data.get('type')
        initiator_id = data.get('initiator_id') or data.get('from_id')
        target_id = data.get('target_id') or data.get('to_id')

        if action_type == 'EMPLOYMENT':
            return EmploymentAction(
                initiator_id, target_id,
                data.get('dev_id'), data.get('wage'), data.get('wage_type'),
                data.get('is_application', False)
            )
        elif action_type == 'TRADE':
            return TradeAction(
                initiator_id, target_id,
                data.get('offer_items', {}), data.get('request_items', {})
            )
        elif action_type == 'CAMPFIRE':
            return CampfireAction(initiator_id, target_id, data.get('is_request', False))
        elif action_type in ['MAINTENANCE', 'UPGRADE']:
            return SystemAction(
                initiator_id, action_type,
                data.get('dev_id'), data.get('cost'), data.get('cost_type')
            )
        else:
            raise ValueError(f"Unknown action type: {action_type}")

    def _update_action(self, user_id, action_id, data):
        original_action = self.find_action(action_id)
        if not original_action:
            return "NOT_FOUND", None

        action_copy = copy.deepcopy(original_action)
        actor = self.players.get(user_id)
        # Accept, Deny, Finalize, etc.
        action_command = data.get('action_command')

        # Apply Lifecycle Changes
        if action_command == 'DENY':
            action_copy.status = 'DENIED'
        elif action_command == 'ACCEPT':
            action_copy.status = 'ACCEPTED'
        elif action_command == 'CANCEL':
            action_copy.status = 'CANCELED'
        elif action_command == 'FINALIZE':
            self._finalize_trade(action_copy, user_id, data)

        # Check Legality
        if not action_copy.is_legal(actor):
            return "ILLEGAL", original_action

        # Save Changes
        self._add_action_to_players(action_copy)

        return f"UPDATED_{action_copy.status}", action_copy

    def _finalize_trade(self, action_copy, user_id, data):
        if action_copy.type != 'TRADE':
            return

        if user_id == action_copy.initiator_id:
            action_copy.actual_offer_items = data.get(
                'actual_items', action_copy.offer_items)
            action_copy.initiator_finalized = True
        elif user_id == action_copy.target_id:
            action_copy.actual_request_items = data.get(
                'actual_items', action_copy.request_items)
            action_copy.target_finalized = True

        if action_copy.initiator_finalized and action_copy.target_finalized:
            action_copy.status = 'COMPLETED'

    def _add_action_to_players(self, action_obj):
        initiator = self.players.get(action_obj.initiator_id)
        target = self.players.get(action_obj.target_id)

        if initiator:
            initiator.actions[action_obj.id] = action_obj
        if target:
            target.actions[action_obj.id] = action_obj

    def find_action(self, action_id):
        for player in self.players.values():
            if action_id in getattr(player, 'actions', {}):
                return player.actions[action_id]
        return None
