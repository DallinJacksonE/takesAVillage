import mysql.connector
from mysql.connector import errorcode
import io


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


# Database Configuration
db_config = {
    'user': 'root',
    'password': 'password',
    'host': '127.0.0.1',
    'database': 'village_db',
    'raise_on_warnings': True
}

db = DatabaseManager(db_config)
