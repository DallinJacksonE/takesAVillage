import type { TrainingGenomeEntry, TrainingGenerationStatisticsDTO } from "@takes-a-village/shared";

import type { DatabaseProvider, JsonObject } from "../../db/contracts.js";
import type { CreateGameOptions } from "../../game-manager/lifecycle.js";
import type { TrainingBotClient } from "./bot-client.js";
import type { TrainingConfig } from "./config.js";
import { mutateGenomeForModel, normalizeGenomeForModel, randomGenomeForModel, type Genome, type RandomSource } from "./genomes.js";
import { buildGenerationStatistics, buildNextPopulation } from "./population.js";
import { presentTrainingSessions } from "./presenter.js";
import type { TrainingAttempt, TrainingSession } from "./session-store.js";

export interface TrainingUpdatePublisher {
  broadcast(sessions: ReturnType<typeof presentTrainingSessions>): void;
}

export interface TrainingOrchestratorOptions {
  database: DatabaseProvider;
  sessions: Map<string, TrainingSession>;
  createGame(hostId: string, ruleset: string, options: CreateGameOptions): string;
  botClient: TrainingBotClient;
  updateHub: TrainingUpdatePublisher;
  idFactory: () => string;
  random?: RandomSource;
  clock?: () => Date;
}

function jsonObject(genome: Genome): JsonObject { return genome; }
function numericFitness(entry: TrainingGenomeEntry): number { return Number(entry.fitness || 0); }

export class TrainingOrchestrator {
  private readonly random: RandomSource;
  private readonly clock: () => Date;
  private readonly locks = new Map<string, Promise<void>>();

  constructor(private readonly options: TrainingOrchestratorOptions) {
    this.random = options.random ?? Math.random;
    this.clock = options.clock ?? (() => new Date());
  }

  async start(config: Readonly<TrainingConfig>): Promise<string> {
    const sessionId = this.options.idFactory();
    const baseGenome = await this.loadBaseGenome(config.baseGenomeId);
    const population = this.initialPopulation(config, baseGenome);
    const session: TrainingSession = {
      ruleset: config.ruleset,
      botCount: config.botCount,
      generationsLeft: config.generations,
      population,
      generation: 1,
      eliteCount: 2,
      selectionSize: Math.min(3, config.botCount),
      mutationStrength: config.mutationStrength,
      mutationRate: config.mutationRate,
      randomImmigrantCount: config.randomImmigrantCount,
      generationStatistics: [],
      botModel: config.botModel,
      gamesPerGeneration: config.gamesPerGeneration,
      gamesCompleted: 0,
      gamesFailed: 0,
      currentGenerationGameIndex: 0,
      fitnessEntries: [],
      games: [],
      allFitnessEntries: [],
      processedGameIds: new Set(),
      processingGameIds: new Set(),
      generationAttempts: new Map(),
      generationTerminalGameIds: new Set(),
      generationScheduled: false,
    };

    await this.options.database.createTrainingBatch(sessionId, {
      ruleset: config.ruleset,
      bot_model: config.botModel,
      bot_count: config.botCount,
      total_generations: config.generations,
      base_genome_id: config.baseGenomeId,
      config: {
        mutation_strength: config.mutationStrength,
        mutation_rate: config.mutationRate,
        random_immigrant_count: config.randomImmigrantCount,
        elite_count: session.eliteCount,
        selection_size: session.selectionSize,
        games_per_generation: session.gamesPerGeneration,
      },
    });
    this.options.sessions.set(sessionId, session);
    await this.heartbeat(sessionId, "starting");
    this.broadcast();
    await this.startGenerationGames(sessionId);
    return sessionId;
  }

  async cancel(sessionId: string, reason: string): Promise<boolean> {
    const existed = await this.withLock(sessionId, () => this.options.sessions.delete(sessionId));
    await this.options.database.updateTrainingBatchStatus(sessionId, "cancelled", reason);
    this.broadcast();
    return existed;
  }

  async handleGameEnded(gameId: string, sessionId: string): Promise<void> {
    const claimed = await this.withLock(sessionId, () => {
      const session = this.options.sessions.get(sessionId);
      if (!session || session.processedGameIds.has(gameId) || session.processingGameIds?.has(gameId)) return false;
      (session.processingGameIds ??= new Set()).add(gameId);
      return true;
    });
    if (!claimed) return;
    await this.heartbeat(sessionId, "collecting_genomes");
    const result = await this.options.botClient.fetchGameGenomes(gameId);
    const entries = result.ok ? result.entries ?? [] : [];
    await this.recordTerminalAttempt(sessionId, gameId, entries, entries.length ? undefined : result.errorMessage ?? "No genome entries returned");
  }

