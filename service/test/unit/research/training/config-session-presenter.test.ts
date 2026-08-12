import { describe, expect, it } from "vitest";

import { createTrainingConfig } from "../../../../src/research/training/config.js";
import { presentTrainingSessions } from "../../../../src/research/training/presenter.js";
import { TrainingSessionStore, type TrainingSession } from "../../../../src/research/training/session-store.js";

function session(): TrainingSession {
  return {
    ruleset: "default",
    botCount: 2,
    generationsLeft: 3,
    population: [{ food_weight: 1 }, { food_weight: 2 }],
    generation: 1,
    eliteCount: 2,
    selectionSize: 2,
    mutationStrength: 0.25,
    mutationRate: 0.15,
    randomImmigrantCount: 1,
    generationStatistics: [],
    botModel: "genetic",
    gamesPerGeneration: 5,
    gamesCompleted: 0,
    gamesFailed: 0,
    currentGenerationGameIndex: 0,
    fitnessEntries: [],
    games: [],
    allFitnessEntries: [],
    processedGameIds: new Set(),
    generationAttempts: new Map(),
    generationTerminalGameIds: new Set(),
    generationScheduled: false,
  };
}

describe("training configuration and session presentation", () => {
  it("applies legacy defaults and clamps games per generation", () => {
    expect(createTrainingConfig()).toMatchObject({
      ruleset: "default",
      botCount: 5,
      generations: 1,
      baseGenomeId: "random",
      botModel: "genetic",
      mutationStrength: 0.25,
      mutationRate: 0.15,
      randomImmigrantCount: 1,
      gamesPerGeneration: 5,
    });
    expect(createTrainingConfig({ gamesPerGeneration: 0 }).gamesPerGeneration).toBe(1);
    expect(createTrainingConfig({ gamesPerGeneration: 99 }).gamesPerGeneration).toBe(50);
  });

  it("does not expose mutable runtime session state", () => {
    const store = new TrainingSessionStore();
    store.add("session-1", session());

    const status = store.get("session-1")!;
    status.generation = 99;
    status.population[0]!.food_weight = 99;

    expect(store.get("session-1")?.generation).toBe(1);
    expect(store.get("session-1")?.population[0]).toEqual({ food_weight: 1 });
    expect(store.remove("session-1")?.generation).toBe(1);
  });

  it("presents only JSON-safe shared session fields", () => {
    const runtime = session();
    runtime.currentGameId = "game-1";
    runtime.gamesCompleted = 2;

    expect(presentTrainingSessions(new Map([["session-1", runtime]]))).toEqual({
      sessions: [{
        session_id: "session-1",
        current_game_id: "game-1",
        ruleset: "default",
        bot_count: 2,
        generation: 1,
        generations_left: 3,
        games_per_generation: 5,
        games_completed: 2,
        games_failed: 0,
        current_generation_game_index: 0,
        population_size: 2,
        elite_count: 2,
        selection_size: 2,
        mutation_strength: 0.25,
        mutation_rate: 0.15,
        random_immigrant_count: 1,
        generation_statistics: [],
      }],
    });
  });
});
