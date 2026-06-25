from BaseBot import BaseBot
from models.goap_genetic.goap_genome import GOAPGenome
from models.goap_genetic.memory import DecisionContext

# We will build these modular files next
from .perception import Perception
from .thinking import Thinker
from .acting import Actuator


class GOAPGenetic(BaseBot):
    """
    A Goal-Oriented Action Planning bot that uses Genetic Weights 
    to evaluate broad goals, rather than scoring individual actions.
    """

    def __init__(self, genome: GOAPGenome | dict):
        super().__init__()
        self.genome = (
            genome if isinstance(genome, GOAPGenome)
            else GOAPGenome.from_dict(genome)
        )
        self.perception = Perception()
        self.thinker = Thinker(self.genome)
        self.actuator = Actuator(self.genome)

    @staticmethod
    def from_json(genome_json: dict):
        return GOAPGenetic(GOAPGenome.from_dict(genome_json))

    def choose_action(self, game_state: dict) -> dict | None:
        """
        The Master Override: The Sense-Think-Act Cycle.
        This function no longer contains complex logic; it only delegates.
        """
        # 0. Base Guardrails
        if game_state.get("status") == "WAITING":
            return None

        me = game_state.get("me", {})
        if self.is_dead_player(me):
            return None
        if me.get("finished_phase"):
            return None

        # --- 1. SENSE (Perception) ---
        # Translate the massive game_state JSON into a clean, typed Memory object.
        memory = self.perception.sense(game_state)

        # Handle hard-stops (like waiting on a pending application)
        if memory.get("is_waiting"):
            self.waiting = True
            return None
        self.waiting = False

        # --- 2. THINK (Decision) ---
        # Evaluate high-level goals using genetic weights and the current memory.
        # e.g., Returns a string or Goal object like "SURVIVE" or "EXPAND"
        winning_goal = self.thinker.evaluate_goals(memory)

        # --- 3. ACT (Execution) ---
        # Retrieve technically valid actions from BaseBot
        available_actions = self.get_available_actions(game_state)
        context = DecisionContext(memory=memory, legal_actions=available_actions)

        # If no actions are available, finish the phase
        if not context.legal_actions:
            return self.format_network_payload(None)

        # Formulate a plan to achieve the winning goal and extract the next logical action
        raw_action = self.actuator.act(
            winning_goal, context.legal_actions, context.memory)
        logger = getattr(self, "logger", None)
        if raw_action and logger and self.actuator.last_debug_explanation:
            logger.info(
                f"GOAP action explanation: {self.actuator.last_debug_explanation}")

        # 4. Use BaseBot to clean and format the final DTO for the server
        return self.format_network_payload(raw_action)
