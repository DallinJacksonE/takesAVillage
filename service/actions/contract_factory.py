import copy
from .contracts import EmploymentContract, TradeContract, CampfireContract
from logger import BackendLogger

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

# ACCEPT/DENY/FINALIZE must always update existing contracts
        if action_command in ["ACCEPT", "DENY", "FINALIZE"]:
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

    def _finalize_trade(self, contract_copy, user_id, data):
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
        
        if contract_copy.actual_request_items != contract_copy.request_items:
            self.game.lie_count[contract_copy.target_id] = self.game.lie_count.get(contract_copy.target_id, 0) + 1

        if contract_copy.actual_offer_items != contract_copy.offer_items:
            self.game.lie_count[contract_copy.initiator_id] = self.game.lie_count.get(contract_copy.initiator_id, 0) + 1
            
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
