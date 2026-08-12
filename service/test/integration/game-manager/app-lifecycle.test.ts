import { describe, expect, it, vi } from "vitest";

import { buildApp } from "../../../src/app.js";
import { MemoryDatabase } from "../../../src/db/memory.js";
import { GameRegistry } from "../../../src/game-manager/registry.js";

describe("application game-manager wiring", () => {
  it("creates managed games, persists phases/completion, and cancels the loop on close", async () => {
    const database = new MemoryDatabase();
    const registry = new GameRegistry();
    let scheduled!: () => void | Promise<void>;
    const handle = { id: 1 };
    const scheduler = {
      setInterval: vi.fn((callback: () => void | Promise<void>) => { scheduled = callback; return handle; }),
      clearInterval: vi.fn(),
    };
    const app = await buildApp({
      databaseType: "memory",
      botSecret: "test-secret",
      database,
      registry,
      scheduler,
    });

    const consent = await app.inject({ method: "POST", url: "/api/consent" });
    const userId = consent.json<{ userId: string }>().userId;
    const created = await app.inject({
      method: "POST",
      url: "/api/newGame",
      headers: { cookie: `user_session=${userId}` },
      payload: { ruleset: "default", botCount: 0 },
    });
    const game = registry.get(created.json<{ gameId: string }>().gameId)!;
    game.addPlayer(userId);
    game.startGame();
    game.nextPhase();
    await Promise.resolve();
    expect(database.workSnapshots).toHaveLength(1);

    game.phase = "NIGHT";
    game.day = game.gameLength;
    game.nextPhase();
    await scheduled();
    expect(registry.get(game.id)).toBeUndefined();
    expect(await database.getAllGames()).toHaveLength(1);

    await app.close();
    expect(scheduler.clearInterval).toHaveBeenCalledWith(handle);
  });
});
