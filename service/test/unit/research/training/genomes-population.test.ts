import { describe, expect, it } from "vitest";

import {
  GENOME_FIELDS,
  GOAP_GENOME_FIELDS,
  mutateGenomeForModel,
  randomGenomeForModel,
} from "../../../../src/research/training/genomes.js";
import {
  buildGenerationStatistics,
  buildNextPopulation,
} from "../../../../src/research/training/population.js";

describe("training genomes and population", () => {
  it("uses distinct GOAP fields and model-specific ranges", () => {
    expect(GOAP_GENOME_FIELDS).toContain("warmth_desperation_weight");
    expect(GOAP_GENOME_FIELDS).toContain("planning_depth_weight");
    expect(GOAP_GENOME_FIELDS).not.toEqual(GENOME_FIELDS);

    const goap = randomGenomeForModel("GOAPGenetic", () => 0);
    expect(Object.values(goap).every((value) => value === -1)).toBe(true);
    const genetic = randomGenomeForModel("genetic", () => 1);
    expect(Object.values(genetic).every((value) => value === 3)).toBe(true);
  });

  it("clamps mutated GOAP genes to minus one through one", () => {
    const genome = Object.fromEntries(GOAP_GENOME_FIELDS.map((field) => [field, 1]));
    const mutant = mutateGenomeForModel("GOAPGenetic", genome, {
      mutationRate: 1,
      mutationStrength: 100,
      random: () => 0,
      gaussian: () => 100,
    });
    expect(Object.values(mutant).every((value) => value === 1)).toBe(true);
  });

  it("builds explanatory generation statistics", () => {
    const stats = buildGenerationStatistics([
      { game_id: "game-1", fitness: 10, stats: { survived: false, resources: { food: 1 }, developments_owned: 0, illegal_action_count: 2 }, genome: { food_weight: 0, wood_weight: 0 } },
      { game_id: "game-1", fitness: 20, stats: { survived: true, resources: { food: 3, wood: 1 }, developments_owned: 2, illegal_action_count: 0 }, genome: { food_weight: 1, wood_weight: -1 } },
      { game_id: "game-1", fitness: 30, stats: { survived: true, resources: { food: 2, iron: 2 }, developments_owned: 1, illegal_action_count: 1 }, genome: { food_weight: -1, wood_weight: 1 } },
    ]);

    expect(stats).toMatchObject({
      best_fitness: 30,
      average_fitness: 20,
      median_fitness: 20,
      worst_fitness: 10,
      average_resources: 3,
      average_developments: 1,
      illegal_action_count: 3,
    });
    expect(stats.survival_rate).toBeCloseTo(2 / 3);
    expect(stats.gene_diversity!.food_weight).toBeGreaterThan(0);
  });

  it("preserves elites and fills the requested population", () => {
    const population = buildNextPopulation("GOAPGenetic", [
      { game_id: "game-1", fitness: 100, genome: { food_weight: 1 } },
      { game_id: "game-1", fitness: 90, genome: { food_weight: 0.5 } },
    ], 4, {
      eliteCount: 1,
      selectionSize: 2,
      mutationStrength: 0,
      mutationRate: 0,
      randomImmigrantCount: 1,
      crossoverChildCount: 1,
      mutationChildCount: 1,
      random: () => 0,
      gaussian: () => 0,
    });

    expect(population).toHaveLength(4);
    expect(population[0]?.food_weight).toBe(1);
    expect(population.some((genome) => genome.food_weight === -1)).toBe(true);
  });
});
