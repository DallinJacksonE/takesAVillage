import uuid
from datetime import datetime


class Contract:
    """Multi-step agreements between players."""

    def __init__(self, initiator_id, target_id, contract_type):
        self.id = str(uuid.uuid4())
        self.initiator_id = initiator_id
        self.target_id = target_id

        self.waiting_on_id = target_id

        self.type = contract_type
        # Status Lifecycle: PENDING -> ACCEPTED -> DENIED | CANCELED | COMPLETED
        self.status = 'PENDING'
        self.created_at = datetime.now()

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


class EmploymentContract(Contract):
    def __init__(self, initiator_id, target_id, dev_id, wage, wage_type, is_application=False):
        super().__init__(initiator_id, target_id, 'EMPLOYMENT')
        self.dev_id = dev_id
        self.wage = int(wage) if wage is not None else 0
        self.wage_type = wage_type
        self.is_application = is_application

    def is_legal(self, player):
        # The employer must own the development to hire someone
        employer_id = self.target_id if self.is_application else self.initiator_id
        if player.session_id == employer_id:
            if str(self.dev_id) not in [str(d) for d in getattr(player, 'developments', [])]:
                return False
        return True


class CampfireContract(Contract):
    def __init__(self, initiator_id, target_id, is_request=False):
        super().__init__(initiator_id, target_id, 'CAMPFIRE')
        self.is_request = is_request

    def is_legal(self, player):
        # If it's an offer, the initiator must not be actively hosting another fire
        if not self.is_request and player.session_id == self.initiator_id:
            return not getattr(player, 'hosting_fire', False)
        return True
