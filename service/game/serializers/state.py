
"""Player-facing state serialization.

The matching frontend DTO definitions live in ``frontend/src/dtos/index.ts``.
"""


def build_player_state(game, session_id):
    player = game.players.get(session_id)
    if not player:
        return None

    me_dict = player.to_dict()
    player_list = [player.to_dict() for player in game.players.values()]

    map_dto = {
        tile_id: tile.to_dict()
        for tile_id, tile in game.map_data.items()
    }

    development_list = [value.to_dict()
                        for _, value in game.developments.items()]
    
    chat_list = [
        chat.to_dict()
        for chat in game.chats
        if session_id in chat.member_ids
    ]

    state_dto = {
        "status": game.status,
        "is_host": (session_id == getattr(game, 'host_id', None)),
        "me": me_dict,
        "day": game.day,
        "game_length": game.game_length,
        "phase": game.phase,
        "time_remaining": game.get_time_remaining(),
        "player_list": player_list,
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

    return state_dto
