import { z } from "zod";

export const jsonValueSchema = z.json();
export type JsonValue = z.infer<typeof jsonValueSchema>;

export const resourceSchema = z.enum(["wood", "food", "iron"]);
export type Resource = z.infer<typeof resourceSchema>;

export const phaseSchema = z.enum(["WORK", "TRADE", "NIGHT"]);
export type Phase = z.infer<typeof phaseSchema>;

export const gameStatusSchema = z.enum(["WAITING", "RUNNING", "ENDED"]);
export type GameStatus = z.infer<typeof gameStatusSchema>;

export const actionStatusSchema = z.enum([
  "PENDING",
  "ACCEPTED",
  "COMMITTED",
  "DENIED",
  "CANCELED",
  "COMPLETED",
]);
export type ActionStatus = z.infer<typeof actionStatusSchema>;

export const resourceBundleSchema = z.object({
  wood: z.number(),
  food: z.number(),
  iron: z.number(),
});
export type ResourceBundle = z.infer<typeof resourceBundleSchema>;

export const partialResourceBundleSchema = resourceBundleSchema.partial();
export type PartialResourceBundle = z.infer<typeof partialResourceBundleSchema>;
