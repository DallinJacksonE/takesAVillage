import random
from dataclasses import dataclass, fields


@dataclass
class GOAPGenome:
    """Genome for GOAP bots.

    GOAP-specific genomes intentionally use a -1.0 to 1.0 gene range so
    evolution can learn attraction and aversion instead of only positive
    biases. Existing GeneticBot genomes can be loaded through from_dict();
    unknown fields are ignored and missing fields use neutral defaults.
    """

    # Resource valuation
    food_weight: float = 0.0
    wood_weight: float = 0.0
    iron_weight: float = 0.0

    # Scarcity response
    food_desperation_weight: float = 0.0
    wood_desperation_weight: float = 0.0
    iron_desperation_weight: float = 0.0
    warmth_desperation_weight: float = 0.0
    sickness_desperation_weight: float = 0.0
    resource_urgency_curve: float = 0.0
    survival_urgency_weight: float = 0.0
    health_risk_weight: float = 0.0
    maintenance_urgency_weight: float = 0.0

    # General strategy
    survival_weight: float = 0.0
    growth_weight: float = 0.0
    reputation_weight: float = 0.0

    # Personality
    aggression_weight: float = 0.0
    cooperation_weight: float = 0.0
    risk_weight: float = 0.0
    trade_deception_weight: float = 0.0
    wage_deception_weight: float = 0.0

    # Development preferences
    farm_preference: float = 0.0
    woods_preference: float = 0.0
    mine_preference: float = 0.0

    # Action biases
    build_weight: float = 0.0
    upgrade_weight: float = 0.0
    maintain_weight: float = 0.0
    contest_weight: float = 0.0
    work_weight: float = 0.0
    fire_weight: float = 0.0
    fire_host_weight: float = 0.0
    fire_guest_weight: float = 0.0

    # Time horizon
    immediate_reward_weight: float = 0.0
    future_reward_weight: float = 0.0
    production_discount_weight: float = 0.0

    # Phase 4 preference curves/costs
    trade_fairness_weight: float = 0.0
    employment_wage_weight: float = 0.0
    employer_exploitation_weight: float = 0.0
    campfire_accept_weight: float = 0.0
    finalize_honesty_weight: float = 0.0
    tie_break_weight: float = 0.0
    action_cost_weight: float = 0.0

    # Social memory / sentiment preferences
    trust_weight: float = 0.0
    fairness_weight: float = 0.0
    generosity_weight: float = 0.0
    hostility_aversion_weight: float = 0.0
    reciprocity_weight: float = 0.0
    gift_gratitude_weight: float = 0.0
    betrayal_sensitivity_weight: float = 0.0
    forgiveness_weight: float = 0.0
    retaliation_weight: float = 0.0

    # Shallow tree-search planning preference
    planning_depth_weight: float = 0.0

    @classmethod
    def field_names(cls) -> set[str]:
        return {field.name for field in fields(cls)}

    @staticmethod
    def clamp_gene(value: float) -> float:
        return max(-1.0, min(1.0, float(value)))

    @classmethod
    def positive_multiplier(cls, value: float) -> float:
        """Map a [-1, 1] gene to a bounded [0, 2] multiplier."""
        return cls.clamp_gene(value) + 1.0

    @classmethod
    def cost_scale(cls, value: float) -> float:
        """Map a [-1, 1] gene to a bounded [0, 1] cost penalty scale."""
        return max(0.0, cls.clamp_gene(value))

    @classmethod
    def from_dict(cls, data: dict | None):
        data = data or {}
        values = {}
        for field in fields(cls):
            raw_value = data.get(field.name, field.default)
            values[field.name] = cls.clamp_gene(raw_value)
        return cls(**values)

    @classmethod
    def random(cls):
        return cls(**{
            field.name: random.uniform(-1.0, 1.0)
            for field in fields(cls)
        })

    @classmethod
    def mutate(cls, genome, mutation_strength=0.25, mutation_rate=0.15):
        parent = cls.from_dict(genome.__dict__ if hasattr(genome, "__dict__") else genome)
        values = {}
        for field in fields(cls):
            value = getattr(parent, field.name)
            if random.random() < mutation_rate:
                value += random.gauss(0, mutation_strength)
            values[field.name] = cls.clamp_gene(value)
        return cls(**values)

    @classmethod
    def crossover(cls, parent_a, parent_b):
        a = cls.from_dict(parent_a.__dict__ if hasattr(parent_a, "__dict__") else parent_a)
        b = cls.from_dict(parent_b.__dict__ if hasattr(parent_b, "__dict__") else parent_b)
        return cls(**{
            field.name: random.choice([
                getattr(a, field.name),
                getattr(b, field.name),
            ])
            for field in fields(cls)
        })
