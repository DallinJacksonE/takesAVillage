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
        )

    @staticmethod
    def crossover(parent_a, parent_b):
        return Genome(
            food_weight=random.choice(
                [parent_a.food_weight, parent_b.food_weight]
            ),
            wood_weight=random.choice(
                [parent_a.wood_weight, parent_b.wood_weight]
            ),
            iron_weight=random.choice(
                [parent_a.iron_weight, parent_b.iron_weight]
            ),
            reputation_weight=random.choice(
                [parent_a.reputation_weight, parent_b.reputation_weight]
            ),
            health_weight=random.choice(
                [parent_a.health_weight, parent_b.health_weight]
            ),
            build_farm_weight=random.choice(
                [parent_a.build_farm_weight, parent_b.build_farm_weight]
            ),
            build_woods_weight=random.choice(
                [parent_a.build_woods_weight, parent_b.build_woods_weight]
            ),
            build_mine_weight=random.choice(
                [parent_a.build_mine_weight, parent_b.build_mine_weight]
            ),
        )
