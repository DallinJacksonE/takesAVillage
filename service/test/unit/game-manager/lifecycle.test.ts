import { describe, expect, it, vi } from "vitest";

import { GameLifecycleService } from "../../../src/game-manager/lifecycle.js";
import { GameRegistry } from "../../../src/game-manager/registry.js";

describe("game lifecycle", () => {
  it("creates a registered game with creation metadata and a phase-completion callback", () => {
    const registry = new GameRegistry();
    const onPhaseCompleted = vi.fn();
    const lifecycle = new GameLifecycleService(registry, {
      idFactory: () => "abcd-efgh",
      clock: () => 100,
      onPhaseCompleted,
    });

    const gameId = lifecycle.createGame("host-1", "default", {
      botCount: 2,
      training: true,
      trainingSessionId: "batch-1",
      trainingGeneration: 3,
    });
    const game = registry.get(gameId);

    expect(gameId).toBe("g_abcd");
    expect(game).toMatchObject({
      id: "g_abcd",
      hostId: "host-1",
      botCount: 2,
      training: true,
      trainingSessionId: "batch-1",
      trainingGeneration: 3,
    });
    game?.addPlayer("host-1");
    game?.startGame();
    game?.nextPhase();
    expect(onPhaseCompleted).toHaveBeenCalledWith(game, "WORK");
  });
});
