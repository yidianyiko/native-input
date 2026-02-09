"""Database migration system for reInput AI input method.

This module provides database migration functionality to handle
schema changes and data migrations over time.
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from ...utils.loguru_config import get_logger

logger = get_logger(__name__)


class Migration:
    """Represents a single database migration."""
    
    def __init__(self, version: int, name: str, up_sql: str, down_sql: str = ""):
        """Initialize migration.
        
        Args:
            version: Migration version number
            name: Migration name/description
            up_sql: SQL to apply migration
            down_sql: SQL to rollback migration (optional)
        """
        self.version = version
        self.name = name
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.timestamp = datetime.now()
    
    def __str__(self):
        return f"Migration {self.version}: {self.name}"


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db_path: str):
        """Initialize migration manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.migrations: List[Migration] = []
        self._register_migrations()
    
    def _register_migrations(self):
        """Register all available migrations."""
        # Migration 1: Initial schema
        self.migrations.append(Migration(
            version=1,
            name="Initial schema creation",
            up_sql="""
                -- Create users table
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create app_windows table
                CREATE TABLE IF NOT EXISTS app_windows (
                    window_id TEXT PRIMARY KEY,
                    process_name TEXT NOT NULL,
                    window_title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create window_contexts table
                CREATE TABLE IF NOT EXISTS window_contexts (
                    context_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    window_id TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    num_messages INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (window_id) REFERENCES app_windows(window_id) ON DELETE CASCADE
                );
                
                -- Create messages table
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    context_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                    type TEXT NOT NULL CHECK (type IN ('original', 'processed')),
                    sequence_number INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (context_id) REFERENCES window_contexts(context_id) ON DELETE CASCADE
                );
                
                -- Create database_metadata table for migration tracking
                CREATE TABLE IF NOT EXISTS database_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Create indexes for performance
                CREATE INDEX IF NOT EXISTS idx_window_contexts_user_id ON window_contexts(user_id);
                CREATE INDEX IF NOT EXISTS idx_window_contexts_window_id ON window_contexts(window_id);
                CREATE INDEX IF NOT EXISTS idx_messages_context_id ON messages(context_id);
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
                CREATE INDEX IF NOT EXISTS idx_messages_sequence ON messages(context_id, sequence_number);
                CREATE INDEX IF NOT EXISTS idx_app_windows_process ON app_windows(process_name);
                
                -- Insert initial metadata
                INSERT OR REPLACE INTO database_metadata (key, value) VALUES ('version', '1');
                INSERT OR REPLACE INTO database_metadata (key, value) VALUES ('created_at', datetime('now'));
            """,
            down_sql="""
                DROP TABLE IF EXISTS messages;
                DROP TABLE IF EXISTS window_contexts;
                DROP TABLE IF EXISTS app_windows;
                DROP TABLE IF EXISTS users;
                DROP TABLE IF EXISTS database_metadata;
            """
        ))
        
        # Future migrations can be added here
        # Example:
        # self.migrations.append(Migration(
        #     version=2,
        #     name="Add user preferences table",
        #     up_sql="CREATE TABLE user_preferences (...);",
        #     down_sql="DROP TABLE user_preferences;"
        # ))
    
    def get_current_version(self) -> int:
        """Get current database version.
        
        Returns:
            Current database version, 0 if not initialized
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if metadata table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='database_metadata'
                """)
                
                if not cursor.fetchone():
                    return 0
                
                # Get version from metadata
                cursor.execute(
                    "SELECT value FROM database_metadata WHERE key = 'version'"
                )
                result = cursor.fetchone()
                return int(result['value']) if result else 0
                
        except Exception as e:
            logger.error(f"Failed to get current database version: {e}")
            return 0
    
    def get_latest_version(self) -> int:
        """Get latest available migration version.
        
        Returns:
            Latest migration version
        """
        return max(m.version for m in self.migrations) if self.migrations else 0
    
    def needs_migration(self) -> bool:
        """Check if database needs migration.
        
        Returns:
            True if migration is needed
        """
        current = self.get_current_version()
        latest = self.get_latest_version()
        return current < latest
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations.
        
        Returns:
            List of migrations that need to be applied
        """
        current_version = self.get_current_version()
        return [m for m in self.migrations if m.version > current_version]
    
    def migrate_up(self, target_version: Optional[int] = None) -> bool:
        """Apply migrations up to target version.
        
        Args:
            target_version: Target version to migrate to. If None, migrates to latest.
            
        Returns:
            True if successful, False otherwise
        """
        if target_version is None:
            target_version = self.get_latest_version()
        
        current_version = self.get_current_version()
        
        if current_version >= target_version:
            logger.info(f"Database is already at version {current_version}")
            return True
        
        # Ensure database directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                
                # Apply migrations in order
                for migration in sorted(self.migrations, key=lambda m: m.version):
                    if migration.version <= current_version:
                        continue
                    if migration.version > target_version:
                        break
                    
                    logger.info(f"Applying {migration}")
                    
                    # Execute migration SQL
                    conn.executescript(migration.up_sql)
                    
                    # Update version in metadata
                    conn.execute(
                        "INSERT OR REPLACE INTO database_metadata (key, value, updated_at) VALUES (?, ?, ?)",
                        ('version', str(migration.version), datetime.now().isoformat())
                    )
                    
                    logger.info(f"Successfully applied {migration}")
                
                conn.execute("COMMIT")
                logger.info(f"Database migrated from version {current_version} to {target_version}")
                return True
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("ROLLBACK")
            except:
                pass
            return False
    
    def migrate_down(self, target_version: int) -> bool:
        """Rollback migrations to target version.
        
        Args:
            target_version: Target version to rollback to
            
        Returns:
            True if successful, False otherwise
        """
        current_version = self.get_current_version()
        
        if current_version <= target_version:
            logger.info(f"Database is already at or below version {target_version}")
            return True
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("BEGIN TRANSACTION")
                
                # Rollback migrations in reverse order
                for migration in sorted(self.migrations, key=lambda m: m.version, reverse=True):
                    if migration.version <= target_version:
                        break
                    if migration.version > current_version:
                        continue
                    
                    if not migration.down_sql:
                        logger.warning(f"No rollback SQL for {migration}")
                        continue
                    
                    logger.info(f"Rolling back {migration}")
                    
                    # Execute rollback SQL
                    conn.executescript(migration.down_sql)
                    
                    logger.info(f"Successfully rolled back {migration}")
                
                # Update version in metadata
                conn.execute(
                    "INSERT OR REPLACE INTO database_metadata (key, value, updated_at) VALUES (?, ?, ?)",
                    ('version', str(target_version), datetime.now().isoformat())
                )
                
                conn.execute("COMMIT")
                logger.info(f"Database rolled back from version {current_version} to {target_version}")
                return True
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("ROLLBACK")
            except:
                pass
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status information.
        
        Returns:
            Dictionary with migration status details
        """
        current_version = self.get_current_version()
        latest_version = self.get_latest_version()
        pending_migrations = self.get_pending_migrations()
        
        return {
            'current_version': current_version,
            'latest_version': latest_version,
            'needs_migration': self.needs_migration(),
            'pending_migrations': [
                {
                    'version': m.version,
                    'name': m.name
                }
                for m in pending_migrations
            ],
            'database_exists': os.path.exists(self.db_path),
            'database_path': self.db_path
        }
    
    def validate_database_schema(self) -> bool:
        """Validate that database schema matches expected structure.
        
        Returns:
            True if schema is valid, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check required tables exist
                required_tables = ['users', 'app_windows', 'window_contexts', 'messages', 'database_metadata']
                
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name IN ({})
                """.format(','.join('?' * len(required_tables))), required_tables)
                
                existing_tables = {row['name'] for row in cursor.fetchall()}
                missing_tables = set(required_tables) - existing_tables
                
                if missing_tables:
                    logger.error(f"Missing required tables: {missing_tables}")
                    return False
                
                # Check required indexes exist
                required_indexes = [
                    'idx_window_contexts_user_id',
                    'idx_window_contexts_window_id',
                    'idx_messages_context_id',
                    'idx_messages_timestamp',
                    'idx_messages_sequence',
                    'idx_app_windows_process'
                ]
                
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' AND name IN ({})
                """.format(','.join('?' * len(required_indexes))), required_indexes)
                
                existing_indexes = {row['name'] for row in cursor.fetchall()}
                missing_indexes = set(required_indexes) - existing_indexes
                
                if missing_indexes:
                    logger.warning(f"Missing recommended indexes: {missing_indexes}")
                    # Don't fail validation for missing indexes, just warn
                
                logger.info("Database schema validation passed")
                return True
                
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False