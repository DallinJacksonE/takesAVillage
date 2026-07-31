import io
import json
import time

import mysql.connector

from service.db.serialization import safe_serialize as _safe_serialize
from service.logging import BackendLogger

db_logger = BackendLogger("db")


class GamesRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_connection(self):
        return self.connection.get_connection()

    def store_game_result(self, game_id, day_num, phase, snapshot_json,
                          training_batch_id=None, training_generation=None,
                          game_type=None, trade_count=None, contest_count=None, lie_count=None):
        conn = self.get_connection()
        if not conn:
            raise ConnectionError("Unable to connect while storing game result")

        cursor = conn.cursor()
        query = """
            INSERT INTO games
            (game_id, day_num, phase, data, game_type, training_batch_id, training_generation, trade_count, contest_count, lie_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            cursor.execute(query, (
                game_id, day_num, phase, snapshot_json,
                game_type or ("training" if training_batch_id else "human"),
                training_batch_id, training_generation, trade_count, contest_count, lie_count))
            conn.commit()
        except mysql.connector.Error as err:
            conn.rollback()
            db_logger.error(f"Error storing game result: {err}")
            raise
        finally:
            cursor.close()
            conn.close()

    def store_game_snapshot(self, game_id: str, day_num: int, phase: str, snapshot_json: str):
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()
        query = "INSERT INTO game_history (game_id, day_num, phase, data) VALUES (%s, %s, %s, %s)"

        try:
            cursor.execute(query, (game_id, day_num, phase, snapshot_json))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error storing game snapshot: {err}")
        finally:
            cursor.close()
            conn.close()

    def store_player_snapshot(self, game_id, day_num, phase, player):
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()
        query = """
            INSERT INTO player_snapshots
            (
                game_id, day_num, phase, player_id, name, health, sickness_chance,
                resources, fire_status, fire_guests, developments, actions,
                committed_action, available_work, finished_phase, timeline, trade_history
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            cursor.execute(query, (
                game_id, day_num, phase, player.session_id, player.name,
                player.health, player.sickness_chance, json.dumps(
                    _safe_serialize(player.resources)),
                player.fire_status, json.dumps(
                    _safe_serialize(player.fire_guests)),
                json.dumps(_safe_serialize(player.developments)), json.dumps(
                    _safe_serialize(player.actions)),
                json.dumps(_safe_serialize(player.committed_action)), json.dumps(
                    _safe_serialize(player.available_work)),
                player.finished_phase, json.dumps(_safe_serialize(
                    player.timeline)), json.dumps(_safe_serialize(player.trade_history))
            ))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error storing player snapshot: {err}")
        finally:
            cursor.close()
            conn.close()

    def store_work_snapshot(self, snapshot):
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()
        query = """
            INSERT INTO work_phase_snapshots
            (game_id, player_id, day_num, health, sickness_chance, wood, food, iron, available_work, committed_action)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            committed = snapshot.get("committed_action")
            cursor.execute(query, (
                snapshot["game_id"], snapshot["player_id"], snapshot["day_num"],
                snapshot["health"], snapshot["sickness_chance"], snapshot["wood"],
                snapshot["food"], snapshot["iron"], json.dumps(
                    snapshot["available_work"]),
                json.dumps(committed) if committed else None
            ))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error storing work snapshot: {err}")
        finally:
            cursor.close()
            conn.close()

    def store_trade_snapshot(self, snapshot):
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()
        query = """
            INSERT INTO trade_phase_snapshots
            (game_id, player_id, day_num, health, sickness_chance, wood, food, iron, trade_history)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                snapshot["game_id"], snapshot["player_id"], snapshot["day_num"],
                snapshot["health"], snapshot["sickness_chance"], snapshot["wood"],
                snapshot["food"], snapshot["iron"], json.dumps(
                    snapshot["trade_history"])
            ))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error storing trade snapshot: {err}")
        finally:
            cursor.close()
            conn.close()

    def store_night_snapshot(self, snapshot):
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()
        query = """
            INSERT INTO night_phase_snapshots
            (game_id, player_id, day_num, health, sickness_chance, wood, food, iron, fire_status, fire_guests)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                snapshot["game_id"], snapshot["player_id"], snapshot["day_num"],
                snapshot["health"], snapshot["sickness_chance"], snapshot["wood"],
                snapshot["food"], snapshot["iron"], snapshot["fire_status"],
                json.dumps(snapshot["fire_guests"])
            ))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error storing night snapshot: {err}")
        finally:
            cursor.close()
            conn.close()

    def get_training_games(self, batch_id: str):
        conn = self.get_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    game_id,
                    training_generation AS generation,
                    trade_count,
                    contest_count,
                    lie_count
                FROM games
                WHERE training_batch_id = %s
                ORDER BY training_generation, created_at
                """,
                (batch_id,)
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    def get_all_games(self):
        conn = self.get_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = """SELECT *
            FROM games FORCE INDEX (idx_created_at)
            ORDER BY created_at DESC
            LIMIT 10;"""
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                if isinstance(row["data"], str):
                    row["data"] = json.loads(row["data"])
            return results
        finally:
            cursor.close()
            conn.close()

    def get_all_game_history(self) -> list:
        conn = self.get_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = "SELECT game_id, day_num, phase, data, created_at FROM game_history ORDER BY created_at DESC"
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                if isinstance(row['data'], str):
                    row['data'] = json.loads(row['data'])
            return results
        except mysql.connector.Error as err:
            db_logger.error(f"Error getting game history: {err}")
            return []
        finally:
            cursor.close()
            conn.close()
