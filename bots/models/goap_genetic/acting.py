from .goals import GOAPGoal, GoalLibrary
from .goap_actions import OneStepPlanner
from .goap_genome import GOAPGenome
from .memory import Memory


class Actuator:
    """
    The Act module. It uses explicit GOAP goals and one-step action templates
    over the currently legal server actions. No plans are cached; every call
    replans from current memory and current legal actions.
    """

    def __init__(self, genome: GOAPGenome):
        self.goal_library = GoalLibrary(genome)
        self.planner = OneStepPlanner(genome)
        self.last_debug_explanation = None
        self.fallback_goal_order = [
            "SURVIVE",
            "SECURE_WARMTH",
            "SECURE_FOOD",
            "PRESERVE_ASSETS",
            "IMPROVE_ASSETS",
            "SECURE_INCOME",
            "RESOLVE_OBLIGATIONS",
            "COOPERATE",
            "INCREASE_PRODUCTION",
            "TRADE_TOWARD_SCARCITY",
            "CONTEST_VALUE",
        ]

    def act(self, winning_goal: GOAPGoal | str, available_actions: list,
            memory: Memory) -> dict | None:
        """
        Plans for the selected goal, then tries next viable explicit goals.
        """
        goal_order = [self._goal_from(winning_goal)]
        goal_order.extend(
            self.goal_library.by_name(goal_name)
            for goal_name in self.fallback_goal_order
            if goal_name != goal_order[0].name
        )

        for goal in goal_order:
            if goal.is_complete(memory):
                continue
            planned = self.planner.plan(goal, available_actions, memory)
            if planned is not None:
                self.last_debug_explanation = planned.explanation
                return planned.server_action

        self.last_debug_explanation = None
        return None

    def _goal_from(self, goal: GOAPGoal | str) -> GOAPGoal:
        if isinstance(goal, GOAPGoal):
            return goal
        aliases = {
            "EXPAND_TERRITORY": "INCREASE_PRODUCTION",
            "MAINTAIN_ASSETS": "PRESERVE_ASSETS",
        }
        return self.goal_library.by_name(aliases.get(goal, goal))
