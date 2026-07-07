import mysql.connector
from mysql.connector import errorcode
import json
import os
import io
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from serializers.snapshots import _safe_serialize
import time
from logger import BackendLogger

# Initialize the Database Logger
db_logger = BackendLogger("db")

# --- Configuration Loader ---


def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.json')

    config_data: dict[str, Any] = {"db": {}, "flask": {}}

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        db_logger.warning(
            "config.json not found, relying on environment variables.")

    config_data['db']['host'] = os.environ.get(
        'DB_HOST', config_data['db'].get('host', '127.0.0.1'))
    config_data['db']['user'] = os.environ.get(
        'DB_USER', config_data['db'].get('user', 'village'))
    config_data['db']['password'] = os.environ.get(
        'DB_PASSWORD', config_data['db'].get('password', 'village_db'))
    config_data['db']['database'] = os.environ.get(
        'DB_NAME', config_data['db'].get('database', 'village_db'))

    config_data['db_type'] = os.environ.get(
        'DB_TYPE', config_data.get('db_type', 'mysql')
    ).strip().lower()

    return config_data


# --- 1. The Contract (Abstract Base Class) ---
class DatabaseProvider(ABC):
    @abstractmethod
    def create_user(self, user_uuid: str, consent_agreed: bool) -> bool: pass
    @abstractmethod
    def user_exists(self, user_uuid: str) -> bool: pass
    @abstractmethod
    def initialize_database(self): pass

    @abstractmethod
    def store_game_snapshot(self, game_id: str, day_num: int,
                            phase: str, snapshot_json: str): pass

    @abstractmethod
    def store_game_result(self, game_id: str, day_num: int,
                          phase: str, snapshot_json: str,
                          training_batch_id=None, training_generation=None,
                          game_type=None): pass

    @abstractmethod
    def get_all_game_history(self) -> list: pass
    @abstractmethod
    def get_all_games(self) -> list: pass
    @abstractmethod
    def store_visualization(self, game_id: str, plot_name: str, figure) -> Any: pass
    @abstractmethod
    def store_player_snapshot(self, game_id, day_num, phase, player): pass
    @abstractmethod
    def store_work_snapshot(self, snapshot): pass
    @abstractmethod
    def store_trade_snapshot(self, snapshot): pass
    @abstractmethod
    def store_night_snapshot(self, snapshot): pass
    @abstractmethod
    def store_genome(self, name: str, shorthand: str, genome_json: str): pass
    @abstractmethod
    def get_all_genomes(self) -> list: pass
    @abstractmethod
    def create_training_batch(self, batch_id: str, config: dict): pass
    @abstractmethod
    def mark_training_batch_game_started(self, batch_id: str, game_id: str,
                                         generation: int): pass
    @abstractmethod
    def append_training_batch_generation_stats(self, batch_id: str,
                                               stats: dict): pass
    @abstractmethod
    def complete_training_batch(self, batch_id: str,
                                final_champion_genome_id: str | None = None): pass
    @abstractmethod
    def get_training_batches(self) -> list: pass
    @abstractmethod
    def get_training_batch(self, batch_id: str) -> dict | None: pass
    @abstractmethod
    def store_research_visualization(self, scope_type: str, scope_id: str,
                                     name: str, title: str, mime_type: str,
                                     image_bytes: bytes,
                                     metadata: dict | None = None) -> Any: pass
    @abstractmethod
    def get_research_visualizations(self, scope_type: str,
                                    scope_id: str) -> list: pass
    @abstractmethod
    def get_research_visualization(self, visualization_id) -> Any: pass

# --- 2. The In-Memory Provider (Dev) ---


