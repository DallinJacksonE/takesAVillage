import type { TrainingGenomeEntry, TrainingGenerationStatisticsDTO } from "@takes-a-village/shared";

import type { JsonObject } from "../../db/contracts.js";

export interface TrainingAttempt {
  attempt: number;
  status: "spawning" | "running" | "completed" | "failed";
  updatedAt: Date;
}

export interface TrainingSession {
  ruleset: string;
  botCount: number;
  generationsLeft: number;
  population: JsonObject[];
  generation: number;
  eliteCount: number;
  selectionSize: number;
  mutationStrength: number;
  mutationRate: number;
  randomImmigrantCount: number;
  generationStatistics: TrainingGenerationStatisticsDTO[];
  botModel: string;
  gamesPerGeneration: number;
  gamesCompleted: number;
  gamesFailed: number;
  currentGenerationGameIndex: number;
  currentGameId?: string;
  fitnessEntries: TrainingGenomeEntry[];
  games: string[];
  allFitnessEntries: TrainingGenomeEntry[];
  processedGameIds: Set<string>;
  processingGameIds?: Set<string>;
  generationAttempts: Map<string, TrainingAttempt>;
  generationTerminalGameIds: Set<string>;
  generationScheduled: boolean;
  baseGenome?: JsonObject;
}

export class TrainingSessionStore {
  private readonly sessions: Map<string, TrainingSession>;

  constructor(sessions?: Map<string, TrainingSession>) {
    this.sessions = sessions ?? new Map();
  }

  add(sessionId: string, session: TrainingSession): void { this.sessions.set(sessionId, session); }
  contains(sessionId: string): boolean { return this.sessions.has(sessionId); }
  remove(sessionId: string): TrainingSession | undefined {
    const session = this.sessions.get(sessionId);
    this.sessions.delete(sessionId);
    return session ? structuredClone(session) : undefined;
  }
  get(sessionId: string): TrainingSession | undefined {
    const session = this.sessions.get(sessionId);
    return session ? structuredClone(session) : undefined;
  }
  list(): Map<string, TrainingSession> { return structuredClone(this.sessions); }
  runtimeSessions(): Map<string, TrainingSession> { return this.sessions; }
}
