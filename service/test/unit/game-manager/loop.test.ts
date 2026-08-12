import { describe, expect, it, vi } from "vitest";

import { Game } from "../../../src/game/game.js";
import { GameLoop } from "../../../src/game-manager/loop.js";
import { GameRegistry } from "../../../src/game-manager/registry.js";

describe("game loop", () => {
  it("ticks every running game and isolates broadcast failures", async () => {
    const registry = new GameRegistry();
    const first = new Game("game-1", "host-1");
    const second = new Game("game-2", "host-2");
    first.status = "RUNNING";
    second.status = "RUNNING";
    vi.spyOn(first, "checkTimer").mockReturnValue(true);
    vi.spyOn(second, "checkTimer").mockReturnValue(true);
    registry.create(first);
    registry.create(second);
    const broadcastStates = vi.fn()
      .mockRejectedValueOnce(new Error("socket failed"))
      .mockResolvedValue(undefined);
    const logger = { error: vi.fn() };
    const loop = new GameLoop({
      registry,
      persistCompleted: vi.fn(),
      broadcastStates,
      logger,
    });

    await loop.tickOnce();

    expect(first.checkTimer).toHaveBeenCalledOnce();
    expect(second.checkTimer).toHaveBeenCalledOnce();
    expect(broadcastStates).toHaveBeenCalledTimes(2);
    expect(logger.error).toHaveBeenCalledOnce();
  });

  it("retains an ended game until persistence succeeds, then removes it exactly once", async () => {
    const registry = new GameRegistry();
    const game = new Game("game-1", "host-1");
    game.status = "ENDED";
    registry.create(game);
    const persistCompleted = vi.fn()
      .mockRejectedValueOnce(new Error("database unavailable"))
      .mockResolvedValue(undefined);
    const loop = new GameLoop({
      registry,
      persistCompleted,
      broadcastStates: vi.fn(),
    });

    await loop.tickOnce();
    expect(registry.get(game.id)).toBe(game);

    await loop.tickOnce();
    await loop.tickOnce();
    expect(persistCompleted).toHaveBeenCalledTimes(2);
    expect(registry.get(game.id)).toBeUndefined();
  });

  it("notifies training completion without blocking removal or later ticks", async () => {
    const registry = new GameRegistry();
    const game = new Game("game-1", "host-1", "default", 0, true, () => 100, {
      trainingSessionId: "batch-1",
    });
    game.status = "ENDED";
    registry.create(game);
    let release!: () => void;
    const blocked = new Promise<void>((resolve) => { release = resolve; });
    const trainingCompletionCallback = vi.fn(() => blocked);
    const loop = new GameLoop({
      registry,
      persistCompleted: vi.fn(),
      broadcastStates: vi.fn(),
      trainingCompletionCallback,
    });
    let tickResolved = false;

    const tick = loop.tickOnce().then(() => { tickResolved = true; });
    await tick;

    expect(trainingCompletionCallback).toHaveBeenCalledWith("game-1", "batch-1");
    expect(registry.get(game.id)).toBeUndefined();
    expect(tickResolved).toBe(true);
    release();
  });

  it("starts and cancels through an injected scheduler without real timers", async () => {
    let scheduled!: () => void | Promise<void>;
    const handle = { id: 1 };
    const scheduler = {
      setInterval: vi.fn((callback: () => void | Promise<void>) => { scheduled = callback; return handle; }),
      clearInterval: vi.fn(),
    };
    const loop = new GameLoop({
      registry: new GameRegistry(),
      persistCompleted: vi.fn(),
      broadcastStates: vi.fn(),
      scheduler,
    });
    const tickOnce = vi.spyOn(loop, "tickOnce").mockResolvedValue(undefined);

    const stop = loop.start(250);
    await scheduled();
    stop();

    expect(scheduler.setInterval).toHaveBeenCalledWith(expect.any(Function), 250);
    expect(tickOnce).toHaveBeenCalledOnce();
    expect(scheduler.clearInterval).toHaveBeenCalledWith(handle);
  });

  it("waits for in-flight phase persistence before storing a completed game", async () => {
    let release!: () => void;
    const phasePersistence = new Promise<void>((resolve) => { release = resolve; });
    const game = new Game("game-1", "host-1", "default", 0, false, () => 100, {
      onPhaseCompleted: () => phasePersistence,
    });
    game.addPlayer("host-1");
    game.startGame();
    game.nextPhase();
    game.status = "ENDED";
    const registry = new GameRegistry();
    registry.create(game);
    const persistCompleted = vi.fn();
    const loop = new GameLoop({ registry, persistCompleted, broadcastStates: vi.fn() });

    const tick = loop.tickOnce();
    await Promise.resolve();
    expect(persistCompleted).not.toHaveBeenCalled();

    release();
    await tick;
    expect(persistCompleted).toHaveBeenCalledOnce();
  });
});
