import io
import json
import time

import mysql.connector


from service.logging import BackendLogger

db_logger = BackendLogger("db")


class VisualizationsRepository:
    def __init__(self, connection):
        self.connection = connection

    def get_connection(self):
        return self.connection.get_connection()

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
        except mysql.connector.Error as err:
            conn.rollback()
            db_logger.error(f"Error deleting research visualizations: {err}")
        finally:
            cursor.close()
            conn.close()

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
