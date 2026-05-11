from dtos import GameStateDTO, PlayerDTO, MapTileDTO


def build_player_state(game, session_id):
    player = game.players.get(session_id)
    if not player:
        return None

    # 1. Build the 'me' DTO for the specific requester
    # Passing game.developments allows the DTO to resolve employment contracts [cite: 184]
    me_dto = PlayerDTO.from_model(
        player,
        [dev for dev in game.developments.values() if dev.owner == session_id],
        game.developments
    )

    # 2. Build the full player list for the village scoreboard/trade selectors
    player_list_dto = []
    for p_id, p_model in game.players.items():
        p_devs = [dev for dev in game.developments.values()
                  if dev.owner == p_id]
        player_list_dto.append(PlayerDTO.from_model(
            p_model, p_devs, game.developments))

    # 3. Build the Map Dictionary (Keyed by Tile ID for O(1) frontend lookup) [cite: 40, 184]
    map_dto = {
        tile_id: MapTileDTO.from_model(tile, game.developments.get(tile_id))
        for tile_id, tile in game.map_data.items()
    }

    # 4. Construct the GameStateDTO with separated economy values [cite: 26, 34]
    state_dto = GameStateDTO(
        status=game.status,
        is_host=(session_id == getattr(game, 'host_id', None)),
        me=me_dto,
        day=game.day,
        phase=game.phase,
        time_remaining=game.get_time_remaining(),
        player_list=player_list_dto,
        map=map_dto,
        # Accessing the ruleset directly to separate these values [cite: 316]
        development_costs=game.rules.DEVELOPMENT_COSTS,
        campfire_cost=game.rules.CAMPFIRE_COST,
        max_fire_seats=game.rules.MAX_FIRE_SEATS,
        chat_messages=[
            # Ensure chat messages are handled as DTOs or serializable dicts [cite: 34]
            msg if isinstance(msg, dict) else msg.to_dict()
            for msg in game.chat_messages
        ],
        ruleset={
            "development_costs": game.rules.DEVELOPMENT_COSTS,
            "campfire_cost": game.rules.CAMPFIRE_COST,
            "max_fire_seats": game.rules.MAX_FIRE_SEATS,
            "starting_inventory": getattr(game.rules, 'STARTING_INVENTORY', {})
        },
        session_id=session_id
    )

    return state_dto.to_dict()
