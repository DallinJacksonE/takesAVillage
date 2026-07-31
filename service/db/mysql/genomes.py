import io
import json
import time

import mysql.connector


from service.logging import BackendLogger

db_logger = BackendLogger("db")


class GenomesRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_connection(self):
        return self.connection.get_connection()

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
            conn.rollback()
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
