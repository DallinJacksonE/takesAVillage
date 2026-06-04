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
            key=lambda a: self.score_action(
                a,
                game,
                player
            )
        )

    def score_action(
        self,
        action,
        game,
        player
    ):

        g = self.genome

        score = 0

        command = action["action_command"]

        resources = player.resources

        food = resources.get("food", 0)
        wood = resources.get("wood", 0)
        iron = resources.get("iron", 0)

        # =====================
        # NEEDS
        # =====================

        food_need = max(0, 5 - food)
        wood_need = max(0, 5 - wood)
        iron_need = max(0, 5 - iron)

        score += (
            food_need *
            g.food_desperation_weight
        )

        score += (
            wood_need *
            g.wood_desperation_weight
        )

        score += (
            iron_need *
            g.iron_desperation_weight
        )

        # =====================
        # BUILD
        # =====================

        if command == "BUILD_DEV":

            score += g.build_weight

            tile_type = (
                action["payload"]
                .get("tile_type")
            )

            if tile_type == "Farm":

                score += (
                    g.farm_preference
                    + g.growth_weight
                )

                if food_need > 0:
                    score += (
                        food_need *
                        g.survival_weight
                    )

            elif tile_type == "Woods":

                score += (
                    g.woods_preference
                    + g.growth_weight
                )

            elif tile_type == "Mine":

                score += (
                    g.mine_preference
                    + g.growth_weight
                )

        # =====================
        # UPGRADE
        # =====================

        elif command == "UPGRADE_DEV":

            score += (
                g.upgrade_weight
                + g.growth_weight
            )

        # =====================
        # MAINTAIN
        # =====================

        elif command == "MAINTAIN_DEV":

            score += (
                g.maintain_weight
                + g.future_reward_weight
            )

        # =====================
        # CONTEST
        # =====================

        elif command == "CONTEST_DEV":

            score += (
                g.contest_weight
                + g.aggression_weight
            )

        # =====================
        # CAMPFIRE
        # =====================

        elif command == "START_FIRE":

            score += (
                g.fire_weight
                + g.cooperation_weight
                + g.reputation_weight
            )

        # =====================
        # WORK
        # =====================

        elif command == "COMMIT_WORK":

            score += g.work_weight

            job = action["payload"]["job"]

            wage = job["wage"]

            wage_type = job["wage_type"]

            if wage_type == "food":

                score += (
                    wage *
                    g.food_weight
                )

                score += (
                    food_need *
                    g.food_desperation_weight
                )

            elif wage_type == "wood":

                score += (
                    wage *
                    g.wood_weight
                )

                score += (
                    wood_need *
                    g.wood_desperation_weight
                )

            elif wage_type == "iron":

                score += (
                    wage *
                    g.iron_weight
                )

                score += (
                    iron_need *
                    g.iron_desperation_weight
                )

        # =====================
        # RANDOMNESS
        # =====================

        score += (
            g.risk_weight *
            0.1
        )

        return score