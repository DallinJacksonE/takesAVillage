import type {
  JsonObject,
  TrainingBatchConfig,
  TrainingBatchRecord,
  TrainingGameRecord,
} from "../contracts.js";
import { decodeJson, rows, type SqlExecutor, type TransactionalSqlExecutor } from "./sql.js";

function decodeBatch(row: Record<string, unknown>): TrainingBatchRecord {
  const config = (decodeJson(row.config) ?? {}) as JsonObject;
  const generationStatistics = (decodeJson(row.generation_statistics) ?? []) as JsonObject[];
  const games = (decodeJson(row.games) ?? []) as TrainingGameRecord[];
  return {
    ...row,
    config,
    generation_statistics: generationStatistics,
    games,
    games_per_generation: typeof config.games_per_generation === "number" ? config.games_per_generation : undefined,
    games_completed: games.filter((game) => ["completed", "failed", "skipped"].includes(game.status)).length,
    games_failed: games.filter((game) => game.status === "failed").length,
  } as TrainingBatchRecord;
}

export class TrainingRepository {
  constructor(private readonly database: TransactionalSqlExecutor) {}

  async createTrainingBatch(batchId: string, config: TrainingBatchConfig): Promise<boolean> {
    await this.database.execute(
      `INSERT INTO training_batches
       (batch_id, status, ruleset, bot_model, bot_count, total_generations, current_generation, last_heartbeat_at, phase, base_genome_id, config, generation_statistics, games)
       VALUES (?, 'running', ?, ?, ?, ?, 0, NOW(), 'pending', ?, ?, ?, ?)`,
      [batchId, config.ruleset ?? null, config.bot_model ?? null, config.bot_count ?? null,
        config.total_generations ?? null, config.base_genome_id ?? null, JSON.stringify(config.config ?? {}), "[]", "[]"],
    );
    return true;
  }

  private async mutateGames(
    batchId: string,
    mutate: (games: TrainingGameRecord[]) => void,
    current?: { gameId: string; generation: number },
  ): Promise<void> {
    const connection = await this.database.getConnection?.();
    const executor = connection ?? this.database;
    try {
      await connection?.beginTransaction();
      const batch = await this.loadTrainingBatch(executor, batchId, true);
      if (!batch) {
        await connection?.rollback();
        return;
      }
      mutate(batch.games);
      if (current) {
        await executor.execute(
          "UPDATE training_batches SET games = ?, status = 'running', current_game_id = ?, current_generation = ? WHERE batch_id = ?",
          [JSON.stringify(batch.games), current.gameId, current.generation, batchId],
        );
      } else {
        await executor.execute("UPDATE training_batches SET games = ? WHERE batch_id = ?", [JSON.stringify(batch.games), batchId]);
      }
      await connection?.commit();
    } catch (error) {
      await connection?.rollback();
      throw error;
    } finally {
      connection?.release();
    }
  }

  async markTrainingBatchGameStarted(batchId: string, gameId: string, generation: number, attempt: number | null = null): Promise<void> {
    await this.mutateGames(batchId, (games) => games.push({
      game_id: gameId,
      generation,
      attempt,
      status: "spawning",
      error_message: null,
      genome_count: 0,
      best_fitness: null,
      average_fitness: null,
    }), { gameId, generation });
  }

  async markTrainingBatchGameRunning(batchId: string, gameId: string): Promise<void> {
    await this.mutateGames(batchId, (games) => {
      const game = games.find((candidate) => candidate.game_id === gameId);
      if (game) game.status = "running";
    });
  }

  async markTrainingBatchGameFailed(batchId: string, gameId: string, errorMessage: string): Promise<void> {
    await this.mutateGames(batchId, (games) => {
      const game = games.find((candidate) => candidate.game_id === gameId);
      if (game) {
        game.status = "failed";
        game.error_message = errorMessage;
      }
    });
  }

  async markTrainingBatchGameCompleted(batchId: string, gameId: string, genomeCount: number, fitnessSummary: JsonObject = {}): Promise<void> {
    await this.mutateGames(batchId, (games) => {
      const game = games.find((candidate) => candidate.game_id === gameId);
      if (game) {
        game.status = "completed";
        game.error_message = null;
        game.genome_count = genomeCount;
        game.best_fitness = typeof fitnessSummary.best_fitness === "number" ? fitnessSummary.best_fitness : null;
        game.average_fitness = typeof fitnessSummary.average_fitness === "number" ? fitnessSummary.average_fitness : null;
      }
    });
  }

  async recordTrainingBatchHeartbeat(batchId: string, phase: string, currentGeneration: number, currentGameId: string | null = null): Promise<void> {
    await this.database.execute(
      "UPDATE training_batches SET last_heartbeat_at = NOW(), phase = ?, current_generation = ?, current_game_id = ? WHERE batch_id = ?",
      [phase, currentGeneration, currentGameId, batchId],
    );
  }

  async updateTrainingBatchStatus(batchId: string, status: string, errorMessage: string | null = null): Promise<void> {
    const terminal = ["completed", "failed", "cancelled", "stalled"].includes(status);
    await this.database.execute(
      `UPDATE training_batches SET status = ?, last_error = ?${terminal ? ", completed_at = NOW()" : ""} WHERE batch_id = ?`,
      [status, errorMessage, batchId],
    );
  }

  async appendTrainingBatchGenerationStats(batchId: string, stats: JsonObject): Promise<void> {
    const batch = await this.getTrainingBatch(batchId);
    if (!batch) return;
    batch.generation_statistics.push(stats);
    await this.database.execute(
      "UPDATE training_batches SET generation_statistics = ? WHERE batch_id = ?",
      [JSON.stringify(batch.generation_statistics), batchId],
    );
  }

  async completeTrainingBatch(batchId: string, finalChampionGenomeId: string | null = null): Promise<void> {
    await this.database.execute(
      "UPDATE training_batches SET status = 'completed', completed_at = NOW(), final_champion_genome_id = ? WHERE batch_id = ?",
      [finalChampionGenomeId, batchId],
    );
  }

  async getTrainingBatches(): Promise<TrainingBatchRecord[]> {
    const [result] = await this.database.execute("SELECT * FROM training_batches ORDER BY started_at DESC");
    return rows(result).map(decodeBatch);
  }

  async getTrainingBatch(batchId: string, forUpdate = false): Promise<TrainingBatchRecord | null> {
    return this.loadTrainingBatch(this.database, batchId, forUpdate);
  }

  private async loadTrainingBatch(executor: SqlExecutor, batchId: string, forUpdate = false): Promise<TrainingBatchRecord | null> {
    const [result] = await executor.execute(
      `SELECT * FROM training_batches WHERE batch_id = ? LIMIT 1${forUpdate ? " FOR UPDATE" : ""}`,
      [batchId],
    );
    const row = rows(result)[0];
    return row ? decodeBatch(row) : null;
  }

  async getTrainingGames(batchId: string): Promise<TrainingGameRecord[]> {
    return (await this.getTrainingBatch(batchId))?.games ?? [];
  }
}
