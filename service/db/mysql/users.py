import io
import json
import time

import mysql.connector


from service.logging import BackendLogger

db_logger = BackendLogger("db")


class UsersRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_connection(self):
        return self.connection.get_connection()

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
            conn.rollback()
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
