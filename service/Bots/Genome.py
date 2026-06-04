import random
from dataclasses import dataclass, fields

# =========================
# Genome
# =========================

@dataclass
class Genome:
    food_weight: float
    wood_weight: float
    iron_weight: float
    reputation_weight: float
    health_weight: float
    build_farm_weight: float
    build_woods_weight: float
    build_mine_weight: float
    upgrade_weight: float
    maintain_weight: float
    contest_weight: float
    survival_weight: float
    growth_weight: float

    @staticmethod
    def random():
        return Genome(
            food_weight=random.uniform(-1, 1),
            wood_weight=random.uniform(-1, 1),
            iron_weight=random.uniform(-1, 1),
            reputation_weight=random.uniform(-1, 1),
            health_weight=random.uniform(-1, 1),
            build_farm_weight=random.uniform(-1, 1),
            build_woods_weight=random.uniform(-1, 1),
            build_mine_weight=random.uniform(-1, 1),
            upgrade_weight=random.uniform(-1, 1),
            maintain_weight=random.uniform(-1, 1),
            contest_weight=random.uniform(-1, 1),
            survival_weight=random.uniform(-1, 1),
            growth_weight=random.uniform(-1, 1)
            )

    @staticmethod
    def mutate(
        genome,
        mutation_strength=0.3,
        mutation_rate=0.2
    ):

        mutated = {}

        for field in fields(Genome):

            value = getattr(genome, field.name)

            if random.random() < mutation_rate:
                value += random.gauss(
                    0,
                    mutation_strength
                )

            mutated[field.name] = value

        return Genome(**mutated)

    @staticmethod
    def crossover(parent_a, parent_b):

        child = {}

        for field in fields(Genome):
            child[field.name] = random.choice([
                getattr(parent_a, field.name),
                getattr(parent_b, field.name)
            ])

        return Genome(**child)

