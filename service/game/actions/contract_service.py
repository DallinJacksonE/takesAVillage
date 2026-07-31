import copy
from .contracts import EmploymentContract, TradeContract, CampfireContract
from service.logging import BackendLogger

cf_logger = BackendLogger("contracts")


class ContractFactory:
    def __init__(self, players, developments, game):
        self.players = players
        self.developments = developments
        self.game = game

    def process_contract(self, user_id, data, action_command=None):
        contract_id = data.get('action_id') or data.get(
            'id') or data.get('contractId') or data.get('actionId')
        existing_contract = self.find_contract(contract_id) if contract_id else None

        # Contract commands always update the referenced shared contract.
        if action_command in [
                "ACCEPT", "DENY", "FINALIZE", "BARTER", "CANCEL"]:
            if not existing_contract:
                cf_logger.error(
                    f"Cannot update missing contract {contract_id}: {data}"
                )
                return "NOT_FOUND", None

            return self._update_contract(
                user_id,
                contract_id,
                data,
                action_command
            )

        # Only creation actions come here
        return self._create_contract(user_id, data)

    def _create_contract(self, user_id, data):
        try:
            new_contract = self._build_contract_from_data(user_id, data)
        except ValueError as e:
            cf_logger.error("Error creating contract", exc=e)
            return "ERROR", None

        self._add_contract_to_players(new_contract)
        return "CREATED", new_contract

    def _build_contract_from_data(self, user_id, data):
        contract_type = data.get('type')
        initiator_id = user_id
        target_id = data.get('target_id') or data.get('to_id')
        initiator = self.players.get(initiator_id)

        if not contract_type:
            cf_logger.error(
                f"Missing contract type. user={user_id}, data={data}"
            )
            raise ValueError("Missing contract type")

        if contract_type == 'EMPLOYMENT':
            is_application = data.get('is_application', False)
            employer_id = target_id if is_application else initiator_id
            development = self.developments.get(data.get('dev_id'))
            if (not development
                    or development.owner != employer_id):
                raise ValueError("Employment development is not owned by employer")
            return EmploymentContract(initiator_id, target_id, data.get('dev_id'), data.get('wage'), data.get('wage_type'), data.get('is_application', False))
        elif contract_type == 'TRADE':
            return TradeContract(initiator_id, target_id, data.get('offer_items', {}), data.get('request_items', {}))
        elif contract_type == 'CAMPFIRE':
            is_request = data.get('is_request', False)
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
        action_command = provided_action_command or data.get('action_command')

        if actor is None or user_id not in {
                original_contract.initiator_id, original_contract.target_id}:
            return "ILLEGAL", original_contract
        if action_command in {"ACCEPT", "DENY", "BARTER"}:
            if original_contract.status != "PENDING":
                return "ILLEGAL", original_contract
            if original_contract.waiting_on_id != user_id:
                return "ILLEGAL", original_contract
        elif action_command == "CANCEL":
            if (original_contract.status != "PENDING"
                    or user_id != original_contract.initiator_id):
                return "ILLEGAL", original_contract
        elif action_command == "FINALIZE":
            if original_contract.status != "ACCEPTED":
                return "ILLEGAL", original_contract

        if (getattr(original_contract, "type", None) == "EMPLOYMENT"
                and action_command == "ACCEPT"):
            employer_id = (
                original_contract.target_id
                if original_contract.is_application
                else original_contract.initiator_id
            )
            development = self.developments.get(original_contract.dev_id)
            if not development or development.owner != employer_id:
                return "ILLEGAL", original_contract

        cf_logger.info(f"Executing Contract Action: {action_command}")

        context = {'players': self.players, 'developments': self.developments, 'game': self.game}
        status = contract_copy.process_action(
            action_command, user_id, data, context)

        if status == "ERROR":
            return "ERROR", original_contract
        if status == "ILLEGAL" or not contract_copy.is_legal(actor):
            return "ILLEGAL", original_contract

        self._add_contract_to_players(contract_copy)
        return status, contract_copy

    def _add_contract_to_players(self, contract_obj):
        initiator = self.players.get(contract_obj.initiator_id)
        target = self.players.get(contract_obj.target_id)
        if initiator:
            initiator.actions[contract_obj.id] = contract_obj
        if target:
            target.actions[contract_obj.id] = contract_obj

    def cleanup_campfire_contracts(self):
        campfire_ids = {
            contract.id for player in self.players.values() for contract in player.actions.values() if getattr(contract, 'type', None) == 'CAMPFIRE'
        }
        if not campfire_ids:
            return 0
        for player in self.players.values():
            for action_id in list(player.actions.keys()):
                if action_id in campfire_ids:
                    del player.actions[action_id]
        return len(campfire_ids)

    def cleanup_end_of_phase(self):
        for player in self.players.values():
            for action_id in list(player.actions.keys()):
                contract = player.actions[action_id]
                if getattr(contract, 'type', None) == 'EMPLOYMENT':
                    del player.actions[action_id]
                elif contract.status in ['PENDING', 'NEGOTIATING']:
                    contract.status = 'EXPIRED'
                    contract.waiting_on_id = None

    def find_contract(self, contract_id):
        for player in self.players.values():
            if contract_id in getattr(player, 'actions', {}):
                return player.actions[contract_id]
        return None