  async reconcileStalled(staleAfterMilliseconds = 600_000, attemptStaleAfterMilliseconds = staleAfterMilliseconds): Promise<void> {
    const now = this.clock().getTime();
    for (const batch of await this.options.database.getTrainingBatches()) {
      if (batch.status !== "running" || this.options.sessions.has(batch.batch_id)) continue;
      const lastSeen = batch.last_heartbeat_at ?? batch.started_at;
      if (lastSeen && now - new Date(lastSeen).getTime() <= staleAfterMilliseconds) continue;
      await this.options.database.updateTrainingBatchStatus(
        batch.batch_id,
        "stalled",
        "Training batch is running in persistence but not active in orchestrator memory.",
      );
    }

    for (const [sessionId, session] of [...this.options.sessions]) {
      for (const [gameId, attempt] of [...session.generationAttempts]) {
        if (!(["spawning", "running"] as const).includes(attempt.status as "spawning" | "running")) continue;
        if (now - attempt.updatedAt.getTime() <= attemptStaleAfterMilliseconds) continue;
        await this.recordTerminalAttempt(sessionId, gameId, [], `Training game attempt is stale in ${attempt.status} state.`);
      }
    }
  }

  private async loadBaseGenome(baseGenomeId: string): Promise<Record<string, unknown> | null> {
    if (baseGenomeId === "random") return null;
    const match = (await this.options.database.getAllGenomes()).find((genome) => genome.name === baseGenomeId || genome.shorthand_name === baseGenomeId);
    return match?.genome_data && typeof match.genome_data === "object" && !Array.isArray(match.genome_data)
      ? match.genome_data as Record<string, unknown>
      : null;
  }

  private initialPopulation(config: Readonly<TrainingConfig>, baseGenome: Record<string, unknown> | null): JsonObject[] {
    if (!baseGenome) return Array.from({ length: config.botCount }, () => jsonObject(randomGenomeForModel(config.botModel, this.random)));
    const normalized = normalizeGenomeForModel(config.botModel, baseGenome);
    return [jsonObject(normalized), ...Array.from({ length: Math.max(0, config.botCount - 1) }, () => jsonObject(mutateGenomeForModel(config.botModel, normalized, { random: this.random })) )];
  }

  private async startGenerationGames(sessionId: string): Promise<void> {
    const attempts = await this.withLock(sessionId, async () => {
      const session = this.options.sessions.get(sessionId);
      if (!session || session.generationScheduled) return [];
      session.generationScheduled = true;
      session.generationAttempts = new Map();
      session.generationTerminalGameIds = new Set();
      const prepared: Array<{ gameId: string; attempt: number }> = [];
      for (let attempt = 1; attempt <= session.gamesPerGeneration; attempt += 1) {
        const gameId = this.options.createGame("TRAINING_ORCHESTRATOR", session.ruleset, {
          botCount: session.botCount,
          training: true,
          trainingSessionId: sessionId,
          trainingGeneration: session.generation,
        });
        session.currentGameId = gameId;
        session.currentGenerationGameIndex = attempt;
        session.games.push(gameId);
        session.generationAttempts.set(gameId, { attempt, status: "spawning", updatedAt: this.clock() });
        await this.options.database.markTrainingBatchGameStarted(sessionId, gameId, session.generation, attempt);
        prepared.push({ gameId, attempt });
      }
      return prepared;
    });
    if (!attempts.length) return;
    await this.heartbeat(sessionId, "spawning");
    this.broadcast();
    await Promise.all(attempts.map(({ gameId, attempt }) => this.spawnAttempt(sessionId, gameId, attempt)));
  }

  private async spawnAttempt(sessionId: string, gameId: string, attempt: number): Promise<void> {
    const session = this.options.sessions.get(sessionId);
    if (!session) return;
    const result = await this.options.botClient.spawnBots({
      gameId,
      botCount: session.botCount,
      baseGenome: session.population,
      botModel: session.botModel,
      trainingAttemptIndex: attempt,
    });
    if (!result.ok) {
      await this.recordTerminalAttempt(sessionId, gameId, [], `Bot service spawn failed: ${result.errorMessage ?? "unknown error"}`);
      return;
    }
    await this.withLock(sessionId, async () => {
      const current = this.options.sessions.get(sessionId);
      const trainingAttempt = current?.generationAttempts.get(gameId);
      if (!current || !trainingAttempt || current.processedGameIds.has(gameId)) return;
      trainingAttempt.status = "running";
      trainingAttempt.updatedAt = this.clock();
      await this.options.database.markTrainingBatchGameRunning(sessionId, gameId);
    });
    await this.heartbeat(sessionId, "running");
  }

