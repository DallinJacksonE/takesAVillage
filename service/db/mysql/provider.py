import time

import mysql.connector


from service.logging import BackendLogger

db_logger = BackendLogger("db")

class MySQLDB:
    def __init__(self, config):
        self.config = config

    def get_connection(self):
        attempts = 10
        for attempt in range(attempts):
            try:
                conn = mysql.connector.connect(**self.config)
                db_logger.info("Connected to MySQL")
                return conn
            except mysql.connector.Error as err:
                db_logger.warning(
                    f"MySQL connection attempt "
                    f"{attempt + 1}/{attempts} failed: {err}"
                )
                time.sleep(3)

        db_logger.error("Could not connect to MySQL after retries")
        return None



    def initialize_database(self):
        conn = self.get_connection()
        if not conn:
            db_logger.error(
                "Failed to connect to DB. Cannot initialize database.")
            return

        cursor = conn.cursor()
        db_logger.info("Ensuring MySQL database tables are initialized...")
        try:
            sql_statements = [
                s.strip() for s in self._get_schema_script().split(';') if s.strip()]
            for statement in sql_statements:
                cursor.execute(statement)
            self._ensure_games_columns(cursor)
            self._ensure_training_batches_columns(cursor)
            conn.commit()
            db_logger.info("MySQL Database is ready.")
        except mysql.connector.Error as err:
            db_logger.error(f"Failed to initialize database tables: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def _get_schema_script(self):
        from pathlib import Path

        schema_path = Path(__file__).resolve().parents[1] / "schema" / "mysql.sql"
        return schema_path.read_text(encoding="utf-8")

    def _ensure_games_columns(self, cursor):
        columns = {
            "game_type": "VARCHAR(32) NOT NULL DEFAULT 'human'",
            "training_batch_id": "VARCHAR(64)",
            "training_generation": "INT",
            "trade_count": "INT NOT NULL DEFAULT 0",
            "contest_count": "INT NOT NULL DEFAULT 0",
            "lie_count": "INT NOT NULL DEFAULT 0"
        }
        for column_name, column_definition in columns.items():
            if not self._column_exists(cursor, "games", column_name):
                cursor.execute(
                    f"ALTER TABLE `games` ADD COLUMN `{column_name}` {column_definition}")

    def _ensure_training_batches_columns(self, cursor):
        columns = {
            "last_heartbeat_at": "DATETIME",
            "phase": "VARCHAR(64)",
            "last_error": "TEXT",
        }
        for column_name, column_definition in columns.items():
            if not self._column_exists(cursor, "training_batches", column_name):
                cursor.execute(
                    f"ALTER TABLE `training_batches` ADD COLUMN `{column_name}` {column_definition}")

    def _column_exists(self, cursor, table_name: str, column_name: str) -> bool:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = %s
              AND COLUMN_NAME = %s
            """,
            (table_name, column_name),
        )
        row = cursor.fetchone()
        return bool(row and row[0])
