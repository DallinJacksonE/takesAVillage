from dtos import GameStateDTO, PlayerDTO, MapTileDTO, message_dto_factory


def build_player_state(game, session_id):
    """
    Constructs the GameStateDTO for a specific player.
    Extracts the data mapping logic out of the core game loop.
    """
    player = game.players.get(session_id)
    if not player:
        return None

    # 1. Build the 'me' PlayerDTO
    # Passing game.developments if your DTO mapping needs global context
    me_dto = PlayerDTO.from_model(
        player, player.developments, game.developments)

    # 2. Build the Player List
    player_list_dto = []
    for p in game.players.values():
        player_list_dto.append(PlayerDTO.from_model(
            p, p.developments, game.developments))

    # 3. Build the Map
    map_dto = [MapTileDTO.from_dict(tile) for tile in game.map_data]

    # 4. Build Messages (using your factory from dtos.py)
    messages_dto = [message_dto_factory(msg)
                    for msg in player.messages.values()]

    # 5. Construct and return final State DTO
    state_dto = GameStateDTO(
        status=game.status,
        is_host=(session_id == game.host_id),
        me=me_dto,
        day=game.day,
        phase=game.phase,
        time_remaining=game.get_time_remaining(),
        player_list=player_list_dto,
        map=map_dto,
        messages=messages_dto,
        session_id=session_id
    )

    return state_dto.to_dict()
