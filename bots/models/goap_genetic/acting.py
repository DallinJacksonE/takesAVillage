from .action_generator import ActionGenerator


class Actuator:
    """
    The Act module. Takes the winning goal and asks the ActionGenerator 
    to provide the best tactical move from the legally available actions.
    """

    def __init__(self):
        self.generator = ActionGenerator()

    def act(self, winning_goal: str, available_actions: list, memory: dict) -> dict | None:
        """
        Routes the winning goal to the appropriate strategy generator.
        """
        chosen_action = None

        if winning_goal == "SURVIVE":
            chosen_action = self.generator.get_survival_action(
                available_actions, memory)

        elif winning_goal == "EXPAND_TERRITORY":
            chosen_action = self.generator.get_expansion_action(
                available_actions, memory)

        elif winning_goal == "MAINTAIN_ASSETS":
            chosen_action = self.generator.get_maintenance_action(
                available_actions, memory)

        elif winning_goal == "SECURE_INCOME":
            chosen_action = self.generator.get_income_action(
                available_actions, memory)

        elif winning_goal == "COOPERATE":
            chosen_action = self.generator.get_cooperation_action(
                available_actions, memory)

        # --- The Fallback Subsumption Architecture ---

        if chosen_action is None:
            chosen_action = self.generator.get_income_action(
                available_actions, memory)

        return chosen_action
