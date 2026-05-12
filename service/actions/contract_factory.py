import copy
from .contracts import EmploymentContract, TradeContract, CampfireContract


class ContractFactory:
    def __init__(self, players):
        self.players = players

    def process_contract(self, user_id, data, action_command=None):
        """Unified entry point for drafting or updating a contract."""

        # Add 'action_id' to the list of keys
        contract_id = data.get('action_id') or data.get(
            'id') or data.get('contractId') or data.get('actionId')

        if contract_id and self.find_contract(contract_id):
            # Pass action_command down to the update logic
            return self._update_contract(user_id, contract_id, data, action_command)
        else:
            return self._create_contract(user_id, data)

    def _create_contract(self, user_id, data):
        try:
            new_contract = self._build_contract_from_data(user_id, data)
        except ValueError as e:
            print(f"Error creating contract: {e}")
            return "ERROR", None

        self._add_contract_to_players(new_contract)
        return "CREATED", new_contract

    def _build_contract_from_data(self, user_id, data):
        contract_type = data.get('type')

        initiator_id = user_id
        target_id = data.get('target_id') or data.get('to_id')
        initiator = self.players.get(initiator_id)

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
            is_request = data.get('is_request', False)
            # Only allow HOST players to offer seats (is_request=False)
            if not is_request and initiator and getattr(initiator, 'fire_status', 'COLD') != 'HOST':
                raise ValueError("Only hosts can offer seats")
            return CampfireContract(initiator_id, target_id, is_request)
        else:
            raise ValueError(f"Unknown contract type: {contract_type}")

    def _update_contract(self, user_id, contract_id, data, provided_action_command=None):
        original_contract = self.find_contract(contract_id)
        if not original_contract:
            return "NOT_FOUND", None

        contract_copy = copy.deepcopy(original_contract)
        actor = self.players.get(user_id)

        # Use the provided command first, fallback to data dict for older calls
        action_command = provided_action_command or data.get(
            'action_command') or data.get('actionCommand')
        print(f"Executing Contract Action: {action_command}")

        # Apply Lifecycle Changes
        if action_command == 'DENY':
            contract_copy.status = 'DENIED'
            contract_copy.waiting_on_id = None

        elif action_command == 'ACCEPT':
            contract_copy.status = 'ACCEPTED'
            contract_copy.waiting_on_id = None

            # NEW: Handle Employment binding
            if getattr(contract_copy, 'type', None) == 'EMPLOYMENT':
                dev_id = getattr(contract_copy, 'dev_id', None)
                if dev_id and dev_id in self.developments:
                    development = self.developments[dev_id]
                    # If it's an application, the initiator is the worker.
                    # If it's an offer, the target is the worker.
                    if getattr(contract_copy, 'is_application', False):
                        development.worker_id = contract_copy.initiator_id
                    else:
                        development.worker_id = contract_copy.target_id

        elif action_command == 'BARTER':
            contract_copy.offer_items = data.get(
                'offer_items', contract_copy.offer_items)
            contract_copy.request_items = data.get(
                'request_items', contract_copy.request_items)

            if user_id == contract_copy.initiator_id:
                contract_copy.waiting_on_id = contract_copy.target_id
            else:
                contract_copy.waiting_on_id = contract_copy.initiator_id

        elif action_command == 'CANCEL':
            contract_copy.status = 'CANCELED'
            contract_copy.waiting_on_id = None

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

    def cleanup_campfire_contracts(self):
        campfire_ids = {
            contract.id
            for player in self.players.values()
            for contract in player.actions.values()
            if getattr(contract, 'type', None) == 'CAMPFIRE'
        }

        if not campfire_ids:
            return 0

        for player in self.players.values():
            for action_id in list(player.actions.keys()):
                if action_id in campfire_ids:
                    del player.actions[action_id]

        return len(campfire_ids)

    def cleanup_pending_contracts(self):
        """Sweeps all unaccepted trades and employment offers at the end of a phase."""
        for player in self.players.values():
            for contract in list(getattr(player, 'actions', {}).values()):
                if contract.status in ['PENDING', 'NEGOTIATING']:
                    contract.status = 'EXPIRED'
                    contract.waiting_on_id = None

    def find_contract(self, contract_id):
        for player in self.players.values():
            if contract_id in getattr(player, 'actions', {}):
                return player.actions[contract_id]
        return None
