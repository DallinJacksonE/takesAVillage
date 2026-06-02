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
    def mutate(genome, mutation_strength=0.3):
        return Genome(
            food_weight=genome.food_weight + random.gauss(0, mutation_strength),
            wood_weight=genome.wood_weight + random.gauss(0, mutation_strength),
            iron_weight=genome.iron_weight + random.gauss(0, mutation_strength),
            reputation_weight=genome.reputation_weight + random.gauss(0, mutation_strength),
            health_weight=genome.health_weight + random.gauss(0, mutation_strength),
            build_farm_weight=genome.build_farm_weight + random.gauss(0, mutation_strength),
            build_woods_weight=genome.build_woods_weight + random.gauss(0, mutation_strength),
            build_mine_weight=genome.build_mine_weight + random.gauss(0, mutation_strength),
            upgrade_weight=genome.upgrade_weight + random.gauss(0, mutation_strength),
            maintain_weight=genome.maintain_weight + random.gauss(0, mutation_strength),
            contest_weight=genome.contest_weight + random.gauss(0, mutation_strength),
            survival_weight=genome.survival_weight + random.gauss(0, mutation_strength),
            growth_weight=genome.growth_weight + random.gauss(0, mutation_strength),
        )

    import random
from dataclasses import dataclass

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

