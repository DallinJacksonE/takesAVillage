import mysql.connector
from mysql.connector import errorcode
import json
import os
import io

# Helper to load config


def load_config():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.json')

    config_data = {"db": {}, "flask": {}}

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        print("config.json not found, relying on environment variables.")

    # Override config with Docker Environment Variables if they exist
    config_data['db']['host'] = os.environ.get(
        'DB_HOST', config_data['db'].get('host', '127.0.0.1'))
    config_data['db']['user'] = os.environ.get(
        'DB_USER', config_data['db'].get('user', 'village'))
    config_data['db']['password'] = os.environ.get(
        'DB_PASSWORD', config_data['db'].get('password', 'village_db'))
    config_data['db']['database'] = os.environ.get(
        'DB_NAME', config_data['db'].get('database', 'village_db'))

    return config_data


# Load the config
config_data = load_config()


class DatabaseManager:
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

    def create_user(self, user_uuid, consent_agreed):
        conn = self.get_connection()
        if not conn:
            print("ERROR: Failed to connect to DB. User not created.")
            return False  # Return failure

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

    def user_exists(self, user_uuid):
        """
        Checks if a user with the given UUID exists in the database.
        Returns True if they exist, False otherwise.
        """
        conn = self.get_connection()
        if not conn:
            return False

        cursor = conn.cursor()
        query = "SELECT 1 FROM users WHERE uuid = %s LIMIT 1"
        try:
            cursor.execute(query, (user_uuid,))
            # If fetchone() returns a result, the user exists
            return cursor.fetchone() is not None
        except mysql.connector.Error as err:
            print(f"Error checking user existence: {err}")
            return False
        finally:
            cursor.close()
            conn.close()

    def initialize_database(self):
        """
        Ensures that all necessary tables exist in the database.
        Uses `CREATE TABLE IF NOT EXISTS` to be idempotent.
        """
        conn = self.get_connection()
        if not conn:
            print("ERROR: Failed to connect to DB. Cannot initialize database.")
            return

        cursor = conn.cursor()
        print("Ensuring database tables are initialized...")
        try:
            # Split the schema script into individual statements and execute them one by one
            sql_statements = [
                s.strip() for s in self._get_schema_script().split(';') if s.strip()]
            for statement in sql_statements:
                cursor.execute(statement)
            conn.commit()
            print("Database is ready.")
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

    def store_game_result(self, game_id, game_data_json):
        """Stores the final JSON state of a game."""
        conn = self.get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO game_history (game_id, data, finished_at) VALUES (%s, %s, NOW())"
        try:
            cursor.execute(query, (game_id, game_data_json))
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def get_all_game_history(self):
        """Retrieves all game history records."""
        conn = self.get_connection()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        query = "SELECT game_id, data, finished_at FROM game_history ORDER BY finished_at DESC"
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            # The 'data' column is likely a JSON string, so we parse it.
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

    def store_visualization(self, game_id, plot_name, figure):
        """
        Converts a matplotlib figure to bytes and stores it in BLOB column.
        """
        buf = io.BytesIO()
        figure.savefig(buf, format='png')
        buf.seek(0)
        image_bytes = buf.read()


if config_data:
    db = DatabaseManager(config_data['db'])
    db.initialize_database()
    print("db setup successful")
else:
    print("failed databse setup: config missing")
