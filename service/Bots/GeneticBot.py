from Bots.Genome import Genome


class GeneticBot:

    def __init__(self, genome):
        self.genome = genome

    def choose_action(self, game, player):

        actions = game.get_available_actions(player)

        if not actions:
            return {
                "action_command": "FINISH_PHASE",
                "payload": {}
            }

        return max(
            actions,
            key=lambda action: self.score_action(
                action,
                game,
                player
            )
        )

    def score_action(self, action, game, player):

        score = 0

        food = player.resources.get("food", 0)
        wood = player.resources.get("wood", 0)
        iron = player.resources.get("iron", 0)

        command = action["action_command"]

        # ------------------
        # BUILD DEV
        # ------------------

        if command == "BUILD_DEV":

            tile_id = action["payload"]["tile_id"]

            tile = game.map_data.get(tile_id)

            if not tile:
                return -9999

            if tile.type == "Farm":
                score += self.genome.build_farm_weight

            elif tile.type == "Woods":
                score += self.genome.build_woods_weight

            elif tile.type == "Mine":
                score += self.genome.build_mine_weight

            score += self.genome.growth_weight

        # ------------------
        # COMMIT WORK
        # ------------------

        elif command == "COMMIT_WORK":

            job = action["payload"]["job"]

            wage = job["wage"]
            wage_type = job["wage_type"]

            if wage_type == "food":

                score += (
                    wage *
                    self.genome.food_weight
                )

                if food == 0:
                    score += (
                        5 *
                        self.genome.survival_weight
                    )

                elif food == 1:
                    score += (
                        2 *
                        self.genome.survival_weight
                    )

            elif wage_type == "wood":

                score += (
                    wage *
                    self.genome.wood_weight
                )

                if wood == 0:
                    score += (
                        3 *
                        self.genome.survival_weight
                    )

            elif wage_type == "iron":

                score += (
                    wage *
                    self.genome.iron_weight
                )

                if iron == 0:
                    score += (
                        2 *
                        self.genome.survival_weight
                    )

        # ------------------
        # UPGRADE DEV
        # ------------------

        elif command == "UPGRADE_DEV":

            score += (
                self.genome.upgrade_weight +
                self.genome.growth_weight
            )

        # ------------------
        # MAINTAIN DEV
        # ------------------

        elif command == "MAINTAIN_DEV":

            score += self.genome.maintain_weight

        # ------------------
        # CONTEST DEV
        # ------------------

        elif command == "CONTEST_DEV":

            score += self.genome.contest_weight

        # ------------------
        # FINISH PHASE
        # ------------------


        return score