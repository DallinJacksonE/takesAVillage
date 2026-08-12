import { trainingSessionsSchema, type TrainingSessionsDTO } from "@takes-a-village/shared";

import type { TrainingSession } from "./session-store.js";

export function presentTrainingSessions(sessions: Map<string, TrainingSession>): TrainingSessionsDTO {
  return trainingSessionsSchema.parse({
    sessions: [...sessions].map(([sessionId, session]) => ({
      session_id: sessionId,
      current_game_id: session.currentGameId,
      ruleset: session.ruleset,
      bot_count: session.botCount,
      generation: session.generation,
      generations_left: session.generationsLeft,
      games_per_generation: session.gamesPerGeneration,
      games_completed: session.gamesCompleted,
      games_failed: session.gamesFailed,
      current_generation_game_index: session.currentGenerationGameIndex,
      population_size: session.population.length,
      elite_count: session.eliteCount,
      selection_size: session.selectionSize,
      mutation_strength: session.mutationStrength,
      mutation_rate: session.mutationRate,
      random_immigrant_count: session.randomImmigrantCount,
      generation_statistics: session.generationStatistics,
    })),
  });
}
