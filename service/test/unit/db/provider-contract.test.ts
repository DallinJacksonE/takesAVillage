import { describe, expect, it } from "vitest";

import { MemoryDatabase } from "../../../src/db/memory.js";

async function exerciseProvider(database: MemoryDatabase) {
  await database.initialize();
  expect(await database.createUser("user-1", true)).toBe(true);
  expect(await database.userExists("user-1")).toBe(true);
  expect(await database.userExists("missing")).toBe(false);

  await database.storeGameSnapshot("game-1", 1, "WORK", { day: 1 });
  await database.storeGameResult("game-1", 2, "NIGHT", { day: 2 }, {
    trainingBatchId: "batch-1",
    trainingGeneration: 2,
    tradeCount: 3,
    contestCount: 4,
    lieCount: 5,
  });
  expect((await database.getAllGameHistory()).map((row) => row.data)).toEqual([
    { day: 2 },
    { day: 1 },
  ]);
  expect((await database.getAllGames())[0]).toMatchObject({
    trade_count: 3,
    contest_count: 4,
    lie_count: 5,
  });

  await database.storeGenome("genome-1", "G1", { food_weight: 1 });
  expect((await database.getAllGenomes())[0]?.genome_data).toEqual({ food_weight: 1 });

  await database.createTrainingBatch("batch-1", {
    ruleset: "default",
    bot_model: "GOAPGenetic",
    bot_count: 2,
    total_generations: 1,
    base_genome_id: "random",
    config: { games_per_generation: 1 },
  });
  await database.markTrainingBatchGameStarted("batch-1", "game-1", 1, 1);
  await database.markTrainingBatchGameRunning("batch-1", "game-1");
  await database.markTrainingBatchGameCompleted("batch-1", "game-1", 2, {
    best_fitness: 10,
    average_fitness: 8,
  });
  await database.appendTrainingBatchGenerationStats("batch-1", {
    generation: 1,
    best_fitness: 10,
  });
  await database.completeTrainingBatch("batch-1", "genome-1");
  expect(await database.getTrainingBatch("batch-1")).toMatchObject({
    status: "completed",
    final_champion_genome_id: "genome-1",
    generation_statistics: [{ generation: 1, best_fitness: 10 }],
    games: [{ game_id: "game-1", status: "completed", genome_count: 2 }],
  });

  const visualizationId = await database.storeResearchVisualization({
    scopeType: "game",
    scopeId: "game-1",
    name: "inventory",
    title: "Inventory",
    mimeType: "image/svg+xml",
    imageBytes: Buffer.from("<svg/>") ,
    metadata: { player: "user-1" },
  });
  const listing = await database.getResearchVisualizations("game", "game-1");
  expect(listing[0]).not.toHaveProperty("image_bytes");
  expect((await database.getResearchVisualization(visualizationId))?.image_bytes).toEqual(Buffer.from("<svg/>"));
  await database.deleteResearchVisualizations("game", "game-1");
  expect(await database.getResearchVisualizations("game", "game-1")).toEqual([]);
}

describe("database provider contract", () => {
  it("preserves users, games, training state, genomes, and visualizations in memory", async () => {
    await exerciseProvider(new MemoryDatabase());
  });
});
