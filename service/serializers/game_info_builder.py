from dtos import GameStateDTO, PlayerDTO, MapTileDTO


def _normalize_committed_action(committed_action):
    if not committed_action:
        return None
    if isinstance(committed_action, dict):
        return committed_action
    return getattr(committed_action, '__dict__', str(committed_action))


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

    session_hist = game.player_history.setdefault(game.day , {})
    session_hist[session_id] = {
        'resources': player.resources.copy(),
        'health': player.health,
        'sickness_chance': player.sickness_chance,
        'developments': list(player.developments),
        'fire_status': getattr(player, 'fire_status', 'COLD'),
        'finished_phase': player.finished_phase,
        'committed_action': _normalize_committed_action(player.committed_action),
        'actions': [getattr(a, 'id', None) for a in player.actions.values()]
    }

    return True


def build_player_hist(game):
    """Return the accumulated player history as day -> session_id -> snapshot."""
    if not hasattr(game, 'player_history'):
        return {}

    daily_history = {}
    for day, hist in game.player_history.items():
        for session_id, snapshot in hist.items():
            day_hist = daily_history.setdefault(day, {})
            day_hist[session_id] = snapshot

    return {
        day: {
            session_id: daily_history[day][session_id]
            for session_id in sorted(daily_history[day].keys())
        }
        for day in sorted(daily_history.keys())
    }


def add_map_hist(game):
    """Capture a daily snapshot of the map into game.map_history."""
    day = getattr(game, 'day', None)
    if day is None:
        return False

    if not hasattr(game, 'map_history'):
        game.map_history = {}

    # Serialize the map data to dicts for storage
    map_snapshot = {}
    for tile_id, tile in game.map_data.items():
        map_snapshot[tile_id] = {
            'id': tile.id,
            'q': tile.q,
            'r': tile.r,
            'type': tile.type,
            'owner_id': tile.owner_id
            'development': tile.development
        }

    game.map_history[day] = map_snapshot
    return True


def build_map_hist(game):
    """Return the accumulated map history as day -> map_snapshot."""
    if not hasattr(game, 'map_history'):
        return {}

    return {
        day: snapshot
        for day, snapshot in sorted(game.map_history.items())
    }
