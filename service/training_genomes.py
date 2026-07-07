import random


GENOME_FIELDS = [
    "food_weight",
    "wood_weight",
    "iron_weight",
    "food_desperation_weight",
    "wood_desperation_weight",
    "iron_desperation_weight",
    "survival_weight",
    "growth_weight",
    "reputation_weight",
    "aggression_weight",
    "cooperation_weight",
    "risk_weight",
    "farm_preference",
    "woods_preference",
    "mine_preference",
    "build_weight",
    "upgrade_weight",
    "maintain_weight",
    "contest_weight",
    "work_weight",
    "fire_weight",
    "immediate_reward_weight",
    "future_reward_weight",

    # Relationship genes
    "greed_weight",
    "friendship_weight",
    "trust_weight",
    "generosity_weight",
    "initial_friendship",
    "initial_generosity",
    "initial_trust",
    "initial_greed",

    "friendship_sensitivity",
    "generosity_sensitivity",
    "trust_sensitivity",
    "greed_sensitivity",

    "honest_trust_increase",
    "honest_friendship_increase",
]

GOAP_GENOME_FIELDS = [
    "food_weight", "wood_weight", "iron_weight",
    "food_desperation_weight", "wood_desperation_weight",
    "iron_desperation_weight", "warmth_desperation_weight",
    "sickness_desperation_weight", "resource_urgency_curve",
    "survival_urgency_weight", "health_risk_weight",
    "maintenance_urgency_weight", "survival_weight", "growth_weight",
    "reputation_weight", "aggression_weight", "cooperation_weight",
    "risk_weight", "trade_deception_weight", "wage_deception_weight",
    "farm_preference", "woods_preference", "mine_preference",
    "build_weight", "upgrade_weight", "maintain_weight", "contest_weight",
    "work_weight", "fire_weight", "fire_host_weight", "fire_guest_weight",
    "immediate_reward_weight", "future_reward_weight",
    "production_discount_weight", "trade_fairness_weight",
    "employment_wage_weight", "employer_exploitation_weight",
    "campfire_accept_weight", "finalize_honesty_weight",
    "tie_break_weight", "action_cost_weight",
]


def _clamp_goap_gene(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def get_genome_fields_for_model(bot_model: str) -> list[str]:
    if bot_model == "GOAPGenetic":
        return GOAP_GENOME_FIELDS
    return GENOME_FIELDS


def random_genome_dict_for_model(bot_model: str) -> dict:
    fields = get_genome_fields_for_model(bot_model)
    if bot_model == "GOAPGenetic":
        return {field: random.uniform(-1, 1) for field in fields}
    return {field: random.uniform(0, 3) for field in fields}


def normalize_genome_for_model(bot_model: str, genome: dict | None) -> dict:
    genome = genome or {}
    if bot_model == "GOAPGenetic":
        return {
            field: _clamp_goap_gene(genome.get(field, 0.0))
            for field in GOAP_GENOME_FIELDS
        }
    return {field: genome.get(field, 0) for field in GENOME_FIELDS}


def mutate_genome_for_model(bot_model: str, genome: dict,
                            mutation_strength=0.25,
                            mutation_rate=0.15) -> dict:
    parent = normalize_genome_for_model(bot_model, genome)
    out = {}
    for key, value in parent.items():
        if random.random() < mutation_rate:
            value = value + random.gauss(0, mutation_strength)
        out[key] = _clamp_goap_gene(value) if bot_model == "GOAPGenetic" else value
    return out


def crossover_genomes_for_model(bot_model: str, a: dict, b: dict) -> dict:
    parent_a = normalize_genome_for_model(bot_model, a)
    parent_b = normalize_genome_for_model(bot_model, b)
    return {
        field: random.choice([parent_a.get(field, 0), parent_b.get(field, 0)])
        for field in get_genome_fields_for_model(bot_model)
    }
