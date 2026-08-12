import { describe, expect, it } from "vitest";

import type { JsonObject } from "../../../../src/db/contracts.js";
import { MemoryDatabase } from "../../../../src/db/memory.js";
import { VisualizationRegistry } from "../../../../src/research/visualizations/registry.js";
import { VisualizationRunner, type VisualizationCommand } from "../../../../src/research/visualizations/runner.js";
import { ResearchVisualizationService } from "../../../../src/research/visualizations/service.js";
import { defaultBatchVisualizationCommands } from "../../../../src/research/visualizations/batch-commands.js";
import { defaultGameVisualizationCommands } from "../../../../src/research/visualizations/game-commands.js";

const command: VisualizationCommand = {
  name: "fitness",
  title: "Fitness Over Time",
  description: "Fitness series",
  render: () => '<svg xmlns="http://www.w3.org/2000/svg"><title>Fitness Over Time</title></svg>',
};

describe("research visualization infrastructure", () => {
  it("rejects duplicate command names", () => {
    const registry = new VisualizationRegistry([command]);
    expect(() => registry.register(command)).toThrow("Duplicate visualization command: fitness");
  });

  it("runs registered commands and persists valid SVG metadata", async () => {
    const database = new MemoryDatabase();
    const runner = new VisualizationRunner(database, new VisualizationRegistry([command]));

    await expect(runner.runAll("game", "game-1", {})).resolves.toHaveLength(1);
    const stored = await database.getResearchVisualizations("game", "game-1");
    expect(stored[0]).toMatchObject({ name: "fitness", title: "Fitness Over Time", mime_type: "image/svg+xml" });
    const bytes = (await database.getResearchVisualization(stored[0]!.id))!.image_bytes!;
    expect(bytes.toString("utf8")).toContain("<svg");
  });

  it("caches completed-game charts and regenerates training-batch charts", async () => {
    const database = new MemoryDatabase();
    const gameRunner = new VisualizationRunner(database, new VisualizationRegistry([command]));
    const batchRunner = new VisualizationRunner(database, new VisualizationRegistry([command]));
    const service = new ResearchVisualizationService(database, gameRunner, batchRunner);

    const firstGame = await service.ensure("game", "game-1", {});
    const secondGame = await service.ensure("game", "game-1", {});
    const firstBatch = await service.ensure("training_batch", "batch-1", {});
    const secondBatch = await service.ensure("training_batch", "batch-1", { generation: 2 } as JsonObject);

    expect(secondGame.map((item) => item.id)).toEqual(firstGame.map((item) => item.id));
    expect(secondBatch).toHaveLength(1);
    expect(secondBatch[0]!.id).not.toBe(firstBatch[0]!.id);
  });

  it("renders all six migrated chart commands deterministically", () => {
    const gameContext = {
      data: {
        map: { "1": {} },
        players: {
          "1": {
            p1: { resources: { food: 3, wood: 2, iron: 1 }, developments: ["farm"], trade_count: 1, committed_action: { type: "CONTEST" } },
          },
        },
      },
    } as JsonObject;
    const batchContext = {
      generation_statistics: [{ generation: 1, best_fitness: 8, average_fitness: 5 }],
      games: [{ game_id: "g1", trade_count: 2, lie_count: 1, contest_count: 3 }],
    } as JsonObject;
    const commands = [...defaultGameVisualizationCommands(), ...defaultBatchVisualizationCommands()];
    const contexts = commands.map((_item, index) => index < 4 ? gameContext : batchContext);

    expect(commands.map((item) => item.name)).toEqual([
      "best_player_inventory_over_time",
      "trades_per_player",
      "developments_built",
      "contests",
      "fitness_over_generations",
      "trading_and_contesting_per_game",
    ]);
    commands.forEach((item, index) => {
      const first = item.render(contexts[index]!);
      expect(item.render(contexts[index]!)).toBe(first);
      expect(first).toContain("<svg");
      expect(first).toContain(item.title);
    });
  });
});
