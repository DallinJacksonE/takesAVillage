import { z } from "zod";

import { jsonValueSchema } from "./common.js";

export const spawnBotsRequestSchema = z.object({
  gameId: z.string(),
  botCount: z.number().int().min(1).max(100),
  botSecret: z.string(),
  botModel: z.string(),
  baseGenome: jsonValueSchema.optional(),
  trainingAttemptIndex: z.number().int().min(1).optional(),
});
export type SpawnBotsRequest = z.infer<typeof spawnBotsRequestSchema>;

export const spawnBotsResponseSchema = z.object({
  status: z.literal("success"),
  message: z.string(),
});
export type SpawnBotsResponse = z.infer<typeof spawnBotsResponseSchema>;

export const botModelsResponseSchema = z.object({
  status: z.literal("success"),
  models: z.array(z.string()),
});
export type BotModelsResponse = z.infer<typeof botModelsResponseSchema>;

export const trainingGenomeEntrySchema = z.object({
  game_id: z.string(),
  fitness: z.number(),
  genome: z.record(z.string(), z.number()),
  stats: z.record(z.string(), jsonValueSchema).optional(),
});
export type TrainingGenomeEntry = z.infer<typeof trainingGenomeEntrySchema>;

export const trainingGenomeEntriesResponseSchema = z.object({
  game_id: z.string().optional(),
  entries: z.array(trainingGenomeEntrySchema),
});

export const bestTrainingGenomeResponseSchema = z.object({
  genome: z.record(z.string(), z.number()).nullable().optional(),
  best_fitness: z.number().optional(),
});
