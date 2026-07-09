from models.utility_genetic.Genome import Genome
from logger import Logger

seeder_logger = Logger("GENETIC_SEEDER")


def seed_genomes(base_genome_dict: dict | None, bot_count: int) -> list[Genome]:
    print(repr(base_genome_dict), type(base_genome_dict), bool(base_genome_dict))
    genomes = []

    if not base_genome_dict:
        seeder_logger.info(f"Creating fresh, randomized gene pool for "
                           f"{bot_count} bots.")
        for _ in range(bot_count):
            genomes.append(Genome.random())
        return genomes

    seeder_logger.info(f"Cloning Champion Genome and generating "
                       f"{bot_count - 1} mutants.")
    parent_genome = Genome(**base_genome_dict)

    genomes.append(parent_genome)

    for _ in range(bot_count - 1):
        mutant = Genome.mutate(parent_genome)
        genomes.append(mutant)

    return genomes
