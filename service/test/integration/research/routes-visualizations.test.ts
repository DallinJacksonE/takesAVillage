import { afterEach, describe, expect, it } from "vitest";

import { researchGameDetailSchema, researchGameListItemSchema, visualizationSchema } from "@takes-a-village/shared";

import { buildApp } from "../../../src/app.js";
import { MemoryDatabase } from "../../../src/db/memory.js";

const apps: Awaited<ReturnType<typeof buildApp>>[] = [];
afterEach(async () => Promise.all(apps.splice(0).map((app) => app.close())));

const gameSnapshot = {
  map: { "1": {} },
  players: {
    "1": {
      "player-1": {
        health: "healthy",
        actions: [],
        resources: { wood: 2, food: 4, iron: 1 },
        fire_status: "WARM",
        developments: ["farm-1"],
        finished_phase: true,
        sickness_chance: 0,
        committed_action: null,
        trade_count: 2,
      },
    },
  },
};

describe("research HTTP routes", () => {
  it("searches and sorts completed games and returns generated SVG detail", async () => {
    const database = new MemoryDatabase();
    await database.storeGameResult("game-b", 4, "NIGHT", gameSnapshot, { gameType: "human" });
    await database.storeGameResult("game-a", 5, "NIGHT", gameSnapshot, { gameType: "training", trainingBatchId: "batch-1" });
    const app = await buildApp({ databaseType: "memory", botSecret: "secret", database });
    apps.push(app);

    const listResponse = await app.inject({ method: "GET", url: "/api/research/games?search=game&sort=name_asc" });
    const listed = researchGameListItemSchema.array().parse(listResponse.json());
    expect(listed.map((game) => game.game_id)).toEqual(["game-a", "game-b"]);

    const detailResponse = await app.inject({ method: "GET", url: "/api/research/games/game-a" });
    const detail = researchGameDetailSchema.parse(detailResponse.json());
    expect(detail.visualizations).toHaveLength(4);
    detail.visualizations.forEach((item) => visualizationSchema.parse(item));

    const image = await app.inject({ method: "GET", url: detail.visualizations[0]!.url });
    expect(image.headers["content-type"]).toContain("image/svg+xml");
    expect(image.body).toContain("<svg");
  });

  it("returns persisted genomes with bot model fallback and route not-found responses", async () => {
    const database = new MemoryDatabase();
    await database.storeGenome("candidate", "C1", { food_weight: 1 });
    const app = await buildApp({
      databaseType: "memory",
      botSecret: "secret",
      database,
      fetchBotModels: async () => [],
    });
    apps.push(app);

    const genomes = (await app.inject({ method: "GET", url: "/api/research/genomes" })).json<{ genomes: Array<{ name: string }>; models: string[] }>();
    expect(genomes).toMatchObject({ genomes: [{ name: "candidate" }], models: ["genetic"] });
    expect((await app.inject({ method: "GET", url: "/api/research/games/missing" })).statusCode).toBe(404);
    expect((await app.inject({ method: "GET", url: "/api/research/visualizations/missing" })).statusCode).toBe(404);
  });
});
