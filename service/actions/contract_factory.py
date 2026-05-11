import copy
from .contracts import EmploymentContract, TradeContract, CampfireContract


class ContractFactory:
    def __init__(self, players):
        self.players = players

    def process_contract(self, user_id, data):
        """Unified entry point for drafting or updating a contract."""
        contract_id = data.get('id') or data.get('contractId')

        if contract_id and self.find_contract(contract_id):
            return self._update_contract(user_id, contract_id, data)
        else:
            return self._create_contract(data)

    def _create_contract(self, data):
        try:
            new_contract = self._build_contract_from_data(data)
        except ValueError as e:
            print(f"Error creating contract: {e}")
            return "ERROR", None

        self._add_contract_to_players(new_contract)
        return "CREATED", new_contract

    def _build_contract_from_data(self, data):
        contract_type = data.get('type')
        initiator_id = data.get('initiator_id') or data.get('from_id')
        target_id = data.get('target_id') or data.get('to_id')

        if contract_type == 'EMPLOYMENT':
            return EmploymentContract(
                initiator_id, target_id,
                data.get('dev_id'), data.get('wage'), data.get('wage_type'),
                data.get('is_application', False)
            )
        elif contract_type == 'TRADE':
            return TradeContract(
                initiator_id, target_id,
                data.get('offer_items', {}), data.get('request_items', {})
            )
        elif contract_type == 'CAMPFIRE':
            return CampfireContract(initiator_id, target_id, data.get('is_request', False))
        else:
            raise ValueError(f"Unknown contract type: {contract_type}")

    def _update_contract(self, user_id, contract_id, data):
        original_contract = self.find_contract(contract_id)
        if not original_contract:
            return "NOT_FOUND", None

        contract_copy = copy.deepcopy(original_contract)
        actor = self.players.get(user_id)
        action_command = data.get('action_command')

        # Apply Lifecycle Changes
        if action_command == 'DENY':
            contract_copy.status = 'DENIED'
        elif action_command == 'ACCEPT':
            contract_copy.status = 'ACCEPTED'
        elif action_command == 'BARTER':
            contract_copy.offer_items = data.get(
                'offer_items', contract_copy.offer_items)
            contract_copy.request_items = data.get(
                'request_items', contract_copy.request_items)

            # NEW: Switch the court flag instead of flipping IDs
            if user_id == contract_copy.initiator_id:
                contract_copy.waiting_on_id = contract_copy.target_id
            else:
                contract_copy.waiting_on_id = contract_copy.initiator_id

        elif action_command == 'CANCEL':
            contract_copy.status = 'CANCELED'
        elif action_command == 'FINALIZE':
            self._finalize_trade(contract_copy, user_id, data)

        # Check Legality
        if not contract_copy.is_legal(actor):
            return "ILLEGAL", original_contract

        # Save Changes
        self._add_contract_to_players(contract_copy)

        return f"UPDATED_{contract_copy.status}", contract_copy

    def _finalize_trade(self, contract_copy, user_id, data):
        """Handles the secret payload drop-off before the trade executes."""
        if contract_copy.type != 'TRADE':
            return

        if user_id == contract_copy.initiator_id:
            contract_copy.actual_offer_items = data.get(
                'actual_items', contract_copy.offer_items)
            contract_copy.initiator_finalized = True
        elif user_id == contract_copy.target_id:
            contract_copy.actual_request_items = data.get(
                'actual_items', contract_copy.request_items)
            contract_copy.target_finalized = True

        if contract_copy.initiator_finalized and contract_copy.target_finalized:
            contract_copy.status = 'COMPLETED'

    def _add_contract_to_players(self, contract_obj):
        initiator = self.players.get(contract_obj.initiator_id)
        target = self.players.get(contract_obj.target_id)

        # Maintained as '.actions' to prevent breaking dependencies in dtos.py or player.py
        if initiator:
            initiator.actions[contract_obj.id] = contract_obj
        if target:
            target.actions[contract_obj.id] = contract_obj

    def find_contract(self, contract_id):
        for player in self.players.values():
            if contract_id in getattr(player, 'actions', {}):
                return player.actions[contract_id]
        return None
