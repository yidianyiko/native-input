"""SQLite database manager for reInput AI input method.

This module provides low-level database connection management, table creation,
and migration functionality using SQLite.
"""

import sqlite3
import os
import threading
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from datetime import datetime

from ...utils.loguru_config import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """SQLite database manager with connection pooling and migration support."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        self.db_path = db_path or self._get_default_db_path()
        self._local = threading.local()
        self._ensure_db_directory()
        self._current_version = 1
        
        logger.info(f"DatabaseManager initialized with db_path: {self.db_path}")
    
    def _get_default_db_path(self) -> str:
        """Get default database path in current directory."""
        # Get current directory and create data subdirectory
        current_dir = os.getcwd()
        data_dir = os.path.join(current_dir, 'data')
        
        # Create directory if it doesn't exist
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        
        return os.path.join(data_dir, 'reInput.db')
    
    def _ensure_db_directory(self):
        """Ensure database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        Path(db_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            # Enable foreign key constraints
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            # Set WAL mode for better concurrency
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            # Set synchronous mode for better performance
            self._local.connection.execute("PRAGMA synchronous = NORMAL")
            
            logger.debug(f"Created new database connection for thread {threading.current_thread().name}")
        
        return self._local.connection
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic transaction handling."""
        conn = self._get_connection()
        try:
            yield conn
        except Exception as e:
            conn.rollback()
            logger.error(f"Database transaction rolled back due to error: {e}")
            raise
        else:
            conn.commit()
    
    def initialize_database(self) -> bool:
        """Initialize database with tables and indexes.
        
        Returns:
            True if initialization successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                # Check if database is already initialized
                if self._is_database_initialized(conn):
                    logger.info("Database already initialized")
                    return True
                
                # Create tables
                self._create_tables(conn)
                
                # Create indexes
                self._create_indexes(conn)
                
                # Set database version
                self._set_database_version(conn, self._current_version)
                
                logger.info("Database initialized successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def _is_database_initialized(self, conn: sqlite3.Connection) -> bool:
        """Check if database is already initialized."""
        try:
            cursor = conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='users'
            """)
            return cursor.fetchone() is not None
        except Exception:
            return False
    
    def _create_tables(self, conn: sqlite3.Connection):
        """Create all database tables."""
        
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL
            )
        """)
        
        # App windows table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS app_windows (
                window_id TEXT PRIMARY KEY,
                process_name TEXT NOT NULL,
                window_title TEXT NOT NULL
            )
        """)
        
        # Window contexts table (sessions)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS window_contexts (
                context_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                window_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                num_messages INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (window_id) REFERENCES app_windows(window_id)
            )
        """)
        
        # Messages table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                context_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                type TEXT NOT NULL CHECK (type IN ('user_input', 'ai_output')),
                sequence_number INTEGER NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (context_id) REFERENCES window_contexts(context_id),
                UNIQUE(context_id, sequence_number)
            )
        """)
        
        # Database metadata table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS database_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        logger.info("Database tables created successfully")
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for performance optimization."""
        
        indexes = [
            # Window context indexes
            "CREATE INDEX IF NOT EXISTS idx_window_context_user ON window_contexts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_window_context_window ON window_contexts(window_id)",
            "CREATE INDEX IF NOT EXISTS idx_window_context_agent_type ON window_contexts(agent_type)",
            
            # Message indexes
            "CREATE INDEX IF NOT EXISTS idx_message_context ON messages(context_id)",
            "CREATE INDEX IF NOT EXISTS idx_message_timestamp ON messages(timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_message_sequence ON messages(context_id, sequence_number)",
            
            # App window indexes
            "CREATE INDEX IF NOT EXISTS idx_app_window_process ON app_windows(process_name)",
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        logger.info("Database indexes created successfully")
    
    def _set_database_version(self, conn: sqlite3.Connection, version: int):
        """Set database version in metadata table."""
        conn.execute("""
            INSERT OR REPLACE INTO database_metadata (key, value, updated_at)
            VALUES ('version', ?, ?)
        """, (str(version), datetime.now().isoformat()))
    
    def get_database_version(self) -> int:
        """Get current database version."""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT value FROM database_metadata WHERE key = 'version'
                """)
                result = cursor.fetchone()
                return int(result[0]) if result else 0
        except Exception as e:
            logger.error(f"Failed to get database version: {e}")
            return 0
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries representing query results
        """
        try:
            with self.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to execute query: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to execute update: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """Execute a query multiple times with different parameters.
        
        Args:
            query: SQL query string
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.executemany(query, params_list)
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Failed to execute batch update: {e}")
            raise
    
    def close_connections(self):
        """Close all database connections."""
        if hasattr(self._local, 'connection'):
            try:
                self._local.connection.close()
                delattr(self._local, 'connection')
                logger.debug("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
    
    def vacuum_database(self):
        """Vacuum database to reclaim space and optimize performance."""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            logger.info("Database vacuumed successfully")
        except Exception as e:
            logger.error(f"Failed to vacuum database: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        try:
            with self.get_connection() as conn:
                # Get database size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                # Get table counts
                tables_info = {}
                for table in ['users', 'app_windows', 'window_contexts', 'messages']:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    tables_info[table] = cursor.fetchone()[0]
                
                return {
                    'db_path': self.db_path,
                    'db_size_bytes': db_size,
                    'version': self.get_database_version(),
                    'tables': tables_info
                }
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}