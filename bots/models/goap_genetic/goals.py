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
