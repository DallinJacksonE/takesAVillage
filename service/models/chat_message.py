
class ChatMessage:
    def __init__(self, id, from_id, to_id, content, timestamp) -> None:
        self.id: str = id
        self.from_id: str = from_id
        self.to_id: str = to_id
        self.content: str = content
        self.timestamp: float = timestamp

    def to_dict(self):
        return {
            "id": self.id,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "content": self.content,
            "timestamp": self.timestamp
        }


"""export interface ChatMessageDTO {
  id: string;
  from_id: string;
  to_id: string; // "GLOBAL" or specific player ID
  content: string;
  timestamp: number;
}"""
