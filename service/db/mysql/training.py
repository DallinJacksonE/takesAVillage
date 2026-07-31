import io
import json
import time

import mysql.connector


from service.logging import BackendLogger

db_logger = BackendLogger("db")


class TrainingRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_connection(self):
        return self.connection.get_connection()

    def _mutate_training_games(self, batch_id: str, mutate,
                               *, current_game_id=None,
                               current_generation=None) -> bool:
        """Serialize read-modify-write updates to the batch games JSON array."""
        conn = self.get_connection()
        if not conn:
            return False
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT games FROM training_batches "
                "WHERE batch_id = %s FOR UPDATE",
                (batch_id,),
            )
            row = cursor.fetchone()
            if not row:
                conn.rollback()
                return False
            games = row.get("games", []) or []
            if isinstance(games, str):
                games = json.loads(games)
            mutate(games)

            clauses = ["games = %s"]
            params: list[object] = [json.dumps(games)]
            if current_game_id is not None:
                clauses.extend([
                    "status = 'running'",
                    "current_game_id = %s",
                    "current_generation = %s",
                ])
                params.extend([current_game_id, current_generation])
            params.append(batch_id)
            cursor.execute(
                f"UPDATE training_batches SET {', '.join(clauses)} "
                "WHERE batch_id = %s",
                tuple(params),
            )
            conn.commit()
            return True
        except (mysql.connector.Error, json.JSONDecodeError) as err:
            conn.rollback()
            db_logger.error(f"Error updating training batch games: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    def create_training_batch(self, batch_id: str, config: dict) -> bool:
        conn = self.get_connection()
        if not conn:
            raise ConnectionError("Could not connect to MySQL")
        cursor = conn.cursor()
        query = """
            INSERT INTO training_batches
            (batch_id, status, ruleset, bot_model, bot_count, total_generations,
             current_generation, last_heartbeat_at, phase, base_genome_id,
             config, generation_statistics, games)
            VALUES (%s, 'running', %s, %s, %s, %s, 0, NOW(), 'pending', %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                batch_id, config.get("ruleset"), config.get("bot_model"),
                config.get("bot_count"), config.get("total_generations"),
                config.get("base_genome_id"), json.dumps(config.get("config", {})),
                json.dumps([]), json.dumps([])))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            conn.rollback()
            db_logger.error(f"Error creating training batch: {err}")
            raise
        finally:
            cursor.close()
            conn.close()

    def mark_training_batch_game_started(self, batch_id: str, game_id: str,
                                         generation: int,
                                         attempt: int | None = None):
        def append_game(games):
            games.append({
                "game_id": game_id,
                "generation": generation,
                "attempt": attempt,
                "status": "spawning",
                "error_message": None,
                "genome_count": 0,
                "best_fitness": None,
                "average_fitness": None,
            })

        return self._mutate_training_games(
            batch_id, append_game,
            current_game_id=game_id,
            current_generation=generation,
        )

    def mark_training_batch_game_running(self, batch_id: str, game_id: str):
        def mark_running(games):
            for game in games:
                if game.get("game_id") == game_id:
                    game["status"] = "running"
                    break

        return self._mutate_training_games(batch_id, mark_running)

    def mark_training_batch_game_failed(self, batch_id: str, game_id: str,
                                        error_message: str):
        def mark_failed(games):
            for game in games:
                if game.get("game_id") == game_id:
                    game["status"] = "failed"
                    game["error_message"] = error_message
                    game["genome_count"] = int(
                        game.get("genome_count", 0) or 0)
                    break

        return self._mutate_training_games(batch_id, mark_failed)

    def mark_training_batch_game_completed(self, batch_id: str, game_id: str,
                                           genome_count: int,
                                           fitness_summary: dict | None = None):
        summary = fitness_summary or {}

        def mark_completed(games):
            for game in games:
                if game.get("game_id") == game_id:
                    game["status"] = "completed"
                    game["error_message"] = None
                    game["genome_count"] = int(genome_count or 0)
                    game["best_fitness"] = summary.get("best_fitness")
                    game["average_fitness"] = summary.get("average_fitness")
                    break

        return self._mutate_training_games(batch_id, mark_completed)

    def record_training_batch_heartbeat(self, batch_id: str, phase: str,
                                        current_generation: int,
                                        current_game_id: str | None = None):
        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE training_batches
                SET last_heartbeat_at = NOW(), phase = %s,
                    current_generation = %s, current_game_id = %s
                WHERE batch_id = %s
                """,
                (phase, current_generation, current_game_id, batch_id),
            )
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error recording training batch heartbeat: {err}")
        finally:
            cursor.close()
            conn.close()

    def update_training_batch_status(self, batch_id: str, status: str,
                                     error_message: str | None = None):
        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        completed_clause = (
            ", completed_at = NOW()"
            if status in ("completed", "failed", "cancelled", "stalled")
            else ""
        )
        try:
            cursor.execute(
                f"""
                UPDATE training_batches
                SET status = %s, last_error = %s{completed_clause}
                WHERE batch_id = %s
                """,
                (status, error_message, batch_id),
            )
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error updating training batch status: {err}")
        finally:
            cursor.close()
            conn.close()

    def append_training_batch_generation_stats(self, batch_id: str, stats: dict):
        batch = self.get_training_batch(batch_id)
        if not batch:
            return
        generation_statistics = batch.get("generation_statistics", [])
        generation_statistics.append(stats)
        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE training_batches SET generation_statistics = %s WHERE batch_id = %s",
                (json.dumps(generation_statistics), batch_id))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error appending training batch stats: {err}")
        finally:
            cursor.close()
            conn.close()

    def complete_training_batch(self, batch_id: str,
                                final_champion_genome_id: str | None = None):
        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        query = """
            UPDATE training_batches
            SET status = 'completed', completed_at = NOW(),
                final_champion_genome_id = %s
            WHERE batch_id = %s
        """
        try:
            cursor.execute(query, (final_champion_genome_id, batch_id))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error completing training batch: {err}")
        finally:
            cursor.close()
            conn.close()

    def get_training_batches(self) -> list:
        conn = self.get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM training_batches ORDER BY started_at DESC")
            return [self._decode_training_batch(row) for row in cursor.fetchall()]
        except mysql.connector.Error as err:
            db_logger.error(f"Error getting training batches: {err}")
            return []
        finally:
            cursor.close()
            conn.close()

    def get_training_batch(self, batch_id: str) -> dict | None:
        conn = self.get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM training_batches WHERE batch_id = %s LIMIT 1",
                (batch_id,))
            row = cursor.fetchone()
            return self._decode_training_batch(row) if row else None
        except mysql.connector.Error as err:
            db_logger.error(f"Error getting training batch: {err}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_training_games(self, batch_id: str) -> list:
        batch = self.get_training_batch(batch_id)
        if not batch:
            return []
        games = batch.get("games", [])
        return games if isinstance(games, list) else []

    def _decode_training_batch(self, row: dict) -> dict:
        for key in ("config", "generation_statistics", "games"):
            if isinstance(row.get(key), str):
                row[key] = json.loads(row[key])
        config = row.get("config", {}) or {}
        games = row.get("games", []) or []
        row["games_per_generation"] = config.get("games_per_generation")
        row["games_completed"] = len([
            game for game in games
            if game.get("status") in ("completed", "failed", "skipped")
        ])
        row["games_failed"] = len([
            game for game in games
            if game.get("status") == "failed"
        ])
        return row
