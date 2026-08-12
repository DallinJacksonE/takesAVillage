import { describe, expect, it } from "vitest";

import { GamesRepository } from "../../../src/db/mysql/games.js";
import { GenomesRepository } from "../../../src/db/mysql/genomes.js";
import { TrainingRepository } from "../../../src/db/mysql/training.js";
import { UsersRepository } from "../../../src/db/mysql/users.js";
import { VisualizationsRepository } from "../../../src/db/mysql/visualizations.js";

class FakeExecutor {
  readonly calls: Array<{ sql: string; values: unknown[] }> = [];
  readonly results: unknown[] = [];

  async execute(sql: string, values: unknown[] = []): Promise<[unknown, unknown[]]> {
    this.calls.push({ sql: sql.replace(/\s+/g, " ").trim(), values });
    return [this.results.shift() ?? { affectedRows: 1, insertId: 1 }, []];
  }
}

describe("MySQL repositories", () => {
  it("uses placeholders and ordered values for writes", async () => {
    const executor = new FakeExecutor();
    const users = new UsersRepository(executor);
    const games = new GamesRepository(executor);
    const genomes = new GenomesRepository(executor);
    const training = new TrainingRepository(executor);
    const visualizations = new VisualizationsRepository(executor);

    await users.createUser("user-1", true);
    await games.storeGameResult("game-1", 2, "NIGHT", { day: 2 }, { tradeCount: 3 });
    await genomes.storeGenome("Genome", "G1", { food_weight: 1 });
    await training.createTrainingBatch("batch-1", { ruleset: "default", config: {} });
    expect(await visualizations.storeResearchVisualization({
      scopeType: "game",
      scopeId: "game-1",
      name: "inventory",
      title: "Inventory",
      mimeType: "image/svg+xml",
      imageBytes: Buffer.from("<svg/>"),
    })).toBe("1");

    expect(executor.calls).toHaveLength(5);
    for (const call of executor.calls) {
      expect(call.sql).toContain("?");
      expect(call.values.length).toBeGreaterThan(0);
    }
    expect(executor.calls[0]?.values).toEqual(["user-1", true]);
    expect(executor.calls[1]?.values).toEqual([
      "game-1", 2, "NIGHT", JSON.stringify({ day: 2 }), "human", null, null, 3, null, null,
    ]);
  });

  it("decodes JSON and binary rows created by the Python service", async () => {
    const executor = new FakeExecutor();
    executor.results.push([
      {
        game_id: "game-1",
        day_num: 2,
        phase: "NIGHT",
        data: JSON.stringify({ day: 2 }),
        created_at: new Date("2026-08-11T00:00:00Z"),
      },
    ]);
    executor.results.push([
      {
        id: 7,
        scope_type: "game",
        scope_id: "game-1",
        name: "inventory",
        title: "Inventory",
        mime_type: "image/svg+xml",
        image_bytes: Buffer.from("<svg/>"),
        metadata: JSON.stringify({ source: "python" }),
        created_at: new Date("2026-08-11T00:00:00Z"),
      },
    ]);

    const games = await new GamesRepository(executor).getAllGames();
    const visualization = await new VisualizationsRepository(executor).getResearchVisualization("7");

    expect(games[0]?.data).toEqual({ day: 2 });
    expect(visualization).toMatchObject({ id: "7", metadata: { source: "python" } });
    expect(visualization?.image_bytes).toEqual(Buffer.from("<svg/>"));
  });
});
