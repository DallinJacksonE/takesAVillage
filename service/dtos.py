from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any


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
    # Note: Kept your spelling to avoid breaking existing frontend logic
    maintenance_days: int
    owner_id: str

    # --- Conflict Flags ---
    is_contested: bool
    contester_id: Optional[str]
    contester_supporters: List[str]
    owner_supporters: List[str]

    @classmethod
    def from_model(cls, dev):
        return cls(
            id=dev.id,
            type=dev.type,
            level=dev.level,
            maintenance_days=dev.maintenance_days,
            owner_id=dev.owner,
            is_contested=dev.is_contested,
            contester_id=dev.contester_id,
            # We use list() here to ensure we pass a copy of the list,
            # preventing accidental reference mutations
            contester_supporters=list(dev.contester_supporters),
            owner_supporters=list(dev.owner_supporters)
        )

    def to_dict(self) -> dict:
        """
        Serializes the DTO into a standard Python dictionary for JSON conversion.
        """
        return {
            "id": self.id,
            "type": self.type,
            "level": self.level,
            "maintenence_days": self.maintenence_days,
            "owner_id": self.owner_id,
            "is_contested": self.is_contested,
            "contester_id": self.contester_id,
            "contester_supporters": self.contester_supporters,
            "owner_supporters": self.owner_supporters
        }


@dataclass
class MapTileDTO:
    id: str
    q: int
    r: int
    type: str
    owner_id: Optional[str]
    development: Optional['DevelopmentDTO'] = None

    @classmethod
    def from_model(cls, tile_model, development_model=None) -> 'MapTileDTO':
        """
        Creates a DTO directly from the backend MapTile model.
        Optionally accepts a development model if one exists on this tile.
        """
        # Convert the development model to a DTO if it was passed in
        dev_dto = None
        if development_model:
            # Assuming DevelopmentDTO also has a from_model method
            dev_dto = DevelopmentDTO.from_model(development_model)

        return cls(
            id=tile_model.id,
            q=tile_model.q,
            r=tile_model.r,
            type=tile_model.type,
            owner_id=tile_model.owner_id,
            development=dev_dto
        )

    def to_dict(self) -> dict:
        """
        Serializes the DTO into a standard Python dictionary for JSON conversion.
        """
        return {
            "id": self.id,
            "q": self.q,
            "r": self.r,
            "type": self.type,
            "owner_id": self.owner_id,
            # Recursively call to_dict() on the nested development if it exists
            "development": self.development.to_dict() if self.development else None
        }

    @classmethod
    def from_dict(cls, tile_dict: dict) -> 'MapTileDTO':
        # Safely extract and convert the nested development data
        dev_data = tile_dict.get('development')

        if isinstance(dev_data, dict):
            # If it's a raw dictionary, instantiate the DTO
            dev_obj = DevelopmentDTO(**dev_data)
        else:
            # If it's already an object or None, pass it through
            dev_obj = dev_data

        return cls(
            id=str(tile_dict.get('id', '')),
            q=int(tile_dict.get('q', 0)),
            r=int(tile_dict.get('r', 0)),
            type=str(tile_dict.get('type', '')),
            owner_id=tile_dict.get('owner_id'),
            development=dev_obj
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

    def to_dict(self) -> dict:
        """
        Serializes the PlayerDTO into a dictionary, ensuring all nested DTOs 
        (like DevelopmentDTO) call their specific to_dict() methods to maintain 
        naming consistency and prevent JSON errors.
        """
        return {
            "id": self.id,
            "name": self.name,
            "health": self.health,
            "fire_status": self.fire_status,
            "sickness_chance": self.sickness_chance,
            "resources": self.resources,
            # Explicitly call to_dict on Developments to maintain naming parity
            "developments": [d.to_dict() for d in self.developments],
            # Simple dataclasses like ActionDTOs can safely use asdict()
            "actions": [asdict(a) for a in self.actions],
            "timeline": self.timeline,
            "finished_phase": self.finished_phase,
            # Manually map WorkActionDTOs to ensure their nested DevelopmentDTOs are serialized
            "available_work": [
                {
                    "development": w.development.to_dict(),
                    "wage": w.wage,
                    "wage_type": w.wage_type,
                    "employer_id": w.employer_id,
                    "action_id": w.action_id
                } for w in self.available_work
            ],
            "committed_action": {
                "development": self.committed_action.development.to_dict(),
                "wage": self.committed_action.wage,
                "wage_type": self.committed_action.wage_type,
                "employer_id": self.committed_action.employer_id,
                "action_id": self.committed_action.action_id
            } if self.committed_action else None
        }

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
            if getattr(dev, 'is_contested', False):
                continue
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
                    if target_dev and not getattr(target_dev, 'is_contested', False):
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
    map: Dict[str, MapTileDTO]
    chat_messages: List[ChatMessageDTO]
    development_costs: Dict[str, Any]
    campfire_cost: int
    max_fire_seats: int
    ruleset: dict  # Keeps a backup of the full ruleset
    session_id: Optional[str] = None

    @classmethod
    def from_model(cls, game, current_player_id: str) -> 'GameStateDTO':
        player_dtos = []
        me_dto = None

        for p_id, player_model in game.players.items():
            my_devs = [dev for dev in game.developments.values()
                       if dev.owner == p_id]
            p_dto = PlayerDTO.from_model(
                player_model, my_devs, game.developments)
            player_dtos.append(p_dto)
            if p_id == current_player_id:
                me_dto = p_dto

        map_dtos = {
            tile_id: MapTileDTO.from_model(
                tile, game.developments.get(tile_id))
            for tile_id, tile in game.map_data.items()
        }

        # Ensure every field expected by the dataclass is passed here [cite: 418]
        return cls(
            status=game.status,
            is_host=(getattr(game, 'host_id', '') == current_player_id),
            me=me_dto,  # Ensure 'me' is passed!
            day=game.day,
            phase=game.phase,
            time_remaining=game.get_time_remaining(),
            player_list=player_dtos,
            map=map_dtos,
            chat_messages=[
                msg if isinstance(
                    msg, ChatMessageDTO) else ChatMessageDTO(**msg)
                for msg in game.chat_messages
            ],
            # Separated values for the frontend [cite: 141, 386]
            development_costs=game.rules.DEVELOPMENT_COSTS,
            campfire_cost=game.rules.CAMPFIRE_COST,
            max_fire_seats=game.rules.MAX_FIRE_SEATS,
            ruleset={
                "development_costs": game.rules.DEVELOPMENT_COSTS,
                "campfire_cost": game.rules.CAMPFIRE_COST,
                "max_fire_seats": game.rules.MAX_FIRE_SEATS,
                "starting_inventory": getattr(game.rules, 'STARTING_INVENTORY', {})
            },
            session_id=current_player_id
        )

    def to_dict(self) -> dict:
        """
        Manually serializes everything to prevent 'MapTile is not JSON serializable'[cite: 147, 419].
        """
        return {
            "status": self.status,
            "is_host": self.is_host,
            "me": self.me.to_dict() if self.me else None,  # Added 'me' serialization
            "day": self.day,
            "phase": self.phase,
            "time_remaining": self.time_remaining,
            "player_list": [p.to_dict() for p in self.player_list],
            "map": {t_id: tile.to_dict() for t_id, tile in self.map.items()},
            "chat_messages": [asdict(m) for m in self.chat_messages],
            "development_costs": self.development_costs,
            "campfire_cost": self.campfire_cost,
            "max_fire_seats": self.max_fire_seats,
            "ruleset": self.ruleset,
            "session_id": self.session_id
        }


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
