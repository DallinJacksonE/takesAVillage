import type { TrainingSessionsDTO } from "@takes-a-village/shared";

import type { DatabaseProvider } from "../../db/contracts.js";
import type { CreateGameOptions } from "../../game-manager/lifecycle.js";
import type { TrainingBotClient } from "./bot-client.js";
import { createTrainingConfig, type TrainingConfigInput } from "./config.js";
import { TrainingOrchestrator, type TrainingUpdatePublisher } from "./orchestrator.js";
import { presentTrainingSessions } from "./presenter.js";
import { TrainingSessionStore, type TrainingSession } from "./session-store.js";

export interface TrainingServiceOptions {
  database: DatabaseProvider;
  createGame(hostId: string, ruleset: string, options: CreateGameOptions): string;
  botClient: TrainingBotClient;
  updateHub: TrainingUpdatePublisher;
  store?: TrainingSessionStore;
  idFactory: () => string;
  random?: () => number;
  clock?: () => Date;
}

function numericOption(value: unknown, fallback: number): number { return typeof value === "number" ? value : fallback; }

export class TrainingService {
  readonly store: TrainingSessionStore;
  private readonly orchestrator: TrainingOrchestrator;

  constructor(private readonly options: TrainingServiceOptions) {
    this.store = options.store ?? new TrainingSessionStore();
    this.orchestrator = new TrainingOrchestrator({
      ...options,
      sessions: this.store.runtimeSessions(),
    });
  }

  async start(input: TrainingConfigInput = {}): Promise<string> {
    return this.orchestrator.start(createTrainingConfig(input));
  }

  async cancel(sessionId: string, reason = "Training cancelled by operator"): Promise<boolean> {
    return this.orchestrator.cancel(sessionId, reason);
  }

  async rerun(batchId: string): Promise<string | null> {
    const batch = await this.options.database.getTrainingBatch(batchId);
    if (!batch) return null;
    const config = batch.config ?? {};
    return this.start({
      ruleset: batch.ruleset ?? "default",
      botCount: batch.bot_count ?? 5,
      generations: batch.total_generations ?? 1,
      baseGenomeId: batch.base_genome_id ?? "random",
      botModel: batch.bot_model ?? "genetic",
      mutationStrength: numericOption(config.mutation_strength, 0.25),
      mutationRate: numericOption(config.mutation_rate, 0.15),
      randomImmigrantCount: numericOption(config.random_immigrant_count, 1),
      gamesPerGeneration: numericOption(config.games_per_generation, batch.games_per_generation ?? 5),
    });
  }

  list(): TrainingSessionsDTO { return presentTrainingSessions(this.store.runtimeSessions()); }
  status(sessionId: string): TrainingSession | undefined { return this.store.get(sessionId); }
  async handleGameEnded(gameId: string, sessionId: string): Promise<void> { await this.orchestrator.handleGameEnded(gameId, sessionId); }
  async reconcileStalled(staleAfterMilliseconds?: number, attemptStaleAfterMilliseconds?: number): Promise<void> {
    await this.orchestrator.reconcileStalled(staleAfterMilliseconds, attemptStaleAfterMilliseconds);
  }
}
