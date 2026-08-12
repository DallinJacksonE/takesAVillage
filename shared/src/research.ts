import { z } from "zod";

import { jsonValueSchema, resourceBundleSchema } from "./common.js";
import { mapTileSchema } from "./game.js";

export const researchPlayerSnapshotSchema = z.object({
  health: z.string(),
  actions: z.array(jsonValueSchema),
  resources: resourceBundleSchema,
  fire_status: z.string(),
  developments: z.array(z.string()),
  finished_phase: z.boolean(),
  sickness_chance: z.number(),
  committed_action: jsonValueSchema.nullable(),
});
export type ResearchPlayerSnapshot = z.infer<typeof researchPlayerSnapshotSchema>;

export const visualizationSchema = z.object({
  id: z.string(),
  scope_type: z.enum(["game", "training_batch"]),
  scope_id: z.string(),
  name: z.string(),
  title: z.string(),
  mime_type: z.literal("image/svg+xml"),
  url: z.string(),
  metadata: z.record(z.string(), jsonValueSchema).optional(),
  created_at: z.string(),
});
export type ResearchVisualizationDTO = z.infer<typeof visualizationSchema>;

export const researchGameSchema = z.object({
  game_id: z.string(),
  day_num: z.number().int(),
  phase: z.string(),
  created_at: z.string(),
  game_type: z.enum(["human", "human_bot", "training"]).optional(),
  training_batch_id: z.string().nullable().optional(),
  training_generation: z.number().int().nullable().optional(),
  visualizations: z.array(visualizationSchema).optional(),
  data: z.object({
    map: z.record(z.string(), z.record(z.string(), mapTileSchema)),
    players: z.record(z.string(), z.record(z.string(), researchPlayerSnapshotSchema)),
  }),
});
export type ResearchGameDTO = z.infer<typeof researchGameSchema>;

export const researchGameListItemSchema = researchGameSchema.pick({
  game_id: true,
  day_num: true,
  phase: true,
  created_at: true,
  game_type: true,
  training_batch_id: true,
  training_generation: true,
}).extend({ game_type: z.enum(["human", "human_bot", "training"]) });
export type ResearchGameListItemDTO = z.infer<typeof researchGameListItemSchema>;

export const researchGameDetailSchema = researchGameSchema.extend({
  visualizations: z.array(visualizationSchema),
});
export type ResearchGameDetailDTO = z.infer<typeof researchGameDetailSchema>;

export const trainingGenerationStatisticsSchema = z.object({
  generation: z.number().int(),
  best_fitness: z.number(),
  average_fitness: z.number(),
  median_fitness: z.number().optional(),
  worst_fitness: z.number().optional(),
  survival_rate: z.number().optional(),
  average_resources: z.number().optional(),
  average_developments: z.number().optional(),
  illegal_action_count: z.number().int().optional(),
  gene_diversity: z.record(z.string(), z.number()).optional(),
});
export type TrainingGenerationStatisticsDTO = z.infer<typeof trainingGenerationStatisticsSchema>;

export const trainingGameSchema = z.object({
  game_id: z.string(),
  generation: z.number().int(),
  attempt: z.number().int().nullable().optional(),
  status: z.enum(["spawning", "running", "completed", "failed", "skipped"]).optional(),
  error_message: z.string().nullable().optional(),
  genome_count: z.number().int().optional(),
  best_fitness: z.number().nullable().optional(),
  average_fitness: z.number().nullable().optional(),
});

export const trainingBatchListItemSchema = z.object({
  batch_id: z.string(),
  status: z.enum(["running", "completed", "failed", "stalled", "cancelled"]),
  ruleset: z.string().optional(),
  bot_model: z.string().optional(),
  bot_count: z.number().int().optional(),
  total_generations: z.number().int().optional(),
  current_generation: z.number().int().optional(),
  current_game_id: z.string().nullable().optional(),
  games_per_generation: z.number().int().optional(),
  games_completed: z.number().int().optional(),
  games_failed: z.number().int().optional(),
  current_generation_game_index: z.number().int().optional(),
  phase: z.string().nullable().optional(),
  last_error: z.string().nullable().optional(),
  last_heartbeat_at: z.string().nullable().optional(),
  started_at: z.string().optional(),
  completed_at: z.string().nullable().optional(),
  generation_statistics: z.array(trainingGenerationStatisticsSchema).optional(),
});
export type TrainingBatchListItemDTO = z.infer<typeof trainingBatchListItemSchema>;

export const trainingBatchDetailSchema = trainingBatchListItemSchema.extend({
  base_genome_id: z.string().nullable().optional(),
  final_champion_genome_id: z.string().nullable().optional(),
  config: z.record(z.string(), jsonValueSchema).optional(),
  games: z.array(trainingGameSchema).optional(),
  visualizations: z.array(visualizationSchema),
});
export type TrainingBatchDetailDTO = z.infer<typeof trainingBatchDetailSchema>;

export const trainingSessionSchema = z.object({
  session_id: z.string(),
  current_game_id: z.string().nullable().optional(),
  ruleset: z.string(),
  bot_count: z.number().int(),
  generation: z.number().int(),
  generations_left: z.number().int(),
  games_per_generation: z.number().int().optional(),
  games_completed: z.number().int().optional(),
  games_failed: z.number().int().optional(),
  current_generation_game_index: z.number().int().optional(),
  population_size: z.number().int(),
  elite_count: z.number().int().optional(),
  selection_size: z.number().int().optional(),
  mutation_strength: z.number().optional(),
  mutation_rate: z.number().optional(),
  random_immigrant_count: z.number().int().optional(),
  generation_statistics: z.array(trainingGenerationStatisticsSchema),
});
export type TrainingSessionDTO = z.infer<typeof trainingSessionSchema>;

export const trainingSessionsSchema = z.object({ sessions: z.array(trainingSessionSchema) });
export type TrainingSessionsDTO = z.infer<typeof trainingSessionsSchema>;
