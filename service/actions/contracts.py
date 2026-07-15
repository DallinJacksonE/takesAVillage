import uuid
from datetime import datetime
from logger import BackendLogger

contract_logger = BackendLogger("contracts")


class Contract:
    def __init__(self, initiator_id, target_id, contract_type):
        self.id = str(uuid.uuid4())
        self.initiator_id = initiator_id
        self.target_id = target_id
        self.waiting_on_id = target_id
        self.type = contract_type
        self.status = 'PENDING'
        self.created_at = datetime.now()
        # self.just_completed = False
        self.command_map = {'DENY': self._handle_deny,
                            'CANCEL': self._handle_cancel}

    def to_dict(self) -> dict:
        return {"id": self.id, "initiator_id": self.initiator_id, "target_id": self.target_id, "type": self.type, "status": self.status, "waiting_on_id": self.waiting_on_id}

    def process_action(self, action_command, user_id, data, context):
        handler = self.command_map.get(action_command)
        if not handler:
            contract_logger.warning(f"Action '{action_command}' not supported by "
                                    f"{self.__class__.__name__}.")
            return "ERROR"
        return handler(user_id, data, context)

    def _handle_deny(self, user_id, data, context):
        self.status = 'DENIED'
        self.waiting_on_id = None
        return f"UPDATED_{self.status}"

    def _handle_cancel(self, user_id, data, context):
        self.status = 'CANCELED'
        self.waiting_on_id = None
        return f"UPDATED_{self.status}"

    def is_legal(self, player) -> bool:
        return True


class TradeContract(Contract):
    def __init__(self, initiator_id, target_id, offer_items, request_items):
        super().__init__(initiator_id, target_id, 'TRADE')
        self.offer_items = offer_items or {}
        self.request_items = request_items or {}
        self.actual_offer_items = self.offer_items.copy()
        self.actual_request_items = self.request_items.copy()
        self.initiator_finalized = False
        self.target_finalized = False
        self.command_map['BARTER'] = self._handle_barter
        self.command_map['FINALIZE'] = self._handle_finalize
        self.command_map['ACCEPT'] = self._handle_accept

    def _handle_accept(self, user_id, data, context):
        self.status = 'ACCEPTED'
        self.waiting_on_id = None
        return f"UPDATED_{self.status}"

    def _handle_barter(self, user_id, data, context):
        self.offer_items = data.get('offer_items', self.offer_items)
        self.request_items = data.get('request_items', self.request_items)
        if user_id == self.initiator_id:
            self.waiting_on_id = self.target_id
        else:
            self.waiting_on_id = self.initiator_id
        return f"UPDATED_{self.status}"

    def _handle_finalize(self, user_id, data, context):
        if user_id == self.initiator_id and self.initiator_finalized:
            return "ILLEGAL"
        if user_id == self.target_id and self.target_finalized:
            return "ILLEGAL"

        if user_id == self.initiator_id:
            self.actual_offer_items = data.get(
                'actual_items', self.offer_items)
            self.initiator_finalized = True
        elif user_id == self.target_id:
            self.actual_request_items = data.get(
                'actual_items', self.request_items)
            self.target_finalized = True

        game = context['game']

        if self.initiator_finalized and self.target_finalized:

            if self.actual_request_items != self.request_items:
                game.lie_count[self.target_id] = (
                    game.lie_count.get(self.target_id, 0) + 1
                )

            if self.actual_offer_items != self.offer_items:
                game.lie_count[self.initiator_id] = (
                    game.lie_count.get(self.initiator_id, 0) + 1
                )
            
            contract_logger.info(
                f"Lie count after finalize: {game.lie_count}"
            )

            self.status = "COMPLETED"
            self.waiting_on_id = None
            game.trade_count += 1
            return "UPDATED_COMPLETED"

        return f"UPDATED_{self.status}"

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({"offer_items": getattr(self, 'offer_items', {}), "request_items": getattr(self, 'request_items', {}), "actual_offer_items": getattr(self, 'actual_offer_items', {}), "actual_request_items": getattr(
            self, 'actual_request_items', {}), "initiator_finalized": getattr(self, 'initiator_finalized', False), "target_finalized": getattr(self, 'target_finalized', False)}) # "just_completed": getattr(self, 'just_completed', False)}
        return base


