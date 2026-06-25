from .domain import Command
from .goap_genome import GOAPGenome
from .memory import Memory


class ActionGenerator:
    """
    The tactical GOAP planner. Contains specialized strategies to map 
    a broad goal into a specific, legally available action.
    """

    def __init__(self, genome: GOAPGenome | None = None):
        self.genome = genome or GOAPGenome()

    def _find_by_command(self, actions: list, command: str) -> dict | None:
        """Helper to quickly extract a specific action type."""
        for a in actions:
            if a.get("action_command") == command:
                return a
        return None

    def _find_all_by_command(self, actions: list, command: str) -> list[dict]:
        return [a for a in actions if a.get("action_command") == command]

    def _resource_value(self, bundle: dict | None, memory: Memory) -> float:
        bundle = bundle or {}
        return (
            bundle.get("food", 0) * self.genome.food_weight
            + bundle.get("wood", 0) * self.genome.wood_weight
            + bundle.get("iron", 0) * self.genome.iron_weight
        )

    def _survival_resource_value(self, bundle: dict | None,
                                 memory: Memory) -> float:
        bundle = bundle or {}
        urgency_curve = GOAPGenome.positive_multiplier(
            self.genome.resource_urgency_curve)
        food_need = (
            self.genome.food_desperation_weight * urgency_curve
            / (memory.get("food", 0) + 1.0))
        wood_need = (
            self.genome.wood_desperation_weight * urgency_curve
            / (memory.get("wood", 0) + 1.0))
        iron_need = (
            self.genome.iron_desperation_weight * urgency_curve
            / (memory.get("iron", 0) + 1.0))
        return (
            bundle.get("food", 0) * (self.genome.food_weight + food_need)
            + bundle.get("wood", 0) * (self.genome.wood_weight + wood_need)
            + bundle.get("iron", 0) * (self.genome.iron_weight + iron_need)
        )

    def _job_value(self, action: dict, memory: Memory) -> float:
        payload = action.get("payload", {})
        job = payload.get("job", {})
        wage_type = payload.get("wage_type") or job.get("wage_type")
        wage = payload.get("wage", job.get("wage", 0))
        if not wage_type:
            return self.genome.work_weight
        return (
            self.genome.work_weight
            + self.genome.employment_wage_weight
            + self._survival_resource_value(
                {wage_type: wage}, memory)
        )

    def _best_by_score(self, actions: list[dict], scorer) -> dict | None:
        if not actions:
            return None
        return max(actions, key=scorer)

    def _development_type_value(self, development_type: str | None,
                                memory: Memory) -> float:
        if development_type == "Farm":
            return (
                self.genome.farm_preference
                + self._survival_resource_value({"food": 1}, memory)
            )
        if development_type == "Woods":
            return (
                self.genome.woods_preference
                + self._survival_resource_value({"wood": 1}, memory)
            )
        if development_type == "Mine":
            return (
                self.genome.mine_preference
                + self._survival_resource_value({"iron": 1}, memory)
            )
        return 0.0

    def _build_value(self, action: dict, memory: Memory) -> float:
        tile_type = action.get("payload", {}).get("_tile_type")
        return self.genome.build_weight + self._development_type_value(
            tile_type, memory)

    def get_survival_action(self, actions: list, memory: Memory) -> dict | None:
        """
        GOAL: Stay alive.
        PLAN: Cure sickness -> Harvest Food -> Get a job for food.
        """
        # Night warmth is a direct survival effect in the current game rules.
        start_fire = self._find_by_command(actions, Command.START_FIRE)
        if start_fire:
            return start_fire

        campfire_requests = [
            a for a in self._find_all_by_command(actions, Command.CAMPFIRE)
            if a.get("payload", {}).get("is_request")
        ]
        if campfire_requests:
            return self._best_by_score(
                campfire_requests,
                lambda _a: (
                    self.genome.survival_weight
                    + self.genome.fire_guest_weight
                    + self.genome.cooperation_weight
                )
            )

        # 2. Intermediate Step: We need food, do we have an accepted job?
        commit_work = self._best_by_score(
            self._find_all_by_command(actions, Command.COMMIT_WORK),
            lambda action: self._job_value(action, memory)
        )
        if commit_work:
            return commit_work

        # 3. Base Precondition: We need a job that pays food
        employment = self._best_by_score(
            self._find_all_by_command(actions, Command.EMPLOYMENT),
            lambda action: self._job_value(action, memory)
        )
        if employment:
            return employment

        return None

    def get_expansion_action(self, actions: list, memory: Memory) -> dict | None:
        """
        GOAL: Grow territory.
        PLAN: Build new -> Contest unowned -> Contest enemies.
        """
        build_action = self._best_by_score(
            self._find_all_by_command(actions, Command.BUILD_DEV),
            lambda action: self._build_value(action, memory)
        )
        if build_action:
            return build_action

        contest_action = self._find_by_command(actions, Command.CONTEST_DEV)
        if contest_action:
            # You can cross-reference with memory["unowned_developments"] here
            return contest_action

        return None

    def get_maintenance_action(self, actions: list, memory: Memory) -> dict | None:
        """
        GOAL: Keep what we have.
        PLAN: Upgrade -> Repair -> Work own base.
        """
        upgrade = self._find_by_command(actions, Command.UPGRADE_DEV)
        if upgrade:
            return upgrade

        return None

    def get_cooperation_action(self, actions: list, memory: Memory) -> dict | None:
        """
        GOAL: Resolve network obligations.
        PLAN: Finalize contracts -> Accept trades.
        """
        finalize = self._find_by_command(actions, Command.FINALIZE)
        if finalize:
            return finalize

        accept = self._find_by_command(actions, Command.ACCEPT)
        if accept:
            return accept

        return None

    def get_income_action(self, actions: list, memory: Memory) -> dict | None:
        """
        GOAL: Get resources quickly without building.
        PLAN: Trade -> Work for others.
        """
        trade = self._find_by_command(actions, Command.TRADE)
        if trade:
            return trade

        return self._find_by_command(actions, Command.EMPLOYMENT)
