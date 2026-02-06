import uuid
import inspect
import copy
from datetime import datetime


class MessageFactory:
    def __init__(self, players):
        self.players = players

    def create_message(self, msg_data):
        """
        Creates a message and adds it to BOTH the sender's and recipient's 
        internal message lists.
        """
        new_message = self.serialize_message(msg_data)

        # Add to Sender
        sender = self.players.get(new_message.from_id)
        if sender:
            sender.messages[new_message.id] = new_message

        # Add to Recipient
        recipient = self.players.get(new_message.to_id)
        if recipient:
            recipient.messages[new_message.id] = new_message
            return True, new_message

        return False, None

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
        """
        Helper to find a message object by ID. 
        Scans players efficiently.
        """
        # We can iterate players, or if we know the context (user_id) we could look there.
        # Since msg_id is unique, we just need to find the first instance.
        for player in self.players.values():
            if msg_id in player.messages:
                return player.messages[msg_id]
        return None

    def update_msg(self, msg_id, user_id, action, values=None, game_phase=None):
        """
        1. Finds original message.
        2. Creates a COPY.
        3. Modifies data on the copy.
        4. Checks is_legal().
        5. If passed, saves copy back to players and handles side effects.
        """
        original_msg = self.find_message(msg_id)
        if not original_msg:
            return False

        # 1. Make a Copy
        msg_copy = copy.deepcopy(original_msg)
        actor = self.players.get(user_id)

        # 2. Modify Data (The "Update" Logic)
        if action == 'BARTER':
            if msg_copy.status not in ['PENDING', 'BARTERING']:
                return False

            # Apply values manually since message classes don't have update()
            if msg_copy.type == 'EMPLOYMENT':
                if 'wage_offer' in values:
                    msg_copy.wage_offer = int(values['wage_offer'])
                if 'wage_type' in values:
                    msg_copy.wage_type = values['wage_type']
            elif msg_copy.type == 'TRADE':
                if 'offer_items' in values:
                    msg_copy.offer_items = values['offer_items']
                if 'request_items' in values:
                    msg_copy.request_items = values['request_items']

            msg_copy.status = 'BARTERING'

        elif action == 'DENY':
            msg_copy.status = 'DENIED'

        elif action == 'ACCEPT':
            msg_copy.status = 'ACCEPTED'

        elif action == 'UPDATE_PAYLOAD':
            if msg_copy.from_id != user_id:
                return False
            if hasattr(msg_copy, 'actual_payout'):
                msg_copy.actual_payout = int(values.get('wage_offer', 0))
                msg_copy.actual_payout_type = values.get('wage_type', 'food')
            elif hasattr(msg_copy, 'actual_offer_items'):
                msg_copy.actual_offer_items = values.get('offer_items', {})

        # 3. Check Legality on the Copy
        # We pass the actor (the person doing the update) to validate ownership/rules
        if not msg_copy.is_legal(actor):
            return False

        # 4. Handle Side Effects (Logic moved from old update_msg)
        if action == 'ACCEPT':
            if game_phase == 'WORK' and msg_copy.type == 'EMPLOYMENT':
                # Lock the employee
                employee = self.players.get(msg_copy.to_id)
                if employee:
                    employee.action_locked = True

            if game_phase == 'NIGHT' and msg_copy.type == 'FIRE':
                beneficiary_id = msg_copy.to_id if msg_copy.action == 'INVITE' else msg_copy.from_id
                provider_id = msg_copy.from_id if msg_copy.action == 'INVITE' else msg_copy.to_id
                if beneficiary_id in self.players:
                    self.players[beneficiary_id].current_fire_host = provider_id

        elif action == 'EXECUTE':
            if msg_copy.type == 'EMPLOYMENT' and msg_copy.status == 'ACCEPTED':
                employer = self.players.get(msg_copy.from_id)
                employee = self.players.get(msg_copy.to_id)
                if employer and employee:
                    amt = msg_copy.actual_payout
                    res = msg_copy.actual_payout_type
                    if employer.resources.get(res, 0) >= amt:
                        employer.resources[res] -= amt
                        employee.resources[res] += amt
                        msg_copy.status = 'COMPLETED'
                    else:
                        return False  # Cannot afford

        # 5. Commit: Save the Copy back to BOTH players involved
        # This replaces the old object with the new state
        sender = self.players.get(msg_copy.from_id)
        recipient = self.players.get(msg_copy.to_id)

        if sender:
            sender.messages[msg_id] = msg_copy
        if recipient:
            recipient.messages[msg_id] = msg_copy

        return True

    def getClassType(self, type):
        return {
            'TEXT': TextMessage,
            'EMPLOYMENT': EmploymentOffer,
            'TRADE': TradeOffer,
            'FIRE': FireOffer,
        }.get(type)

# --- Message Classes (Unchanged but included for context) ---


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
        return True  # Default true


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
        # Only check legality if the player updating is the Employer (sender)
        # If the employee is accepting, they don't need to own the development
        if player.session_id == self.from_id:
            if str(self.dev_id) not in [str(d) for d in player.developments]:
                # Note: Assuming player.developments is list of IDs.
                # If it's list of objects, logic needs to match your Development class.
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
