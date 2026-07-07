from dataclasses import dataclass
from typing import Callable

from .action_features import ActionFeatureCalculator, ActionUtilityScorer
from .domain import Command
from .goals import GOAPGoal
from .goap_genome import GOAPGenome
from .memory import Memory


EffectFactory = Callable[[Memory, dict], dict]
CostFn = Callable[[Memory, dict], float]
PreconditionFn = Callable[[Memory, dict], bool]


@dataclass(frozen=True)
class PlannedAction:
    """One legal server action bound to a GOAP action template."""
    template_name: str
    server_action: dict
    effects: dict
    cost: float
    score: float = 0.0
    features: dict | None = None
    explanation: dict | None = None


@dataclass(frozen=True)
class ActionTemplate:
    """GOAP action template over server-derived legal actions."""
    name: str
    command: str
    effects: dict | EffectFactory
    cost: CostFn
    precondition: PreconditionFn | None = None

    def bind(self, legal_actions: list[dict], memory: Memory) -> list[PlannedAction]:
        planned = []
        for action in legal_actions:
            if action.get("action_command") != self.command:
                continue
            if self.precondition and not self.precondition(memory, action):
                continue
            effects = self.effects(memory, action) if callable(self.effects) else dict(self.effects)
            planned.append(PlannedAction(
                template_name=self.name,
                server_action=action,
                effects=effects,
                cost=self.cost(memory, action),
            ))
        return planned