class InMemoryDB(DatabaseProvider):
    def __init__(self):
        self.users = {}
        self.history = []
        self.visualizations = {}
        self.genomes = []
        self.training_batches = {}
        self.research_visualizations = {}
        self.next_visualization_id = 1

    def create_user(self, user_uuid: str, consent_agreed: bool) -> bool:
        self.users[user_uuid] = {
            "consent_agreed": consent_agreed,
            "created_at": datetime.now()
        }
        return True

    def user_exists(self, user_uuid: str) -> bool:
        return user_uuid in self.users

    def initialize_database(self):
        db_logger.info(
            "InMemoryDB ready. (Note: Data wipes on container restart)")
        
    def delete_research_visualizations(self, scope_type: str, scope_id: str):
        self.research_visualizations = {
            key: value
            for key, value in self.research_visualizations.items()
            if not (
                value["scope_type"] == scope_type
                and value["scope_id"] == scope_id
            )
        }

    def store_game_result(self, game_id, day_num, phase, snapshot_json,
                          training_batch_id=None, training_generation=None,
                          game_type=None):
        if isinstance(snapshot_json, str):
            data = json.loads(snapshot_json)
        else:
            data = snapshot_json

        self.history.append({
            "game_id": game_id,
            "day_num": day_num,
            "phase": phase,
            "data": data,
            "training_batch_id": training_batch_id,
            "training_generation": training_generation,
            "game_type": game_type or ("training" if training_batch_id else "human"),
            "created_at": datetime.now()
        })

    def store_game_snapshot(self, game_id: str, day_num: int, phase: str, snapshot_json: str):
        self.history.append({
            "game_id": game_id,
            "day_num": day_num,
            "phase": phase,
            "data": json.loads(snapshot_json),
            "created_at": datetime.now()
        })

    def get_all_games(self):
        return sorted(self.history, key=lambda x: x['created_at'], reverse=True)

    def get_all_game_history(self) -> list:
        return sorted(self.history, key=lambda x: x['created_at'], reverse=True)

    def store_visualization(self, game_id: str, plot_name: str, figure):
        buf = io.BytesIO()
        figure.savefig(buf, format='png')
        buf.seek(0)

        if game_id not in self.visualizations:
            self.visualizations[game_id] = {}
        self.visualizations[game_id][plot_name] = buf.read()

    def store_player_snapshot(self, game_id, day_num, phase, player):
        pass

    def store_work_snapshot(self, snapshot):
        pass

    def store_trade_snapshot(self, snapshot):
        pass

    def store_night_snapshot(self, snapshot):
        pass

    def store_genome(self, name: str, shorthand: str, genome_json: str):
        self.genomes.append({
            "name": name,
            "shorthand_name": shorthand,
            "genome_data": json.loads(genome_json),
            "created_at": datetime.now()
        })

    def get_all_genomes(self) -> list:
        return sorted(self.genomes, key=lambda x: x['created_at'], reverse=True)

    def create_training_batch(self, batch_id: str, config: dict):
        now = datetime.now()
        self.training_batches[batch_id] = {
            "batch_id": batch_id,
            "status": "running",
            "ruleset": config.get("ruleset"),
            "bot_model": config.get("bot_model"),
            "bot_count": config.get("bot_count"),
            "total_generations": config.get("total_generations"),
            "current_generation": 0,
            "current_game_id": None,
            "started_at": now,
            "completed_at": None,
            "base_genome_id": config.get("base_genome_id"),
            "final_champion_genome_id": None,
            "config": config.get("config", {}),
            "generation_statistics": [],
            "games": [],
        }

    def mark_training_batch_game_started(self, batch_id: str, game_id: str,
                                         generation: int):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        batch["status"] = "running"
        batch["current_game_id"] = game_id
        batch["current_generation"] = generation
        if not isinstance(batch.get("games"), list):
            batch["games"] = []
        batch["games"].append({
            "game_id": game_id,
            "generation": generation,
        })

    def append_training_batch_generation_stats(self, batch_id: str, stats: dict):
        batch = self.training_batches.get(batch_id)
        if batch:
            batch.setdefault("generation_statistics", []).append(stats)

    def complete_training_batch(self, batch_id: str,
                                final_champion_genome_id: str | None = None):
        batch = self.training_batches.get(batch_id)
        if not batch:
            return
        batch["status"] = "completed"
        batch["completed_at"] = datetime.now()
        batch["final_champion_genome_id"] = final_champion_genome_id

    def get_training_batches(self) -> list:
        return sorted(
            [dict(batch) for batch in self.training_batches.values()],
            key=lambda batch: batch["started_at"], reverse=True)

    def get_training_batch(self, batch_id: str) -> dict | None:
        batch = self.training_batches.get(batch_id)
        return dict(batch) if batch else None

    def store_research_visualization(self, scope_type: str, scope_id: str,
                                     name: str, title: str, mime_type: str,
                                     image_bytes: bytes,
                                     metadata: dict | None = None):
        visualization_id = str(self.next_visualization_id)
        self.next_visualization_id += 1
        self.research_visualizations[visualization_id] = {
            "id": visualization_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "name": name,
            "title": title,
            "mime_type": mime_type,
            "image_bytes": image_bytes,
            "metadata": metadata or {},
            "created_at": datetime.now(),
        }
        return visualization_id

    def get_research_visualizations(self, scope_type: str, scope_id: str) -> list:
        visualizations = []
        for visualization in self.research_visualizations.values():
            if (visualization["scope_type"] == scope_type and
                    visualization["scope_id"] == scope_id):
                item = dict(visualization)
                item.pop("image_bytes", None)
                item["url"] = f"/api/research/visualizations/{item['id']}"
                visualizations.append(item)
        return sorted(visualizations, key=lambda item: item["created_at"])

    def get_research_visualization(self, visualization_id):
        visualization = self.research_visualizations.get(str(visualization_id))
        return dict(visualization) if visualization else None


