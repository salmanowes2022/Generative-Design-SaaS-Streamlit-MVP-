"""
Database connection and operations using psycopg
"""
import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
from app.infra.config import settings


class Database:
    """Database connection manager"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, connection_string: Optional[str] = None):
        if self._initialized:
            return
        self.connection_string = connection_string or settings.DATABASE_URL
        self._conn = None
        self._initialized = True
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = psycopg.connect(
            self.connection_string,
            row_factory=dict_row
        )
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        """Execute a query without returning results"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
    
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """Fetch a single row"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
                if row is None:
                    return None

                # If the driver returned a tuple/sequence instead of a dict, convert
                if not isinstance(row, dict):
                    colnames = [d.name for d in cur.description]
                    return dict(zip(colnames, row))

                return row
    
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all rows"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

                if not rows:
                    return []

                # If rows are tuples/sequences instead of dicts, convert them
                if not isinstance(rows[0], dict):
                    colnames = [d.name for d in cur.description]
                    return [dict(zip(colnames, r)) for r in rows]

                return rows
    
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a row and return the inserted data"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"""
            INSERT INTO {table} ({columns})
            VALUES ({placeholders})
            RETURNING *
        """
        return self.fetch_one(query, tuple(data.values()))
    
    def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: tuple) -> Optional[Dict[str, Any]]:
        """Update rows and return the first updated row"""
        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        query = f"""
            UPDATE {table}
            SET {set_clause}
            WHERE {where_clause}
            RETURNING *
        """
        params = tuple(data.values()) + where_params
        return self.fetch_one(query, params)


# Initialize database instance (singleton)
db = Database()


def get_db() -> Database:
    """Get the database instance"""
    return db