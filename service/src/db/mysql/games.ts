import type { JsonValue } from "@takes-a-village/shared";

import type { GameRecord, GameResultOptions } from "../contracts.js";
import { decodeJson, rows, type SqlExecutor } from "./sql.js";

function decodeGame(row: Record<string, unknown>): GameRecord {
  return { ...row, data: decodeJson(row.data) } as GameRecord;
}

export class GamesRepository {
  constructor(private readonly database: SqlExecutor) {}

  async storeGameSnapshot(gameId: string, dayNum: number, phase: string, snapshot: JsonValue): Promise<void> {
    await this.database.execute(
      "INSERT INTO game_history (game_id, day_num, phase, data) VALUES (?, ?, ?, ?)",
      [gameId, dayNum, phase, JSON.stringify(snapshot)],
    );
  }

  async storeGameResult(gameId: string, dayNum: number, phase: string, snapshot: JsonValue, options: GameResultOptions = {}): Promise<void> {
    await this.database.execute(
      `INSERT INTO games
       (game_id, day_num, phase, data, game_type, training_batch_id, training_generation, trade_count, contest_count, lie_count)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        gameId,
        dayNum,
        phase,
        JSON.stringify(snapshot),
        options.gameType ?? (options.trainingBatchId ? "training" : "human"),
        options.trainingBatchId ?? null,
        options.trainingGeneration ?? null,
        options.tradeCount ?? null,
        options.contestCount ?? null,
        options.lieCount ?? null,
      ],
    );
  }

  async getAllGameHistory(): Promise<GameRecord[]> {
    const [result] = await this.database.execute(
      "SELECT game_id, day_num, phase, data, created_at FROM game_history ORDER BY created_at DESC",
    );
    return rows(result).map(decodeGame);
  }

  async getAllGames(): Promise<GameRecord[]> {
    const [result] = await this.database.execute("SELECT * FROM games ORDER BY created_at DESC LIMIT 10");
    return rows(result).map(decodeGame);
  }

  async storePlayerSnapshot(gameId: string, dayNum: number, phase: string, player: JsonValue): Promise<void> {
    const value = player as Record<string, unknown>;
    const resources = value.resources as Record<string, unknown> | undefined;
    await this.database.execute(
      `INSERT INTO player_snapshots
       (game_id, day_num, phase, player_id, name, health, sickness_chance, resources, fire_status, fire_guests, developments, actions, committed_action, available_work, finished_phase, timeline, trade_history)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [gameId, dayNum, phase, value.session_id ?? value.id, value.name, value.health, value.sickness_chance,
        JSON.stringify(resources ?? {}), value.fire_status, JSON.stringify(value.fire_guests ?? []),
        JSON.stringify(value.developments ?? []), JSON.stringify(value.actions ?? []),
        value.committed_action == null ? null : JSON.stringify(value.committed_action),
        JSON.stringify(value.available_work ?? []), value.finished_phase ?? false,
        JSON.stringify(value.timeline ?? []), JSON.stringify(value.trade_history ?? [])],
    );
  }

  async storeWorkSnapshot(snapshot: JsonValue): Promise<void> {
    const value = snapshot as Record<string, unknown>;
    await this.database.execute(
      `INSERT INTO work_phase_snapshots
       (game_id, player_id, day_num, health, sickness_chance, wood, food, iron, available_work, committed_action)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [value.game_id, value.player_id, value.day_num, value.health, value.sickness_chance, value.wood, value.food, value.iron,
        JSON.stringify(value.available_work ?? []), value.committed_action == null ? null : JSON.stringify(value.committed_action)],
    );
  }

  async storeTradeSnapshot(snapshot: JsonValue): Promise<void> {
    const value = snapshot as Record<string, unknown>;
    await this.database.execute(
      `INSERT INTO trade_phase_snapshots
       (game_id, player_id, day_num, health, sickness_chance, wood, food, iron, trade_history)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [value.game_id, value.player_id, value.day_num, value.health, value.sickness_chance, value.wood, value.food, value.iron, JSON.stringify(value.trade_history ?? [])],
    );
  }

  async storeNightSnapshot(snapshot: JsonValue): Promise<void> {
    const value = snapshot as Record<string, unknown>;
    await this.database.execute(
      `INSERT INTO night_phase_snapshots
       (game_id, player_id, day_num, health, sickness_chance, wood, food, iron, fire_status, fire_guests)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [value.game_id, value.player_id, value.day_num, value.health, value.sickness_chance, value.wood, value.food, value.iron, value.fire_status, JSON.stringify(value.fire_guests ?? [])],
    );
  }
}