class EmploymentContract(Contract):
    def __init__(self, initiator_id, target_id, dev_id, wage, wage_type, is_application=False):
        super().__init__(initiator_id, target_id, 'EMPLOYMENT')
        self.dev_id = dev_id
        self.wage = int(wage) if wage is not None else 0
        self.wage_type = wage_type
        self.is_application = is_application
        self.command_map['ACCEPT'] = self._handle_accept

    def _handle_accept(self, user_id, data, context):
        players = context.get('players', {})
        developments = context.get('developments', {})
        worker_id = self.initiator_id if getattr(
            self, 'is_application', False) else self.target_id
        employer_id = self.target_id if getattr(
            self, 'is_application', False) else self.initiator_id
        worker = players.get(worker_id)
        employer = players.get(employer_id)
        development = developments.get(self.dev_id)

        if development:
            development.worker_id = worker_id
            contract_logger.info(f"Successfully bound Worker "
                                 f"{worker_id} to Development {self.dev_id}")
            if worker:
                hired_job = {"development": development.to_dict() if hasattr(development, 'to_dict') else development.__dict__, "wage": getattr(
                    self, 'wage', 1), "wage_type": getattr(self, 'wage_type', 'food'), "employer_id": employer_id, "action_id": self.id}
                if not hasattr(worker, 'available_work'):
                    worker.available_work = []
                worker.available_work.append(hired_job)
                try:
                    wage_amt = int(getattr(self, 'wage', 0))
                except Exception:
                    wage_amt = 0
                if wage_amt > 0 and isinstance(employer_id, str) and employer_id.startswith("bot_"):
                    trade = TradeContract(employer_id, worker_id, {
                                          getattr(self, 'wage_type', 'food'): wage_amt}, {})
                    if worker:
                        if not hasattr(worker, 'actions'):
                            worker.actions = {}
                        worker.actions[trade.id] = trade
                    if employer:
                        if not hasattr(employer, 'actions'):
                            employer.actions = {}
                        employer.actions[trade.id] = trade
        else:
            contract_logger.warning(
                f"Development {self.dev_id} not found during contract acceptance.")

        self.status = 'ACCEPTED'
        self.waiting_on_id = None
        return f"UPDATED_{self.status}"

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({"dev_id": getattr(self, 'dev_id', None), "wage": getattr(self, 'wage', None), "wage_type": getattr(
            self, 'wage_type', None), "is_application": getattr(self, 'is_application', False)})
        return base

    def is_legal(self, player):
        employer_id = self.target_id if self.is_application else self.initiator_id
        if player.session_id == employer_id:
            if str(self.dev_id) not in [str(d) for d in getattr(player, 'developments', [])]:
                return False
        return True


class CampfireContract(Contract):
    def __init__(self, initiator_id, target_id, is_request=False):
        super().__init__(initiator_id, target_id, 'CAMPFIRE')
        self.is_request = is_request
        self.command_map['ACCEPT'] = self._handle_accept

    def _handle_accept(self, user_id, data, context):
        if self.status != "PENDING":
            contract_logger.info(f"Ignoring duplicate ACCEPT for contract "
                                 f"{self.id} (status={self.status})")
            return "ILLEGAL"
        self.status = 'ACCEPTED'
        self.waiting_on_id = None
        return f"UPDATED_{self.status}"

    def to_dict(self) -> dict:
        base = super().to_dict()
        base.update({"is_request": getattr(self, 'is_request', False)})
        return base

    def is_legal(self, player):
        if not self.is_request and player.session_id == self.initiator_id:
            return not getattr(player, 'hosting_fire', False)
        return True
