from dataclasses import dataclass

from ..goap_genome import GOAPGenome
from ..memory import Memory


RESOURCE_TYPES = ("food", "wood", "iron")


@dataclass(frozen=True)
class ResourceValuator:
    """Genome-aware marginal resource valuation for action scoring.

    The legal action source only determines what can be attempted. This helper
    estimates how good or dangerous resource deltas are in the current state,
    with explicit reserve pressure so GOAP does not spend the last survival
    resources on low-value actions.
    """

    genome: GOAPGenome

    def action_utility(self, features: dict[str, float], memory: Memory) -> float:
        score = 0.0
        for resource in RESOURCE_TYPES:
            score += self.marginal_gain(resource, features.get(f"{resource}_delta", 0.0), memory)
            score -= self.marginal_cost(resource, features.get(f"{resource}_cost", 0.0), memory)
        score -= self.reserve_penalty(features, memory)
        return score

    def marginal_gain(self, resource: str, amount: float, memory: Memory) -> float:
        amount = max(0.0, float(amount or 0.0))
        if amount == 0.0:
            return 0.0
        total = 0.0
        current = float(memory.get(resource, 0) or 0)
        for step in range(int(amount)):
            total += self._unit_value(resource, current + step, memory)
        fractional = amount - int(amount)
        if fractional:
            total += fractional * self._unit_value(resource, current + int(amount), memory)
        return total

    def marginal_cost(self, resource: str, amount: float, memory: Memory) -> float:
        amount = max(0.0, float(amount or 0.0))
        if amount == 0.0:
            return 0.0
        total = 0.0
        current = float(memory.get(resource, 0) or 0)
        for step in range(int(amount)):
            total += self._unit_value(resource, max(0.0, current - step - 1.0), memory)
        fractional = amount - int(amount)
        if fractional:
            total += fractional * self._unit_value(resource, max(0.0, current - amount), memory)
        return total

    def reserve_penalty(self, features: dict[str, float], memory: Memory) -> float:
        """Extra penalty for spending below survival reserves."""
        penalty = 0.0
        phase = memory.get("phase")
        for resource in RESOURCE_TYPES:
            spent = float(features.get(f"{resource}_cost", 0.0) or 0.0)
            if spent <= 0.0:
                continue
            remaining = float(memory.get(resource, 0) or 0) - spent
            reserve = self._reserve_for(resource, phase, memory)
            if remaining < reserve:
                penalty += (reserve - remaining) * (1.0 + self.genome.survival_weight)
        return penalty

    def _reserve_for(self, resource: str, phase: str | None, memory: Memory) -> float:
        if resource == "food":
            return 1.0
        if resource == "wood":
            cold = memory.get("fire_status") == "COLD"
            return 1.0 if cold or phase in {"WORK", "NIGHT"} else 0.0
        return 0.0

    def _future_deficit_value(self, resource: str, memory: Memory) -> float:
        maintenance_deficit = float((memory.get("maintenance_resource_deficits", {}) or {}).get(resource, 0.0) or 0.0)
        upgrade_deficit = float((memory.get("upgrade_resource_deficits", {}) or {}).get(resource, 0.0) or 0.0)
        return (
            maintenance_deficit * (self.genome.maintain_weight + self.genome.survival_weight)
            + upgrade_deficit * (self.genome.upgrade_weight + self.genome.future_reward_weight)
        )

    def _unit_value(self, resource: str, inventory_level: float, memory: Memory) -> float:
        base = getattr(self.genome, f"{resource}_weight")
        desperation = getattr(self.genome, f"{resource}_desperation_weight")
        scarcity = 1.0 / (inventory_level + 1.0)
        urgency = GOAPGenome.positive_multiplier(self.genome.resource_urgency_curve)
        value = base + desperation * scarcity * urgency
        value += self._future_deficit_value(resource, memory)
        if resource == "wood" and memory.get("fire_status") == "COLD":
            value += self.genome.warmth_desperation_weight
        if resource == "food" and inventory_level <= 1.0:
            value += self.genome.survival_weight
        return max(0.0, value)
