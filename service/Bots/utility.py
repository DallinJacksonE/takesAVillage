# service/bots/utility.py


class BotUtility:

    @staticmethod
    def can_afford(player, cost_dict):
        for resource, amount in cost_dict.items():
            if player.resources.get(resource, 0) < amount:
                return False
        return True

    @staticmethod
    def get_empty_tiles(game_state):
        empty_tiles = []

        for tile in game_state.map_data.values():
            if tile.development is None:
                empty_tiles.append(tile)

        return empty_tiles

    @staticmethod
    def get_affordable_tiles(game_state, player):
        affordable = []

        for tile in BotUtility.get_empty_tiles(game_state):
            dev_type = tile.type

            build_cost = game_state.development_costs.get(
                dev_type,
                {}
            ).get("build", {})

            if BotUtility.can_afford(player, build_cost):
                affordable.append(tile)

        return affordable

    @staticmethod
    def get_owned_developments(game_state, player):
        result = []

        for dev_id in player.developments:
            dev = game_state.developments.get(dev_id)

            if dev:
                result.append(dev)

        return result