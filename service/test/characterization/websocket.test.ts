import { afterAll, beforeAll, describe, expect, it } from "vitest";
import WebSocket from "ws";

import {
  consentSchema,
  newGameResponseSchema,
  outboundGameEventSchema,
  type OutboundGameEvent,
} from "@takes-a-village/shared";

import { startService, type RunningService } from "./harness.js";

class MessageQueue {
  private readonly messages: unknown[] = [];
  private readonly waiters: Array<(message: unknown) => void> = [];

  constructor(socket: WebSocket) {
    socket.on("message", (data) => {
      const message: unknown = JSON.parse(data.toString());
      const waiter = this.waiters.shift();
      if (waiter) waiter(message);
      else this.messages.push(message);
    });
  }

  async next(): Promise<OutboundGameEvent> {
    const message = this.messages.length > 0
      ? this.messages.shift()
      : await new Promise<unknown>((resolveMessage) => this.waiters.push(resolveMessage));
    return outboundGameEventSchema.parse(message);
  }

  async event<T extends OutboundGameEvent["event"]>(event: T): Promise<Extract<OutboundGameEvent, { event: T }>> {
    for (;;) {
      const message = await this.next();
      if (message.event === event) return message as Extract<OutboundGameEvent, { event: T }>;
    }
  }
}

describe("legacy Python game WebSocket compatibility", () => {
  let service: RunningService;
  let socket: WebSocket;
  let messages: MessageQueue;
  let gameId: string;
  let userId: string;
  let cookie: string;

  beforeAll(async () => {
    service = await startService();
    const consentResponse = await fetch(`${service.baseUrl}/api/consent`, { method: "POST" });
    userId = consentSchema.parse(await consentResponse.json()).userId;
    cookie = consentResponse.headers.getSetCookie()[0]?.split(";", 1)[0] ?? "";
    const gameResponse = await fetch(`${service.baseUrl}/api/newGame`, {
      method: "POST",
      headers: { "content-type": "application/json", cookie },
      body: JSON.stringify({ ruleset: "default", botCount: 0, botGenome: "random", botModel: "genetic" }),
    });
    gameId = newGameResponseSchema.parse(await gameResponse.json()).gameId;
    socket = new WebSocket(service.baseUrl.replace("http", "ws") + "/ws", { headers: { cookie } });
    await new Promise<void>((resolveOpen, rejectOpen) => {
      socket.once("open", resolveOpen);
      socket.once("error", rejectOpen);
    });
    messages = new MessageQueue(socket);
  });

  afterAll(async () => {
    socket?.close();
    await service.stop();
  });

  it("joins, emits the canonical waiting state, and starts the game", async () => {
    socket.send(JSON.stringify({ event: "join_room", data: { gameId, userId } }));

    expect((await messages.event("chat_history")).data).toEqual([]);
    const waitingState = (await messages.event("game_state")).data;
    expect(waitingState).toMatchObject({ status: "WAITING", session_id: userId, map: {} });
    expect((await messages.event("room_update")).data.player_count).toBe(1);

    socket.send(JSON.stringify({ event: "start_game_request", data: { gameId, userId } }));
    expect((await messages.event("game_started")).data.day).toBe(1);
    const runningState = (await messages.event("game_state")).data;
    expect(runningState.status).toBe("RUNNING");
    expect(Object.keys(runningState.map).length).toBeGreaterThan(0);
  });
});