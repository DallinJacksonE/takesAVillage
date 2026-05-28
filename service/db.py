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
# --- Configuration Loader ---


def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.json')

    config_data: dict[str, Any] = {"db": {}, "flask": {}}

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print("config.json not found, relying on environment variables.")

    # Override config with Docker Environment Variables
    config_data['db']['host'] = os.environ.get(
        'DB_HOST', config_data['db'].get('host', '127.0.0.1'))
    config_data['db']['user'] = os.environ.get(
        'DB_USER', config_data['db'].get('user', 'village'))
    config_data['db']['password'] = os.environ.get(
        'DB_PASSWORD', config_data['db'].get('password', 'village_db'))
    config_data['db']['database'] = os.environ.get(
        'DB_NAME', config_data['db'].get('database', 'village_db'))

    # NEW: Catch the DB_TYPE flag to determine which database to build
    config_data['db_type'] = os.environ.get('DB_TYPE', 'mysql').lower()

    return config_data


# --- 1. The Contract (Abstract Base Class) ---

class DatabaseProvider(ABC):
    @abstractmethod
    def create_user(self, user_uuid: str, consent_agreed: bool) -> bool:
        pass

    @abstractmethod
    def user_exists(self, user_uuid: str) -> bool:
        pass

    @abstractmethod
    def initialize_database(self):
        pass

    @abstractmethod
    def store_game_result(
        self,
        game_id: str,
        day_num: int,
        phase: str,
        snapshot_json: str
    ):
        pass

    @abstractmethod
    def get_all_game_history(self) -> list:
        pass

    @abstractmethod
    def store_visualization(self, game_id: str, plot_name: str, figure):
        pass

    @abstractmethod
    def store_player_snapshot(
        self,
        game_id,
        day_num,
        phase,
        player
    ):
        pass

    @abstractmethod
    def store_work_snapshot(self, snapshot):
        pass

    @abstractmethod
    def store_trade_snapshot(self, snapshot):
        pass

    @abstractmethod
    def store_night_snapshot(self, snapshot):
        pass


# --- 2. The In-Memory Provider (Dev) ---

class InMemoryDB(DatabaseProvider):
    def __init__(self):
        self.users = {}
        self.history = []
        self.visualizations = {}

    def create_user(self, user_uuid: str, consent_agreed: bool) -> bool:
        self.users[user_uuid] = {
            "consent_agreed": consent_agreed,
            "created_at": datetime.now()
        }
        return True

    def user_exists(self, user_uuid: str) -> bool:
        return user_uuid in self.users

    def initialize_database(self):
        print("✅ InMemoryDB ready. (Note: Data wipes on container restart)")

    def store_game_result(
        self,
        game_id: str,
        day_num: int,
        phase: str,
        snapshot_json: str
    ):
        self.history.append({
            "game_id": game_id,
            "day_num": day_num,
            "phase": phase,
            "data": json.loads(snapshot_json),
            "created_at": datetime.now()
        })
        # print(self.history)

    def get_all_game_history(self) -> list:
        # Return sorted by finished_at descending to mimic SQL ORDER BY DESC
        return sorted(self.history, key=lambda x: x['finished_at'], reverse=True)

    def store_visualization(self, game_id: str, plot_name: str, figure):
        buf = io.BytesIO()
        figure.savefig(buf, format='png')
        buf.seek(0)

        if game_id not in self.visualizations:
            self.visualizations[game_id] = {}
        self.visualizations[game_id][plot_name] = buf.read()

    def store_player_snapshot(
        self,
        game_id,
        day_num,
        phase,
        player
    ):
        pass


    def store_work_snapshot(self, snapshot):
        pass


    def store_trade_snapshot(self, snapshot):
        pass


    def store_night_snapshot(self, snapshot):
        pass


# --- 3. The MySQL Provider (Prod) ---

