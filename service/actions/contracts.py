import uuid
from datetime import datetime


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

        # The Command Map: Routes action commands to specific class methods
        self.command_map = {
            'DENY': self._handle_deny,
            'CANCEL': self._handle_cancel
        }

    def process_action(self, action_command, user_id, data, context):
        """Unified handler that routes commands using the command map."""
        handler = self.command_map.get(action_command)

        if not handler:
            print(f"Action '{action_command}' not supported by"
                  f" {self.__class__.__name__}.")
            return "ERROR"

        # Execute the mapped function and return the resulting status string
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

        # Register specific commands for trade
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

        # Flip the turn based on who sent the counter-offer
        if user_id == self.initiator_id:
            self.waiting_on_id = self.target_id
        else:
            self.waiting_on_id = self.initiator_id

        return f"UPDATED_{self.status}"

    def _handle_finalize(self, user_id, data, context):
        """Handles the secret payload drop-off before the trade executes."""
        if user_id == self.initiator_id:
            self.actual_offer_items = data.get(
                'actual_items', self.offer_items)
            self.initiator_finalized = True
        elif user_id == self.target_id:
            self.actual_request_items = data.get(
                'actual_items', self.request_items)
            self.target_finalized = True

        if self.initiator_finalized and self.target_finalized:
            self.status = 'COMPLETED'
            return "UPDATED_COMPLETED"

        return f"UPDATED_{self.status}"


class EmploymentContract(Contract):
    def __init__(self, initiator_id, target_id, dev_id, wage, wage_type, is_application=False):
        super().__init__(initiator_id, target_id, 'EMPLOYMENT')
        self.dev_id = dev_id
        self.wage = int(wage) if wage is not None else 0
        self.wage_type = wage_type
        self.is_application = is_application

        # Register the specific ACCEPT command for employment
        self.command_map['ACCEPT'] = self._handle_accept

    def _handle_accept(self, user_id, data, context):
        # 1. Define roles based on whether this is an application or an offer
        if self.is_application:
            # The initiator (worker) applied. The target (employer) must accept.
            employer_id = self.target_id
            worker_id = self.initiator_id
        else:
            # The initiator (employer) sent an offer. The target (worker) must accept.
            employer_id = self.initiator_id
            worker_id = self.target_id

        # 2. Strict Validation: Only the target can accept the contract
        if user_id != self.target_id:
            print(f"Action Denied: User "
                  f"{user_id} is not authorized to accept this contract.")
            return "ILLEGAL"

        # 3. Bind the worker to the development
        developments = context.get('developments', {})
        development = developments.get(self.dev_id)

        if development:
            development.worker_id = worker_id
            print(f"Successfully bound Worker "
                  f"{worker_id} to Development {self.dev_id}")
        else:
            print(f"Warning: Development "
                  f"{self.dev_id} not found during contract acceptance.")

        # 4. Finalize the state
        self.status = 'ACCEPTED'
        self.waiting_on_id = None

        return f"UPDATED_{self.status}"

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

        self.command_map['ACCEPT'] = self._handle_accept

    def _handle_accept(self, user_id, data, context):
        self.status = 'ACCEPTED'
        self.waiting_on_id = None
        return f"UPDATED_{self.status}"

    def is_legal(self, player):
        # If it's an offer, the initiator must not be actively hosting another fire
        if not self.is_request and player.session_id == self.initiator_id:
            return not getattr(player, 'hosting_fire', False)
        return True
