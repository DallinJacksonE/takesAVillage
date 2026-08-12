import type { JsonValue } from "@takes-a-village/shared";

import type {
  DatabaseProvider,
  GameRecord,
  GameResultOptions,
  GenomeRecord,
  JsonObject,
  StoreVisualizationInput,
  TrainingBatchConfig,
  TrainingBatchRecord,
  TrainingGameRecord,
  VisualizationRecord,
} from "./contracts.js";

function clone<T>(value: T): T {
  return structuredClone(value);
}

export class MemoryDatabase implements DatabaseProvider {
  private readonly users = new Map<string, { consentAgreed: boolean; createdAt: Date }>();
  private readonly history: GameRecord[] = [];
  private readonly games: GameRecord[] = [];
  private readonly genomes: GenomeRecord[] = [];
  private readonly trainingBatches = new Map<string, TrainingBatchRecord>();
  private readonly visualizations = new Map<string, VisualizationRecord>();
  readonly playerSnapshots: JsonValue[] = [];
  readonly workSnapshots: JsonValue[] = [];
  readonly tradeSnapshots: JsonValue[] = [];
  readonly nightSnapshots: JsonValue[] = [];
  private nextVisualizationId = 1;

  async initialize(): Promise<void> {}
  async close(): Promise<void> {}

  async createUser(userId: string, consentAgreed = true): Promise<boolean> {
    this.users.set(userId, { consentAgreed, createdAt: new Date() });
    return true;
  }

  async userExists(userId: string): Promise<boolean> {
    return this.users.has(userId);
  }

  async storeGameSnapshot(gameId: string, dayNum: number, phase: string, snapshot: JsonValue): Promise<void> {
    this.history.push({ game_id: gameId, day_num: dayNum, phase, data: clone(snapshot), created_at: new Date() });
  }

  async storeGameResult(gameId: string, dayNum: number, phase: string, snapshot: JsonValue, options: GameResultOptions = {}): Promise<void> {
    const row: GameRecord = {
      game_id: gameId,
      day_num: dayNum,
      phase,
      data: clone(snapshot),
      created_at: new Date(),
      game_type: options.gameType ?? (options.trainingBatchId ? "training" : "human"),
      training_batch_id: options.trainingBatchId ?? null,
      training_generation: options.trainingGeneration ?? null,
      trade_count: options.tradeCount ?? null,
      contest_count: options.contestCount ?? null,
      lie_count: options.lieCount ?? null,
    };
    this.games.push(row);
    this.history.push(row);
  }

  async getAllGameHistory(): Promise<GameRecord[]> {
    return clone([...this.history].reverse());
  }

  async getAllGames(): Promise<GameRecord[]> {
    return clone([...this.games].reverse());
  }

  async storePlayerSnapshot(gameId: string, dayNum: number, phase: string, player: JsonValue): Promise<void> {
    this.playerSnapshots.push({ game_id: gameId, day_num: dayNum, phase, player } as JsonValue);
  }
  async storeWorkSnapshot(snapshot: JsonValue): Promise<void> { this.workSnapshots.push(clone(snapshot)); }
  async storeTradeSnapshot(snapshot: JsonValue): Promise<void> { this.tradeSnapshots.push(clone(snapshot)); }
  async storeNightSnapshot(snapshot: JsonValue): Promise<void> { this.nightSnapshots.push(clone(snapshot)); }

  async storeGenome(name: string, shorthand: string, genome: JsonValue): Promise<void> {
    this.genomes.push({ id: this.genomes.length + 1, name, shorthand_name: shorthand, genome_data: clone(genome), created_at: new Date() });
  }

  async getAllGenomes(): Promise<GenomeRecord[]> { return clone([...this.genomes].reverse()); }

  async createTrainingBatch(batchId: string, config: TrainingBatchConfig): Promise<boolean> {
    const now = new Date();
    const nestedConfig = clone(config.config ?? {});
    this.trainingBatches.set(batchId, {
      ...clone(config),
      batch_id: batchId,
      status: "running",
      current_generation: 0,
      current_game_id: null,
      started_at: now,
      completed_at: null,
      last_heartbeat_at: now,
      phase: "pending",
      last_error: null,
      final_champion_genome_id: null,
      config: nestedConfig,
      generation_statistics: [],
      games: [],
      games_per_generation: typeof nestedConfig.games_per_generation === "number" ? nestedConfig.games_per_generation : undefined,
      games_completed: 0,
      games_failed: 0,
    });
    return true;
  }

  private findBatch(batchId: string): TrainingBatchRecord | undefined { return this.trainingBatches.get(batchId); }

  async markTrainingBatchGameStarted(batchId: string, gameId: string, generation: number, attempt: number | null = null): Promise<void> {
    const batch = this.findBatch(batchId);
    if (!batch) return;
    batch.status = "running";
    batch.current_game_id = gameId;
    batch.current_generation = generation;
    batch.games.push({ game_id: gameId, generation, attempt, status: "spawning", error_message: null, genome_count: 0, best_fitness: null, average_fitness: null });
  }

