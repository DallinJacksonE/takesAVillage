class ActionGenerator:
    """
    The tactical GOAP planner. Contains specialized strategies to map 
    a broad goal into a specific, legally available action.
    """

    def __init__(self):
        pass

    def _find_by_command(self, actions: list, command: str) -> dict | None:
        """Helper to quickly extract a specific action type."""
        for a in actions:
            if a.get("action_command") == command:
                return a
        return None

    def get_survival_action(self, actions: list, memory: dict) -> dict | None:
        """
        GOAL: Stay alive.
        PLAN: Cure sickness -> Harvest Food -> Get a job for food.
        """
        # 1. Immediate Threat: Sickness
        if memory.get("sickness_chance", 0.0) > 0.0:
            campfire_action = self._find_by_command(actions, "CAMPFIRE")
            if campfire_action:
                return campfire_action

        # 2. Intermediate Step: We need food, do we have an accepted job?
        commit_work = self._find_by_command(actions, "COMMIT_WORK")
        if commit_work:
            # You would add logic here to check if the job yields food specifically
            return commit_work

        # 3. Base Precondition: We need a job that pays food
        employment = self._find_by_command(actions, "EMPLOYMENT")
        if employment:
            # Filter the employment payload for farms/food wages
            # return employment
            pass

        return None

    def get_expansion_action(self, actions: list, memory: dict) -> dict | None:
        """
        GOAL: Grow territory.
        PLAN: Build new -> Contest unowned -> Contest enemies.
        """
        build_action = self._find_by_command(actions, "BUILD")
        if build_action:
            return build_action

        contest_action = self._find_by_command(actions, "CONTEST")
        if contest_action:
            # You can cross-reference with memory["unowned_developments"] here
            return contest_action

        return None

    def get_maintenance_action(self, actions: list, memory: dict) -> dict | None:
        """
        GOAL: Keep what we have.
        PLAN: Upgrade -> Repair -> Work own base.
        """
        upgrade = self._find_by_command(actions, "UPGRADE")
        if upgrade:
            return upgrade

        return None

    def get_cooperation_action(self, actions: list, memory: dict) -> dict | None:
        """
        GOAL: Resolve network obligations.
        PLAN: Finalize contracts -> Accept trades.
        """
        finalize = self._find_by_command(actions, "FINALIZE")
        if finalize:
            return finalize

        accept = self._find_by_command(actions, "ACCEPT")
        if accept:
            return accept

        return None

    def get_income_action(self, actions: list, memory: dict) -> dict | None:
        """
        GOAL: Get resources quickly without building.
        PLAN: Trade -> Work for others.
        """
        trade = self._find_by_command(actions, "TRADE")
        if trade:
            return trade

        return self._find_by_command(actions, "EMPLOYMENT")