class MySQLDB(DatabaseProvider):
    def __init__(self, config):
        self.config = config

    def get_connection(self):

        attempts = 10

        for attempt in range(attempts):

            try:
                conn = mysql.connector.connect(**self.config)

                print("✅ Connected to MySQL")

                return conn

            except mysql.connector.Error as err:

                print(
                    f"MySQL connection attempt "
                    f"{attempt + 1}/{attempts} failed: {err}"
                )

                time.sleep(3)

        print("❌ Could not connect to MySQL after retries")

        return None

    def create_user(self, user_uuid: str, consent_agreed: bool) -> bool:
        conn = self.get_connection()
        if not conn:
            print("ERROR: Failed to connect to DB. User not created.")
            return False

        cursor = conn.cursor()
        query = "INSERT INTO users (uuid, consent_agreed, created_at) VALUES (%s, %s, NOW())"
        try:
            cursor.execute(query, (user_uuid, consent_agreed))
            conn.commit()
            return True
        except mysql.connector.Error as err:
            print(f"Error creating user: {err}")
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
            print(f"Error checking user existence: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    def initialize_database(self):
        conn = self.get_connection()
        if not conn:
            print("ERROR: Failed to connect to DB. Cannot initialize database.")
            return

        cursor = conn.cursor()
        print("Ensuring MySQL database tables are initialized...")
        try:
            sql_statements = [
                s.strip() for s in self._get_schema_script().split(';') if s.strip()]
            for statement in sql_statements:
                cursor.execute(statement)
            conn.commit()
            print("✅ MySQL Database is ready.")
        except mysql.connector.Error as err:
            print(f"Failed to initialize database tables: {err}")
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
        """

    def store_game_result(
        self,
        game_id: str,
        day_num: int,
        phase: str,
        snapshot_json: str
    ):
        conn = self.get_connection()

        if not conn:
            return

        cursor = conn.cursor()

        query = """
            INSERT INTO game_history
            (
                game_id,
                day_num,
                phase,
                data
            )
            VALUES (%s, %s, %s, %s)
        """

        try:
            cursor.execute(
                query,
                (
                    game_id,
                    day_num,
                    phase,
                    snapshot_json
                )
            )

            conn.commit()

        except mysql.connector.Error as err:
            print(f"Error storing game result: {err}")

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
                game_id,
                day_num,
                phase,

                player_id,
                name,

                health,
                sickness_chance,

                resources,
                fire_status,
                fire_guests,

                developments,
                actions,
                committed_action,
                available_work,

                finished_phase,

                timeline,
                trade_history
            )
            VALUES
            (
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s,
                %s, %s
            )
        """

        try:

            cursor.execute(query, (
                game_id,
                day_num,
                phase,

                player.session_id,
                player.name,

                player.health,
                player.sickness_chance,

                json.dumps(_safe_serialize(player.resources)),
                player.fire_status,
                json.dumps(_safe_serialize(player.fire_guests)),

                json.dumps(_safe_serialize(player.developments)),
                json.dumps(_safe_serialize(player.actions)),
                json.dumps(_safe_serialize(player.committed_action)),
                json.dumps(_safe_serialize(player.available_work)),

                player.finished_phase,

                json.dumps(_safe_serialize(player.timeline)),
                json.dumps(_safe_serialize(player.trade_history))
            ))

            conn.commit()

        except mysql.connector.Error as err:
            print(f"Error storing player snapshot: {err}")

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
            (
                game_id,
                player_id,
                day_num,

                health,
                sickness_chance,

                wood,
                food,
                iron,

                available_work,

                committed_action
            )
            VALUES
            (
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s,
                %s
            )
        """

        try:

            committed = snapshot.get("committed_action")

            cursor.execute(query, (

                snapshot["game_id"],
                snapshot["player_id"],
                snapshot["day_num"],

                snapshot["health"],
                snapshot["sickness_chance"],

                snapshot["wood"],
                snapshot["food"],
                snapshot["iron"],

                json.dumps(snapshot["available_work"]),

                json.dumps(committed)
                if committed else None
            ))

            conn.commit()

        except mysql.connector.Error as err:
            print(f"Error storing work snapshot: {err}")

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
            (
                game_id,
                player_id,
                day_num,

                health,
                sickness_chance,

                wood,
                food,
                iron,

                trade_history
            )
            VALUES
            (
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s
            )
        """

        try:

            cursor.execute(query, (

                snapshot["game_id"],
                snapshot["player_id"],
                snapshot["day_num"],

                snapshot["health"],
                snapshot["sickness_chance"],

                snapshot["wood"],
                snapshot["food"],
                snapshot["iron"],

                json.dumps(snapshot["trade_history"])
            ))

            conn.commit()

        except mysql.connector.Error as err:
            print(f"Error storing trade snapshot: {err}")

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
            (
                game_id,
                player_id,
                day_num,

                health,
                sickness_chance,

                wood,
                food,
                iron,

                fire_status,
                fire_guests
            )
            VALUES
            (
                %s, %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s
            )
        """

        try:

            cursor.execute(query, (

                snapshot["game_id"],
                snapshot["player_id"],
                snapshot["day_num"],

                snapshot["health"],
                snapshot["sickness_chance"],

                snapshot["wood"],
                snapshot["food"],
                snapshot["iron"],

                snapshot["fire_status"],

                json.dumps(snapshot["fire_guests"])
            ))

            conn.commit()

        except mysql.connector.Error as err:
            print(f"Error storing night snapshot: {err}")

        finally:
            cursor.close()
            conn.close()

    def get_all_game_history(self) -> list:
        conn = self.get_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT
                game_id,
                day_num,
                phase,
                data,
                created_at
            FROM game_history
            ORDER BY created_at DESC
            """
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            for row in results:
                if isinstance(row['data'], str):
                    row['data'] = json.loads(row['data'])
            return results
        except mysql.connector.Error as err:
            print(f"Error getting game history: {err}")
            return []
        finally:
            cursor.close()
            conn.close()

    def store_visualization(self, game_id: str, plot_name: str, figure):
        # Existing logic handles mapping matplotlib to bytes
        buf = io.BytesIO()
        figure.savefig(buf, format='png')
        buf.seek(0)
        image_bytes = buf.read()
        # TODO: Implement SQL BLOB insertion logic here if required in Prod


# --- 4. The Database Factory ---

def get_database(config) -> DatabaseProvider:
    """
    Reads the config and returns the appropriate database provider class.
    """
    db_type = config.get('db_type', 'mysql')

    if db_type == 'memory':
        print("🔧 DEV MODE: Instantiating In-Memory Database...")
        return InMemoryDB()
    else:
        print("🔌 PROD MODE: Instantiating MySQL Database...")
        return MySQLDB(config['db'])


# --- Active Instance Setup ---

# 1. Load the OS Environment / Config variables
config_data = load_config()

# 2. Get the requested database provider
db = get_database(config_data)

# 3. Ensure tables/dicts are primed for action
print("INITIALIZING DATABASE...")
db.initialize_database()
