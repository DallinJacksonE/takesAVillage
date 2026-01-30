import mysql.connector
from mysql.connector import errorcode
import json
import os
import io

# Helper to load config


def load_config():
    # Construct full path to ensure it works regardless
    # of where you run the script from
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, 'config.json')

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"WARNING: Configuration file not found at {config_path}")
        return None


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
        cursor = conn.cursor()
        query = "INSERT INTO users (uuid, consent_agreed, created_at) VALUES (%s, %s, NOW())"
        try:
            cursor.execute(query, (user_uuid, consent_agreed))
            conn.commit()
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

    def store_visualization(self, game_id, plot_name, figure):
        """
        Converts a matplotlib figure to bytes and stores it in BLOB column.
        """
        buf = io.BytesIO()
        figure.savefig(buf, format='png')
        buf.seek(0)
        image_bytes = buf.read()

        conn = self.get_connection()
        cursor = conn.cursor()
        query = "INSERT INTO visualizations (game_id, plot_name, image_blob) VALUES (%s, %s, %s)"
        try:
            cursor.execute(query, (game_id, plot_name, image_bytes))
            conn.commit()
        finally:
            cursor.close()
            conn.close()


if config_data:
    db = DatabaseManager(config_data['db'])
else:
    # Fallback or exit if config is missing
    db = DatabaseManager({})
