import mysql from "mysql2/promise";
import { describe, expect, it } from "vitest";

import { loadServiceConfig } from "../../../src/config.js";
import { MySqlDatabase } from "../../../src/db/mysql/provider.js";

const configPath = process.env.MYSQL_TEST_CONFIG_PATH;
const integration = configPath ? it : it.skip;

describe("MySQL provider integration", () => {
  integration("keeps the Python schema and JSON rows compatible", async () => {
    const serviceConfig = await loadServiceConfig(configPath);
    if (serviceConfig.database.type !== "mysql") throw new Error("MySQL integration config must select mysql");
    const config = serviceConfig.database;
    const database = new MySqlDatabase(config);
    const direct = await mysql.createConnection({
      host: config.host,
      port: config.port,
      user: config.user,
      password: config.password,
      database: config.name,
    });
    const suffix = crypto.randomUUID().slice(0, 8);
    const userId = `user-${suffix}`;
    const gameId = `python-${suffix}`;
    const batchId = `batch-${suffix}`;

    try {
      await database.initialize();
      expect(await database.createUser(userId, true)).toBe(true);
      expect(await database.userExists(userId)).toBe(true);
      await direct.execute(
        "INSERT INTO games (game_id, day_num, phase, data) VALUES (?, ?, ?, ?)",
        [gameId, 2, "NIGHT", JSON.stringify({ producer: "python" })],
      );
      expect((await database.getAllGames()).find((row) => row.game_id === gameId)?.data).toEqual({ producer: "python" });
      await database.storeGameSnapshot(gameId, 1, "WORK", { day: 1 });
      await database.storePlayerSnapshot(gameId, 1, "WORK", {
        session_id: userId,
        name: "Player",
        health: "HEALTHY",
        sickness_chance: 0,
        resources: {},
        fire_status: "NONE",
        fire_guests: [],
        developments: [],
        actions: [],
        committed_action: null,
        available_work: [],
        finished_phase: false,
        timeline: [],
        trade_history: [],
      });
      await database.storeWorkSnapshot({ game_id: gameId, player_id: userId, day_num: 1, health: "HEALTHY", sickness_chance: 0, wood: 0, food: 0, iron: 0, available_work: [], committed_action: null });
      await database.storeTradeSnapshot({ game_id: gameId, player_id: userId, day_num: 1, health: "HEALTHY", sickness_chance: 0, wood: 0, food: 0, iron: 0, trade_history: [] });
      await database.storeNightSnapshot({ game_id: gameId, player_id: userId, day_num: 1, health: "HEALTHY", sickness_chance: 0, wood: 0, food: 0, iron: 0, fire_status: "NONE", fire_guests: [] });
      await database.storeGenome(`genome-${suffix}`, "G1", { food_weight: 1 });
      expect((await database.getAllGenomes()).some((row) => row.name === `genome-${suffix}`)).toBe(true);

      await database.createTrainingBatch(batchId, { config: { games_per_generation: 2 } });
      await Promise.all([
        database.markTrainingBatchGameStarted(batchId, `${gameId}-a`, 1),
        database.markTrainingBatchGameStarted(batchId, `${gameId}-b`, 1),
      ]);
      expect(new Set((await database.getTrainingGames(batchId)).map((game) => game.game_id))).toEqual(
        new Set([`${gameId}-a`, `${gameId}-b`]),
      );
      const visualizationId = await database.storeResearchVisualization({
        scopeType: "game",
        scopeId: gameId,
        name: "inventory",
        title: "Inventory",
        mimeType: "image/svg+xml",
        imageBytes: Buffer.from("<svg/>"),
        metadata: { source: "typescript" },
      });
      expect((await database.getResearchVisualization(visualizationId))?.metadata).toEqual({ source: "typescript" });
      expect((await database.getResearchVisualizations("game", gameId))[0]?.id).toBe(visualizationId);
      await database.deleteResearchVisualizations("game", gameId);
    } finally {
      await direct.end();
      await database.close();
    }
  });
});
