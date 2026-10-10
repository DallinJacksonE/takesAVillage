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
            ORDER BY created_at DESC;"""
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

    def get_game(self, game_id: str):
        conn = self.get_connection()
        if not conn:
            return None

        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM games WHERE game_id = %s LIMIT 1;"
        try:
            cursor.execute(query, (game_id,))
            row = cursor.fetchone()
            if row and isinstance(row.get("data"), str):
                row["data"] = json.loads(row["data"])
            return row
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


