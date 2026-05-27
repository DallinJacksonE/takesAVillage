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

def build_work_snapshot(player, game_state):
    """
    Creates a snapshot of the work phase for a given player, including
    available jobs and committed actions.

    Intended for:
    - informing the frontend of work options
    - AI decision-making during the work phase
    """

    return {
        "game_id": game_state.id,
        "player_id": player.session_id,
        "health": player.health,
        "sickness_chance": player.sickness_chance,
        "day_num": game_state.day,
        "wood": player.resources.get("wood", 0),
        "food": player.resources.get("food", 0),
        "iron": player.resources.get("iron", 0),
        "available_work": [
            _safe_serialize(work)
            for work in player.available_work
        ],
        "day_num": game_state.day,
        "committed_action": _safe_serialize(player.committed_action)
    }

def build_trade_snapshot(player, game_state):
    """
    Creates a snapshot of the trade state for a given player, including
    their current resources and trade history.

    Intended for:
    - informing the frontend of trade options and history
    - AI decision-making during the trade phase
    """

    return {
        "game_id": game_state.id,
        "player_id": player.session_id,
        "health": player.health,
        "sickness_chance": player.sickness_chance,
        "wood": player.resources.get("wood", 0),
        "food": player.resources.get("food", 0),
        "iron": player.resources.get("iron", 0),
        "day_num": game_state.day,  
        "trade_history": _safe_serialize(player.trade_history)
    }

def build_night_snapshot(player, game_state):
    """
    Creates a snapshot of the night phase for a given player, including
    their health status and fire information.

    Intended for:
    - informing the frontend of night phase outcomes
    - AI decision-making during the night phase
    """

    return {
        "game_id": game_state.id,
        "player_id": player.session_id,
        "health": player.health,
        "day_num": game_state.day,
        "sickness_chance": player.sickness_chance,
        "wood": player.resources.get("wood", 0),
        "food": player.resources.get("food", 0),
        "iron": player.resources.get("iron", 0),
        "fire_status": player.fire_status,
        "fire_guests": _safe_serialize(player.fire_guests)
    }