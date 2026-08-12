import { describe, expect, it, vi } from "vitest";

import { BotServiceClient } from "../../../../src/research/training/bot-client.js";

describe("training bot client", () => {
  it("sends the shared spawn payload including attempt index", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: "success", message: "ok" }), { status: 200 }));
    const client = new BotServiceClient("http://bots:8001/", "secret", { fetcher });

    expect(await client.spawnBots({ gameId: "game-1", botCount: 2, botModel: "GOAPGenetic", baseGenome: [{ food_weight: 1 }], trainingAttemptIndex: 3 })).toEqual({ ok: true });
    expect(fetcher).toHaveBeenCalledWith("http://bots:8001/api/spawn_bots", expect.objectContaining({
      method: "POST",
      body: JSON.stringify({ gameId: "game-1", botCount: 2, botSecret: "secret", botModel: "GOAPGenetic", baseGenome: [{ food_weight: 1 }], trainingAttemptIndex: 3 }),
    }));
  });

  it("retries all-genome retrieval then falls back to the legacy best-genome endpoint", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(new Response("not ready", { status: 404 }))
      .mockResolvedValueOnce(new Response("not ready", { status: 404 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ genome: { food_weight: 2 }, best_fitness: 7 }), { status: 200 }));
    const sleep = vi.fn().mockResolvedValue(undefined);
    const client = new BotServiceClient("http://bots:8001", "secret", { fetcher, sleep, genomeFetchAttempts: 2 });

    expect(await client.fetchGameGenomes("game-1")).toEqual({
      ok: true,
      entries: [{ game_id: "game-1", fitness: 7, genome: { food_weight: 2 } }],
    });
    expect(sleep).toHaveBeenCalledOnce();
    expect(fetcher).toHaveBeenLastCalledWith("http://bots:8001/api/genomes/game-1", expect.any(Object));
  });

  it("returns errors instead of throwing on rejected bot requests", async () => {
    const client = new BotServiceClient("http://bots:8001", "secret", {
      fetcher: vi.fn().mockRejectedValue(new Error("offline")),
      genomeFetchAttempts: 1,
    });
    await expect(client.spawnBots({ gameId: "g", botCount: 1, botModel: "genetic" })).resolves.toEqual({ ok: false, errorMessage: "offline" });
  });
});