  async markTrainingBatchGameRunning(batchId: string, gameId: string): Promise<void> {
    const game = this.findBatch(batchId)?.games.find((candidate) => candidate.game_id === gameId);
    if (game) game.status = "running";
  }

  async markTrainingBatchGameFailed(batchId: string, gameId: string, errorMessage: string): Promise<void> {
    const batch = this.findBatch(batchId);
    const game = batch?.games.find((candidate) => candidate.game_id === gameId);
    if (!batch || !game) return;
    game.status = "failed";
    game.error_message = errorMessage;
    this.updateGameCounts(batch);
  }

  async markTrainingBatchGameCompleted(batchId: string, gameId: string, genomeCount: number, fitnessSummary: JsonObject = {}): Promise<void> {
    const batch = this.findBatch(batchId);
    const game = batch?.games.find((candidate) => candidate.game_id === gameId);
    if (!batch || !game) return;
    game.status = "completed";
    game.error_message = null;
    game.genome_count = genomeCount;
    game.best_fitness = typeof fitnessSummary.best_fitness === "number" ? fitnessSummary.best_fitness : null;
    game.average_fitness = typeof fitnessSummary.average_fitness === "number" ? fitnessSummary.average_fitness : null;
    this.updateGameCounts(batch);
  }

  private updateGameCounts(batch: TrainingBatchRecord): void {
    batch.games_completed = batch.games.filter((game) => ["completed", "failed", "skipped"].includes(game.status)).length;
    batch.games_failed = batch.games.filter((game) => game.status === "failed").length;
  }

  async recordTrainingBatchHeartbeat(batchId: string, phase: string, currentGeneration: number, currentGameId: string | null = null): Promise<void> {
    const batch = this.findBatch(batchId);
    if (!batch) return;
    batch.last_heartbeat_at = new Date();
    batch.phase = phase;
    batch.current_generation = currentGeneration;
    batch.current_game_id = currentGameId;
  }

  async updateTrainingBatchStatus(batchId: string, status: string, errorMessage: string | null = null): Promise<void> {
    const batch = this.findBatch(batchId);
    if (!batch) return;
    batch.status = status;
    batch.last_error = errorMessage;
    if (["completed", "failed", "cancelled", "stalled"].includes(status)) batch.completed_at = new Date();
  }

  async appendTrainingBatchGenerationStats(batchId: string, stats: JsonObject): Promise<void> {
    this.findBatch(batchId)?.generation_statistics.push(clone(stats));
  }

  async completeTrainingBatch(batchId: string, finalChampionGenomeId: string | null = null): Promise<void> {
    const batch = this.findBatch(batchId);
    if (!batch) return;
    batch.status = "completed";
    batch.completed_at = new Date();
    batch.final_champion_genome_id = finalChampionGenomeId;
  }

  async getTrainingBatches(): Promise<TrainingBatchRecord[]> {
    return clone([...this.trainingBatches.values()].sort((a, b) => b.started_at.getTime() - a.started_at.getTime()));
  }
  async getTrainingBatch(batchId: string): Promise<TrainingBatchRecord | null> { return clone(this.findBatch(batchId) ?? null); }
  async getTrainingGames(batchId: string): Promise<TrainingGameRecord[]> { return clone(this.findBatch(batchId)?.games ?? []); }

  async storeResearchVisualization(input: StoreVisualizationInput): Promise<string> {
    const id = String(this.nextVisualizationId++);
    this.visualizations.set(id, {
      id,
      scope_type: input.scopeType,
      scope_id: input.scopeId,
      name: input.name,
      title: input.title,
      mime_type: input.mimeType,
      image_bytes: Buffer.from(input.imageBytes),
      metadata: clone(input.metadata ?? {}),
      created_at: new Date(),
    });
    return id;
  }

  async getResearchVisualizations(scopeType: string, scopeId: string): Promise<VisualizationRecord[]> {
    return [...this.visualizations.values()]
      .filter((item) => item.scope_type === scopeType && item.scope_id === scopeId)
      .sort((a, b) => a.created_at.getTime() - b.created_at.getTime())
      .map(({ image_bytes: _imageBytes, ...item }) => clone({ ...item, url: `/api/research/visualizations/${item.id}` }));
  }

  async getResearchVisualization(visualizationId: string): Promise<VisualizationRecord | null> {
    const item = this.visualizations.get(visualizationId);
    return item ? { ...clone(item), image_bytes: item.image_bytes ? Buffer.from(item.image_bytes) : undefined } : null;
  }

  async deleteResearchVisualizations(scopeType: string, scopeId: string): Promise<void> {
    for (const [id, item] of this.visualizations) {
      if (item.scope_type === scopeType && item.scope_id === scopeId) this.visualizations.delete(id);
    }
  }
}
