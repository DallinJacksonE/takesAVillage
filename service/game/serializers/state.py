
"""Player-facing state serialization.

The matching frontend DTO definitions live in ``frontend/src/dtos/index.ts``.
"""

from service.game.state.intents import (
    ContestIntent,
    MaintainIntent,
    UpgradeIntent,
    WorkIntent,
)
from service.game.state.night import build_night_locations


WORK_ANIMATIONS: dict[str, str] = {
    "Farm": "WORK_FARM",
    "Woods": "WORK_WOODS",
    "Mine": "WORK_MINE",
}


def build_development_state(game, development):
    """Serialize a development with live contest participation."""
    state = development.to_dict()
    if game.phase != "WORK" or not state.get("is_contested", False):
        return state

    contest_intents = [
        intent
        for intent in getattr(game, "phase_intents", {}).values()
        if isinstance(intent, ContestIntent)
        and intent.development_id == development.id
    ]
    state["contester_supporters"] = sorted(
        intent.player_id
        for intent in contest_intents
        if intent.side == "CONTESTER"
    )
    state["owner_supporters"] = sorted(
        intent.player_id
        for intent in contest_intents
        if intent.side == "OWNER"
    )
    return state


def build_player_visual_state(game, player):
    """Project only the public state required to place and animate a player."""
    night_transition = getattr(game, "night_transition", None)
    if night_transition:
        transition_visual = night_transition["visuals"].get(player.session_id)
        if transition_visual:
            return transition_visual

    if game.phase == "NIGHT":
        location = build_night_locations(game)[player.session_id]
        if player.health == "dead":
            return {"animation": "DEAD", "location": location}
        if player.health in ("sick", "recovering"):
            return {"animation": "SICK", "location": location}
        return {"animation": "IDLE", "location": location}

    if player.health == "dead":
        return {"animation": "DEAD", "location": {"kind": "HOME"}}
    if player.health in ("sick", "recovering"):
        return {"animation": "SICK", "location": {"kind": "HOME"}}

    if game.phase == "TRADE":
        accepted_trades = sorted(
            (
                action
                for action in getattr(player, "actions", {}).values()
                if getattr(action, "type", None) == "TRADE"
                and getattr(action, "status", None) == "ACCEPTED"
            ),
            key=lambda action: action.id,
        )
        if accepted_trades:
            trade = accepted_trades[0]
            side = (
                "INITIATOR"
                if trade.initiator_id == player.session_id
                else "TARGET"
            )
            return {
                "animation": "CARRY",
                "location": {
                    "kind": "TRADE",
                    "id": trade.id,
                    "side": side,
                },
            }

    intent = getattr(game, "phase_intents", {}).get(player.session_id)
    if game.phase == "WORK" and intent is not None:
        location = {
            "kind": "DEVELOPMENT",
            "id": intent.development_id,
        }
        if isinstance(intent, WorkIntent):
            development = game.developments.get(intent.development_id)
            animation = WORK_ANIMATIONS.get(
                getattr(development, "type", None), "IDLE")
        elif isinstance(intent, (MaintainIntent, UpgradeIntent)):
            animation = "BUILD"
        elif isinstance(intent, ContestIntent):
            animation = "CONTEST"
        else:
            animation = "IDLE"
        return {"animation": animation, "location": location}

    committed_action = getattr(player, "committed_action", None)
    if (
        game.phase == "WORK"
        and isinstance(committed_action, dict)
        and committed_action.get("Action") == "Build"
        and committed_action.get("Tile_Id")
    ):
        return {
            "animation": "BUILD",
            "location": {
                "kind": "TILE",
                "id": committed_action["Tile_Id"],
            },
        }

    return {"animation": "IDLE", "location": {"kind": "HOME"}}


def build_public_player_state(game, player):
    """Serialize identity and visible village state without private decisions."""
    reaction = getattr(player, "reaction", None)
    if reaction and reaction["expires_at"] <= game._clock():
        reaction = None
    return {
        "id": player.session_id,
        "name": player.name,
        "health": player.health,
        "fire_status": player.fire_status,
        "fire_guests": list(player.fire_guests),
        "developments": list(player.developments),
        "finished_phase": player.finished_phase,
        "phase_state": player.phase_state,
        "visual_state": build_player_visual_state(game, player),
        "reaction": reaction,
    }


def build_public_interactions(game):
    """Project shared activity without exposing private contract terms."""
    if game.phase != "TRADE":
        return []

    interactions = {}
    for player in game.players.values():
        for action in getattr(player, "actions", {}).values():
            if getattr(action, "type", None) != "TRADE":
                continue
            interactions[action.id] = {
                "id": action.id,
                "kind": "TRADE",
                "participant_ids": [
                    action.initiator_id,
                    action.target_id,
                ],
                "status": action.status,
            }
    return [interactions[key] for key in sorted(interactions)]


def build_player_state(game, session_id):
    player = game.players.get(session_id)
    if not player:
        return None

    me_dict = player.to_dict()
    player_list = [
        build_public_player_state(game, visible_player)
        for visible_player in game.players.values()
    ]

    map_dto = {}
    for tile_id, tile in game.map_data.items():
        tile_state = tile.to_dict()
        if tile.development:
            tile_state["development"] = build_development_state(
                game, tile.development)
        map_dto[tile_id] = tile_state

    development_list = [
        build_development_state(game, value)
        for _, value in game.developments.items()
    ]
    
    chat_list = [
        chat.to_dict()
        for chat in game.chats
        if session_id in chat.member_ids
    ]

    state_dto = {
        "status": game.status,
        "state_revision": getattr(game, "state_revision", 0),
        "is_host": (session_id == getattr(game, 'host_id', None)),
        "me": me_dict,
        "day": game.day,
        "game_length": game.game_length,
        "phase": game.phase,
        "time_remaining": game.get_time_remaining(),
        "player_list": player_list,
        "public_interactions": build_public_interactions(game),
        "map": map_dto,
        "host_connected": game.host_connected,
        "developments": development_list,
        "chats": chat_list, # Include chats in the state DTO
        "development_costs": game.rules.DEVELOPMENT_COSTS,
        "max_fire_seats": game.rules.MAX_FIRE_SEATS,
        "campfire_cost": game.rules.CAMPFIRE_COST,
        "session_id": session_id,
        "cold_sickness_rate": float(game.rules.COLD_SICKNESS_INCREASE),
        "hunger_sickness_rate": float(game.rules.HUNGER_SICKNESS_INCREASE),
        "recovery_rate": float(game.rules.RECOVERY_RATE),
        "training": game.training
    }

    night_transition = getattr(game, "night_transition", None)
    if night_transition:
        state_dto["night_transition"] = {
            "id": night_transition["id"],
            "deadline": night_transition["deadline"],
            "affected_player_ids": list(
                night_transition["affected_player_ids"]),
        }

    return state_dto
