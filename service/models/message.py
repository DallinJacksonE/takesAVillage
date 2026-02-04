import uuid
from datetime import datetime


class Message:
    def __init__(self, from_id, to_id, type):
        self.id = str(uuid.uuid4())
        self.from_id = from_id
        self.to_id = to_id
        self.type = type  # 'TEXT', 'EMPLOYMENT', 'TRADE', 'FIRE'
        self.status = 'PENDING'  # PENDING, BARTERING, ACCEPTED, DENIED, COMPLETED
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

    def update(self, data):
        """Validates and updates message details."""
        pass


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
        self.wage_type = wage_type  # 'food', 'wood', 'ferrous'

        # Lying component: The employer can change this before paying
        self.actual_payout = self.wage_offer
        self.actual_payout_type = self.wage_type

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "dev_id": self.dev_id,
            "wage_offer": self.wage_offer,
            "wage_type": self.wage_type,
            # We do NOT send actual_payout to the frontend until transaction is done
        })
        return data

    def update(self, data):
        if 'wage_offer' in data:
            self.wage_offer = int(data['wage_offer'])
        if 'wage_type' in data:
            self.wage_type = data['wage_type']


class TradeOffer(Message):
    def __init__(self, from_id, to_id, offer_items, request_items):
        super().__init__(from_id, to_id, 'TRADE')
        # Format: {'food': 5, 'wood': 0}
        self.offer_items = offer_items
        self.request_items = request_items

        # Lying Component: Set to offer_items initially
        self.actual_offer_items = offer_items.copy()

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "offer_items": self.offer_items,
            "request_items": self.request_items
        })
        return data

    def update(self, data):
        if 'offer_items' in data:
            self.offer_items = data['offer_items']
        if 'request_items' in data:
            self.request_items = data['request_items']


class FireOffer(Message):
    def __init__(self, from_id, to_id, action):
        super().__init__(from_id, to_id, 'FIRE')
        self.action = action  # 'INVITE' or 'REQUEST'

    def to_dict(self):
        data = super().to_dict()
        data['action'] = self.action
        return data
