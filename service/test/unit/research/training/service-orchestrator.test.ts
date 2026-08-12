import { describe, expect, it, vi } from "vitest";

import { MemoryDatabase } from "../../../../src/db/memory.js";
import { GameLifecycleService } from "../../../../src/game-manager/lifecycle.js";
import type { CreateGameOptions } from "../../../../src/game-manager/lifecycle.js";
import { GameRegistry } from "../../../../src/game-manager/registry.js";
import { TrainingService } from "../../../../src/research/training/service.js";

function dependencies(overrides: Record<string, unknown> = {}) {
  const database = new MemoryDatabase();
  const registry = new GameRegistry();
  const hub = { broadcast: vi.fn() };
  const botClient = {
    spawnBots: vi.fn().mockResolvedValue({ ok: true }),
    fetchGameGenomes: vi.fn().mockResolvedValue({ ok: true, entries: [] }),
  };
  let id = 0;
  const lifecycle = new GameLifecycleService(registry, { idFactory: () => `${++id}abc-uuid` });
  return {
    database,
    registry,
    hub,
    botClient,
    service: new TrainingService({
      database,
      createGame: (hostId: string, ruleset: string, options: CreateGameOptions) => lifecycle.createGame(hostId, ruleset, options),
      botClient,
      updateHub: hub,
      idFactory: () => "session-1",
      random: () => 0.5,
      ...overrides,
    }),
  };
}

describe("training service orchestration", () => {
  it("persists before publishing a session and schedules generation games concurrently", async () => {
    const { service, database, registry, botClient } = dependencies();
    const sessionId = await service.start({ botCount: 2, generations: 2, gamesPerGeneration: 3, botModel: "GOAPGenetic" });

    expect(sessionId).toBe("session-1");
    expect(registry.size).toBe(3);
    expect([...registry.values()].every((game) => game.trainingSessionId === sessionId && game.trainingGeneration === 1)).toBe(true);
    expect(botClient.spawnBots).toHaveBeenCalledTimes(3);
    expect((await database.getTrainingBatch(sessionId))?.games).toHaveLength(3);
    expect(service.list().sessions[0]).toMatchObject({ games_per_generation: 3, current_generation_game_index: 3 });
  });

  it("does not publish or create games when batch persistence fails", async () => {
    const database = new MemoryDatabase();
    vi.spyOn(database, "createTrainingBatch").mockRejectedValue(new Error("database unavailable"));
    const { service, registry } = dependencies({ database });

    await expect(service.start({ botCount: 1, gamesPerGeneration: 1 })).rejects.toThrow("database unavailable");
    expect(service.list()).toEqual({ sessions: [] });
    expect(registry.size).toBe(0);
  });

  it("deduplicates completion, aggregates fitness, and completes the final generation", async () => {
    const { service, database, botClient } = dependencies();
    botClient.fetchGameGenomes.mockResolvedValue({
      ok: true,
      entries: [
        { game_id: "g", fitness: 10, genome: { food_weight: 1 }, stats: { survived: true, resources: { food: 2 } } },
        { game_id: "g", fitness: 6, genome: { food_weight: 0.5 }, stats: { survived: false, resources: { food: 0 } } },
      ],
    });
    await service.start({ botCount: 2, generations: 1, gamesPerGeneration: 1 });
    const gameId = service.list().sessions[0]!.current_game_id!;

    await Promise.all([
      service.handleGameEnded(gameId, "session-1"),
      service.handleGameEnded(gameId, "session-1"),
    ]);

    expect(botClient.fetchGameGenomes).toHaveBeenCalledOnce();
    expect(service.list()).toEqual({ sessions: [] });
    expect((await database.getTrainingBatch("session-1"))?.status).toBe("completed");
    expect((await database.getTrainingGames("session-1"))[0]).toMatchObject({ status: "completed", genome_count: 2, best_fitness: 10, average_fitness: 8 });
    expect(await database.getAllGenomes()).toHaveLength(1);
  });

  it("counts spawn failures as terminal attempts and completes without genomes", async () => {
    const { service, database, botClient } = dependencies();
    botClient.spawnBots.mockResolvedValue({ ok: false, errorMessage: "offline" });

    await service.start({ botCount: 1, generations: 1, gamesPerGeneration: 1 });

    expect(service.list()).toEqual({ sessions: [] });
    expect((await database.getTrainingGames("session-1"))[0]).toMatchObject({ status: "failed", error_message: "Bot service spawn failed: offline" });
    expect((await database.getTrainingBatch("session-1"))?.status).toBe("completed");
  });

  it("cancels active sessions and reruns persisted configuration", async () => {
    const { service, database } = dependencies();
    await service.start({ botCount: 1, generations: 2, gamesPerGeneration: 1, mutationRate: 0.4 });
    expect(await service.cancel("session-1", "operator")).toBe(true);
    expect((await database.getTrainingBatch("session-1"))?.status).toBe("cancelled");

    const rerunId = await service.rerun("session-1");
    expect(rerunId).toBe("session-1");
    expect(service.list().sessions[0]).toMatchObject({ bot_count: 1, games_per_generation: 1, mutation_rate: 0.4 });
  });

  it("marks stale persisted batches and stale active attempts", async () => {
    const now = new Date("2026-01-01T00:10:00Z");
    const { service, database } = dependencies({ clock: () => now });
    await database.createTrainingBatch("missing", {});
    const missing = await database.getTrainingBatch("missing");
    missing!.last_heartbeat_at = new Date("2026-01-01T00:00:00Z");
    vi.spyOn(database, "getTrainingBatches").mockResolvedValue([missing!]);

    await service.reconcileStalled(30_000);

    expect((await database.getTrainingBatch("missing"))?.status).toBe("stalled");
  });
});
