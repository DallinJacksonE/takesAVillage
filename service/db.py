import mysql.connector
from mysql.connector import errorcode
import json
import os
import io
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
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
    def store_game_result(self, game_id: str, game_data_json: str):
        pass

    @abstractmethod
    def get_all_game_history(self) -> list:
        pass

    @abstractmethod
    def store_visualization(self, game_id: str, plot_name: str, figure):
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

    def store_game_result(self, game_id: str, game_data_json: str):
        # Convert JSON string to dict for storage to mimic how MySQL handles JSON columns
        parsed_data = json.loads(game_data_json) if isinstance(
            game_data_json, str) else game_data_json
        self.history.append({
            "game_id": game_id,
            "data": parsed_data,
            "finished_at": datetime.now().isoformat()
        })

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


# --- 3. The MySQL Provider (Prod) ---

class MySQLDB(DatabaseProvider):
    def __init__(self, config):
        self.config = config

    def get_connection(self):
        try:
            return mysql.connector.connect(**self.config)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
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
              `game_id` VARCHAR(12) NOT NULL,
              `data` JSON NOT NULL,
              `finished_at` DATETIME NOT NULL
            );
        """

    def store_game_result(self, game_id: str, game_data_json: str):
        conn = self.get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        query = "INSERT INTO game_history (game_id, data, finished_at) VALUES (%s, %s, NOW())"
        try:
            cursor.execute(query, (game_id, game_data_json))
            conn.commit()
        except mysql.connector.Error as err:
            print(f"Error storing game result: {err}")
        finally:
            cursor.close()
            conn.close()

    def get_all_game_history(self) -> list:
        conn = self.get_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = "SELECT game_id, data, finished_at FROM game_history ORDER BY finished_at DESC"
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
db.initialize_database()
