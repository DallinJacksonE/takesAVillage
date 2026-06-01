from Genome import Genome

# service/Bots/genetic_bot.py

class GeneticBot:

    def __init__(self, genome):
        self.genome = genome

    def choose_action(self, game, player):

        actions = game.get_available_actions(player)
        if not actions:
            return None
        
        return max(
            actions,
            key=lambda a: self.score_action(a, game, player)
        )
    
    def score_action(self, action, game, player):

        score = 0

        food = player.resources["food"]
        wood = player.resources["wood"]
        iron = player.resources["iron"]

        # ------------------
        # BUILD ACTIONS
        # ------------------

        if action["action_type"] == "BUILD":

            tile_type = action["tile_type"]

            if tile_type == "Farm":

                score += self.genome.build_farm_weight

                if food < 2:
                    score += 5

            elif tile_type == "Woods":

                score += self.genome.build_woods_weight

            elif tile_type == "Mine":

                score += self.genome.build_mine_weight

            return score

        # ------------------
        # WORK ACTIONS
        # ------------------

        wage = action["wage"]

        if action["wage_type"] == "food":

            score += (
                wage
                * self.genome.food_weight
            )

            if food == 0:
                score += 10

        elif action["wage_type"] == "wood":

            score += (
                wage
                * self.genome.wood_weight
            )

        elif action["wage_type"] == "iron":

            score += (
                wage
                * self.genome.iron_weight
            )

        return score