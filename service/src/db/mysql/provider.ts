import type { JsonValue, ServiceConfig } from "@takes-a-village/shared";

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
} from "../contracts.js";
import { createMySqlPool, type ClosableSqlExecutor } from "./connection.js";
import { GamesRepository } from "./games.js";
import { GenomesRepository } from "./genomes.js";
import { initializeSchema } from "./schema.js";
import { TrainingRepository } from "./training.js";
import { UsersRepository } from "./users.js";
import { VisualizationsRepository } from "./visualizations.js";

export class MySqlDatabase implements DatabaseProvider {
  private readonly users: UsersRepository;
  private readonly games: GamesRepository;
  private readonly genomes: GenomesRepository;
  private readonly training: TrainingRepository;
  private readonly visualizations: VisualizationsRepository;

  constructor(config: ServiceConfig["database"], private readonly database: ClosableSqlExecutor = createMySqlPool(config)) {
    this.users = new UsersRepository(database);
    this.games = new GamesRepository(database);
    this.genomes = new GenomesRepository(database);
    this.training = new TrainingRepository(database);
    this.visualizations = new VisualizationsRepository(database);
  }

  async initialize(): Promise<void> { await initializeSchema(this.database); }
  async close(): Promise<void> { await this.database.end?.(); }

  async createUser(userId: string, consentAgreed = true): Promise<boolean> { return this.users.createUser(userId, consentAgreed); }
  async userExists(userId: string): Promise<boolean> { return this.users.userExists(userId); }

  async storeGameSnapshot(gameId: string, dayNum: number, phase: string, snapshot: JsonValue): Promise<void> {
    await this.games.storeGameSnapshot(gameId, dayNum, phase, snapshot);
  }
  async storeGameResult(gameId: string, dayNum: number, phase: string, snapshot: JsonValue, options: GameResultOptions = {}): Promise<void> {
    await this.games.storeGameResult(gameId, dayNum, phase, snapshot, options);
  }
  async getAllGameHistory(): Promise<GameRecord[]> { return this.games.getAllGameHistory(); }
  async getAllGames(): Promise<GameRecord[]> { return this.games.getAllGames(); }
  async storePlayerSnapshot(gameId: string, dayNum: number, phase: string, player: JsonValue): Promise<void> {
    await this.games.storePlayerSnapshot(gameId, dayNum, phase, player);
  }
  async storeWorkSnapshot(snapshot: JsonValue): Promise<void> { await this.games.storeWorkSnapshot(snapshot); }
  async storeTradeSnapshot(snapshot: JsonValue): Promise<void> { await this.games.storeTradeSnapshot(snapshot); }
  async storeNightSnapshot(snapshot: JsonValue): Promise<void> { await this.games.storeNightSnapshot(snapshot); }

  async storeGenome(name: string, shorthand: string, genome: JsonValue): Promise<void> { await this.genomes.storeGenome(name, shorthand, genome); }
  async getAllGenomes(): Promise<GenomeRecord[]> { return this.genomes.getAllGenomes(); }

  async createTrainingBatch(batchId: string, config: TrainingBatchConfig): Promise<boolean> { return this.training.createTrainingBatch(batchId, config); }
  async markTrainingBatchGameStarted(batchId: string, gameId: string, generation: number, attempt: number | null = null): Promise<void> {
    await this.training.markTrainingBatchGameStarted(batchId, gameId, generation, attempt);
  }
  async markTrainingBatchGameRunning(batchId: string, gameId: string): Promise<void> { await this.training.markTrainingBatchGameRunning(batchId, gameId); }
  async markTrainingBatchGameFailed(batchId: string, gameId: string, errorMessage: string): Promise<void> {
    await this.training.markTrainingBatchGameFailed(batchId, gameId, errorMessage);
  }
  async markTrainingBatchGameCompleted(batchId: string, gameId: string, genomeCount: number, fitnessSummary: JsonObject = {}): Promise<void> {
    await this.training.markTrainingBatchGameCompleted(batchId, gameId, genomeCount, fitnessSummary);
  }
  async recordTrainingBatchHeartbeat(batchId: string, phase: string, currentGeneration: number, currentGameId: string | null = null): Promise<void> {
    await this.training.recordTrainingBatchHeartbeat(batchId, phase, currentGeneration, currentGameId);
  }
  async updateTrainingBatchStatus(batchId: string, status: string, errorMessage: string | null = null): Promise<void> {
    await this.training.updateTrainingBatchStatus(batchId, status, errorMessage);
  }
  async appendTrainingBatchGenerationStats(batchId: string, stats: JsonObject): Promise<void> {
    await this.training.appendTrainingBatchGenerationStats(batchId, stats);
  }
  async completeTrainingBatch(batchId: string, finalChampionGenomeId: string | null = null): Promise<void> {
    await this.training.completeTrainingBatch(batchId, finalChampionGenomeId);
  }
  async getTrainingBatches(): Promise<TrainingBatchRecord[]> { return this.training.getTrainingBatches(); }
  async getTrainingBatch(batchId: string): Promise<TrainingBatchRecord | null> { return this.training.getTrainingBatch(batchId); }
  async getTrainingGames(batchId: string): Promise<TrainingGameRecord[]> { return this.training.getTrainingGames(batchId); }

  async storeResearchVisualization(input: StoreVisualizationInput): Promise<string> {
    return this.visualizations.storeResearchVisualization(input);
  }
  async getResearchVisualizations(scopeType: string, scopeId: string): Promise<VisualizationRecord[]> {
    return this.visualizations.getResearchVisualizations(scopeType, scopeId);
  }
  async getResearchVisualization(visualizationId: string): Promise<VisualizationRecord | null> {
    return this.visualizations.getResearchVisualization(visualizationId);
  }
  async deleteResearchVisualizations(scopeType: string, scopeId: string): Promise<void> {
    await this.visualizations.deleteResearchVisualizations(scopeType, scopeId);
  }
}
