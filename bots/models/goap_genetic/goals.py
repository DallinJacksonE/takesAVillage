<<<<<<< HEAD
from dataclasses import dataclass
from typing import Callable

from .goap_genome import GOAPGenome
from .memory import Memory


UtilityFn = Callable[[Memory], float]
CompletionFn = Callable[[Memory], bool]
ProgressFn = Callable[[Memory, dict], float]


@dataclass(frozen=True)
class GOAPGoal:
    """Explicit desired world state for the GOAP planner."""
    name: str
    desired_state: dict
    utility: UtilityFn
    is_complete: CompletionFn
    progress: ProgressFn


class GoalLibrary:
    """Builds genome-weighted goals without hiding preferences in perception."""

    def __init__(self, genome: GOAPGenome):
        self.genome = genome
        self._goals = self._build_goals()

    def all_goals(self) -> list[GOAPGoal]:
        return list(self._goals)

    def by_name(self, name: str) -> GOAPGoal:
        for goal in self._goals:
            if goal.name == name:
                return goal
        raise KeyError(name)

    def _build_goals(self) -> list[GOAPGoal]:
        return [
            GOAPGoal(
                name="SURVIVE",
                desired_state={"alive": True, "sickness_risk_reduced": True},
                utility=self._survival_utility,
                is_complete=lambda memory: memory.get("health") == "dead",
                progress=self._survival_progress,
            ),
            GOAPGoal(
                name="SECURE_FOOD",
                desired_state={"food_delta": "positive"},
                utility=lambda memory: self._resource_need(memory, "food")
                * self.genome.food_desperation_weight,
                is_complete=lambda memory: memory.get("food", 0) > 0,
                progress=lambda memory, effects: effects.get("food_delta", 0)
                * self._resource_need(memory, "food")
                * (self.genome.food_desperation_weight + self.genome.food_weight),
            ),
            GOAPGoal(
                name="SECURE_WOOD",
                desired_state={"wood_delta": "positive"},
                utility=lambda memory: self._resource_need(memory, "wood")
                * self.genome.wood_desperation_weight,
                is_complete=lambda memory: memory.get("wood", 0) > 0,
                progress=lambda memory, effects: effects.get("wood_delta", 0)
                * self._resource_need(memory, "wood")
                * (self.genome.wood_desperation_weight + self.genome.wood_weight),
            ),
            GOAPGoal(
                name="SECURE_WARMTH",
                desired_state={"warmth": True},
                utility=lambda memory: (
                    self.genome.warmth_desperation_weight
                    if memory.get("fire_status") == "COLD" else 0.0
                ),
                is_complete=lambda memory: memory.get("fire_status") != "COLD",
                progress=lambda _memory, effects: effects.get("warmth", 0)
                * (self.genome.warmth_desperation_weight + self.genome.fire_weight),
            ),
            GOAPGoal(
                name="INCREASE_PRODUCTION",
                desired_state={"production_capacity": "increased"},
                utility=lambda _memory: (
                    self.genome.growth_weight + self.genome.build_weight
                ) * GOAPGenome.positive_multiplier(self.genome.production_discount_weight),
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("production_capacity", 0)
                * (self.genome.growth_weight + self.genome.build_weight)
                * GOAPGenome.positive_multiplier(self.genome.production_discount_weight),
            ),
            GOAPGoal(
                name="PRESERVE_ASSETS",
                desired_state={"asset_preservation": True},
                utility=lambda memory: len(memory.get("my_developments", []))
                * self.genome.maintain_weight
                * GOAPGenome.positive_multiplier(self.genome.maintenance_urgency_weight),
                is_complete=lambda memory: not memory.get("my_developments"),
                progress=lambda _memory, effects: effects.get("asset_preservation", 0)
                * self.genome.maintain_weight
                * GOAPGenome.positive_multiplier(self.genome.maintenance_urgency_weight),
            ),
            GOAPGoal(
                name="IMPROVE_ASSETS",
                desired_state={"asset_level": "increased"},
                utility=lambda memory: len(memory.get("my_developments", []))
                * self.genome.upgrade_weight,
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("asset_level_delta", 0)
                * self.genome.upgrade_weight,
            ),
            GOAPGoal(
                name="SECURE_INCOME",
                desired_state={"resource_delta": "positive"},
                utility=lambda _memory: (
                    self.genome.work_weight
                    + self.genome.immediate_reward_weight
                    + self.genome.employment_wage_weight
                    + self.genome.employer_exploitation_weight
                ),
                is_complete=lambda _memory: False,
                progress=self._income_progress,
            ),
            GOAPGoal(
                name="RESOLVE_OBLIGATIONS",
                desired_state={"obligations_resolved": True},
                utility=lambda memory: len(memory.get("pending_contracts", []))
                * (self.genome.cooperation_weight
                   + self.genome.reputation_weight
                   + self.genome.finalize_honesty_weight),
                is_complete=lambda memory: not memory.get("pending_contracts"),
                progress=lambda _memory, effects: effects.get("obligation_resolution", 0)
                * (self.genome.cooperation_weight
                   + self.genome.reputation_weight
                   + self.genome.finalize_honesty_weight),
            ),
            GOAPGoal(
                name="TRADE_TOWARD_SCARCITY",
                desired_state={"trade_option": True},
                utility=lambda _memory: (
                    self.genome.trade_deception_weight
                    + self.genome.trade_fairness_weight
                    + self.genome.risk_weight
                ),
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("trade_option", 0)
                * (self.genome.trade_deception_weight
                   + self.genome.trade_fairness_weight
                   + self.genome.risk_weight),
            ),
            GOAPGoal(
                name="CONTEST_VALUE",
                desired_state={"contest_value": True},
                utility=lambda memory: len(memory.get("other_player_developments", []))
                * (self.genome.aggression_weight + self.genome.contest_weight),
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("contest_value", 0)
                * (self.genome.aggression_weight + self.genome.contest_weight),
            ),
            GOAPGoal(
                name="COOPERATE",
                desired_state={"cooperation": True},
                utility=lambda memory: len(memory.get("pending_contracts", []))
                * (self.genome.cooperation_weight
                   + self.genome.campfire_accept_weight),
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("cooperation", 0)
                * (self.genome.cooperation_weight
                   + self.genome.campfire_accept_weight),
            ),
        ]

    def _resource_need(self, memory: Memory, resource: str) -> float:
        return (
            1.0 / (memory.get(resource, 0) + 1.0)
            * GOAPGenome.positive_multiplier(self.genome.resource_urgency_curve)
        )

    def _survival_utility(self, memory: Memory) -> float:
        score = 0.0
        score += self._resource_need(memory, "food") * self.genome.food_desperation_weight
        score += self._resource_need(memory, "wood") * self.genome.wood_desperation_weight
        if memory.get("fire_status") == "COLD":
            score += self.genome.warmth_desperation_weight
        score += memory.get("sickness_chance", 0.0) * self.genome.sickness_desperation_weight * GOAPGenome.positive_multiplier(self.genome.health_risk_weight)
        return score * self.genome.survival_weight * GOAPGenome.positive_multiplier(self.genome.survival_urgency_weight)

    def _survival_progress(self, memory: Memory, effects: dict) -> float:
        score = 0.0
        score += effects.get("warmth", 0) * (self.genome.fire_weight + self.genome.warmth_desperation_weight)
        score += effects.get("food_delta", 0) * self._resource_need(memory, "food") * self.genome.food_desperation_weight
        score += effects.get("wood_delta", 0) * self._resource_need(memory, "wood") * self.genome.wood_desperation_weight
        score += effects.get("sickness_risk_delta", 0) * self.genome.sickness_desperation_weight
        return score

    def _income_progress(self, memory: Memory, effects: dict) -> float:
        wage_multiplier = GOAPGenome.positive_multiplier(
            self.genome.employment_wage_weight)
        return wage_multiplier * (
            effects.get("food_delta", 0) * (self.genome.food_weight + self._resource_need(memory, "food") * self.genome.food_desperation_weight)
            + effects.get("wood_delta", 0) * (self.genome.wood_weight + self._resource_need(memory, "wood") * self.genome.wood_desperation_weight)
            + effects.get("iron_delta", 0) * (self.genome.iron_weight + self._resource_need(memory, "iron") * self.genome.iron_desperation_weight)
        )
