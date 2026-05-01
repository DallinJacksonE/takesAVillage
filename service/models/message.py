import uuid
import copy
from datetime import datetime


# --- Barter Strategy Handlers ---

class BarterHandler:
    def apply_barter(self, _message, _data):
        raise NotImplementedError


class TradeBarterHandler(BarterHandler):
    def apply_barter(self, message, data):
        # Update the terms based on the incoming payload
        message.offer_items = data.get('offer_items', message.offer_items)
        message.request_items = data.get(
            'request_items', message.request_items
        )


class EmploymentBarterHandler(BarterHandler):
    def apply_barter(self, message, data):
        # Update the wages
        message.wage_offer = int(data.get('wage_offer', message.wage_offer))
        message.wage_type = data.get('wage_type', message.wage_type)


# --- Core Message Models ---

class Message:
    def __init__(self, from_id, to_id, msg_type, barter_handler=None):
        self.id = str(uuid.uuid4())
        self.from_id = from_id
        self.to_id = to_id
        self.type = msg_type
        self.status = 'PENDING'
        # The ball always starts in the receiver's court
        self.pending_action_from = to_id
        self.created_at = datetime.now()
        self.is_system = False
        self.barter_handler = barter_handler
        self.bartered = False

    def is_legal(self, _player) -> bool:
        return True

    def barter(self, data):
        if self.barter_handler:
            self.barter_handler.apply_barter(self, data)

        self.status = 'BARTERING'
        self.bartered = True
        # Flip the ball into the other player's court
        if self.pending_action_from == self.from_id:
            self.pending_action_from = self.to_id
        else:
            self.pending_action_from = self.from_id


class TextMessage(Message):
    def __init__(self, from_id, to_id, content):
        super().__init__(from_id, to_id, 'TEXT')
        self.content = content


class EmploymentOffer(Message):
    def __init__(self, from_id, to_id, dev_id, wage_offer, wage_type):
        super().__init__(
            from_id, to_id, 'EMPLOYMENT', EmploymentBarterHandler()
        )
        self.dev_id = dev_id
        self.wage_offer = int(wage_offer) if wage_offer is not None else 0
        self.wage_type = wage_type
        self.actual_payout = self.wage_offer
        self.actual_payout_type = self.wage_type

    def is_legal(self, player):
        # Only the employer needs to own the dev to validate the offer
        if player.session_id == self.from_id:
            if str(self.dev_id) not in [str(d) for d in player.developments]:
                return False
        return True


class TradeOffer(Message):
    def __init__(self, from_id, to_id, offer_items, request_items):
        super().__init__(from_id, to_id, 'TRADE', TradeBarterHandler())
        self.offer_items = offer_items or {}
        self.request_items = request_items or {}
        self.actual_offer_items = self.offer_items.copy()
        self.actual_request_items = self.request_items.copy()
        self.sender_finalized = False
        self.recipient_finalized = False


class FireOffer(Message):
    def __init__(self, from_id, to_id, action):
        super().__init__(from_id, to_id, 'FIRE')
        self.action = action

    def is_legal(self, player):
        if self.action == 'INVITE' and player.session_id == self.from_id:
            return not player.hosting_fire
        return True


# --- Factory ---

class MessageFactory:
    def __init__(self, players):
        self.players = players

    def process_message(self, user_id, data):
        """
        Unified entry point.
        """
        msg_id = data.get('id') or data.get('msgId')

        if msg_id and self.find_message(msg_id):
            return self._update_message(user_id, msg_id, data)
        else:
            return self._create_message(data)

    def _create_message(self, msg_data):
        """Creates a new message and adds it to players."""
        try:
            new_message = self.build_message_from_data(msg_data)
        except ValueError as e:
            print(f"Error creating message: {e}")
            return "ERROR", None

        # Add to Sender
        sender = self.players.get(new_message.from_id)
        if sender:
            sender.messages[new_message.id] = new_message

        # Add to Recipient
        recipient = self.players.get(new_message.to_id)
        if recipient:
            recipient.messages[new_message.id] = new_message
            return "CREATED", new_message

        return "ERROR", None

    def build_message_from_data(self, data):
        """Explicitly maps incoming data to the correct domain object."""
        msg_type = data.get('type')
        from_id = data.get('from_id')
        to_id = data.get('to_id')

        if msg_type == 'TEXT':
            return TextMessage(from_id, to_id, data.get('content', ''))

        elif msg_type == 'EMPLOYMENT':
            return EmploymentOffer(
                from_id,
                to_id,
                data.get('dev_id'),
                data.get('wage_offer'),
                data.get('wage_type')
            )

        elif msg_type == 'TRADE':
            return TradeOffer(
                from_id,
                to_id,
                data.get('offer_items', {}),
                data.get('request_items', {}),
            )

        elif msg_type == 'FIRE':
            return FireOffer(from_id, to_id, data.get('action'))

        else:
            raise ValueError(f"Unknown message type: {msg_type}")

    def _update_message(self, user_id, msg_id, data):
        original_msg = self.find_message(msg_id)
        if not original_msg:
            return "NOT_FOUND", None

        msg_copy = copy.deepcopy(original_msg)
        actor = self.players.get(user_id)
        action = data.get('action')

        # Apply Actions (extracted to lower complexity)
        if action == 'BARTER':
            msg_copy.barter(data)
        elif action == 'DENY':
            msg_copy.status = 'DENIED'
        elif action == 'ACCEPT':
            msg_copy.status = 'ACCEPTED'
        elif action == 'FINALIZE':
            self._finalize_trade(msg_copy, user_id, data)

        # 3. Check Legality
        if not msg_copy.is_legal(actor):
            return "ILLEGAL", original_msg

        # 4. Save Changes
        sender = self.players.get(msg_copy.from_id)
        recipient = self.players.get(msg_copy.to_id)

        if sender:
            sender.messages[msg_id] = msg_copy
        if recipient:
            recipient.messages[msg_id] = msg_copy

        # 5. Return Status for Side Effects
        if action == 'ACCEPT' and msg_copy.type == 'EMPLOYMENT':
            return "ACCEPTED_EMPLOYMENT", msg_copy
        elif (action == 'FINALIZE' and msg_copy.type == 'TRADE'
              and msg_copy.status == 'COMPLETED'):
            return "TRADE_COMPLETED", msg_copy

        return "UPDATED", msg_copy

    def _finalize_trade(self, msg_copy, user_id, data):
        """Helper to process trade finalization steps"""
        if msg_copy.type != 'TRADE':
            return

        if user_id == msg_copy.from_id:
            msg_copy.actual_offer_items = data.get(
                'actual_items',
                getattr(msg_copy, 'actual_offer_items', msg_copy.offer_items)
            )
            msg_copy.sender_finalized = True
        elif user_id == msg_copy.to_id:
            msg_copy.actual_request_items = data.get(
                'actual_items',
                getattr(msg_copy, 'actual_request_items',
                        msg_copy.request_items)
            )
            msg_copy.recipient_finalized = True

        if getattr(msg_copy, 'sender_finalized', False) and \
           getattr(msg_copy, 'recipient_finalized', False):
            msg_copy.status = 'COMPLETED'

    def _add_message_to_players(self, message):
        sender = self.players.get(message.from_id)
        recipient = self.players.get(message.to_id)
        if sender:
            sender.messages[message.id] = message
        if recipient:
            recipient.messages[message.id] = message

    def find_message(self, msg_id):
        for player in self.players.values():
            if msg_id in player.messages:
                return player.messages[msg_id]
        return None
