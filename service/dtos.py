from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


@dataclass
class MapTileDTO:
    id: str
    q: int
    r: int
    type: str
    owner_id: Optional[str]

    @classmethod
    def from_dict(cls, tile_dict: dict) -> 'MapTileDTO':
        return cls(
            id=str(tile_dict.get('id', '')),
            q=int(tile_dict.get('q', 0)),
            r=int(tile_dict.get('r', 0)),
            type=str(tile_dict.get('type', '')),
            owner_id=tile_dict.get('owner_id')
        )

# --- Message DTOs ---


@dataclass
class MessageDTO:
    """Base class containing fields common to all messages."""
    id: str
    from_id: str
    to_id: str
    type: str
    status: str
    pending_action_from: str
    is_system: bool = False


@dataclass
class TextMessageDTO(MessageDTO):
    content: Optional[str] = None


@dataclass
class EmploymentMessageDTO(MessageDTO):
    dev_id: Optional[str] = None
    wage_offer: Optional[int] = None
    wage_type: Optional[str] = None
    bartered: bool = False


@dataclass
class TradeMessageDTO(MessageDTO):
    offer_items: Optional[Dict[str, int]] = None
    request_items: Optional[Dict[str, int]] = None
    actual_offer_items: Optional[Dict[str, int]] = None
    actual_request_items: Optional[Dict[str, int]] = None
    sender_finalized: bool = False
    recipient_finalized: bool = False
    bartered: bool = False


@dataclass
class ShareFireMessageDTO(MessageDTO):
    action: Optional[str] = None


def message_dto_factory(msg) -> MessageDTO:
    """Safely converts a domain Message into its correct DTO subclass."""
    base_kwargs = {
        "id": msg.id,
        "from_id": msg.from_id,
        "to_id": msg.to_id,
        "type": msg.type,
        "status": msg.status,
        "pending_action_from": getattr(
            msg, 'pending_action_from', msg.to_id
        ),
        "is_system": msg.is_system
    }

    if msg.type == 'TEXT':
        return TextMessageDTO(
            **base_kwargs,
            content=getattr(msg, 'content', None)
        )

    elif msg.type == 'EMPLOYMENT':
        return EmploymentMessageDTO(
            **base_kwargs,
            dev_id=getattr(msg, 'dev_id', None),
            wage_offer=getattr(msg, 'wage_offer', None),
            wage_type=getattr(msg, 'wage_type', None),
            bartered=getattr(msg, 'bartered', False)
        )

    elif msg.type == 'TRADE':
        return TradeMessageDTO(
            **base_kwargs,
            offer_items=getattr(msg, 'offer_items', None),
            request_items=getattr(msg, 'request_items', None),
            actual_offer_items=getattr(msg, 'actual_offer_items', None),
            actual_request_items=getattr(msg, 'actual_request_items', None),
            sender_finalized=getattr(msg, 'sender_finalized', False),
            recipient_finalized=getattr(msg, 'recipient_finalized', False),
            bartered=getattr(msg, 'bartered', False)
        )

    elif msg.type == 'FIRE':
        return ShareFireMessageDTO(
            **base_kwargs,
            action=getattr(msg, 'action', None)
        )

    return MessageDTO(**base_kwargs)

# --- Core Game DTOs ---


@dataclass
class DevelopmentDTO:
    id: str
    type: str
    level: int
    maintenence_days: int
    owner_id: str

    @classmethod
    def from_model(cls, dev):
        return cls(
            id=dev.id,
            type=dev.type,
            level=dev.level,
            maintenence_days=dev.maintenence_days,
            owner_id=dev.owner
        )


@dataclass
class WorkActionDTO:
    development: DevelopmentDTO
    wage: int
    wage_type: str
    employer_id: str
    message_id: Optional[str] = None


@dataclass
class PlayerDTO:
    id: str
    name: str
    health: str
    fire_status: str
    sickness_chance: float
    resources: Dict[str, int]
    developments: List[DevelopmentDTO]
    available_work: List[WorkActionDTO]
    committed_action: Optional[WorkActionDTO]
    finished_phase: bool

    @classmethod
    def from_model(cls, player, my_devs_full, game_devs=None):
        # game_devs is a dictionary of ALL developments in the game,
        # which we need to resolve the details of accepted job offers.

        devs = [DevelopmentDTO.from_model(d) for d in my_devs_full]
        available_work = []

        # --- 1. Inherent Work (Own Developments) ---
        # Map development types to their generated resource
        DEV_OUTPUT_MAP = {
            "Farm": "food",
            "Woods": "wood",
            "Mine": "iron"
        }

        for dev in my_devs_full:
            res_type = DEV_OUTPUT_MAP.get(dev.type, "food")
            wage = dev.level

            available_work.append(WorkActionDTO(
                development=DevelopmentDTO.from_model(dev),
                wage=wage,
                wage_type=res_type,
                employer_id=player.session_id  # They are their own employer!
            ))

        # --- 2. Accepted Job Offers ---
        # Scrape the inbox for accepted employment messages
        if game_devs:
            for msg in player.messages.values():
                if msg.type == "EMPLOYMENT" and msg.status == "ACCEPTED":
                    target_dev = game_devs.get(msg.dev_id)
                    if target_dev:
                        available_work.append(WorkActionDTO(
                            development=DevelopmentDTO.from_model(target_dev),
                            wage=msg.wage_offer,
                            wage_type=msg.wage_type,
                            employer_id=msg.from_id,
                            message_id=msg.id
                        ))

        # --- 3. Committed Action ---
        committed_dto = None
        if getattr(player, 'committed_action', None):
            ca = player.committed_action
            if isinstance(ca, dict):
                dev_data = ca.get('development', {})
                committed_dto = WorkActionDTO(
                    development=DevelopmentDTO(**dev_data),
                    wage=ca.get('wage', 0),
                    wage_type=ca.get('wage_type', 'food'),
                    employer_id=ca.get('employer_id', ''),
                    message_id=ca.get('message_id')
                )

        return cls(
            id=player.session_id,
            name=player.name,
            health=player.health,
            fire_status=getattr(player, 'fire_status', 'COLD'),
            sickness_chance=player.sickness_chance,
            resources=player.resources,
            developments=devs,
            available_work=available_work,
            committed_action=committed_dto,
            finished_phase=player.finished_phase
        )


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
    session_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JoinableGameDTO:
    id: str
    name: str
    players: str
    isRejoinable: bool = False


@dataclass
class ActiveGamesDTO:
    games: List[JoinableGameDTO]


@dataclass
class ResearchGameDTO:
    game_id: str
    finished_at: str
    data: GameStateDTO


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
