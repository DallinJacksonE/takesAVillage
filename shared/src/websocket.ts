import { z } from "zod";

import { jsonValueSchema } from "./common.js";
import { chatMessageSchema, gameStateSchema } from "./game.js";
import { trainingSessionsSchema } from "./research.js";

export const gameActionPayloadSchema = z.object({
  gameId: z.string(),
  userId: z.string(),
  action_command: z.string(),
  payload: z.record(z.string(), jsonValueSchema),
});
export type GameActionPayload<T = unknown> = Omit<z.infer<typeof gameActionPayloadSchema>, "payload"> & { payload: T };

export const inboundGameEventSchema = z.discriminatedUnion("event", [
  z.object({ event: z.literal("join_room"), data: z.object({ gameId: z.string(), userId: z.string(), botSecret: z.string().optional() }) }),
  z.object({ event: z.literal("start_game_request"), data: z.object({ gameId: z.string(), userId: z.string() }) }),
  z.object({ event: z.literal("request_update"), data: z.object({ gameId: z.string(), userId: z.string() }) }),
  z.object({ event: z.literal("send_chat"), data: z.object({ gameId: z.string(), userId: z.string(), content: z.string(), to_id: z.string() }) }),
  z.object({ event: z.literal("create_chat"), data: z.object({ gameId: z.string(), userId: z.string(), name: z.string(), memberIds: z.array(z.string()) }) }),
  z.object({ event: z.literal("submit_action"), data: gameActionPayloadSchema }),
]);
export type InboundGameEvent = z.infer<typeof inboundGameEventSchema>;

export const outboundGameEventSchema = z.discriminatedUnion("event", [
  z.object({ event: z.literal("room_update"), data: z.object({ player_count: z.number().int() }) }),
  z.object({ event: z.literal("game_state"), data: gameStateSchema }),
  z.object({ event: z.literal("game_started"), data: z.object({ day: z.number().int() }) }),
  z.object({ event: z.literal("chat_history"), data: z.array(chatMessageSchema) }),
  z.object({ event: z.literal("new_chat_message"), data: chatMessageSchema }),
  z.object({ event: z.literal("error"), data: z.object({ message: z.string(), action_command: z.string().optional() }) }),
]);
export type OutboundGameEvent = z.infer<typeof outboundGameEventSchema>;

export const trainingSessionsEventSchema = z.object({
  event: z.literal("training_sessions"),
  data: trainingSessionsSchema,
});
export type TrainingSessionsEvent = z.infer<typeof trainingSessionsEventSchema>;