  private async recordTerminalAttempt(sessionId: string, gameId: string, entries: TrainingGenomeEntry[], errorMessage?: string): Promise<void> {
    let startNextGeneration = false;
    await this.withLock(sessionId, async () => {
      const session = this.options.sessions.get(sessionId);
      if (!session || session.processedGameIds.has(gameId)) return;
      session.processingGameIds?.delete(gameId);
      session.processedGameIds.add(gameId);
      session.generationTerminalGameIds.add(gameId);
      const attempt = session.generationAttempts.get(gameId);
      if (attempt) {
        attempt.status = entries.length ? "completed" : "failed";
        attempt.updatedAt = this.clock();
      }
      if (entries.length) {
        session.fitnessEntries.push(...entries);
        session.allFitnessEntries.push(...entries);
        const fitnesses = entries.map(numericFitness);
        await this.options.database.markTrainingBatchGameCompleted(sessionId, gameId, entries.length, {
          best_fitness: Math.max(...fitnesses),
          average_fitness: fitnesses.reduce((sum, value) => sum + value, 0) / fitnesses.length,
        });
      } else {
        session.gamesFailed += 1;
        await this.options.database.markTrainingBatchGameFailed(sessionId, gameId, errorMessage ?? "No genome entries returned");
      }
      session.gamesCompleted = session.generationTerminalGameIds.size;
      if (session.gamesCompleted >= session.gamesPerGeneration) startNextGeneration = await this.completeGeneration(sessionId, session);
      else this.broadcast();
    });
    if (startNextGeneration) await this.startGenerationGames(sessionId);
  }

  private async completeGeneration(sessionId: string, session: TrainingSession): Promise<boolean> {
    await this.heartbeat(sessionId, "aggregating_generation");
    const combined = new Map<string, TrainingGenomeEntry & { games: number }>();
    for (const entry of session.fitnessEntries) {
      const key = JSON.stringify(Object.fromEntries(Object.entries(entry.genome).sort(([a], [b]) => a.localeCompare(b))));
      const existing = combined.get(key);
      if (existing) {
        existing.fitness += entry.fitness;
        existing.games += 1;
      } else combined.set(key, { ...structuredClone(entry), fitness: entry.fitness, games: 1 });
    }
    const sorted = [...combined.values()].map(({ games, ...entry }) => ({ ...entry, fitness: entry.fitness / games })).sort((a, b) => b.fitness - a.fitness);
    let bestGenome: Genome | undefined;
    if (sorted.length) {
      bestGenome = normalizeGenomeForModel(session.botModel, sorted[0]!.genome);
      const statistics = buildGenerationStatistics(sorted);
      const generationStatistics: TrainingGenerationStatisticsDTO = { ...statistics, generation: session.generation };
      session.generationStatistics.push(generationStatistics);
      await this.options.database.appendTrainingBatchGenerationStats(sessionId, generationStatistics as JsonObject);
      const slots = session.botCount - session.randomImmigrantCount - 2;
      const crossoverChildren = Math.floor(slots / 2);
      session.population = buildNextPopulation(session.botModel, sorted, session.botCount, {
        eliteCount: session.eliteCount,
        selectionSize: session.selectionSize,
        mutationStrength: session.mutationStrength,
        mutationRate: session.mutationRate,
        randomImmigrantCount: session.randomImmigrantCount,
        crossoverChildCount: crossoverChildren,
        mutationChildCount: slots - crossoverChildren,
        random: this.random,
      });
      session.fitnessEntries = [];
      session.baseGenome = bestGenome;
    }
    session.gamesCompleted = 0;
    session.gamesFailed = 0;
    session.currentGenerationGameIndex = 0;
    session.processedGameIds = new Set();
    session.processingGameIds = new Set();
    session.generationTerminalGameIds = new Set();
    session.generationAttempts = new Map();
    session.generationScheduled = false;
    session.generationsLeft -= 1;
    this.broadcast();
    if (session.generationsLeft > 0) {
      session.generation += 1;
      return true;
    }

    const genome = bestGenome ?? session.population[0];
    let champion: string | null = null;
    if (genome) {
      champion = `genome_gen_${sessionId.slice(0, 6)}`;
      await this.options.database.storeGenome(champion, `G${this.options.idFactory().slice(0, 3).toUpperCase()}`, genome);
    }
    await this.options.database.completeTrainingBatch(sessionId, champion);
    this.options.sessions.delete(sessionId);
    this.broadcast();
    return false;
  }

  private async heartbeat(sessionId: string, phase: string): Promise<void> {
    const session = this.options.sessions.get(sessionId);
    if (!session) return;
    await this.options.database.recordTrainingBatchHeartbeat(sessionId, phase, session.generation, session.currentGameId ?? null);
  }

  private broadcast(): void { this.options.updateHub.broadcast(presentTrainingSessions(this.options.sessions)); }

  private async withLock<T>(sessionId: string, action: () => T | Promise<T>): Promise<T> {
    const previous = this.locks.get(sessionId) ?? Promise.resolve();
    let release!: () => void;
    const current = new Promise<void>((resolve) => { release = resolve; });
    this.locks.set(sessionId, current);
    await previous;
    try { return await action(); }
    finally {
      release();
      if (this.locks.get(sessionId) === current) this.locks.delete(sessionId);
    }
  }
}
