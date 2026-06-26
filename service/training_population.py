import random
from statistics import mean, median, pstdev

from training_genomes import (
    crossover_genomes_for_model,
    mutate_genome_for_model,
    normalize_genome_for_model,
    random_genome_dict_for_model,
)


def build_generation_statistics(entries: list[dict]) -> dict:
    fitnesses = [float(entry.get("fitness", 0) or 0) for entry in entries]
    stats = [entry.get("stats", {}) or {} for entry in entries]
    genomes = [entry.get("genome", {}) or {} for entry in entries]
    resource_totals = [
        sum((entry_stats.get("resources", {}) or {}).values())
        for entry_stats in stats
    ]
    development_counts = [
        float(entry_stats.get("developments_owned", 0) or 0)
        for entry_stats in stats
    ]
    illegal_counts = [
        int(entry_stats.get("illegal_action_count", 0) or 0)
        for entry_stats in stats
    ]
    gene_fields = sorted({field for genome in genomes for field in genome.keys()})
    gene_diversity = {
        field: pstdev([
            float(genome.get(field, 0) or 0)
            for genome in genomes
        ]) if len(genomes) > 1 else 0.0
        for field in gene_fields
    }

    return {
        "best_fitness": max(fitnesses) if fitnesses else 0.0,
        "average_fitness": mean(fitnesses) if fitnesses else 0.0,
        "median_fitness": median(fitnesses) if fitnesses else 0.0,
        "worst_fitness": min(fitnesses) if fitnesses else 0.0,
        "survival_rate": mean([
            1.0 if entry_stats.get("survived") else 0.0
            for entry_stats in stats
        ]) if stats else 0.0,
        "average_resources": mean(resource_totals) if resource_totals else 0.0,
        "average_developments": mean(development_counts) if development_counts else 0.0,
        "illegal_action_count": sum(illegal_counts),
        "gene_diversity": gene_diversity,
    }


def build_next_population(bot_model: str, entries: list[dict], bot_count: int,
                          elite_count: int, selection_size: int,
                          mutation_strength: float,
                          mutation_rate: float,
                          random_immigrant_count: int = 1) -> list[dict]:
    entries_sorted = sorted(
        entries,
        key=lambda entry: float(entry.get("fitness", 0) or 0),
        reverse=True,
    )
    parents = [
        normalize_genome_for_model(bot_model, entry.get("genome"))
        for entry in entries_sorted[:selection_size]
        if entry.get("genome")
    ]
    if not parents:
        return [random_genome_dict_for_model(bot_model) for _ in range(bot_count)]

    next_population = []
    for index in range(min(elite_count, len(parents), bot_count)):
        next_population.append(parents[index])

    immigrant_slots = min(
        max(0, random_immigrant_count),
        max(0, bot_count - len(next_population)),
    )
    while len(next_population) < bot_count - immigrant_slots:
        if len(parents) >= 2:
            parent_a, parent_b = random.sample(parents, 2)
            child = crossover_genomes_for_model(bot_model, parent_a, parent_b)
        else:
            child = dict(parents[0])
        next_population.append(mutate_genome_for_model(
            bot_model, child,
            mutation_strength=mutation_strength,
            mutation_rate=mutation_rate,
        ))

    for _ in range(bot_count - len(next_population)):
        next_population.append(random_genome_dict_for_model(bot_model))

    return next_population[:bot_count]
