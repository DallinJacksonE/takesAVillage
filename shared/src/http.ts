import { z } from "zod";

import { jsonValueSchema } from "./common.js";
import { gameStateSchema, genomeSchema } from "./game.js";
import {
  researchGameDetailSchema,
  researchGameListItemSchema,
  trainingBatchDetailSchema,
  trainingBatchListItemSchema,
  trainingSessionsSchema,
} from "./research.js";

export const newGameRequestSchema = z.object({
  ruleset: z.string().default("default"),
  botCount: z.number().int().min(0).default(0),
  botGenome: z.string().default("random"),
  botModel: z.string().default("genetic"),
});
export type NewGameRequest = z.infer<typeof newGameRequestSchema>;

export const joinGameRequestSchema = z.object({ gameId: z.string() });
export type JoinGameRequest = z.infer<typeof joinGameRequestSchema>;

export const botJoinRequestSchema = z.object({ gameId: z.string(), botSecret: z.string() });
export type BotJoinRequest = z.infer<typeof botJoinRequestSchema>;

export const trainingRequestSchema = z.object({
  ruleset: z.string().default("default"),
  botCount: z.number().int().default(5),
  generations: z.number().int().default(1),
  baseGenome: z.string().default("random"),
  botModel: z.string().default("genetic"),
  mutationStrength: z.number().default(0.25),
  mutationRate: z.number().default(0.15),
  randomImmigrantCount: z.number().int().default(1),
  gamesPerGeneration: z.number().int().default(5),
});
export type TrainingRequest = z.infer<typeof trainingRequestSchema>;

export const cancelTrainingRequestSchema = z.object({
  reason: z.string().default("Training cancelled by operator"),
});
export type CancelTrainingRequest = z.infer<typeof cancelTrainingRequestSchema>;

export const messageResponseSchema = z.object({ message: z.string() });
export const trainingControlResponseSchema = messageResponseSchema.extend({
  batch_id: z.string().optional(),
  source_batch_id: z.string().optional(),
});

export const genomesResponseSchema = z.object({
  genomes: z.array(genomeSchema),
  models: z.array(z.string()),
});
export type GenomesResponseDTO = z.infer<typeof genomesResponseSchema>;

export const newGameResponseSchema = z.object({ gameId: z.string() });
export type NewGameDTO = z.infer<typeof newGameResponseSchema>;
export type JoinGameDTO = NewGameDTO;

export const newGameOptionsSchema = z.object({
  options: z.record(z.string(), z.record(z.string(), jsonValueSchema)),
});
export type NewGameOptionsDTO = z.infer<typeof newGameOptionsSchema>;

export const consentSchema = z.object({ message: z.string(), userId: z.string() });
export type ConsentDTO = z.infer<typeof consentSchema>;

export const verifySessionSchema = z.object({ userId: z.string(), message: z.string() });

export const joinableGameSchema = z.object({
  id: z.string(),
  name: z.string(),
  players: z.string(),
  isRejoinable: z.boolean().optional(),
});
export type JoinableGameDTO = z.infer<typeof joinableGameSchema>;

export const activeGamesSchema = z.object({ games: z.array(joinableGameSchema) });
export type ActiveGamesDTO = z.infer<typeof activeGamesSchema>;

export const httpContractSchemas = {
  gameState: gameStateSchema,
  researchGames: z.array(researchGameListItemSchema),
  researchGameDetail: researchGameDetailSchema,
  trainingBatches: z.object({ batches: z.array(trainingBatchListItemSchema) }),
  trainingBatchDetail: trainingBatchDetailSchema,
  trainingSessions: trainingSessionsSchema,
} as const;