class OneStepPlanner:
    """Scores legal actions, with optional shallow repeated-effect lookahead."""

    def __init__(self, genome: GOAPGenome, planning_depth: int = 1):
        self.genome = genome
        self.planning_depth = max(1, min(3, int(planning_depth)))
        self.templates = self._build_templates()
        self.feature_calculator = ActionFeatureCalculator()
        self.feature_scorer = ActionUtilityScorer(genome)

    def plan(self, goal: GOAPGoal, legal_actions: list[dict],
             memory: Memory) -> PlannedAction | None:
        candidates = []
        for template in self.templates:
            candidates.extend(template.bind(legal_actions, memory))

        scored = []
        for candidate in candidates:
            features = self.feature_calculator.calculate(
                candidate.server_action, memory)
            features.update(candidate.effects)
            feature_evaluation = self.feature_scorer.score(features)
            goal_progress = goal.progress(memory, features)
            lookahead_score = self._lookahead_score(goal, memory, features)
            score = goal_progress + feature_evaluation.score + lookahead_score
            if score < 0:
                continue
            scored.append(PlannedAction(
                template_name=candidate.template_name,
                server_action=candidate.server_action,
                effects=candidate.effects,
                cost=candidate.cost,
                score=score,
                features=features,
                explanation={
                    "goal": goal.name,
                    "template": candidate.template_name,
                    "score": score,
                    "goal_progress": goal_progress,
                    "feature_utility": feature_evaluation.score,
                    "lookahead_score": lookahead_score,
                    "planning_depth": self.planning_depth,
                    "cost": candidate.cost,
                    "features": features,
                    "weights": feature_evaluation.weights,
                    "contributions": feature_evaluation.contributions,
                    "top_features": feature_evaluation.top_features(),
                },
            ))

        if not scored:
            return None
        return max(scored, key=lambda action: action.score)

    def _lookahead_score(self, goal: GOAPGoal, memory: Memory,
                         features: dict[str, float]) -> float:
        """Approximate a depth-limited action tree without simulating server state.

        The bot currently only receives legal actions for the current state.
        Until the service exposes a transition model, the safest tree is a
        bounded repeated-effect projection: after selecting an action, estimate
        how the same factual effects would continue to advance the selected
        goal over the next two plies. This gives evolution a hook to prefer
        actions with compounding value while keeping server legality intact.
        """
        if self.planning_depth <= 1 or self.genome.planning_depth_weight == 0:
            return 0.0

        total = 0.0
        discount = 0.5 * GOAPGenome.positive_multiplier(
            self.genome.planning_depth_weight)
        for depth in range(2, self.planning_depth + 1):
            total += goal.progress(memory, features) * (discount ** (depth - 1))
        return total

    def _build_templates(self) -> list[ActionTemplate]:
        return [
            ActionTemplate(
                name="start-fire",
                command=Command.START_FIRE,
                effects={"warmth": 1, "sickness_risk_delta": 1},
                cost=lambda memory, _action: self._resource_bundle_cost(
                    memory.get("campfire_cost", {})),
            ),
            ActionTemplate(
                name="request-campfire-seat",
                command=Command.CAMPFIRE,
                effects={"warmth": 1, "cooperation": 1},
                cost=lambda _memory, _action: 0.0,
                precondition=lambda _memory, action: action.get("payload", {}).get("is_request", False),
            ),
            ActionTemplate(
                name="apply-for-work",
                command=Command.EMPLOYMENT,
                effects=self._wage_effects,
                cost=lambda _memory, _action: 0.0,
            ),
            ActionTemplate(
                name="commit-work",
                command=Command.COMMIT_WORK,
                effects=self._wage_effects,
                cost=lambda _memory, _action: 0.0,
            ),
            ActionTemplate(
                name="build-development",
                command=Command.BUILD_DEV,
                effects=self._build_effects,
                cost=self._build_cost,
            ),
            ActionTemplate(
                name="maintain-development",
                command=Command.MAINTAIN_DEV,
                effects={"asset_preservation": 1},
                cost=self._development_action_cost,
            ),
            ActionTemplate(
                name="upgrade-development",
                command=Command.UPGRADE_DEV,
                effects={"asset_level_delta": 1, "production_capacity": 1},
                cost=self._development_action_cost,
            ),
            ActionTemplate(
                name="contest-development",
                command=Command.CONTEST_DEV,
                effects={"contest_value": 1},
                cost=lambda _memory, _action: 0.0,
            ),
            ActionTemplate(
                name="draft-trade",
                command=Command.TRADE,
                effects={"trade_option": 1},
                cost=lambda _memory, _action: 0.0,
            ),
            ActionTemplate(
                name="accept-contract",
                command=Command.ACCEPT,
                effects={"cooperation": 1, "obligation_resolution": 1},
                cost=lambda _memory, _action: 0.0,
            ),
            ActionTemplate(
                name="finalize-contract",
                command=Command.FINALIZE,
                effects={"cooperation": 1, "obligation_resolution": 1},
                cost=lambda _memory, _action: 0.0,
            ),
        ]

    def _wage_effects(self, _memory: Memory, action: dict) -> dict:
        payload = action.get("payload", {})
        job = payload.get("job", {})
        wage_type = payload.get("wage_type") or job.get("wage_type")
        wage = payload.get("wage", job.get("wage", 0))
        if wage_type not in ["food", "wood", "iron"]:
            return {"resource_delta": 0}
        return {
            "resource_delta": wage,
            f"{wage_type}_delta": wage,
        }

    def _build_effects(self, _memory: Memory, action: dict) -> dict:
        tile_type = action.get("payload", {}).get("_tile_type")
        effects = {"production_capacity": 1}
        resource = {
            "Farm": "food_delta",
            "Woods": "wood_delta",
            "Mine": "iron_delta",
        }.get(tile_type)
        if resource:
            effects[resource] = 1
        return effects

    def _build_cost(self, memory: Memory, action: dict) -> float:
        tile_type = action.get("payload", {}).get("_tile_type")
        build_cost = memory.get("development_costs", {}).get(
            tile_type, {}).get("build", {})
        return self._resource_bundle_cost(build_cost)

    def _development_action_cost(self, memory: Memory, action: dict) -> float:
        dev_id = action.get("payload", {}).get("dev_id")
        for key in ["my_developments", "other_player_developments", "unowned_developments"]:
            for dev in memory.get(key, []):
                if dev.get("id") == dev_id:
                    return self._resource_bundle_cost(
                        dev.get("upgrade_cost")
                        or dev.get("maintenance_cost")
                        or {})
        return 0.0

    def _resource_bundle_cost(self, bundle: dict | None) -> float:
        bundle = bundle or {}
        raw_cost = (
            bundle.get("food", 0) * self.genome.food_weight
            + bundle.get("wood", 0) * self.genome.wood_weight
            + bundle.get("iron", 0) * self.genome.iron_weight
        )
        return (
            raw_cost
            * GOAPGenome.cost_scale(self.genome.action_cost_weight)
            / (sum(bundle.values()) + 1.0)
        )
