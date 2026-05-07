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

# --- Chat DTO (Pure Social) ---


@dataclass
class ChatMessageDTO:
    id: str
    from_id: str
    to_id: str
    content: str
    timestamp: float

# --- Action DTOs (The New Contracts) ---


@dataclass
class ActionDTO:
    """Base class containing fields common to all actions/contracts."""
    id: str
    initiator_id: str
    target_id: str
    type: str
    status: str


@dataclass
class EmploymentActionDTO(ActionDTO):
    dev_id: Optional[str] = None
    wage: Optional[int] = None
    wage_type: Optional[str] = None
    is_application: bool = False


@dataclass
class TradeActionDTO(ActionDTO):
    offer_items: Optional[Dict[str, int]] = None
    request_items: Optional[Dict[str, int]] = None
    actual_offer_items: Optional[Dict[str, int]] = None
    actual_request_items: Optional[Dict[str, int]] = None
    initiator_finalized: bool = False
    target_finalized: bool = False


@dataclass
class CampfireActionDTO(ActionDTO):
    is_request: bool = False


@dataclass
class SystemActionDTO(ActionDTO):
    dev_id: Optional[str] = None
    cost: Optional[int] = None
    cost_type: Optional[str] = None


def action_dto_factory(action) -> ActionDTO:
    """Safely converts a domain Action into its correct DTO subclass."""
    base_kwargs = {
        "id": action.id,
        "initiator_id": action.initiator_id,
        "target_id": action.target_id,
        "type": action.type,
        "status": action.status
    }

    if action.type == 'EMPLOYMENT':
        return EmploymentActionDTO(
            **base_kwargs,
            dev_id=getattr(action, 'dev_id', None),
            wage=getattr(action, 'wage', None),
            wage_type=getattr(action, 'wage_type', None),
            is_application=getattr(action, 'is_application', False)
        )

    elif action.type == 'TRADE':
        return TradeActionDTO(
            **base_kwargs,
            offer_items=getattr(action, 'offer_items', None),
            request_items=getattr(action, 'request_items', None),
            actual_offer_items=getattr(action, 'actual_offer_items', None),
            actual_request_items=getattr(action, 'actual_request_items', None),
            initiator_finalized=getattr(action, 'initiator_finalized', False),
            target_finalized=getattr(action, 'target_finalized', False)
        )

    elif action.type == 'CAMPFIRE':
        return CampfireActionDTO(
            **base_kwargs,
            is_request=getattr(action, 'is_request', False)
        )

    elif action.type in ['MAINTENANCE', 'UPGRADE']:
        return SystemActionDTO(
            **base_kwargs,
            dev_id=getattr(action, 'dev_id', None),
            cost=getattr(action, 'cost', None),
            cost_type=getattr(action, 'cost_type', None)
        )

    return ActionDTO(**base_kwargs)

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
    action_id: Optional[str] = None


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
    actions: List[ActionDTO]
    timeline: List[dict]
    finished_phase: bool

    @classmethod
    def from_model(cls, player, my_devs_full, game_devs=None):
        devs = [DevelopmentDTO.from_model(d) for d in my_devs_full]
        available_work = []

        # --- 1. Inherent Work (Own Developments) ---
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
                employer_id=player.session_id
            ))

        # --- 2. Accepted Job Offers ---
        if game_devs:
            for action in player.actions.values():
                if action.type == "EMPLOYMENT" and action.status == "ACCEPTED":
                    target_dev = game_devs.get(action.dev_id)
                    if target_dev:
                        employer_id = action.target_id if action.is_application else action.initiator_id

                        available_work.append(WorkActionDTO(
                            development=DevelopmentDTO.from_model(target_dev),
                            wage=action.wage,
                            wage_type=action.wage_type,
                            employer_id=employer_id,
                            action_id=action.id
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
                    action_id=ca.get('action_id')
                )

        # --- 4. Serialize the Actions ---
        actions_dto = [action_dto_factory(a) for a in player.actions.values()]

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
            actions=actions_dto,
            timeline=player.timeline,
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
    chat_messages: List[ChatMessageDTO]  # The dedicated UI chat array
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
