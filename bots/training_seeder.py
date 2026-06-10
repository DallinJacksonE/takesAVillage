from models.genetic.Genome import Genome


def seed_genomes(base_genome_dict: dict | None, bot_count: int) -> list[Genome]:
    """
    Takes an optional base genome and returns a list of Genomes for the new bots.
    If no base is provided, returns all random genomes.
    If a base is provided, returns 1 exact copy (Elitism) and N-1 mutated variants.
    """
    genomes = []

    if not base_genome_dict:
        # Fresh gene pool
        for _ in range(bot_count):
            genomes.append(Genome.random())
        return genomes

    # Reconstruct the parent Genome object from the JSON dict
    parent_genome = Genome(**base_genome_dict)

    # 1. Elitism: Keep the exact champion to ensure we don't regress
    genomes.append(parent_genome)

    # 2. Mutate the rest
    for _ in range(bot_count - 1):
        mutant = Genome.mutate(parent_genome)
        genomes.append(mutant)

    return genomes
