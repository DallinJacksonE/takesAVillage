from BaseBot import BaseBot
from models.genetic.Genome import Genome


class GeneticBot(BaseBot):
    def __init__(self, genome):
        self.genome = genome
        super().__init__()

    @staticmethod
    def from_json(genome_json):
        return GeneticBot(Genome(**genome_json))
    
    def resource_value(self,bundle):
        return (
            bundle.get("food", 0) * self.genome.food_weight +
            bundle.get("wood", 0) * self.genome.wood_weight +
            bundle.get("iron", 0) * self.genome.iron_weight
        )

    def choose_action(self, game_state: dict) -> dict | None:
        """
        Evaluates actions using genetic weights and returns a
        formatted payload.
        """
        me = game_state.get("me", {})

        if game_state.get("status") == "WAITING":
            return None

        actions = self.get_available_actions(game_state)

        if me.get("health") == "dead":
            return None

        if me.get("finished_phase"):
            if game_state.get("phase") == "WORK":

                accept_action = next(
                    (
                        a for a in actions
                        if a["action_command"] == "ACCEPT"
                    ),
                    None
                )

                if accept_action:
                    return self.format_network_payload(accept_action)

            return None

        # 1. Fetch valid moves from the base class parser
        actions = self.get_available_actions(game_state)

        print(f"available actions for bot: {actions}")

        if self.waiting:
            return None
        
        # 2. If no valid moves, finish the phase
        if not actions:
            return self.format_network_payload(None)

        # 3. Score and select the best action
        best_action = max(
            actions,
            key=lambda a: self.score_action(a, game_state)
        )

        # 4. Use the base class to clean and format the DTO
        return self.format_network_payload(best_action)

    def score_action(self, action: dict, game_state: dict) -> float:
        """Scores an action dict using the bot's genome."""
        g = self.genome
        score = 0
        command = action["action_command"]
        contract = None
        me = game_state.get("me", {})

        if "action_id" in action.get("payload", {}):
            action_id = action["payload"]["action_id"]

            contract = next(
                (
                    a for a in me.get("actions", [])
                    if a.get("id") == action_id
                ),
                None
            )

        contract_type = contract.get("type") if contract else None

        if "action_id" in action["payload"]:
            action_id = action["payload"]["action_id"]
            contract = next(
                ( 
                    a for a in me.get("actions", [])
                    if a["id"] == action_id
                )
                , None
            )
            
        resources = me.get("resources", {"wood": 0, "food": 0, "iron": 0})

        food = resources.get("food", 0)
        wood = resources.get("wood", 0)
        iron = resources.get("iron", 0)

        # =====================
        # NEEDS
        # =====================
        food_need = max(0, 5 - food)
        wood_need = max(0, 5 - wood)
        iron_need = max(0, 5 - iron)

        score += (food_need * g.food_desperation_weight)
        score += (wood_need * g.wood_desperation_weight)
        score += (iron_need * g.iron_desperation_weight)

        if command == "EMPLOYMENT":
            score +=100

        # =====================
        # BUILD
        # =====================
        if command == "BUILD_DEV":
            score += g.build_weight

            # Retrieve the injected hidden type from BaseBot
            tile_type = action["payload"].get("_tile_type")

            if tile_type == "Farm":
                score += (g.farm_preference + g.growth_weight)
                if food_need > 0:
                    score += (food_need * g.survival_weight)
            elif tile_type == "Woods":
                score += (g.woods_preference + g.growth_weight)
            elif tile_type == "Mine":
                score += (g.mine_preference + g.growth_weight)

        # =====================
        # UPGRADE / MAINTAIN / CONTEST
        # =====================
        elif command == "UPGRADE_DEV":
            score += (g.upgrade_weight + g.growth_weight)
        elif command == "MAINTAIN_DEV":
            score += (g.maintain_weight + g.future_reward_weight)
        elif command == "CONTEST_DEV":
            score += (g.contest_weight + g.aggression_weight)

        # =====================
        # CAMPFIRE
        # =====================
        elif command == "START_FIRE":
            score += (g.fire_weight + g.cooperation_weight +
                      g.reputation_weight)

        # =====================
        # WORK
        # =====================
        elif command == "COMMIT_WORK":
            score += g.work_weight
            job = action["payload"]["job"]
            wage = job.get("wage", 0)
            wage_type = job.get("wage_type")

            if wage_type == "food":
                score += (wage * g.food_weight)
                score += (food_need * g.food_desperation_weight)
            elif wage_type == "wood":
                score += (wage * g.wood_weight)
                score += (wood_need * g.wood_desperation_weight)
            elif wage_type == "iron":
                score += (wage * g.iron_weight)
                score += (iron_need * g.iron_desperation_weight)

            if job.get("action_id"):
                score += 10000

        elif command == "ACCEPT":
            score += g.cooperation_weight + g.reputation_weight
            score += 10000000

            if contract and contract_type == "TRADE":

                if contract["initiator_id"] == me["id"]:
                    given = contract.get("offer_items", {})
                    received = contract.get("request_items", {})
                else:
                    given = contract.get("request_items", {})
                    received = contract.get("offer_items", {})

                score += (
                    self.resource_value(received)
                    - self.resource_value(given)
                )
        # =====================
        # RANDOMNESS
        # =====================
        score += (g.risk_weight * 0.1)

        return score
