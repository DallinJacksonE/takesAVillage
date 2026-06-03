class Chat:
    def __init__(
        self,
        chat_id,
        name,
        creator_id,
        member_ids
    ):
        self.id = chat_id
        self.name = name
        self.creator_id = creator_id
        self.member_ids = member_ids

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "creator_id": self.creator_id,
            "member_ids": self.member_ids
        }