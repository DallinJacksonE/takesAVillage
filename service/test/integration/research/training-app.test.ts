import { afterEach, describe, expect, it, vi } from "vitest";

import { trainingSessionsSchema } from "@takes-a-village/shared";

import { buildApp } from "../../../src/app.js";
import { MemoryDatabase } from "../../../src/db/memory.js";
import { GameRegistry } from "../../../src/game-manager/registry.js";
import { TrainingService } from "../../../src/research/training/service.js";

const apps: Awaited<ReturnType<typeof buildApp>>[] = [];
afterEach(async () => Promise.all(apps.splice(0).map((app) => app.close())));

describe("training application wiring", () => {
  it("starts, lists, cancels, reruns, and receives game completion through the manager", async () => {
    const database = new MemoryDatabase();
    const registry = new GameRegistry();
    const spawnBots = vi.fn().mockResolvedValue({ ok: true });
    const fetchGameGenomes = vi.fn().mockResolvedValue({ ok: true, entries: [] });
    const app = await buildApp({
      databaseType: "memory",
      botSecret: "secret",
      database,
      registry,
      trainingBotClient: { spawnBots, fetchGameGenomes },
      trainingIdFactory: (() => { let id = 0; return () => `session-${++id}`; })(),
    });
    apps.push(app);

    expect((await app.inject({ method: "POST", url: "/api/research/train", payload: { botCount: 1, generations: 2, gamesPerGeneration: 1 } })).statusCode).toBe(200);
    await vi.waitFor(() => expect(spawnBots).toHaveBeenCalledOnce());
    const sessions = trainingSessionsSchema.parse((await app.inject({ method: "GET", url: "/api/research/training-sessions" })).json());
    expect(sessions.sessions[0]?.session_id).toBe("session-1");

    const batches = (await app.inject({ method: "GET", url: "/api/research/training-batches" })).json<{ batches: Array<{ batch_id: string }> }>();
    expect(batches.batches[0]?.batch_id).toBe("session-1");
    expect((await app.inject({ method: "POST", url: "/api/research/training-batches/session-1/cancel", payload: { reason: "operator" } })).statusCode).toBe(200);
    expect((await app.inject({ method: "POST", url: "/api/research/training-batches/session-1/rerun" })).statusCode).toBe(200);
    await vi.waitFor(() => expect(spawnBots).toHaveBeenCalledTimes(2));
  });

  it("returns not found for unknown cancel and rerun batches", async () => {
    const app = await buildApp({ databaseType: "memory", botSecret: "secret" });
    apps.push(app);
    expect((await app.inject({ method: "POST", url: "/api/research/training-batches/missing/cancel" })).statusCode).toBe(404);
    expect((await app.inject({ method: "POST", url: "/api/research/training-batches/missing/rerun" })).statusCode).toBe(404);
  });
});