# --- 3. The MySQL Provider (Prod) ---
class MySQLDB(DatabaseProvider):
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

    def create_user(self, user_uuid: str, consent_agreed: bool) -> bool:
        conn = self.get_connection()
        if not conn:
            db_logger.error("Failed to connect to DB. User not created.")
            return False

        cursor = conn.cursor()
        query = "INSERT INTO users (uuid, consent_agreed, created_at) VALUES (%s, %s, NOW())"
        try:
            cursor.execute(query, (user_uuid, consent_agreed))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            db_logger.error(f"Error creating user: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    def user_exists(self, user_uuid: str) -> bool:
        conn = self.get_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        query = "SELECT 1 FROM users WHERE uuid = %s LIMIT 1"
        try:
            cursor.execute(query, (user_uuid,))
            return cursor.fetchone() is not None
        except mysql.connector.Error as err:
            db_logger.error(f"Error checking user existence: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

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
            conn.commit()
            db_logger.info("MySQL Database is ready.")
        except mysql.connector.Error as err:
            db_logger.error(f"Failed to initialize database tables: {err}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    def _get_schema_script(self):
        return """
            CREATE TABLE IF NOT EXISTS `users` (
              `id` INT AUTO_INCREMENT PRIMARY KEY,
              `uuid` VARCHAR(36) NOT NULL UNIQUE,
              `consent_agreed` BOOLEAN NOT NULL,
              `created_at` DATETIME NOT NULL
            );
            CREATE TABLE IF NOT EXISTS `game_history` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `phase` VARCHAR(32) NOT NULL,
                `data` JSON NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX(`game_id`),
                INDEX(`day_num`),
                INDEX(`phase`)
            );
            CREATE TABLE IF NOT EXISTS `work_phase_snapshots` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `player_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `health` VARCHAR(16) NOT NULL,
                `sickness_chance` FLOAT NOT NULL,
                `wood` INT NOT NULL DEFAULT 0,
                `food` INT NOT NULL DEFAULT 0,
                `iron` INT NOT NULL DEFAULT 0,
                `available_work` JSON NOT NULL,
                `committed_action` JSON,
                INDEX(`game_id`),
                INDEX(`player_id`),
                INDEX(`day_num`)
            );
            CREATE TABLE IF NOT EXISTS `trade_phase_snapshots` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `player_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `health` VARCHAR(16) NOT NULL,
                `sickness_chance` FLOAT NOT NULL,
                `wood` INT NOT NULL DEFAULT 0,
                `food` INT NOT NULL DEFAULT 0,
                `iron` INT NOT NULL DEFAULT 0,
                `trade_history` JSON NOT NULL,
                INDEX(`game_id`),
                INDEX(`player_id`),
                INDEX(`day_num`)
            );
            CREATE TABLE IF NOT EXISTS `night_phase_snapshots` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL,
                `player_id` VARCHAR(64) NOT NULL,
                `day_num` INT NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `health` VARCHAR(16) NOT NULL,
                `sickness_chance` FLOAT NOT NULL,
                `wood` INT NOT NULL DEFAULT 0,
                `food` INT NOT NULL DEFAULT 0,
                `iron` INT NOT NULL DEFAULT 0,
                `fire_status` VARCHAR(16) NOT NULL,
                `fire_guests` JSON NOT NULL,
                INDEX(`game_id`),
                INDEX(`player_id`),
                INDEX(`day_num`)
            );
            CREATE TABLE IF NOT EXISTS `games` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `game_id` VARCHAR(64) NOT NULL UNIQUE,
                `day_num` INT NOT NULL,
                `phase` VARCHAR(32) NOT NULL,
                `data` JSON NOT NULL,
                `game_type` VARCHAR(32) NOT NULL DEFAULT 'human',
                `training_batch_id` VARCHAR(64),
                `training_generation` INT,
                `trade_count` INT NOT NULL DEFAULT 0,
                `contest_count` INT NOT NULL DEFAULT 0,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_created_at (created_at),
                INDEX idx_training_batch_id (training_batch_id)
            );
            CREATE TABLE IF NOT EXISTS `training_batches` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `batch_id` VARCHAR(64) NOT NULL UNIQUE,
                `status` VARCHAR(32) NOT NULL,
                `ruleset` VARCHAR(64),
                `bot_model` VARCHAR(64),
                `bot_count` INT,
                `total_generations` INT,
                `current_generation` INT DEFAULT 0,
                `current_game_id` VARCHAR(64),
                `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                `completed_at` DATETIME,
                `base_genome_id` VARCHAR(64),
                `final_champion_genome_id` VARCHAR(64),
                `config` JSON,
                `generation_statistics` JSON,
                `games` JSON,
                INDEX idx_training_batches_started_at (started_at)
            );
            CREATE TABLE IF NOT EXISTS `research_visualizations` (
                `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
                `scope_type` VARCHAR(32) NOT NULL,
                `scope_id` VARCHAR(64) NOT NULL,
                `name` VARCHAR(128) NOT NULL,
                `title` VARCHAR(255) NOT NULL,
                `mime_type` VARCHAR(64) NOT NULL,
                `image_bytes` LONGBLOB NOT NULL,
                `metadata` JSON,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_research_visualizations_scope (scope_type, scope_id)
            );
            CREATE TABLE IF NOT EXISTS `genomes` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `shorthand_name` VARCHAR(4) NOT NULL,
                `name` VARCHAR(64) NOT NULL,
                `genome_data` JSON NOT NULL,
                `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """

    def _ensure_games_columns(self, cursor):
        columns = {
            "game_type": "VARCHAR(32) NOT NULL DEFAULT 'human'",
            "training_batch_id": "VARCHAR(64)",
            "training_generation": "INT",
            "trade_count": "INT NOT NULL DEFAULT 0",
            "contest_count": "INT NOT NULL DEFAULT 0"
        }
        for column_name, column_definition in columns.items():
            if not self._column_exists(cursor, "games", column_name):
                cursor.execute(
                    f"ALTER TABLE `games` ADD COLUMN `{column_name}` {column_definition}")

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

    def store_game_result(self, game_id, day_num, phase, snapshot_json,
                          training_batch_id=None, training_generation=None,
                          game_type=None, trade_count=None, contest_count=None):
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()
        query = """
            INSERT INTO games
            (game_id, day_num, phase, data, game_type, training_batch_id, training_generation, trade_count, contest_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        try:
            cursor.execute(query, (
                game_id, day_num, phase, snapshot_json,
                game_type or ("training" if training_batch_id else "human"),
                training_batch_id, training_generation, trade_count, contest_count))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error storing game result: {err}")
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

    def delete_research_visualizations(self, scope_type: str, scope_id: str):
        conn = self.get_connection()
        if not conn:
            return

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM research_visualizations
                WHERE scope_type = %s
                AND scope_id = %s
                """,
                (scope_type, scope_id),
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def store_genome(self, name: str, shorthand: str, genome_json: str):
        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        query = "INSERT INTO genomes (name, shorthand_name, genome_data) VALUES (%s, %s, %s)"
        try:
            cursor.execute(query, (name, shorthand, genome_json))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error storing genome: {err}")
        finally:
            cursor.close()
            conn.close()

    def get_all_genomes(self) -> list:
        conn = self.get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM genomes ORDER BY created_at DESC"
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                if isinstance(row['genome_data'], str):
                    row['genome_data'] = json.loads(row['genome_data'])
            return results
        except mysql.connector.Error as err:
            db_logger.error(f"Error getting genomes: {err}")
            return []
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
                    training_generation,
                    trade_count,
                    contest_count
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

    def create_training_batch(self, batch_id: str, config: dict):
        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        query = """
            INSERT INTO training_batches
            (batch_id, status, ruleset, bot_model, bot_count, total_generations,
             current_generation, base_genome_id, config, generation_statistics, games)
            VALUES (%s, 'running', %s, %s, %s, %s, 0, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                batch_id, config.get("ruleset"), config.get("bot_model"),
                config.get("bot_count"), config.get("total_generations"),
                config.get("base_genome_id"), json.dumps(config.get("config", {})),
                json.dumps([]), json.dumps([])))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error creating training batch: {err}")
        finally:
            cursor.close()
            conn.close()

    def mark_training_batch_game_started(self, batch_id: str, game_id: str,
                                         generation: int):
        batch = self.get_training_batch(batch_id)
        if not batch:
            return
        games = batch.get("games", [])
        games.append({"game_id": game_id, "generation": generation})
        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        query = """
            UPDATE training_batches
            SET status = 'running', current_game_id = %s,
                current_generation = %s, games = %s
            WHERE batch_id = %s
        """
        try:
            cursor.execute(query, (game_id, generation, json.dumps(games), batch_id))
            conn.commit()
        except mysql.connector.Error as err:
            db_logger.error(f"Error updating training batch game: {err}")
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

    def _decode_training_batch(self, row: dict) -> dict:
        for key in ("config", "generation_statistics", "games"):
            if isinstance(row.get(key), str):
                row[key] = json.loads(row[key])
        return row

    def store_research_visualization(self, scope_type: str, scope_id: str,
                                     name: str, title: str, mime_type: str,
                                     image_bytes: bytes,
                                     metadata: dict | None = None):
        conn = self.get_connection()
        if not conn:
            return None
        cursor = conn.cursor()
        query = """
            INSERT INTO research_visualizations
            (scope_type, scope_id, name, title, mime_type, image_bytes, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (
                scope_type, scope_id, name, title, mime_type, image_bytes,
                json.dumps(metadata or {})))
            conn.commit()
            return str(cursor.lastrowid)
        except mysql.connector.Error as err:
            db_logger.error(f"Error storing research visualization: {err}")
            return None
        finally:
            cursor.close()
            conn.close()

    def get_research_visualizations(self, scope_type: str, scope_id: str) -> list:
        conn = self.get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, scope_type, scope_id, name, title, mime_type, metadata, created_at
            FROM research_visualizations
            WHERE scope_type = %s AND scope_id = %s
            ORDER BY created_at ASC
        """
        try:
            cursor.execute(query, (scope_type, scope_id))
            rows = cursor.fetchall()
            for row in rows:
                row["id"] = str(row["id"])
                if isinstance(row.get("metadata"), str):
                    row["metadata"] = json.loads(row["metadata"])
                row["url"] = f"/api/research/visualizations/{row['id']}"
            return rows
        except mysql.connector.Error as err:
            db_logger.error(f"Error getting research visualizations: {err}")
            return []
        finally:
            cursor.close()
            conn.close()

    def get_research_visualization(self, visualization_id):
        conn = self.get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM research_visualizations WHERE id = %s LIMIT 1",
                (visualization_id,))
            row = cursor.fetchone()
            if row and isinstance(row.get("metadata"), str):
                row["metadata"] = json.loads(row["metadata"])
            if row:
                row["id"] = str(row["id"])
            return row
        except mysql.connector.Error as err:
            db_logger.error(f"Error getting research visualization: {err}")
            return None
        finally:
            cursor.close()
            conn.close()

    def store_visualization(self, game_id: str, plot_name: str, figure):
        buf = io.BytesIO()
        figure.savefig(buf, format='png')
        buf.seek(0)
        image_bytes = buf.read()
        return self.store_research_visualization(
            scope_type="game",
            scope_id=game_id,
            name=plot_name,
            title=plot_name.replace("_", " ").title(),
            mime_type="image/png",
            image_bytes=image_bytes,
        )


# --- 4. The Database Factory ---
def get_database(config) -> DatabaseProvider:
    db_type = config.get('db_type', 'mysql')
    if db_type == 'memory':
        db_logger.info("🔧 DEV MODE: Instantiating In-Memory Database...")
        return InMemoryDB()
    else:
        db_logger.info("🔌 PROD MODE: Instantiating MySQL Database...")
        return MySQLDB(config['db'])


# --- Active Instance Setup ---
config_data = load_config()
db = get_database(config_data)
db_logger.info("INITIALIZING DATABASE...")
db.initialize_database()
