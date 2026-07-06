import random
from dataclasses import dataclass, fields


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
            values[field.name] = random.uniform(0, 3)

        return Genome(**values)

    @staticmethod
    def mutate(
        genome,
        mutation_strength=0.25,
        mutation_rate=0.15
    ):

        values = {}

        for field in fields(Genome):

            value = getattr(
                genome,
                field.name
            )

            if random.random() < mutation_rate:

                value += random.gauss(
                    0,
                    mutation_strength
                )

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