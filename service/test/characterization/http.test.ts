import { afterAll, beforeAll, describe, expect, it } from "vitest";

import {
  activeGamesSchema,
  botJoinRequestSchema,
  consentSchema,
  joinGameRequestSchema,
  newGameOptionsSchema,
  newGameRequestSchema,
  newGameResponseSchema,
  researchGameListItemSchema,
} from "@takes-a-village/shared";

import { startService, type RunningService } from "./harness.js";

describe("service HTTP compatibility", () => {
  let service: RunningService;
  let cookie: string;
  let userId: string;
  let gameId: string;

  beforeAll(async () => {
    service = await startService();
  });

  afterAll(async () => {
    await service.stop();
  });

  it("issues and verifies a consent session", async () => {
    const consentResponse = await fetch(`${service.baseUrl}/api/consent`, { method: "POST" });
    expect(consentResponse.status).toBe(200);
    const consent = consentSchema.parse(await consentResponse.json());
    userId = consent.userId;
    cookie = consentResponse.headers.getSetCookie()[0]?.split(";", 1)[0] ?? "";
    expect(cookie).toBe(`user_session=${userId}`);

    const verifyResponse = await fetch(`${service.baseUrl}/api/verifySession`, {
      headers: { cookie },
    });
    expect(verifyResponse.status).toBe(200);
    expect(await verifyResponse.json()).toMatchObject({ userId, message: "Session valid" });
  });

  it("rejects active games without a session", async () => {
    expect((await fetch(`${service.baseUrl}/api/activeGames`)).status).toBe(403);
  });

  it("lists rules and creates a game using the public contract", async () => {
    const optionsResponse = await fetch(`${service.baseUrl}/api/newGame`);
    expect(optionsResponse.status).toBe(200);
    expect(Object.keys(newGameOptionsSchema.parse(await optionsResponse.json()).options)).toContain("default");

    const request = newGameRequestSchema.parse({ ruleset: "default", botCount: 0 });
    const createResponse = await fetch(`${service.baseUrl}/api/newGame`, {
      method: "POST",
      headers: { "content-type": "application/json", cookie },
      body: JSON.stringify(request),
    });
    expect(createResponse.status).toBe(200);
    gameId = newGameResponseSchema.parse(await createResponse.json()).gameId;

    const activeResponse = await fetch(`${service.baseUrl}/api/activeGames`, { headers: { cookie } });
    const active = activeGamesSchema.parse(await activeResponse.json());
    // The legacy lifecycle adds the host on WebSocket join, not HTTP creation.
    expect(active.games).toContainEqual(expect.objectContaining({ id: gameId, isRejoinable: false }));
  });

  it("joins an existing game and enforces bot authentication", async () => {
    const joinRequest = joinGameRequestSchema.parse({ gameId });
    const joinResponse = await fetch(`${service.baseUrl}/api/joinGame`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(joinRequest),
    });
    expect(joinResponse.status).toBe(200);
    expect(newGameResponseSchema.parse(await joinResponse.json()).gameId).toBe(gameId);

    const rejected = await fetch(`${service.baseUrl}/api/botJoinGame`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(botJoinRequestSchema.parse({ gameId, botSecret: "wrong" })),
    });
    expect(rejected.status).toBe(403);

    const accepted = await fetch(`${service.baseUrl}/api/botJoinGame`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ gameId, botSecret: "characterization-secret" }),
    });
    expect(accepted.status).toBe(200);
    expect(await accepted.json()).toMatchObject({ gameId });
  });

  it("returns research games in the shared shape", async () => {
    const response = await fetch(`${service.baseUrl}/api/research/games`);
    expect(response.status).toBe(200);
    const payload = await response.json();
    expect(Array.isArray(payload)).toBe(true);
    for (const item of payload) researchGameListItemSchema.parse(item);
  });
});