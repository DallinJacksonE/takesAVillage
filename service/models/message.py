import uuid
import inspect
import copy
from datetime import datetime


class MessageFactory:
    def __init__(self, players):
        self.players = players

    def process_message(self, user_id, data):
        """
        Unified entry point.
        If 'id' exists in data, it updates the existing message.
        Otherwise, it creates a new one.
        Returns: (status_code, message_object)
        """
        msg_id = data.get('id') or data.get('msgId')

        if msg_id and self.find_message(msg_id):
            return self._update_message(user_id, msg_id, data)
        else:
            return self._create_message(data)

    def _create_message(self, msg_data):
        """Creates a new message and adds it to players."""
        try:
            new_message = self.serialize_message(msg_data)
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

    def _update_message(self, user_id, msg_id, data):
        """Updates an existing message based on action (ACCEPT, DENY, BARTER)."""
        original_msg = self.find_message(msg_id)
        if not original_msg:
            return "NOT_FOUND", None

        # 1. Work on a copy
        msg_copy = copy.deepcopy(original_msg)
        actor = self.players.get(user_id)
        action = data.get('action')

        # 2. Apply Changes
        if action == 'BARTER':
            if msg_copy.status not in ['PENDING', 'BARTERING']:
                return "INVALID_STATE", msg_copy

            # Update fields based on provided data
            if msg_copy.type == 'EMPLOYMENT':
                msg_copy.wage_offer = int(
                    data.get('wage_offer', msg_copy.wage_offer))
                msg_copy.wage_type = data.get('wage_type', msg_copy.wage_type)
            elif msg_copy.type == 'TRADE':
                msg_copy.offer_items = data.get(
                    'offer_items', msg_copy.offer_items)
                msg_copy.request_items = data.get(
                    'request_items', msg_copy.request_items)

            msg_copy.status = 'BARTERING'

        elif action == 'DENY':
            msg_copy.status = 'DENIED'

        elif action == 'ACCEPT':
            msg_copy.status = 'ACCEPTED'

        elif action == 'EXECUTE':
            # Internal system action usually, but can be triggered here
            pass

        # 3. Check Legality
        if not msg_copy.is_legal(actor):
            return "ILLEGAL", original_msg

        # 4. Save Changes (Replace old message)
        sender = self.players.get(msg_copy.from_id)
        recipient = self.players.get(msg_copy.to_id)

        if sender:
            sender.messages[msg_id] = msg_copy
        if recipient:
            recipient.messages[msg_id] = msg_copy

        # 5. Return Status for Side Effects
        if action == 'ACCEPT' and msg_copy.type == 'EMPLOYMENT':
            return "ACCEPTED_EMPLOYMENT", msg_copy

        return "UPDATED", msg_copy

    def serialize_message(self, msg_data):
        msg_type = msg_data.get('type')
        message_class = self.getClassType(msg_type)
        if not message_class:
            raise ValueError(f"Unknown message type: {msg_type}")

        init_signature = inspect.signature(message_class.__init__)
        expected_args = [
            p.name for p in init_signature.parameters.values() if p.name != 'self']
        constructor_inputs = {k: msg_data[k]
                              for k in expected_args if k in msg_data}
        return message_class(**constructor_inputs)

    def find_message(self, msg_id):
        for player in self.players.values():
            if msg_id in player.messages:
                return player.messages[msg_id]
        return None

    def getClassType(self, type):
        return {
            'TEXT': TextMessage,
            'EMPLOYMENT': EmploymentOffer,
            'TRADE': TradeOffer,
            'FIRE': FireOffer,
        }.get(type)

# --- Message Classes ---


class Message:
    def __init__(self, from_id, to_id, type):
        self.id = str(uuid.uuid4())
        self.from_id = from_id
        self.to_id = to_id
        self.type = type
        self.status = 'PENDING'
        self.created_at = datetime.now()
        self.is_system = False

    def to_dict(self):
        return {
            "id": self.id,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "type": self.type,
            "status": self.status,
            "is_system": self.is_system
        }

    def is_legal(self, player):
        return True


class TextMessage(Message):
    def __init__(self, from_id, to_id, content):
        super().__init__(from_id, to_id, 'TEXT')
        self.content = content

    def to_dict(self):
        data = super().to_dict()
        data['content'] = self.content
        return data


class EmploymentOffer(Message):
    def __init__(self, from_id, to_id, dev_id, wage_offer, wage_type):
        super().__init__(from_id, to_id, 'EMPLOYMENT')
        self.dev_id = dev_id
        self.wage_offer = int(wage_offer)
        self.wage_type = wage_type
        self.actual_payout = self.wage_offer
        self.actual_payout_type = self.wage_type

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "dev_id": self.dev_id,
            "wage_offer": self.wage_offer,
            "wage_type": self.wage_type,
        })
        return data

    def is_legal(self, player):
        # Only sender needs to own the dev to update terms.
        # Receiver accepting doesn't need ownership.
        if player.session_id == self.from_id:
            if str(self.dev_id) not in [str(d) for d in player.developments]:
                return False
        return True


class TradeOffer(Message):
    def __init__(self, from_id, to_id, offer_items, request_items):
        super().__init__(from_id, to_id, 'TRADE')
        self.offer_items = offer_items
        self.request_items = request_items
        self.actual_offer_items = offer_items.copy()

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "offer_items": self.offer_items,
            "request_items": self.request_items
        })
        return data


class FireOffer(Message):
    def __init__(self, from_id, to_id, action):
        super().__init__(from_id, to_id, 'FIRE')
        self.action = action

    def to_dict(self):
        data = super().to_dict()
        data['action'] = self.action
        return data

    def is_legal(self, player):
        if self.action == 'INVITE' and player.session_id == self.from_id:
            return not player.hosting_fire
        return True
