import time
import uuid


def _safe_serialize(obj):

    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, (list, tuple, set)):
        return [_safe_serialize(v) for v in obj]

    if isinstance(obj, dict):
        return {
            str(k): _safe_serialize(v)
            for k, v in obj.items()
        }

    if hasattr(obj, 'to_dict'):
        return _safe_serialize(obj.to_dict())

    if hasattr(obj, '__dict__'):
        return _safe_serialize(vars(obj))

    return str(obj)


def build_game_snapshot(game):

    return {
        "snapshot_id": str(uuid.uuid4()),

        "timestamp": time.time(),

        "game_id": game.id,

        "day": game.day,

        "phase": game.phase,

        "status": game.status,

        "players": {
            session_id: _safe_serialize(player)
            for session_id, player
            in game.players.items()
        },

        "map": {
            tile_id: _safe_serialize(tile)
            for tile_id, tile
            in game.map_data.items()
        },

        "developments": _safe_serialize(
            game.developments
        ),

        "chat_messages": _safe_serialize(
            game.chat_messages
        )
    }

def build_player_snapshot(player, day):
    """
    Creates a fully JSON-safe player snapshot.

    Intended for:
    - database storage
    - replay systems
    - AI training
    - debugging
    - analytics
    """

    return {

        # ==========================================
        # METADATA
        # ==========================================
        "day": int(day),

        "snapshot_id": str(uuid.uuid4()),

        "timestamp": time.time(),

        # ==========================================
        # PLAYER IDENTITY
        # ==========================================

        "player_id": player.session_id,

        "name": player.name,

        # ==========================================
        # SURVIVAL STATE
        # ==========================================

        "health": player.health,

        "sickness_chance": player.sickness_chance,

        # ==========================================
        # RESOURCES
        # ==========================================

        "resources": _safe_serialize(
            player.resources
        ),

        # ==========================================
        # FIRE / SOCIAL
        # ==========================================

        "fire_status": player.fire_status,

        "fire_guests": _safe_serialize(
            player.fire_guests
        ),

        # ==========================================
        # DEVELOPMENTS
        # ==========================================

        "developments": _safe_serialize(
            player.developments
        ),

        # ==========================================
        # ACTIONS
        # ==========================================

        "actions": _safe_serialize(
            list(player.actions.values())
        ),

        "committed_action": _safe_serialize(
            player.committed_action
        ),

        "available_work": _safe_serialize(
            player.available_work
        ),

        # ==========================================
        # TURN STATE
        # ==========================================

        "finished_phase": player.finished_phase,

        # ==========================================
        # SOCIAL / RESEARCH DATA
        # ==========================================

        "timeline": _safe_serialize(
            player.timeline
        ),

        "trade_history": _safe_serialize(
            player.trade_history
        )
    }