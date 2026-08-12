import { z } from "zod";

import {
  actionSchema,
  tradeHistorySchema,
} from "./actions.js";
import {
  gameStatusSchema,
  jsonValueSchema,
  partialResourceBundleSchema,
  phaseSchema,
  resourceBundleSchema,
  resourceSchema,
} from "./common.js";

export const genomeSchema = z.object({
  id: z.number(),
  shorthand_name: z.string(),
  name: z.string(),
  genome_data: jsonValueSchema,
  created_at: z.string(),
});
export type GenomeDTO = z.infer<typeof genomeSchema>;

export const developmentActionsSchema = z.object({
  build: partialResourceBundleSchema,
  maintain: partialResourceBundleSchema,
  upgrade: partialResourceBundleSchema,
});
export type DevelopmentActions = z.infer<typeof developmentActionsSchema>;
export const developmentCostsDictSchema = z.record(z.string(), developmentActionsSchema);
export type DevelopmentCostsDict = z.infer<typeof developmentCostsDictSchema>;

export const chatMessageSchema = z.object({
  id: z.string(),
  from_id: z.string(),
  content: z.string(),
  to_id: z.string().optional(),
  created_at: z.string().optional(),
  timestamp: z.number().optional(),
});
export type ChatMessageDTO = z.infer<typeof chatMessageSchema>;

export const chatSchema = z.object({
  id: z.string(),
  name: z.string(),
  member_ids: z.array(z.string()),
  creator_id: z.string(),
});
export type ChatDTO = z.infer<typeof chatSchema>;

export const developmentSchema = z.object({
  id: z.string(),
  type: z.enum(["Farm", "Woods", "Mine"]),
  level: z.number(),
  maintenance_days: z.number(),
  owner_id: z.string(),
  is_contested: z.boolean().optional(),
  contest_initiator_id: z.string().nullable().optional(),
  contester_supporters: z.array(z.string()).optional(),
  owner_supporters: z.array(z.string()).optional(),
  maintenance_cost: z.record(z.string(), z.number()),
  upgrade_cost: z.record(z.string(), z.number()),
  can_upgrade: z.boolean(),
  pending_contest: z.boolean(),
});
export type DevelopmentDTO = z.infer<typeof developmentSchema>;

export const mapTileSchema = z.object({
  id: z.string(),
  q: z.number(),
  r: z.number(),
  type: z.enum(["Farm", "Woods", "Mine"]),
  development: developmentSchema.nullable().optional(),
});
export type MapTileDTO = z.infer<typeof mapTileSchema>;

export const workActionSchema = z.object({
  development: developmentSchema,
  wage: z.number(),
  wage_type: resourceSchema,
  employer_id: z.string(),
  action_id: z.string(),
});
export type WorkActionDTO = z.infer<typeof workActionSchema>;

export const commitWorkPayloadSchema = z.object({ job: workActionSchema });
export type CommitWorkPayload = z.infer<typeof commitWorkPayloadSchema>;

export const committedContestActionSchema = z.object({
  type: z.literal("CONTEST_ACTION"),
  dev_id: z.string(),
  side: z.enum(["CONTESTER", "OWNER"]),
});
export type CommittedContestActionDTO = z.infer<typeof committedContestActionSchema>;

export const developmentCostConfigSchema = z.object({
  build: partialResourceBundleSchema,
  maintain: partialResourceBundleSchema,
  upgrade: partialResourceBundleSchema,
});
export type DevelopmentCostConfig = z.infer<typeof developmentCostConfigSchema>;

export const fireHistorySchema = z.object({
  fire_id: z.string(),
  host_id: z.string(),
  role: z.enum(["host", "guest"]),
  guests: z.array(z.string()),
});
export type FireHistoryDTO = z.infer<typeof fireHistorySchema>;

export const playerSchema = z.object({
  id: z.string(),
  name: z.string(),
  health: z.enum(["healthy", "sick", "recovering", "dead"]),
  sickness_chance: z.number(),
  fire_status: z.enum(["COLD", "HOST", "GUEST"]),
  fire_guests: z.array(z.string()),
  resources: resourceBundleSchema,
  developments: z.array(z.string()),
  available_work: z.array(workActionSchema),
  committed_action: z.union([workActionSchema, committedContestActionSchema]).nullable(),
  actions: z.array(actionSchema),
  timeline: z.array(jsonValueSchema),
  finished_phase: z.boolean(),
  trade_history: z.array(tradeHistorySchema).optional(),
  fire_history: z.array(fireHistorySchema).optional(),
});
export type PlayerDTO = z.infer<typeof playerSchema>;

export const gameStateSchema = z.object({
  status: gameStatusSchema,
  is_host: z.boolean(),
  host_connected: z.boolean(),
  me: playerSchema,
  day: z.number().int(),
  game_length: z.number().int(),
  phase: phaseSchema,
  time_remaining: z.number().int(),
  player_list: z.array(playerSchema),
  map: z.record(z.string(), mapTileSchema),
  developments: z.array(developmentSchema),
  chats: z.array(chatSchema),
  development_costs: developmentCostsDictSchema,
  max_fire_seats: z.number().int(),
  campfire_cost: partialResourceBundleSchema,
  session_id: z.string().optional(),
  cold_sickness_rate: z.number(),
  hunger_sickness_rate: z.number(),
  recovery_rate: z.number(),
  training: z.boolean(),
});
export type GameStateDTO = z.infer<typeof gameStateSchema>;
