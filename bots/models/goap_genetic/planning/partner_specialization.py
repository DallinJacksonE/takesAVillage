from dataclasses import dataclass

from ..memory import Memory


RESOURCE_TYPES = ("food", "wood", "iron")
DEVELOPMENT_RESOURCE = {"Farm": "food", "Woods": "wood", "Mine": "iron"}


@dataclass(frozen=True)
class PartnerSpecialistAnalyzer:
    """Derives factual partner specialization and trust signals.

    This helper stays model-local and preference-light. It summarizes visible
    production capacity and relationship sentiment so goals, legal action
    generation, and action scoring can decide whether cooperation is worthwhile.
    """

    def analyze(self, memory: Memory) -> dict[str, dict]:
        production = self.partner_production_by_resource(memory)
        specializations = self.partner_specializations(production)
        trusted_scores = self.trusted_partner_scores(memory)
        complementary_scores = self.complementary_partner_scores(
            memory, production)
        support_needs = self.partner_support_needs(memory, production)
        return {
            "partner_production_by_resource": production,
            "partner_specializations": specializations,
            "trusted_partner_scores": trusted_scores,
            "complementary_partner_scores": complementary_scores,
            "partner_support_needs": support_needs,
        }

    def partner_production_by_resource(self, memory: Memory) -> dict[str, dict[str, float]]:
        production: dict[str, dict[str, float]] = {}
        my_id = memory.get("my_id")
        for dev in memory.get("other_player_developments", []) or []:
            owner_id = dev.get("owner_id")
            if not owner_id or owner_id == my_id:
                continue
            resource = DEVELOPMENT_RESOURCE.get(dev.get("type"))
            if not resource:
                continue
            owner_production = production.setdefault(owner_id, {})
            owner_production[resource] = owner_production.get(
                resource, 0.0) + self._development_output(dev)
        return production

    def partner_specializations(self, production: dict[str, dict[str, float]]) -> dict[str, str]:
        specializations = {}
        for player_id, resources in production.items():
            if not resources:
                continue
            resource, amount = max(resources.items(), key=lambda item: item[1])
            if amount > 0.0:
                specializations[player_id] = resource
        return specializations

    def trusted_partner_scores(self, memory: Memory) -> dict[str, float]:
        scores = {}
        for player_id, relationship in (memory.get("relationships", {}) or {}).items():
            confidence = self._float(relationship.get("confidence"))
            positive = (
                self._float(relationship.get("trust"))
                + 0.5 * self._float(relationship.get("fairness"))
                + 0.25 * self._float(relationship.get("generosity"))
                + 0.25 * self._float(relationship.get("reciprocity"))
            )
            hostility = self._float(relationship.get("hostility"))
            scores[player_id] = confidence * (positive - hostility)
        return scores

    def complementary_partner_scores(
        self,
        memory: Memory,
        production: dict[str, dict[str, float]],
    ) -> dict[str, float]:
        needs = self._needed_resources(memory)
        scores = {}
        for player_id, resources in production.items():
            score = 0.0
            for resource, amount in resources.items():
                score += amount * needs.get(resource, 0.0)
            if score > 0.0:
                scores[player_id] = score
        return scores

    def partner_support_needs(
        self,
        memory: Memory,
        production: dict[str, dict[str, float]],
    ) -> dict[str, dict[str, float]]:
        """Infer resources partners may need from visible complementary gaps.

        Without private inventories, support opportunities stay conservative:
        partners are considered likely to need resources they do not visibly
        produce, especially when we have surplus above a survival reserve.
        """
        surplus = self._surplus_resources(memory)
        needs = {}
        for player_id, resources in production.items():
            player_needs = {}
            for resource, amount in surplus.items():
                if amount <= 0.0 or resources.get(resource, 0.0) > 0.0:
                    continue
                player_needs[resource] = amount
            if player_needs:
                needs[player_id] = player_needs
        return needs

    def _needed_resources(self, memory: Memory) -> dict[str, float]:
        needs = {}
        for resource in RESOURCE_TYPES:
            current = self._float(memory.get(resource))
            scarcity = 1.0 / (current + 1.0)
            maintenance = self._float(
                (memory.get("maintenance_resource_deficits", {}) or {}).get(resource))
            upgrade = self._float(
                (memory.get("upgrade_resource_deficits", {}) or {}).get(resource))
            needs[resource] = scarcity + maintenance + upgrade
        return needs

    def _surplus_resources(self, memory: Memory) -> dict[str, float]:
        return {
            resource: max(0.0, self._float(memory.get(resource)) - self._reserve_for(resource, memory))
            for resource in RESOURCE_TYPES
        }

    def _reserve_for(self, resource: str, memory: Memory) -> float:
        if resource == "food":
            return 1.0
        if resource == "wood" and memory.get("fire_status") == "COLD":
            return 1.0
        future_need = self._float(
            (memory.get("maintenance_resource_deficits", {}) or {}).get(resource))
        return future_need

    def _development_output(self, dev: dict) -> float:
        return max(0.0, self._float(dev.get("level"), default=1.0))

    def _float(self, value, default: float = 0.0) -> float:
        try:
            return float(value if value is not None else default)
        except (TypeError, ValueError):
            return default