=======
from dataclasses import dataclass
from typing import Callable

from .goap_genome import GOAPGenome
from .memory import Memory


UtilityFn = Callable[[Memory], float]
CompletionFn = Callable[[Memory], bool]
ProgressFn = Callable[[Memory, dict], float]


@dataclass(frozen=True)
class GOAPGoal:
    """Explicit desired world state for the GOAP planner."""
    name: str
    desired_state: dict
    utility: UtilityFn
    is_complete: CompletionFn
    progress: ProgressFn


class GoalLibrary:
    """Builds genome-weighted goals without hiding preferences in perception."""

    def __init__(self, genome: GOAPGenome):
        self.genome = genome
        self._goals = self._build_goals()

    def all_goals(self) -> list[GOAPGoal]:
        return list(self._goals)

    def available_goals(self, memory: Memory) -> list[GOAPGoal]:
        phase = memory.get("phase")
        phase_goal_names = {
            "WORK": [
                "SURVIVE", "SECURE_FOOD", "SECURE_WOOD",
                "STAFF_PRODUCTION", "MAINTAIN_PRODUCTION",
                "GATHER_MAINTENANCE_RESOURCES", "UPGRADE_PRODUCTION",
                "GATHER_UPGRADE_RESOURCES", "PRESERVE_ASSETS", "IMPROVE_ASSETS",
                "SECURE_INCOME", "INCREASE_PRODUCTION", "CONTEST_VALUE",
            ],
            "TRADE": [
                "SURVIVE", "SECURE_FOOD", "SECURE_WOOD",
                "RESOLVE_OBLIGATIONS", "TRADE_TOWARD_SCARCITY", "COOPERATE",
            ],
            "NIGHT": [
                "SECURE_WARMTH", "SURVIVE", "COOPERATE",
                "RESOLVE_OBLIGATIONS",
            ],
        }
        names = phase_goal_names.get(phase, [goal.name for goal in self._goals])
        goals_by_name = {goal.name: goal for goal in self._goals}
        return [
            goals_by_name[name]
            for name in names
            if name in goals_by_name and not goals_by_name[name].is_complete(memory)
        ]

    def by_name(self, name: str) -> GOAPGoal:
        for goal in self._goals:
            if goal.name == name:
                return goal
        raise KeyError(name)

    def _build_goals(self) -> list[GOAPGoal]:
        return [
            GOAPGoal(
                name="SURVIVE",
                desired_state={"alive": True, "sickness_risk_reduced": True},
                utility=self._survival_utility,
                is_complete=lambda memory: not self._has_survival_pressure(memory),
                progress=self._survival_progress,
            ),
            GOAPGoal(
                name="SECURE_FOOD",
                desired_state={"food_delta": "positive"},
                utility=lambda memory: self._resource_need(memory, "food")
                * self.genome.food_desperation_weight,
                is_complete=lambda memory: memory.get("food", 0) >= 3,
                progress=lambda memory, effects: effects.get("food_delta", 0)
                * self._resource_need(memory, "food")
                * (self.genome.food_desperation_weight + self.genome.food_weight),
            ),
            GOAPGoal(
                name="SECURE_WOOD",
                desired_state={"wood_delta": "positive"},
                utility=lambda memory: self._resource_need(memory, "wood")
                * self.genome.wood_desperation_weight,
                is_complete=lambda memory: memory.get("wood", 0) >= self._wood_target(memory),
                progress=lambda memory, effects: effects.get("wood_delta", 0)
                * self._resource_need(memory, "wood")
                * (self.genome.wood_desperation_weight + self.genome.wood_weight),
            ),
            GOAPGoal(
                name="SECURE_WARMTH",
                desired_state={"warmth": True},
                utility=lambda memory: (
                    self.genome.warmth_desperation_weight
                    if memory.get("fire_status") == "COLD" else 0.0
                ),
                is_complete=lambda memory: memory.get("fire_status") != "COLD",
                progress=lambda _memory, effects: effects.get("warmth", 0)
                * (self.genome.warmth_desperation_weight + self.genome.fire_weight),
            ),
            GOAPGoal(
                name="INCREASE_PRODUCTION",
                desired_state={"production_capacity": "increased"},
                utility=lambda _memory: (
                    self.genome.growth_weight + self.genome.build_weight
                ) * GOAPGenome.positive_multiplier(self.genome.production_discount_weight),
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("production_capacity", 0)
                * (self.genome.growth_weight + self.genome.build_weight)
                * GOAPGenome.positive_multiplier(self.genome.production_discount_weight),
            ),
            GOAPGoal(
                name="PRESERVE_ASSETS",
                desired_state={"asset_preservation": True},
                utility=self._preserve_assets_utility,
                is_complete=lambda memory: self._maintenance_pressure(memory) == 0.0,
                progress=lambda memory, effects: effects.get("asset_preservation", 0)
                * self.genome.maintain_weight
                * self._maintenance_pressure(memory),
            ),
            GOAPGoal(
                name="IMPROVE_ASSETS",
                desired_state={"asset_level": "increased"},
                utility=lambda memory: len(memory.get("my_developments", []))
                * self.genome.upgrade_weight,
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("asset_level_delta", 0)
                * self.genome.upgrade_weight,
            ),
            GOAPGoal(
                name="STAFF_PRODUCTION",
                desired_state={"owned_development_worked": True},
                utility=lambda memory: len(memory.get("workable_owned_developments", []) or [])
                * (self.genome.work_weight + self.genome.future_reward_weight),
                is_complete=lambda memory: not memory.get("workable_owned_developments"),
                progress=lambda _memory, effects: (
                    effects.get("owned_work_output", 0)
                    + effects.get("production_delta", 0)
                ) * (self.genome.work_weight + self.genome.future_reward_weight),
            ),
            GOAPGoal(
                name="MAINTAIN_PRODUCTION",
                desired_state={"maintenance_secured": True},
                utility=self._maintain_production_utility,
                is_complete=lambda memory: (
                    not memory.get("at_risk_developments")
                    or bool(memory.get("maintenance_resource_deficits"))
                ),
                progress=lambda _memory, effects: (
                    effects.get("maintenance_loss_avoided", 0)
                    + effects.get("asset_preservation", 0)
                ) * self.genome.maintain_weight,
            ),
            GOAPGoal(
                name="GATHER_MAINTENANCE_RESOURCES",
                desired_state={"maintenance_resources_available": True},
                utility=lambda memory: self._deficit_total(memory, "maintenance_resource_deficits")
                * (self.genome.maintain_weight + self.genome.survival_weight),
                is_complete=lambda memory: not memory.get("maintenance_resource_deficits"),
                progress=lambda memory, effects: self._resource_deficit_progress(
                    memory, effects, "maintenance_resource_deficits")
                * (self.genome.maintain_weight + self.genome.survival_weight),
            ),
            GOAPGoal(
                name="UPGRADE_PRODUCTION",
                desired_state={"upgrade_roi_realized": True},
                utility=self._upgrade_production_utility,
                is_complete=lambda memory: (
                    not memory.get("upgradable_developments")
                    or bool(memory.get("upgrade_resource_deficits"))
                    or self._has_survival_pressure(memory)
                ),
                progress=lambda _memory, effects: (
                    effects.get("upgrade_roi", 0)
                    + effects.get("asset_level_delta", 0)
                ) * (self.genome.upgrade_weight + self.genome.future_reward_weight),
            ),
            GOAPGoal(
                name="GATHER_UPGRADE_RESOURCES",
                desired_state={"upgrade_resources_available": True},
                utility=lambda memory: self._deficit_total(memory, "upgrade_resource_deficits")
                * (self.genome.upgrade_weight + self.genome.future_reward_weight)
                * self._development_safety_multiplier(memory),
                is_complete=lambda memory: (
                    not memory.get("upgrade_resource_deficits")
                    or self._has_survival_pressure(memory)
                ),
                progress=lambda memory, effects: self._resource_deficit_progress(
                    memory, effects, "upgrade_resource_deficits")
                * (self.genome.upgrade_weight + self.genome.future_reward_weight),
            ),
            GOAPGoal(
                name="SECURE_INCOME",
                desired_state={"resource_delta": "positive"},
                utility=lambda _memory: (
                    self.genome.work_weight
                    + self.genome.immediate_reward_weight
                    + self.genome.employment_wage_weight
                    + self.genome.employer_exploitation_weight
                ),
                is_complete=lambda _memory: False,
                progress=self._income_progress,
            ),
            GOAPGoal(
                name="RESOLVE_OBLIGATIONS",
                desired_state={"obligations_resolved": True},
                utility=lambda memory: len(memory.get("pending_contracts", []))
                * (self.genome.cooperation_weight
                   + self.genome.reputation_weight
                   + self.genome.finalize_honesty_weight),
                is_complete=lambda memory: not memory.get("pending_contracts"),
                progress=lambda _memory, effects: effects.get("obligation_resolution", 0)
                * (self.genome.cooperation_weight
                   + self.genome.reputation_weight
                   + self.genome.finalize_honesty_weight),
            ),
            GOAPGoal(
                name="TRADE_TOWARD_SCARCITY",
                desired_state={"trade_option": True},
                utility=lambda _memory: (
                    self.genome.trade_deception_weight
                    + self.genome.trade_fairness_weight
                    + self.genome.risk_weight
                ),
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("trade_option", 0)
                * (self.genome.trade_deception_weight
                   + self.genome.trade_fairness_weight
                   + self.genome.risk_weight),
            ),
            GOAPGoal(
                name="CONTEST_VALUE",
                desired_state={"contest_value": True},
                utility=lambda memory: len(memory.get("other_player_developments", []))
                * (self.genome.aggression_weight + self.genome.contest_weight),
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("contest_value", 0)
                * (self.genome.aggression_weight + self.genome.contest_weight),
            ),
            GOAPGoal(
                name="COOPERATE",
                desired_state={"cooperation": True},
                utility=lambda memory: len(memory.get("pending_contracts", []))
                * (self.genome.cooperation_weight
                   + self.genome.campfire_accept_weight),
                is_complete=lambda _memory: False,
                progress=lambda _memory, effects: effects.get("cooperation", 0)
                * (self.genome.cooperation_weight
                   + self.genome.campfire_accept_weight),
            ),
        ]

    def _deficit_total(self, memory: Memory, key: str) -> float:
        return float(sum((memory.get(key, {}) or {}).values()))

    def _resource_deficit_progress(self, memory: Memory, effects: dict, key: str) -> float:
        deficits = memory.get(key, {}) or {}
        progress = 0.0
        for resource, needed in deficits.items():
            progress += min(float(needed), float(effects.get(f"{resource}_delta", 0.0) or 0.0))
        return progress

    def _development_safety_multiplier(self, memory: Memory) -> float:
        if self._has_survival_pressure(memory):
            return 0.0
        if memory.get("at_risk_developments") and memory.get("maintenance_resource_deficits"):
            return 0.0
        return 1.0

    def _maintain_production_utility(self, memory: Memory) -> float:
        at_risk_count = len(memory.get("at_risk_developments", []) or [])
        if at_risk_count == 0 or memory.get("maintenance_resource_deficits"):
            return 0.0
        return (
            at_risk_count
            * self.genome.maintain_weight
            * GOAPGenome.positive_multiplier(self.genome.maintenance_urgency_weight)
        )

    def _upgrade_production_utility(self, memory: Memory) -> float:
        opportunity = float(sum((memory.get("upgrade_opportunity_value_by_resource", {}) or {}).values()))
        if opportunity <= 0.0:
            return 0.0
        return (
            opportunity
            * (self.genome.upgrade_weight + self.genome.future_reward_weight)
            * GOAPGenome.positive_multiplier(self.genome.production_discount_weight)
            * self._development_safety_multiplier(memory)
        )

    def _resource_need(self, memory: Memory, resource: str) -> float:
        return (
            1.0 / (memory.get(resource, 0) + 1.0)
            * GOAPGenome.positive_multiplier(self.genome.resource_urgency_curve)
        )

    def _wood_target(self, memory: Memory) -> int:
        return 2 if memory.get("fire_status") == "COLD" or memory.get("phase") in {"WORK", "NIGHT"} else 1

    def _has_survival_pressure(self, memory: Memory) -> bool:
        return (
            memory.get("health") in {"sick", "recovering"}
            or memory.get("food", 0) <= 1
            or memory.get("fire_status") == "COLD"
            or float(memory.get("sickness_chance", 0.0) or 0.0) > 0.25
        )

    def _maintenance_pressure(self, memory: Memory) -> float:
        pressure = 0.0
        for dev in memory.get("my_developments", []) or []:
            days = float(dev.get("maintenance_days", 0) or 0)
            pressure += max(0.0, 3.0 - days) / 3.0
        return pressure

    def _preserve_assets_utility(self, memory: Memory) -> float:
        return (
            self._maintenance_pressure(memory)
            * self.genome.maintain_weight
            * GOAPGenome.positive_multiplier(self.genome.maintenance_urgency_weight)
        )

    def _survival_utility(self, memory: Memory) -> float:
        score = 0.0
        score += self._resource_need(memory, "food") * self.genome.food_desperation_weight
        score += self._resource_need(memory, "wood") * self.genome.wood_desperation_weight
        if memory.get("fire_status") == "COLD":
            score += self.genome.warmth_desperation_weight
        score += memory.get("sickness_chance", 0.0) * self.genome.sickness_desperation_weight * GOAPGenome.positive_multiplier(self.genome.health_risk_weight)
        return score * self.genome.survival_weight * GOAPGenome.positive_multiplier(self.genome.survival_urgency_weight)

    def _survival_progress(self, memory: Memory, effects: dict) -> float:
        score = 0.0
        score += effects.get("warmth", 0) * (self.genome.fire_weight + self.genome.warmth_desperation_weight)
        score += effects.get("food_delta", 0) * self._resource_need(memory, "food") * self.genome.food_desperation_weight
        score += effects.get("wood_delta", 0) * self._resource_need(memory, "wood") * self.genome.wood_desperation_weight
        score += effects.get("sickness_risk_delta", 0) * self.genome.sickness_desperation_weight
        return score

    def _income_progress(self, memory: Memory, effects: dict) -> float:
        wage_multiplier = GOAPGenome.positive_multiplier(
            self.genome.employment_wage_weight)
        return wage_multiplier * (
            effects.get("food_delta", 0) * (self.genome.food_weight + self._resource_need(memory, "food") * self.genome.food_desperation_weight)
            + effects.get("wood_delta", 0) * (self.genome.wood_weight + self._resource_need(memory, "wood") * self.genome.wood_desperation_weight)
            + effects.get("iron_delta", 0) * (self.genome.iron_weight + self._resource_need(memory, "iron") * self.genome.iron_desperation_weight)
        )
>>>>>>> 5aae65484608285345edeb4ee838d500ef4f5a69
