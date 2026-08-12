import { describe, expect, expectTypeOf, it } from "vitest";

import {
  actionSchema,
  gameStateSchema,
  rootConfigSchema,
  serviceConfigSchema,
  spawnBotsRequestSchema,
  trainingGenomeEntriesResponseSchema,
  visualizationSchema,
  type GameStateDTO,
  type RootConfig,
} from "../src/index.js";

const serializedState = {
  status: "RUNNING",
  is_host: true,
  host_connected: true,
  me: {
    id: "player-1",
    name: "Ada",
    health: "healthy",
    sickness_chance: 0,
    fire_status: "COLD",
    fire_guests: [],
    resources: { wood: 1, food: 2, iron: 3 },
    developments: [],
    available_work: [],
    committed_action: null,
    actions: [],
    timeline: [],
    finished_phase: false,
  },
  day: 1,
  game_length: 10,
  phase: "WORK",
  time_remaining: 30,
  player_list: [],
  map: {},
  developments: [],
  chats: [],
  development_costs: {},
  max_fire_seats: 4,
  campfire_cost: { wood: 1, food: 0, iron: 0 },
  session_id: "player-1",
  cold_sickness_rate: 0.1,
  hunger_sickness_rate: 0.2,
  recovery_rate: 0.3,
  training: false,
};

describe("shared contracts", () => {
  it("accepts the canonical Python serializer game shape", () => {
    expect(gameStateSchema.parse(serializedState)).toEqual(serializedState);
    expectTypeOf<GameStateDTO>().toMatchTypeOf<typeof serializedState>();
  });

  it("rejects frontend-only status drift", () => {
    expect(() => gameStateSchema.parse({ ...serializedState, status: "ACTIVE" })).toThrow();
  });

  it("accepts an accepted Python trade contract with no waiting player", () => {
    expect(actionSchema.parse({
      id: "trade-1",
      initiator_id: "player-1",
      target_id: "player-2",
      type: "TRADE",
      status: "ACCEPTED",
      waiting_on_id: null,
      offer_items: { food: 2 },
      request_items: { wood: 1 },
      actual_offer_items: { food: 2 },
      actual_request_items: { wood: 1 },
      initiator_finalized: false,
      target_finalized: false,
    })).toMatchObject({ waiting_on_id: null });
  });

  it("preserves the waiting player field on Python employment contracts", () => {
    expect(actionSchema.parse({
      id: "employment-1",
      initiator_id: "player-1",
      target_id: "player-2",
      type: "EMPLOYMENT",
      status: "ACCEPTED",
      waiting_on_id: null,
      dev_id: "dev-1",
      wage: 2,
      wage_type: "food",
      is_application: false,
    })).toMatchObject({ waiting_on_id: null });
  });

  it("accepts the canonical Python contest commitment shape", () => {
    const committedAction = {
      type: "CONTEST_ACTION",
      dev_id: "dev-1",
      side: "CONTESTER",
    };
    expect(gameStateSchema.parse({
      ...serializedState,
      me: { ...serializedState.me, committed_action: committedAction },
    }).me.committed_action).toEqual(committedAction);
  });

  it("requires globally non-conflicting development and production ports", () => {
    const valid: RootConfig = {
      development: { database: 23308, service: 25000, bots: 28001, frontend: 24999 },
      production: { database: 33308, service: 35000, bots: 38001, frontend: 34999 },
    };
    expect(rootConfigSchema.parse(valid)).toEqual(valid);
    expect(() => rootConfigSchema.parse({ ...valid, production: { ...valid.production, service: valid.development.service } })).toThrow();
  });

  it("validates private service configuration", () => {
    expect(serviceConfigSchema.parse({
      database: { type: "memory", host: "db", port: 3306, user: "village", password: "test", name: "village" },
      bots: { secret: "test-secret", httpUrl: "http://bots:8001", gameServerHttpUrl: "http://service:5000", gameServerWsUrl: "ws://service:5000/ws" },
    }).bots.secret).toBe("test-secret");
  });

  it("uses SVG as the visualization contract", () => {
    expect(visualizationSchema.parse({
      id: "viz-1",
      scope_type: "game",
      scope_id: "game-1",
      name: "inventory",
      title: "Inventory",
      mime_type: "image/svg+xml",
      url: "/api/research/visualizations/viz-1",
      created_at: "2026-08-11T00:00:00Z",
    }).mime_type).toBe("image/svg+xml");
  });

  it("validates training bot spawn attempts and returned genome entries", () => {
    expect(spawnBotsRequestSchema.parse({
      gameId: "game-1",
      botCount: 2,
      botSecret: "secret",
      botModel: "GOAPGenetic",
      baseGenome: [{ food_weight: 1 }],
      trainingAttemptIndex: 3,
    }).trainingAttemptIndex).toBe(3);
    expect(trainingGenomeEntriesResponseSchema.parse({
      game_id: "game-1",
      entries: [{ game_id: "game-1", fitness: 8, genome: { food_weight: 1 } }],
    }).entries).toHaveLength(1);
  });
});
