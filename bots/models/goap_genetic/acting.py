from .goals import GOAPGoal, GoalLibrary
from .goap_actions import OneStepPlanner
from .goap_genome import GOAPGenome
from .memory import Memory
from .planning.decision_trace import DecisionTrace


class Actuator:
    """
    The Act module. It scores every legal action against phase-relevant active
    goals and chooses the strongest goal/action pair. Plans are not cached;
    every call replans from the current memory and legal actions.
    """

    def __init__(self, genome: GOAPGenome):
        self.goal_library = GoalLibrary(genome)
        self.planner = OneStepPlanner(genome, planning_depth=3)
        self.last_debug_explanation = None

    def act(self, winning_goal: GOAPGoal | str, available_actions: list,
            memory: Memory) -> dict | None:
        """Return the best action across all active phase-relevant goals."""
        active_goals = self._active_goals(winning_goal, memory)
        scored_plans = []
        for goal in active_goals:
            planned = self.planner.plan(goal, available_actions, memory)
            if planned is None:
                continue
            goal_utility = goal.utility(memory)
            total_score = planned.score + max(0.0, goal_utility)
            scored_plans.append((total_score, goal_utility, goal, planned))

        if not scored_plans:
            self.last_debug_explanation = None
            return None

        total_score, goal_utility, goal, planned = max(
            scored_plans,
            key=lambda item: item[0],
        )
        self.last_debug_explanation = DecisionTrace.from_plan(
            goal, planned, goal_utility, total_score).as_dict()
        return planned.server_action

    def _active_goals(self, winning_goal: GOAPGoal | str,
                      memory: Memory) -> list[GOAPGoal]:
        goals = self.goal_library.available_goals(memory)
        if not goals:
            goals = [goal for goal in self.goal_library.all_goals() if not goal.is_complete(memory)]
        preferred = self._goal_from(winning_goal)
        if preferred and not preferred.is_complete(memory) and preferred not in goals:
            goals.insert(0, preferred)
        return goals

    def _goal_from(self, goal: GOAPGoal | str) -> GOAPGoal | None:
        if isinstance(goal, GOAPGoal):
            return goal
        aliases = {
            "EXPAND_TERRITORY": "INCREASE_PRODUCTION",
            "MAINTAIN_ASSETS": "PRESERVE_ASSETS",
        }
        try:
            return self.goal_library.by_name(aliases.get(goal, goal))
        except KeyError:
            return None
