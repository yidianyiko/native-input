"""Database Service Interfaces

Defines abstract interfaces for database services to provide
clear contracts and enable dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...services.database.models import (
    User, AppWindow, WindowContext, Message,
    MessageRole, MessageType
)


class IDatabaseService(ABC):
    """Interface for high-level database operations."""
    
    # User operations
    @abstractmethod
    def create_user(self, display_name: str, user_id: Optional[str] = None) -> User:
        """Create a new user."""
    
    @abstractmethod
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
    
    @abstractmethod
    def get_or_create_user(self, user_id: str, display_name: str) -> User:
        """Get existing user or create new one."""
    
    @abstractmethod
    def update_user(self, user_id: str, display_name: str) -> bool:
        """Update user display name."""
    
    @abstractmethod
    def delete_user(self, user_id: str) -> bool:
        """Delete user and all related data."""
    
    # AppWindow operations
    @abstractmethod
    def create_app_window(self, process_name: str, window_title: str, 
                         window_id: Optional[str] = None) -> AppWindow:
        """Create a new app window."""
    
    @abstractmethod
    def get_app_window(self, window_id: str) -> Optional[AppWindow]:
        """Get app window by ID."""
    
    @abstractmethod
    def get_or_create_app_window(self, process_name: str, window_title: str) -> AppWindow:
        """Get existing app window or create new one based on process and title."""
    
    @abstractmethod
    def update_app_window(self, window_id: str, process_name: Optional[str] = None, 
                         window_title: Optional[str] = None) -> bool:
        """Update app window information."""
    
    @abstractmethod
    def delete_app_window(self, window_id: str) -> bool:
        """Delete app window and all related data."""
    
    # WindowContext operations
    @abstractmethod
    def create_window_context(self, user_id: str, window_id: str, agent_type: str,
                            context_id: Optional[str] = None) -> WindowContext:
        """Create a new window context (session)."""
    
    @abstractmethod
    def get_window_context(self, context_id: str) -> Optional[WindowContext]:
        """Get window context by ID."""
    
    @abstractmethod
    def get_window_contexts_by_window(self, window_id: str, limit: Optional[int] = None) -> List[WindowContext]:
        """Get window contexts for a specific window."""
    
    @abstractmethod
    def get_window_contexts_by_user(self, user_id: str, limit: Optional[int] = None) -> List[WindowContext]:
        """Get window contexts for a specific user."""
    
    @abstractmethod
    def update_window_context_message_count(self, context_id: str) -> bool:
        """Update message count for a window context."""
    
    @abstractmethod
    def delete_window_context(self, context_id: str) -> bool:
        """Delete window context and all related messages."""
    
    # Message operations
    @abstractmethod
    def create_message(self, context_id: str, role: MessageRole, type: MessageType,
                      content: str, message_id: Optional[str] = None) -> Message:
        """Create a new message."""
    
    @abstractmethod
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID."""
    
    @abstractmethod
    def get_messages_by_context(self, context_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get messages for a specific context."""
    
    @abstractmethod
    def get_recent_messages(self, context_id: str, limit: int = 10) -> List[Message]:
        """Get recent messages for a context."""
    
    @abstractmethod
    def delete_message(self, message_id: str) -> bool:
        """Delete a message."""
    
    # Utility methods
    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
    
    @abstractmethod
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old data beyond specified days."""


class IDatabaseManager(ABC):
    """Interface for low-level database management."""
    
    @abstractmethod
    def initialize_database(self) -> bool:
        """Initialize database and create tables."""
    
    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results."""
    
    @abstractmethod
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows."""
    
    @abstractmethod
    def execute_batch(self, query: str, params_list: List[tuple]) -> int:
        """Execute batch operations."""
    
    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
    
    @abstractmethod
    def cleanup_database(self) -> bool:
        """Clean up database connections and resources."""


class IMigrationManager(ABC):
    """Interface for database migration management."""
    
    @abstractmethod
    def get_current_version(self) -> int:
        """Get current database version."""
    
    @abstractmethod
    def get_latest_version(self) -> int:
        """Get latest available migration version."""
    
    @abstractmethod
    def needs_migration(self) -> bool:
        """Check if database needs migration."""
    
    @abstractmethod
    def migrate_up(self, target_version: Optional[int] = None) -> bool:
        """Apply migrations up to target version."""
    
    @abstractmethod
    def migrate_down(self, target_version: int) -> bool:
        """Rollback migrations to target version."""
    
    @abstractmethod
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status information."""
    
    @abstractmethod
    def validate_database_schema(self) -> bool:
        """Validate that database schema matches expected structure."""