from dtos import GameStateDTO, PlayerDTO, MapTileDTO


def build_player_state(game, session_id):
    player = game.players.get(session_id)
    if not player:
        return None

    me_dto = PlayerDTO.from_model(
        player, player.developments, game.developments)

    player_list_dto = []
    for p in game.players.values():
        player_list_dto.append(PlayerDTO.from_model(
            p, p.developments, game.developments))

    map_dto = [MapTileDTO.from_dict(tile) for tile in game.map_data]

    # Construct and return final State DTO
    state_dto = GameStateDTO(
        status=game.status,
        is_host=(session_id == game.host_id),
        me=me_dto,
        day=game.day,
        phase=game.phase,
        time_remaining=game.get_time_remaining(),
        player_list=player_list_dto,
        map=map_dto,
        chat_messages=game.chat_messages,  # The new pure chat array!
        session_id=session_id
    )

    return state_dto.to_dict()
