"""Player-facing state projections for clients and bots.

Projections are read models derived from authoritative game state. They should
not mutate gameplay objects; command handlers still validate final legality.
"""

from service.game.state.legal_actions import get_legal_actions


RESOURCE_KEYS = ("wood", "food", "iron")


def build_phase_projection(game, player_id):
    """Return the projection matching the game's current phase."""
    if game.phase == "TRADE":
        return build_trade_projection(game, player_id)
    if game.phase == "NIGHT":
        return build_night_projection(game, player_id)
    return build_work_projection(game, player_id)


def build_work_projection(game, player_id):
    player = _require_player(game, player_id)
    projection = _base_projection(game, player)
    projection.update({
        "available_work": _safe_serialize(player.available_work),
        "committed_action": _safe_serialize(player.committed_action),
        "my_developments": _safe_serialize([
            development for development in game.developments.values()
            if development.owner == player.session_id
        ]),
    })
    return projection


def build_trade_projection(game, player_id):
    player = _require_player(game, player_id)
    projection = _base_projection(game, player)
    projection.update({
        "actions": _safe_serialize(list(player.actions.values())),
        "trade_history": _safe_serialize(player.trade_history),
    })
    return projection


def build_night_projection(game, player_id):
    player = _require_player(game, player_id)
    projection = _base_projection(game, player)
    projection.update({
        "fire_status": player.fire_status,
        "fire_guests": _safe_serialize(player.fire_guests),
    })
    return projection


def _base_projection(game, player):
    resources = {
        resource: player.resources.get(resource, 0)
        for resource in RESOURCE_KEYS
    }
    return {
        "game_id": game.id,
        "player_id": player.session_id,
        "phase": game.phase,
        "day_num": game.day,
        "health": player.health,
        "sickness_chance": player.sickness_chance,
        "resources": _safe_serialize(player.resources),
        "phase_state": player.phase_state,
        "finished_phase": player.finished_phase,
        "legal_actions": _safe_serialize(
            get_legal_actions(game, player.session_id)),
        **resources,
    }


def _require_player(game, player_id):
    player = game.players.get(player_id)
    if not player:
        raise KeyError(f"Unknown player: {player_id}")
    return player


def _safe_serialize(obj):
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, (list, tuple, set)):
        return [_safe_serialize(value) for value in obj]
    if isinstance(obj, dict):
        return {str(key): _safe_serialize(value) for key, value in obj.items()}
    if hasattr(obj, "to_dict"):
        return _safe_serialize(obj.to_dict())
    if hasattr(obj, "__dict__"):
        return _safe_serialize(vars(obj))
    return str(obj)
