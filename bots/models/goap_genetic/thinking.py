from models.goap_genetic.goap_genome import GOAPGenome
from models.goap_genetic.goals import GoalLibrary, GOAPGoal
from models.goap_genetic.memory import Memory


class Thinker:
    """
    The Think module. Takes the objective memory and uses the Genome 
    to evaluate the utility of high-level goals using dynamic utility curves,
    with zero hardcoded ideals.
    """

    def __init__(self, genome: GOAPGenome):
        self.genome = genome
        self.goal_library = GoalLibrary(genome)

    def evaluate_goals(self, memory: Memory) -> GOAPGoal:
        """
        Calculates utility scores for broad GOAP goals and returns the highest.
        """
        scored_goals = [
            (goal, goal.utility(memory) + self.genome.tie_break_weight)
            for goal in self.goal_library.all_goals()
        ]

        return max(scored_goals, key=lambda item: item[1])[0]

    # --- Utility Scoring Functions ---

    def _score_survival(self, memory: Memory) -> float:
        return self.goal_library.by_name("SURVIVE").utility(memory)

    def _score_maintenance(self, memory: Memory) -> float:
        return self.goal_library.by_name("PRESERVE_ASSETS").utility(memory)

    def _score_expansion(self, memory: Memory) -> float:
        return self.goal_library.by_name("INCREASE_PRODUCTION").utility(memory)

    def _score_income(self, memory: Memory) -> float:
        return self.goal_library.by_name("SECURE_INCOME").utility(memory)

    def _score_cooperation(self, memory: Memory) -> float:
        return self.goal_library.by_name("COOPERATE").utility(memory)
