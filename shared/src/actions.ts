import { z } from "zod";

import {
  actionStatusSchema,
  partialResourceBundleSchema,
  resourceSchema,
} from "./common.js";

export const baseActionSchema = z.object({
  id: z.string(),
  initiator_id: z.string(),
  target_id: z.string().optional(),
  status: actionStatusSchema,
  waiting_on_id: z.string().nullable().optional(),
});
export type BaseActionDTO = z.infer<typeof baseActionSchema>;

export const employmentActionSchema = baseActionSchema.extend({
  type: z.literal("EMPLOYMENT"),
  dev_id: z.string().optional(),
  wage: z.number().optional(),
  wage_type: resourceSchema.optional(),
  is_application: z.boolean(),
});
export type EmploymentActionDTO = z.infer<typeof employmentActionSchema>;

export const tradeActionSchema = baseActionSchema.extend({
  type: z.enum(["TRADE", "BARTER"]),
  offer_items: partialResourceBundleSchema.optional(),
  request_items: partialResourceBundleSchema.optional(),
  actual_offer_items: partialResourceBundleSchema.optional(),
  actual_request_items: partialResourceBundleSchema.optional(),
  initiator_finalized: z.boolean(),
  target_finalized: z.boolean(),
  waiting_on_id: z.string().nullable(),
});
export type TradeActionDTO = z.infer<typeof tradeActionSchema>;

export const campfireActionSchema = baseActionSchema.extend({
  type: z.enum(["CAMPFIRE", "START_FIRE"]),
  is_request: z.boolean(),
});
export type CampfireActionDTO = z.infer<typeof campfireActionSchema>;

export const systemActionSchema = baseActionSchema.extend({
  type: z.enum(["MAINTENANCE", "UPGRADE"]),
  dev_id: z.string().optional(),
  cost: z.number().optional(),
  cost_type: resourceSchema.optional(),
});
export type SystemActionDTO = z.infer<typeof systemActionSchema>;

export const contestActionSchema = baseActionSchema.extend({
  type: z.enum(["CONTEST", "JOIN_CONTEST"]),
  dev_id: z.string(),
});
export type ContestActionDTO = z.infer<typeof contestActionSchema>;

export const actionSchema = z.union([
  employmentActionSchema,
  tradeActionSchema,
  campfireActionSchema,
  systemActionSchema,
  contestActionSchema,
]);
export type ActionDTO = z.infer<typeof actionSchema>;

export const tradeHistorySchema = z.object({
  id: z.string(),
  initiator_id: z.string(),
  target_id: z.string(),
  offered: partialResourceBundleSchema,
  requested: partialResourceBundleSchema,
  actual_sent: partialResourceBundleSchema,
  actual_received: partialResourceBundleSchema,
});
export type TradeHistoryDTO = z.infer<typeof tradeHistorySchema>;

export const buildDevPayloadSchema = z.object({ tile_id: z.string() });
export type BuildDevPayload = z.infer<typeof buildDevPayloadSchema>;

export const targetDevPayloadSchema = z.object({ dev_id: z.string() });
export type TargetDevPayload = z.infer<typeof targetDevPayloadSchema>;

export const contestDevPayloadSchema = z.object({
  dev_id: z.string(),
  target_id: z.string().optional(),
  side: z.enum(["INITIATOR", "CONTESTER", "OWNER"]).optional(),
});
export type ContestDevPayload = z.infer<typeof contestDevPayloadSchema>;

export const contractActionPayloadSchema = z.object({
  action_id: z.string(),
  type: z.string().optional(),
});
export type ContractActionPayload = z.infer<typeof contractActionPayloadSchema>;

export const draftTradePayloadSchema = z.object({
  target_id: z.string(),
  offer_items: partialResourceBundleSchema,
  request_items: partialResourceBundleSchema,
  type: z.literal("TRADE"),
});
export type DraftTradePayload = z.infer<typeof draftTradePayloadSchema>;

export const counterTradePayloadSchema = z.object({
  action_id: z.string(),
  offer_items: partialResourceBundleSchema,
  request_items: partialResourceBundleSchema,
});
export type CounterTradePayload = z.infer<typeof counterTradePayloadSchema>;

export const finalizeTradePayloadSchema = z.object({
  action_id: z.string(),
  actual_items: partialResourceBundleSchema,
});
export type FinalizeTradePayload = z.infer<typeof finalizeTradePayloadSchema>;

export const draftEmploymentPayloadSchema = z.object({
  target_id: z.string(),
  dev_id: z.string(),
  wage: z.number(),
  wage_type: resourceSchema,
  is_application: z.boolean(),
  type: z.literal("EMPLOYMENT"),
});
export type DraftEmploymentPayload = z.infer<typeof draftEmploymentPayloadSchema>;

export const draftCampfirePayloadSchema = z.object({
  target_id: z.string(),
  is_request: z.boolean(),
  type: z.literal("CAMPFIRE"),
});
export type DraftCampfirePayload = z.infer<typeof draftCampfirePayloadSchema>;
