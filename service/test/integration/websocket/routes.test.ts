import { afterEach, describe, expect, it } from "vitest";
import WebSocket from "ws";

import {
  outboundGameEventSchema,
  trainingSessionsEventSchema,
  type TrainingSessionsDTO,
} from "@takes-a-village/shared";

import { TrainingUpdateHub } from "../../../src/api/websocket/training-router.js";
import { buildApp } from "../../../src/app.js";

const apps: Array<Awaited<ReturnType<typeof buildApp>>> = [];

class PacketQueue {
  private readonly packets: unknown[] = [];
  private readonly waiters: Array<(packet: unknown) => void> = [];

  push(packet: unknown): void {
    const waiter = this.waiters.shift();
    if (waiter) waiter(packet);
    else this.packets.push(packet);
  }

  async next(): Promise<unknown> {
    const packet = this.packets.shift();
    if (packet) return packet;
    return await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error("Timed out waiting for WebSocket packet")), 2_000);
      this.waiters.push((value) => {
        clearTimeout(timer);
        resolve(value);
      });
    });
  }
}

async function openSocket(url: string, cookie?: string): Promise<{ socket: WebSocket; queue: PacketQueue }> {
  const socket = new WebSocket(url, cookie ? { headers: { cookie } } : undefined);
  const queue = new PacketQueue();
  socket.on("message", (raw) => queue.push(JSON.parse(raw.toString())));
  await new Promise<void>((resolve, reject) => {
    socket.once("open", resolve);
    socket.once("error", reject);
  });
  return { socket, queue };
}

async function nextEvent(queue: PacketQueue, event: string): Promise<unknown> {
  for (;;) {
    const packet = await queue.next() as { event?: string };
    if (packet.event === event) return packet;
  }
}

async function startApp(options: Parameters<typeof buildApp>[0]): Promise<{ app: Awaited<ReturnType<typeof buildApp>>; baseUrl: string }> {
  const app = await buildApp(options);
  apps.push(app);
  await app.listen({ host: "127.0.0.1", port: 0 });
  const address = app.server.address();
  if (!address || typeof address === "string") throw new Error("Expected TCP address");
  return { app, baseUrl: `http://127.0.0.1:${address.port}` };
}

afterEach(async () => {
  await Promise.all(apps.splice(0).map((app) => app.close()));
});

describe("TypeScript WebSocket routes", () => {
  it("replaces duplicate game connections and keeps the replacement usable", async () => {
    const { app, baseUrl } = await startApp({ databaseType: "memory", botSecret: "test-secret" });
    const consent = await app.inject({ method: "POST", url: "/api/consent" });
    const userId = consent.json<{ userId: string }>().userId;
    const setCookie = consent.headers["set-cookie"];
    const cookie = (Array.isArray(setCookie) ? setCookie[0] : setCookie)!.split(";", 1)[0]!;
    const gameResponse = await app.inject({
      method: "POST",
      url: "/api/newGame",
      headers: { cookie },
      payload: { ruleset: "default", botCount: 0 },
    });
    const gameId = gameResponse.json<{ gameId: string }>().gameId;
    const wsUrl = `${baseUrl.replace("http", "ws")}/ws`;
    const { socket: first, queue: firstQueue } = await openSocket(wsUrl, cookie);
    first.send(JSON.stringify({ event: "join_room", data: { gameId, userId } }));
    await nextEvent(firstQueue, "room_update");

    const replaced = new Promise<number>((resolve) => first.once("close", resolve));
    const { socket: replacement, queue: replacementQueue } = await openSocket(wsUrl, cookie);
    replacement.send(JSON.stringify({ event: "join_room", data: { gameId, userId } }));
    expect(await replaced).toBe(4001);
    await nextEvent(replacementQueue, "room_update");

    replacement.send(JSON.stringify([]));
    expect(outboundGameEventSchema.parse(await replacementQueue.next())).toEqual({
      event: "error",
      data: { message: "Invalid WebSocket packet." },
    });
    replacement.send(JSON.stringify({ event: "request_update", data: { gameId, userId } }));
    expect(outboundGameEventSchema.parse(await nextEvent(replacementQueue, "game_state")).event).toBe("game_state");
    replacement.close();
  });

  it("enforces browser-cookie and registered-bot authentication", async () => {
    const { app, baseUrl } = await startApp({ databaseType: "memory", botSecret: "test-secret" });
    const consent = await app.inject({ method: "POST", url: "/api/consent" });
    const hostId = consent.json<{ userId: string }>().userId;
    const setCookie = consent.headers["set-cookie"];
    const cookie = (Array.isArray(setCookie) ? setCookie[0] : setCookie)!.split(";", 1)[0]!;
    const gameResponse = await app.inject({
      method: "POST",
      url: "/api/newGame",
      headers: { cookie },
      payload: { ruleset: "default", botCount: 0 },
    });
    const gameId = gameResponse.json<{ gameId: string }>().gameId;
    const wsUrl = `${baseUrl.replace("http", "ws")}/ws`;

    const { socket: unauthenticated, queue: unauthenticatedQueue } = await openSocket(wsUrl);
    unauthenticated.send(JSON.stringify({ event: "join_room", data: { gameId, userId: hostId } }));
    expect(await unauthenticatedQueue.next()).toEqual({
      event: "error",
      data: { message: "WebSocket authentication failed." },
    });
    unauthenticated.close();

    const botJoin = await app.inject({
      method: "POST",
      url: "/api/botJoinGame",
      payload: { gameId, botSecret: "test-secret" },
    });
    const botId = botJoin.json<{ userId: string }>().userId;
    const { socket: bot, queue: botQueue } = await openSocket(wsUrl);
    bot.send(JSON.stringify({ event: "join_room", data: { gameId, userId: botId, botSecret: "wrong" } }));
    expect(await botQueue.next()).toEqual({
      event: "error",
      data: { message: "WebSocket authentication failed." },
    });
    bot.send(JSON.stringify({ event: "join_room", data: { gameId, userId: botId, botSecret: "test-secret" } }));
    expect(outboundGameEventSchema.parse(await nextEvent(botQueue, "room_update")).event).toBe("room_update");
    bot.close();
  });

  it("sends training state on connection and subsequent hub updates", async () => {
    const hub = new TrainingUpdateHub();
    let sessions: TrainingSessionsDTO = { sessions: [] };
    const { baseUrl } = await startApp({
      databaseType: "memory",
      botSecret: "test-secret",
      trainingHub: hub,
      listTrainingSessions: () => sessions,
    });
    const { socket, queue } = await openSocket(`${baseUrl.replace("http", "ws")}/ws/research/training-sessions`);
    expect(trainingSessionsEventSchema.parse(await queue.next())).toEqual({
      event: "training_sessions",
      data: { sessions: [] },
    });

    sessions = {
      sessions: [{
        session_id: "session-1",
        ruleset: "default",
        bot_count: 2,
        generation: 1,
        generations_left: 1,
        population_size: 2,
        generation_statistics: [],
      }],
    };
    hub.broadcast(sessions);
    expect(trainingSessionsEventSchema.parse(await queue.next()).data.sessions[0]?.session_id).toBe("session-1");
    socket.close();
  });
});
