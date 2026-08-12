import type { TrainingGenerationStatisticsDTO, TrainingGenomeEntry } from "@takes-a-village/shared";

import {
  crossoverGenomesForModel,
  mutateGenomeForModel,
  normalizeGenomeForModel,
  randomGenomeForModel,
  type Genome,
  type RandomSource,
} from "./genomes.js";

function mean(values: number[]): number { return values.length ? values.reduce((total, value) => total + value, 0) / values.length : 0; }
function median(values: number[]): number {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle]! : (sorted[middle - 1]! + sorted[middle]!) / 2;
}
function populationStandardDeviation(values: number[]): number {
  if (values.length < 2) return 0;
  const average = mean(values);
  return Math.sqrt(mean(values.map((value) => (value - average) ** 2)));
}

export function buildGenerationStatistics(entries: TrainingGenomeEntry[]): TrainingGenerationStatisticsDTO {
  const fitnesses = entries.map((entry) => Number(entry.fitness || 0));
  const stats = entries.map((entry) => entry.stats ?? {});
  const fields = [...new Set(entries.flatMap((entry) => Object.keys(entry.genome)))].sort();
  return {
    generation: 0,
    best_fitness: fitnesses.length ? Math.max(...fitnesses) : 0,
    average_fitness: mean(fitnesses),
    median_fitness: median(fitnesses),
    worst_fitness: fitnesses.length ? Math.min(...fitnesses) : 0,
    survival_rate: mean(stats.map((item) => item.survived ? 1 : 0)),
    average_resources: mean(stats.map((item) => {
      const resources = item.resources;
      return resources && typeof resources === "object" && !Array.isArray(resources)
        ? Object.values(resources).reduce<number>((total, value) => total + (typeof value === "number" ? value : 0), 0)
        : 0;
    })),
    average_developments: mean(stats.map((item) => typeof item.developments_owned === "number" ? item.developments_owned : 0)),
    illegal_action_count: stats.reduce((total, item) => total + (typeof item.illegal_action_count === "number" ? item.illegal_action_count : 0), 0),
    gene_diversity: Object.fromEntries(fields.map((field) => [field, populationStandardDeviation(entries.map((entry) => entry.genome[field] ?? 0))])),
  };
}

export interface PopulationOptions {
  eliteCount: number;
  selectionSize: number;
  mutationStrength: number;
  mutationRate: number;
  randomImmigrantCount?: number;
  crossoverChildCount?: number;
  mutationChildCount?: number;
  random?: RandomSource;
  gaussian?: () => number;
}

function pick<T>(items: T[], random: RandomSource): T { return items[Math.min(items.length - 1, Math.floor(random() * items.length))]!; }

export function buildNextPopulation(
  botModel: string,
  entries: TrainingGenomeEntry[],
  botCount: number,
  options: PopulationOptions,
): Genome[] {
  const random = options.random ?? Math.random;
  const parents = [...entries]
    .sort((a, b) => b.fitness - a.fitness)
    .slice(0, options.selectionSize)
    .map((entry) => normalizeGenomeForModel(botModel, entry.genome));
  if (!parents.length) return Array.from({ length: botCount }, () => randomGenomeForModel(botModel, random));

  const output = parents.slice(0, Math.min(options.eliteCount, parents.length, botCount));
  for (let index = 0; index < (options.crossoverChildCount ?? 0) && output.length < botCount; index += 1) {
    const first = parents[index % parents.length]!;
    const second = parents[(index + 1) % parents.length]!;
    output.push(parents.length > 1 ? crossoverGenomesForModel(botModel, first, second, random) : { ...first });
  }
  for (let index = 0; index < (options.mutationChildCount ?? 0) && output.length < botCount; index += 1) {
    output.push(mutateGenomeForModel(botModel, parents[index % parents.length]!, { ...options, random }));
  }
  const immigrantSlots = Math.min(Math.max(0, options.randomImmigrantCount ?? 1), Math.max(0, botCount - output.length));
  for (let index = 0; index < immigrantSlots; index += 1) output.push(randomGenomeForModel(botModel, random));
  while (output.length < botCount) output.push(mutateGenomeForModel(botModel, pick(parents, random), { ...options, random }));
  return output.slice(0, botCount);
}
