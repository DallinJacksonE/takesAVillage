from dataclasses import dataclass

from .domain import Command
from .goap_genome import GOAPGenome
from .memory import Memory


RESOURCE_TYPES = ("food", "wood", "iron")
DEVELOPMENT_PRODUCTION = {
    "Farm": "food",
    "Woods": "wood",
    "Mine": "iron",
}


@dataclass(frozen=True)
class ActionUtilityEvaluation:
    """Genome-weighted utility score for factual action features."""
    score: float
    weights: dict[str, float]
    contributions: dict[str, float]

    def top_features(self, limit: int = 3) -> list[str]:
        ranked = sorted(
            self.contributions.items(),
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        return [name for name, value in ranked[:limit] if value != 0.0]


class ActionFeatureCalculator:
    """Calculates factual, normalized features for a legal server action.

    This layer intentionally does not decide whether a feature is good or bad.
    It only describes observable action consequences in a common vocabulary so
    genome weights can express preference separately.
    """

    def calculate(self, action: dict, memory: Memory) -> dict[str, float]:
        command = action.get("action_command")
        payload = action.get("payload", {})
        features: dict[str, float] = {}

        if command == Command.EMPLOYMENT:
            self._add_wage_features(features, payload)
            features["contract_obligation"] = 1.0
            features["social_exposure"] = 1.0
            self._add_counterparty_sentiment(
                features, payload.get("target_id"), memory)
        elif command == Command.COMMIT_WORK:
            self._add_wage_features(features, payload.get("job", {}))
            features["helps_self"] = 1.0
            self._add_counterparty_sentiment(
                features, payload.get("job", {}).get("employer_id"), memory)
        elif command == Command.BUILD_DEV:
            tile_type = payload.get("_tile_type")
            self._add_resource_cost(features, self._build_cost(tile_type, memory))
            self._add_production_features(features, tile_type, memory, level=1.0)
            features["helps_self"] = 1.0
        elif command in (Command.UPGRADE_DEV, Command.MAINTAIN_DEV, Command.CONTEST_DEV):
            dev = self._development_for_action(payload, memory)
            if dev:
                if command == Command.UPGRADE_DEV:
                    self._add_resource_cost(features, dev.get("upgrade_cost", {}))
                    self._add_production_features(
                        features,
                        dev.get("type"),
                        memory,
                        level=float(dev.get("level", 1) + 1),
                    )
                elif command == Command.MAINTAIN_DEV:
                    self._add_resource_cost(features, dev.get("maintenance_cost", {}))
                    features["maintenance_days_saved"] = self._remaining_day_fraction(
                        memory,
                        float(dev.get("maintenance_days", 0)),
                    )
                else:
                    features["contested_value"] = self._development_value(dev, memory)
                    side = payload.get("side")
                    if side == "INITIATOR":
                        features["harms_other"] = 1.0
                    elif side == "OWNER":
                        features["helps_self"] = 1.0 if dev.get("owner_id") == memory.get("my_id") else 0.0
                        features["helps_other"] = 0.0 if dev.get("owner_id") == memory.get("my_id") else 1.0
                    elif side == "CONTESTER":
                        features["helps_other"] = 1.0
        elif command == Command.START_FIRE:
            self._add_resource_cost(features, memory.get("campfire_cost", {}))
            features["fire_risk_delta"] = self._fire_risk_delta(memory)
            features["helps_self"] = 1.0
        elif command == Command.CAMPFIRE:
            features["fire_risk_delta"] = self._fire_risk_delta(memory)
            self._add_counterparty_sentiment(
                features, payload.get("target_id"), memory)
            if payload.get("is_request"):
                features["helps_self"] = 1.0
            else:
                features["helps_other"] = 1.0
                features["social_exposure"] = 1.0
        elif command in (Command.ACCEPT, Command.DENY, Command.FINALIZE):
            contract = self._contract_for_action(payload, memory)
            if contract:
                self._add_contract_features(features, command, contract, memory)
        elif command == Command.TRADE:
            self._add_trade_bundle_features(
                features,
                given=payload.get("offer_items", {}),
                received=payload.get("request_items", {}),
            )
            features["social_exposure"] = 1.0
            self._add_counterparty_sentiment(
                features, payload.get("target_id"), memory)

        return {key: float(value) for key, value in features.items() if value != 0.0}

    def _add_wage_features(self, features: dict[str, float], wage_source: dict) -> None:
        wage_type = wage_source.get("wage_type")
        wage = float(wage_source.get("wage", 0) or 0)
        if wage_type in RESOURCE_TYPES and wage:
            features[f"{wage_type}_delta"] = features.get(f"{wage_type}_delta", 0.0) + wage
            features["resource_delta"] = features.get("resource_delta", 0.0) + wage

    def _add_resource_cost(self, features: dict[str, float], cost: dict | None) -> None:
        cost = cost or {}
        total = 0.0
        for resource in RESOURCE_TYPES:
            amount = float(cost.get(resource, 0) or 0)
            if amount:
                features[f"{resource}_cost"] = features.get(f"{resource}_cost", 0.0) + amount
                total += amount
        if total:
            features["resource_cost"] = features.get("resource_cost", 0.0) + total

    def _add_production_features(
        self,
        features: dict[str, float],
        development_type: str | None,
        memory: Memory,
        level: float,
    ) -> None:
        resource = DEVELOPMENT_PRODUCTION.get(development_type)
        if not resource:
            return
        remaining_fraction = self._remaining_day_fraction(memory)
        production_delta = max(0.0, level) * remaining_fraction
        features["production_delta"] = features.get("production_delta", 0.0) + production_delta
        features[f"{resource}_production_delta"] = features.get(f"{resource}_production_delta", 0.0) + production_delta

    def _build_cost(self, tile_type: str | None, memory: Memory) -> dict:
        if tile_type is None:
            return {}
        return memory.get("development_costs", {}).get(tile_type, {}).get("build", {})

    def _remaining_day_fraction(self, memory: Memory, days: float | None = None) -> float:
        game_length = float(memory.get("game_length", 0) or 0)
        if game_length <= 0:
            return 0.0
        if days is None:
            days = max(0.0, game_length - float(memory.get("day", 0) or 0))
        return max(0.0, min(1.0, float(days) / game_length))

    def _development_for_action(self, payload: dict, memory: Memory) -> dict | None:
        dev_id = payload.get("dev_id")
        for group in ["my_developments", "other_player_developments", "unowned_developments", "contested_developments"]:
            for dev in memory.get(group, []) or []:
                if dev.get("id") == dev_id:
                    return dev
        return None

    def _development_value(self, dev: dict, memory: Memory) -> float:
        level = float(dev.get("level", 1) or 1)
        return max(0.0, level * self._remaining_day_fraction(memory))

    def _fire_risk_delta(self, memory: Memory) -> float:
        if memory.get("fire_status") != "COLD":
            return 0.0
        return float(memory.get("cold_sickness_rate", 0.0) or 0.0)

    def _contract_for_action(self, payload: dict, memory: Memory) -> dict | None:
        action_id = payload.get("action_id")
        for contract in memory.get("pending_contracts", []) or []:
            if contract.get("id") == action_id:
                return contract
        return None

    def _add_contract_features(
        self,
        features: dict[str, float],
        command: str,
        contract: dict,
        memory: Memory,
    ) -> None:
        features["contract_obligation"] = 1.0
        contract_type = contract.get("type")
        if command == Command.DENY:
            features["social_exposure"] = -1.0
            return

        if contract_type == "TRADE":
            my_id = memory.get("my_id")
            counterparty_id = self._counterparty_for_contract(contract, my_id)
            self._add_counterparty_sentiment(features, counterparty_id, memory)
            if contract.get("initiator_id") == my_id:
                given = contract.get("offer_items", {})
                received = contract.get("request_items", {})
            else:
                given = contract.get("request_items", {})
                received = contract.get("offer_items", {})
            self._add_trade_bundle_features(features, given=given, received=received)
        elif contract_type == "EMPLOYMENT":
            self._add_counterparty_sentiment(
                features,
                self._counterparty_for_contract(contract, memory.get("my_id")),
                memory,
            )
            self._add_wage_features(features, contract)
            features["helps_other"] = 1.0
        elif contract_type == "CAMPFIRE":
            self._add_counterparty_sentiment(
                features,
                self._counterparty_for_contract(contract, memory.get("my_id")),
                memory,
            )
            features["fire_risk_delta"] = self._fire_risk_delta(memory)
            features["helps_self"] = 1.0

    def _counterparty_for_contract(self, contract: dict, my_id: str | None) -> str | None:
        if contract.get("initiator_id") == my_id:
            return contract.get("target_id")
        if contract.get("target_id") == my_id:
            return contract.get("initiator_id")
        return contract.get("target_id") or contract.get("initiator_id")

    def _add_counterparty_sentiment(
        self,
        features: dict[str, float],
        counterparty_id: str | None,
        memory: Memory,
    ) -> None:
        if not counterparty_id:
            return
        relationship = (memory.get("relationships", {}) or {}).get(counterparty_id)
        if not relationship:
            return
        confidence = float(relationship.get("confidence", 0.0) or 0.0)
        trust = float(relationship.get("trust", 0.0) or 0.0)
        fairness = float(relationship.get("fairness", 0.0) or 0.0)
        generosity = float(relationship.get("generosity", 0.0) or 0.0)
        hostility = float(relationship.get("hostility", 0.0) or 0.0)
        reciprocity = float(relationship.get("reciprocity", 0.0) or 0.0)

        features["counterparty_trust"] = trust * confidence
        features["counterparty_fairness"] = fairness * confidence
        features["counterparty_generosity"] = generosity * confidence
        features["counterparty_hostility"] = hostility * confidence
        features["counterparty_reciprocity"] = reciprocity * confidence
        features["counterparty_confidence"] = confidence
        features["expected_cheat_risk"] = max(0.0, -trust) * confidence

    def _add_trade_bundle_features(
        self,
        features: dict[str, float],
        given: dict | None,
        received: dict | None,
    ) -> None:
        given_total = float(sum((given or {}).values()))
        received_total = float(sum((received or {}).values()))
        if given_total:
            features["trade_given_value"] = features.get("trade_given_value", 0.0) + given_total
        if received_total:
            features["trade_received_value"] = features.get("trade_received_value", 0.0) + received_total
            features["resource_delta"] = features.get("resource_delta", 0.0) + received_total


class ActionUtilityScorer:
    """Scores factual features as a genome-weighted dot product."""

    def __init__(self, genome: GOAPGenome):
        self.genome = genome

    def score(self, features: dict[str, float]) -> ActionUtilityEvaluation:
        weights = self.weights()
        contributions = {
            feature: float(value) * weights.get(feature, 0.0)
            for feature, value in features.items()
        }
        return ActionUtilityEvaluation(
            score=sum(contributions.values()),
            weights={feature: weights.get(feature, 0.0) for feature in features},
            contributions=contributions,
        )

    def weights(self) -> dict[str, float]:
        cost_weight = -GOAPGenome.cost_scale(self.genome.action_cost_weight)
        return {
            "food_delta": self.genome.food_weight,
            "wood_delta": self.genome.wood_weight,
            "iron_delta": self.genome.iron_weight,
            "resource_delta": self.genome.immediate_reward_weight,
            "food_production_delta": self.genome.food_weight + self.genome.future_reward_weight,
            "wood_production_delta": self.genome.wood_weight + self.genome.future_reward_weight,
            "iron_production_delta": self.genome.iron_weight + self.genome.future_reward_weight,
            "production_delta": self.genome.growth_weight + self.genome.future_reward_weight,
            "resource_cost": cost_weight,
            "food_cost": 0.0,
            "wood_cost": 0.0,
            "iron_cost": 0.0,
            "maintenance_days_saved": self.genome.maintain_weight,
            "fire_risk_delta": self.genome.fire_weight + self.genome.sickness_desperation_weight,
            "trade_received_value": self.genome.trade_fairness_weight,
            "trade_given_value": -self.genome.trade_fairness_weight,
            "contract_obligation": self.genome.finalize_honesty_weight + self.genome.reputation_weight,
            "contested_value": self.genome.contest_weight + self.genome.aggression_weight,
            "helps_self": self.genome.survival_weight,
            "helps_other": self.genome.cooperation_weight,
            "harms_other": self.genome.aggression_weight - self.genome.cooperation_weight,
            "social_exposure": self.genome.reputation_weight + self.genome.cooperation_weight,
            "counterparty_trust": self.genome.trust_weight,
            "counterparty_fairness": self.genome.fairness_weight,
            "counterparty_generosity": self.genome.generosity_weight + self.genome.gift_gratitude_weight,
            "counterparty_hostility": -self.genome.hostility_aversion_weight,
            "counterparty_reciprocity": self.genome.reciprocity_weight,
            "counterparty_confidence": self.genome.forgiveness_weight,
            "expected_cheat_risk": -self.genome.betrayal_sensitivity_weight,
        }
