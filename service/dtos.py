from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class PlayerDTO:
    id: str
    name: str
    health: str
    sickness_chance: float
    resources: Dict[str, int]
    developments: List['DevelopmentDTO']
    available_work: List[str]
    finished_phase: bool

@dataclass
class DevelopmentDTO:
    id: str
    type: str
    level: int
    maintenence_days: int
    owner_id: str

@dataclass
class MapTileDTO:
    id: str
    q: int
    r: int
    type: str
    owner_id: Optional[str]

@dataclass
class MessageDTO:
    id: str
    from_id: str
    to_id: str
    type: str
    content: Optional[str]
    offer_items: Optional[Dict[str, int]]
    request_items: Optional[Dict[str, int]]
    wage_offer: Optional[int]
    wage_type: Optional[str]
    dev_id: Optional[str]
    status: str
    is_system: Optional[bool]

@dataclass
class GameStateDTO:
    status: str
    is_host: bool
    me: PlayerDTO
    day: int
    phase: str
    time_remaining: int
    player_list: List[PlayerDTO]
    map: List[MapTileDTO]
    messages: List[MessageDTO]
    session_id: Optional[str]

@dataclass
class ResearchGameDTO:
    game_id: str
    finished_at: str
    data: GameStateDTO

@dataclass
class JoinableGameDTO:
    id: str
    name: str
    players: str

@dataclass
class NewGameDTO:
    gameId: str

@dataclass
class JoinGameDTO:
    gameId: str

@dataclass
class ConsentDTO:
    message: str
    userId: str

@dataclass
class ActiveGamesDTO:
    games: List[JoinableGameDTO]
