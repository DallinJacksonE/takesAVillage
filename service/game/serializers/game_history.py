from .snapshots import _safe_serialize

def _normalize_committed_action(committed_action):
    return _safe_serialize(committed_action)


def add_player_hist(game, session_id):
    """Capture a daily snapshot for one player into game.player_history."""

    player = game.players.get(session_id)

    if not player:
        return False

    if not hasattr(game, 'player_history'):
        game.player_history = {}

    day = getattr(game, 'day', None)

    if day is None:
        return False

    session_hist = game.player_history.setdefault(day, {})

    session_hist[session_id] = {
        'resources': _safe_serialize(player.resources),
        'health': player.health,
        'sickness_chance': player.sickness_chance,

        # FIXED
        'developments': _safe_serialize(player.developments),

        'fire_status': getattr(player, 'fire_status', 'COLD'),
        'finished_phase': player.finished_phase,

        'committed_action': _normalize_committed_action(
            player.last_committed_action
        ),

        'actions': _safe_serialize(
            list(player.actions.values())
        ),
        
        'trade_count': player.trade_count
    }

    return True


def build_player_hist(game):
    """Return the accumulated player history."""

    if not hasattr(game, 'player_history'):
        return {}

    return {
        day: {
            session_id: snapshot
            for session_id, snapshot in sorted(hist.items())
        }
        for day, hist in sorted(game.player_history.items())
    }


def add_map_hist(game):
    """Capture a daily snapshot of the map."""

    day = getattr(game, 'day', None)

    if day is None:
        return False

    if not hasattr(game, 'map_history'):
        game.map_history = {}

    map_snapshot = {}

    for tile_id, tile in game.map_data.items():

        map_snapshot[tile_id] = {
            'id': tile.id,
            'q': tile.q,
            'r': tile.r,
            'type': tile.type,

            # FIXED
            'development': _safe_serialize(tile.development)
        }

    game.map_history[day] = map_snapshot

    return True


def build_map_hist(game):
    """Return accumulated map history."""

    if not hasattr(game, 'map_history'):
        return {}

    return {
        day: snapshot
        for day, snapshot in sorted(game.map_history.items())
    }