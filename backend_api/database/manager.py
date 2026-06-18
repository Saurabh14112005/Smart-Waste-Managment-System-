import sqlite3
import os
import logging
from backend_dashboard.config import DB_PATH

class DatabaseManager:
    @staticmethod
    def get_connection():
        """Returns a cached connection to the SQLite database."""
        try:
            if not os.path.exists(DB_PATH):
                logging.error(f"Database not found at {DB_PATH}")
                raise FileNotFoundError("System Database Missing")
            
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logging.error(f"DB Connection Error: {e}")
            return None

db_manager = DatabaseManager()
