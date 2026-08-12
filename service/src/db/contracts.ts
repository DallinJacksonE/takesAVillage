import type { JsonValue } from "@takes-a-village/shared";

export type JsonObject = Record<string, JsonValue>;

export interface GameResultOptions {
  trainingBatchId?: string | null;
  trainingGeneration?: number | null;
  gameType?: "human" | "human_bot" | "training";
  tradeCount?: number | null;
  contestCount?: number | null;
  lieCount?: number | null;
}

export interface GameRecord {
  game_id: string;
  day_num: number;
  phase: string;
  data: JsonValue;
  created_at: Date;
  game_type?: string;
  training_batch_id?: string | null;
  training_generation?: number | null;
  trade_count?: number | null;
  contest_count?: number | null;
  lie_count?: number | null;
}

export interface GenomeRecord {
  id: number;
  name: string;
  shorthand_name: string;
  genome_data: JsonValue;
  created_at: Date;
}

export interface TrainingGameRecord {
  game_id: string;
  generation: number;
  attempt: number | null;
  status: "spawning" | "running" | "completed" | "failed" | "skipped";
  error_message: string | null;
  genome_count: number;
  best_fitness: number | null;
  average_fitness: number | null;
}

export interface TrainingBatchConfig {
  ruleset?: string;
  bot_model?: string;
  bot_count?: number;
  total_generations?: number;
  base_genome_id?: string | null;
  config?: JsonObject;
}

export interface TrainingBatchRecord {
  batch_id: string;
  status: string;
  ruleset?: string;
  bot_model?: string;
  bot_count?: number;
  total_generations?: number;
  base_genome_id?: string | null;
  current_generation: number;
  current_game_id: string | null;
  started_at: Date;
  completed_at: Date | null;
  last_heartbeat_at: Date;
  phase: string;
  last_error: string | null;
  final_champion_genome_id: string | null;
  config: JsonObject;
  generation_statistics: JsonObject[];
  games: TrainingGameRecord[];
  games_per_generation?: number;
  games_completed: number;
  games_failed: number;
}

export interface StoreVisualizationInput {
  scopeType: "game" | "training_batch";
  scopeId: string;
  name: string;
  title: string;
  mimeType: string;
  imageBytes: Buffer;
  metadata?: JsonObject;
}

export interface VisualizationRecord {
  id: string;
  scope_type: "game" | "training_batch";
  scope_id: string;
  name: string;
  title: string;
  mime_type: string;
  metadata: JsonObject;
  created_at: Date;
  url?: string;
  image_bytes?: Buffer;
}

export interface DatabaseProvider {
  initialize(): Promise<void>;
  close(): Promise<void>;
  createUser(userId: string, consentAgreed?: boolean): Promise<boolean>;
  userExists(userId: string): Promise<boolean>;
  storeGameSnapshot(gameId: string, dayNum: number, phase: string, snapshot: JsonValue): Promise<void>;
  storeGameResult(gameId: string, dayNum: number, phase: string, snapshot: JsonValue, options?: GameResultOptions): Promise<void>;
  getAllGameHistory(): Promise<GameRecord[]>;
  getAllGames(): Promise<GameRecord[]>;
  storePlayerSnapshot(gameId: string, dayNum: number, phase: string, player: JsonValue): Promise<void>;
  storeWorkSnapshot(snapshot: JsonValue): Promise<void>;
  storeTradeSnapshot(snapshot: JsonValue): Promise<void>;
  storeNightSnapshot(snapshot: JsonValue): Promise<void>;
  storeGenome(name: string, shorthand: string, genome: JsonValue): Promise<void>;
  getAllGenomes(): Promise<GenomeRecord[]>;
  createTrainingBatch(batchId: string, config: TrainingBatchConfig): Promise<boolean>;
  markTrainingBatchGameStarted(batchId: string, gameId: string, generation: number, attempt?: number | null): Promise<void>;
  markTrainingBatchGameRunning(batchId: string, gameId: string): Promise<void>;
  markTrainingBatchGameFailed(batchId: string, gameId: string, errorMessage: string): Promise<void>;
  markTrainingBatchGameCompleted(batchId: string, gameId: string, genomeCount: number, fitnessSummary?: JsonObject): Promise<void>;
  recordTrainingBatchHeartbeat(batchId: string, phase: string, currentGeneration: number, currentGameId?: string | null): Promise<void>;
  updateTrainingBatchStatus(batchId: string, status: string, errorMessage?: string | null): Promise<void>;
  appendTrainingBatchGenerationStats(batchId: string, stats: JsonObject): Promise<void>;
  completeTrainingBatch(batchId: string, finalChampionGenomeId?: string | null): Promise<void>;
  getTrainingBatches(): Promise<TrainingBatchRecord[]>;
  getTrainingBatch(batchId: string): Promise<TrainingBatchRecord | null>;
  getTrainingGames(batchId: string): Promise<TrainingGameRecord[]>;
  storeResearchVisualization(input: StoreVisualizationInput): Promise<string>;
  getResearchVisualizations(scopeType: string, scopeId: string): Promise<VisualizationRecord[]>;
  getResearchVisualization(visualizationId: string): Promise<VisualizationRecord | null>;
  deleteResearchVisualizations(scopeType: string, scopeId: string): Promise<void>;
}

export type UserDatabase = Pick<DatabaseProvider, "initialize" | "close" | "createUser" | "userExists">;
