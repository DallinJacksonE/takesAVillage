export interface TrainingConfig {
  ruleset: string;
  botCount: number;
  generations: number;
  baseGenomeId: string;
  botModel: string;
  mutationStrength: number;
  mutationRate: number;
  randomImmigrantCount: number;
  gamesPerGeneration: number;
}

export type TrainingConfigInput = Partial<TrainingConfig>;

export function createTrainingConfig(input: TrainingConfigInput = {}): Readonly<TrainingConfig> {
  return Object.freeze({
    ruleset: input.ruleset ?? "default",
    botCount: input.botCount ?? 5,
    generations: input.generations ?? 1,
    baseGenomeId: input.baseGenomeId ?? "random",
    botModel: input.botModel ?? "genetic",
    mutationStrength: input.mutationStrength ?? 0.25,
    mutationRate: input.mutationRate ?? 0.15,
    randomImmigrantCount: input.randomImmigrantCount ?? 1,
    gamesPerGeneration: Math.max(1, Math.min(50, Math.trunc(input.gamesPerGeneration ?? 5))),
  });
}
