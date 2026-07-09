import random
from dataclasses import dataclass, fields

GENE_RANGES = {

    # -----------------------------
    # Resource valuation
    # -----------------------------
    "food_weight": (0.0, 3.0),
    "wood_weight": (0.0, 3.0),
    "iron_weight": (0.0, 3.0),

    # -----------------------------
    # Scarcity response
    # -----------------------------
    "food_desperation_weight": (0.0, 3.0),
    "wood_desperation_weight": (0.0, 3.0),
    "iron_desperation_weight": (0.0, 3.0),

    # -----------------------------
    # General strategy
    # -----------------------------
    "survival_weight": (0.0, 3.0),
    "growth_weight": (0.0, 3.0),
    "reputation_weight": (0.0, 3.0),

    # -----------------------------
    # Personality
    # -----------------------------
    "aggression_weight": (0.0, 3.0),
    "cooperation_weight": (0.0, 3.0),
    "risk_weight": (0.0, 3.0),

    # -----------------------------
    # Development preferences
    # -----------------------------
    "farm_preference": (0.0, 3.0),
    "woods_preference": (0.0, 3.0),
    "mine_preference": (0.0, 3.0),

    # -----------------------------
    # Action biases
    # -----------------------------
    "build_weight": (0.0, 3.0),
    "upgrade_weight": (0.0, 3.0),
    "maintain_weight": (0.0, 3.0),
    "contest_weight": (0.0, 3.0),
    "work_weight": (0.0, 3.0),
    "fire_weight": (0.0, 3.0),

    # -----------------------------
    # Time horizon
    # -----------------------------
    "immediate_reward_weight": (0.0, 3.0),
    "future_reward_weight": (0.0, 3.0),

    # -----------------------------
    # Initial relationship beliefs
    # -----------------------------

    "greed_weight": (0.0, 1.0),
    "friendship_weight": (0.0, 1.0),
    "trust_weight": (0.0, 1.0),
    "generosity_weight": (0.0, 1.0),

    "initial_friendship": (-1.0, 1.0),
    "initial_generosity": (-1.0, 1.0),
    "initial_trust": (-1.0, 1.0),
    "initial_greed": (-1.0, 1.0),

    # -----------------------------
    # Relationship learning rates
    # -----------------------------
    "friendship_sensitivity": (0.0, 1.0),
    "generosity_sensitivity": (0.0, 1.0),
    "trust_sensitivity": (0.0, 1.0),
    "greed_sensitivity": (0.0, 1.0),

    # -----------------------------
    # Positive interaction rewards
    # -----------------------------
    "honest_trust_increase": (0.0, 1.0),
    "honest_friendship_increase": (0.0, 1.0),
}


@dataclass
class Genome:

    # Resource valuation
    food_weight: float
    wood_weight: float
    iron_weight: float

    # Scarcity response
    food_desperation_weight: float
    wood_desperation_weight: float
    iron_desperation_weight: float

    # General strategy
    survival_weight: float
    growth_weight: float
    reputation_weight: float

    # Personality
    aggression_weight: float
    cooperation_weight: float
    risk_weight: float

    # Development preferences
    farm_preference: float
    woods_preference: float
    mine_preference: float

    # Action biases
    build_weight: float
    upgrade_weight: float
    maintain_weight: float
    contest_weight: float
    work_weight: float
    fire_weight: float

    # Time horizon
    immediate_reward_weight: float
    future_reward_weight: float

    # Relationship weights
    greed_weight: float
    friendship_weight: float
    trust_weight: float
    generosity_weight: float

    initial_friendship: float
    initial_generosity: float
    initial_trust: float
    initial_greed: float

    friendship_sensitivity: float
    generosity_sensitivity: float
    trust_sensitivity: float
    greed_sensitivity: float

    honest_trust_increase: float
    honest_friendship_increase: float

    @staticmethod
    def random():

        values = {}

        for field in fields(Genome):
            low, high = GENE_RANGES[field.name]
            values[field.name] = random.uniform(low, high)

        return Genome(**values)

    @staticmethod
    def mutate(
        genome,
        mutation_strength=0.25,
        mutation_rate=0.15
    ):

        values = {}

        for field in fields(Genome):
            value = getattr(genome, field.name)

            if random.random() < mutation_rate:
                value += random.uniform(-mutation_strength, mutation_strength)

            low, high = GENE_RANGES[field.name]
            value = max(low, min(high, value))

            values[field.name] = value

        return Genome(**values)

    @staticmethod
    def crossover(parent_a, parent_b):

        values = {}

        for field in fields(Genome):

            values[field.name] = random.choice([
                getattr(parent_a, field.name),
                getattr(parent_b, field.name)
            ])

        return Genome(**values)