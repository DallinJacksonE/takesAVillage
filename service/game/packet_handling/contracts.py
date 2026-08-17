import math
import uuid
from datetime import datetime
from service.game.state.events import PlayerResourcesTransferred, TradeFinalized
from service.logging import BackendLogger

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
        self.status = 'DENIED'
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

            target_lied = self.actual_request_items != self.request_items
            initiator_lied = self.actual_offer_items != self.offer_items
            
            contract_logger.info(
                f"Lie count after finalize: {game.lie_count}"
            )

            self.status = "FINALIZED"
            self.waiting_on_id = None
            game.apply_event(TradeFinalized(
                self.id,
                initiator_lied=initiator_lied,
                target_lied=target_lied,
            ))
            return "UPDATED_FINALIZED"

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
        from service.game.packet_handling.campfire import seat_guest

        if not seat_guest(context["game"], self):
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


def execute_trade(game_state, action):
    initiator = game_state.players.get(action.initiator_id)
    target = game_state.players.get(action.target_id)
    if not initiator or not target:
        return False

    if any(record.get("id") == action.id
           for record in initiator.trade_history):
        return False
    if any(record.get("id") == action.id
           for record in target.trade_history):
        return False

    item_groups = (
        getattr(action, 'actual_offer_items', {}),
        getattr(action, 'actual_request_items', {}),
    )
    if any(
        not isinstance(resource, str)
        or isinstance(amount, bool)
        or not isinstance(amount, (int, float))
        or not math.isfinite(amount)
        or amount < 0
        for items in item_groups
        for resource, amount in items.items()
    ):
        return False

    initiator_box = {}
    for resource, amount in getattr(
            action, 'actual_offer_items', {}).items():
        transferred = min(amount, initiator.resources.get(resource, 0))
        initiator_box[resource] = transferred

    target_box = {}
    for resource, amount in getattr(
            action, 'actual_request_items', {}).items():
        transferred = min(amount, target.resources.get(resource, 0))
        target_box[resource] = transferred

    transfer_events = []
    if initiator_box:
        transfer_events.append(PlayerResourcesTransferred(
            initiator.session_id,
            target.session_id,
            initiator_box.copy(),
        ))
    if target_box:
        transfer_events.append(PlayerResourcesTransferred(
            target.session_id,
            initiator.session_id,
            target_box.copy(),
        ))
    game_state.apply_events(transfer_events)

    initiator.add_timeline_event(
        "TRADE_RESOLVED",
        {"trade_id": action.id,
         "sent": initiator_box,
         "received": target_box})
    target.add_timeline_event(
        "TRADE_RESOLVED",
        {"trade_id": action.id,
         "sent": target_box,
         "received": initiator_box})

    initiator.trade_history.append({
        "id": action.id,
        "initiator_id": action.initiator_id,
        "target_id": action.target_id,
        "offered": action.offer_items,
        "requested": action.request_items,
        "actual_sent": initiator_box,
        "actual_received": target_box,
    })
    target.trade_history.append({
        "id": action.id,
        "initiator_id": action.target_id,
        "target_id": action.initiator_id,
        "offered": action.request_items,
        "requested": action.offer_items,
        "actual_sent": target_box,
        "actual_received": initiator_box,
    })
    initiator.trade_count += 1
    target.trade_count += 1
    return True

