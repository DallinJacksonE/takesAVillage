from pydantic import BaseModel


class NewGameRequest(BaseModel):
    ruleset: str = "default"
    botCount: int = 0
    botGenome: str = "random"
    botModel: str = "genetic"


class JoinGameRequest(BaseModel):
    gameId: str


class BotJoinRequest(BaseModel):
    gameId: str
    botSecret: str
