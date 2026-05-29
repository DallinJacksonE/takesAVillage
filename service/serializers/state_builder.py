
# called by broadcast state in game_manager


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

    state_dto = {
        "status": game.status,
        "is_host": (session_id == getattr(game, 'host_id', None)),
        "me": me_dict,
        "day": game.day,
        "phase": game.phase,
        "time_remaining": game.get_time_remaining(),
        "player_list": player_list,
        "map": map_dto,
        "developments": development_list,
        "development_costs": game.rules.DEVELOPMENT_COSTS,
        "max_fire_seats": game.rules.MAX_FIRE_SEATS,
        "campfire_cost": game.rules.CAMPFIRE_COST,
        "session_id": session_id,
        "cold_sickness_rate": float(game.rules.COLD_SICKNESS_INCREASE),
        "hunger_sickness_rate": float(game.rules.HUNGER_SICKNESS_INCREASE),
        "recovery_rate": float(game.rules.RECOVERY_RATE),
    }
    # print(f"-------State_Builder-------\n"
    #      f"player: {state_dto['me']}")
    return state_dto


"""export interface GameStateDTO {
  status: "WAITING" | "ACTIVE" | "ENDED";
  is_host: boolean;
  me: PlayerDTO;
  day: number;
  phase: Phase;
  time_remaining: number;
  player_list: PlayerDTO[];
  map: MapTileDTO[];
  developments: DevelopmentDTO[];
  chat_messages: ChatMessageDTO[];
  economy_config: Record<"Farm" | "Woods" | "Mine", DevelopmentCostConfig>;
  development_costs: DevelopmentCostsDict;
  max_fire_seats: number;
  campfire_cost: ResourceBundle;
  session_id?: string;
}"""
