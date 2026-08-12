import { describe, expect, it } from "vitest";

import { MemoryDatabase } from "../../../src/db/memory.js";
import { Game } from "../../../src/game/game.js";
import { persistCompletedGame, persistPhaseCompletion } from "../../../src/game-manager/persistence.js";

function runningGame(training = false): Game {
  const game = new Game("game-1", "player-1", "default", 0, training, () => 100);
  game.addPlayer("player-1");
  game.startGame();
  return game;
}

describe("game persistence", () => {
  it("stores each non-training phase snapshot and a game snapshot at night", async () => {
    const database = new MemoryDatabase();
    const game = runningGame();

    await persistPhaseCompletion(database, game, "WORK");
    await persistPhaseCompletion(database, game, "TRADE");
    await persistPhaseCompletion(database, game, "NIGHT");

    expect(database.workSnapshots).toHaveLength(1);
    expect(database.tradeSnapshots).toHaveLength(1);
    expect(database.nightSnapshots).toHaveLength(1);
    expect(await database.getAllGameHistory()).toHaveLength(1);
    expect((await database.getAllGameHistory())[0]).toMatchObject({
      game_id: "game-1",
      day_num: 1,
      phase: "NIGHT",
    });
  });

  it("does not store phase snapshots for training games", async () => {
    const database = new MemoryDatabase();
    await persistPhaseCompletion(database, runningGame(true), "WORK");
    expect(database.workSnapshots).toEqual([]);
  });

  it("stores completed-game history and creation metadata in the deployed row shape", async () => {
    const database = new MemoryDatabase();
    const game = new Game("game-1", "player-1", "default", 2, true, () => 100, {
      trainingSessionId: "batch-1",
      trainingGeneration: 4,
    });
    game.addPlayer("player-1");
    game.startGame();
    game.gameLength = 1;
    game.phase = "NIGHT";
    game.tradeCount = 3;
    game.contestCount = 2;
    game.lieCount.set("player-1", 4);
    game.nextPhase();

    await persistCompletedGame(database, game);

    expect((await database.getAllGames())[0]).toMatchObject({
      game_id: "game-1",
      game_type: "training",
      training_batch_id: "batch-1",
      training_generation: 4,
      trade_count: 3,
      contest_count: 2,
      lie_count: 4,
      data: {
        training: true,
        training_session_id: "batch-1",
        training_generation: 4,
        map: { "1": expect.any(Object) },
        players: { "1": { "player-1": expect.any(Object) } },
      },
    });
  });
});
