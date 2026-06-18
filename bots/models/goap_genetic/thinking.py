from models.genetic.Genome import Genome


class Thinker:
    """
    The Think module. Takes the objective memory and uses the Genome 
    to evaluate the utility of high-level goals using dynamic utility curves,
    with zero hardcoded ideals.
    """

    def __init__(self, genome: Genome):
        self.genome = genome

    def evaluate_goals(self, memory: dict) -> str:
        """
        Calculates utility scores for broad GOAP goals and returns the highest.
        """
        goals = {
            "SURVIVE": self._score_survival(memory),
            "MAINTAIN_ASSETS": self._score_maintenance(memory),
            "EXPAND_TERRITORY": self._score_expansion(memory),
            "SECURE_INCOME": self._score_income(memory),
            "COOPERATE": self._score_cooperation(memory)
        }

        # Add a tiny bit of genetic randomness to break ties or shake up strict loops
        for goal in goals:
            goals[goal] += (self.genome.risk_weight * 0.1)

        # Return the string name of the highest scoring goal
        best_goal = max(goals, key=goals.get)
        return best_goal

    # --- Utility Scoring Functions ---

    def _score_survival(self, memory: dict) -> float:
        score = 0.0

        # INVERSE CURVE: The closer to 0 a resource is, the closer the urgency is to 1.0.
        # Adding 1 prevents division by zero. We multiply by 10 to give desperation
        # a high enough ceiling to outcompete growth when starving.
        food_urgency = 10.0 / (memory["food"] + 1.0)
        wood_urgency = 10.0 / (memory["wood"] + 1.0)
        iron_urgency = 10.0 / (memory["iron"] + 1.0)

        # Apply genetic desperation weights to the objective urgency
        score += (food_urgency * self.genome.food_desperation_weight)
        score += (wood_urgency * self.genome.wood_desperation_weight)
        score += (iron_urgency * self.genome.iron_desperation_weight)

        # Health risks also trigger survival instincts, inversely scaled by risk tolerance
        if memory["sickness_chance"] > 0:
            risk_aversion = max(0.1, 3.0 - self.genome.risk_weight)
            score += (memory["sickness_chance"] * 10 * risk_aversion)

        return score * self.genome.survival_weight

    def _score_maintenance(self, memory: dict) -> float:
        score = 0.0
        my_devs = memory.get("my_developments", [])

        if not my_devs:
            return 0.0  # Cannot maintain what we do not own

        # Linear desire to maintain based on how many assets the bot holds
        score += len(my_devs) * self.genome.future_reward_weight
        score += self.genome.maintain_weight + self.genome.upgrade_weight

        return score

    def _score_expansion(self, memory: dict) -> float:
        score = 0.0

        # Genetic baseline desire to build
        score += self.genome.build_weight

        # LINEAR CURVE: Surplus fuels expansion.
        # As resources climb, survival utility drops, and this surplus utility takes over.
        surplus_factor = (memory["food"] + memory["wood"])
        score += (surplus_factor * self.genome.growth_weight)

        # If there are enemy developments, aggression factors in
        if memory.get("other_player_developments"):
            score += self.genome.aggression_weight
            score += self.genome.contest_weight

        return score

    def _score_income(self, memory: dict) -> float:
        score = 0.0

        # Baseline desire for immediate wage payouts
        score += self.genome.immediate_reward_weight
        score += self.genome.work_weight

        # If we lack developments to generate our own income, we are more likely to work
        if not memory.get("my_developments"):
            score += self.genome.work_weight * 2.0

        return score

    def _score_cooperation(self, memory: dict) -> float:
        score = 0.0

        # If we have pending contracts, resolving them is a cooperative priority
        pending = memory.get("pending_contracts", [])
        if pending:
            score += (len(pending) * 5.0)  # Immediate mechanical incentive

        score += self.genome.cooperation_weight
        score += self.genome.reputation_weight

        return score
