"""High-level database service for reInput AI input method.

This module provides high-level CRUD operations and business logic
for database interactions using the models and database manager.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from .database_manager import DatabaseManager
from .models import (
    User, AppWindow, WindowContext, Message,
    MessageRole, MessageType,
    message_role_from_string, message_type_from_string,
    message_role_to_string, message_type_to_string
)
from ...utils.loguru_config import get_logger

logger = get_logger(__name__)


class DatabaseService:
    """High-level database service providing CRUD operations."""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Initialize database service.
        
        Args:
            db_manager: DatabaseManager instance. If None, creates a new one.
        """
        self.db_manager = db_manager or DatabaseManager()
        self._ensure_initialized()
        
        logger.info("DatabaseService initialized")
    
    def _ensure_initialized(self):
        """Ensure database is initialized."""
        if not self.db_manager.initialize_database():
            raise RuntimeError("Failed to initialize database")
    
    # User operations
    
    def create_user(self, display_name: str, user_id: Optional[str] = None) -> User:
        """Create a new user.
        
        Args:
            display_name: User display name
            user_id: Optional user ID. If None, generates a UUID.
            
        Returns:
            Created User object
        """
        if user_id is None:
            user_id = str(uuid.uuid4())
        
        user = User(user_id=user_id, display_name=display_name)
        
        try:
            self.db_manager.execute_update(
                "INSERT INTO users (user_id, display_name) VALUES (?, ?)",
                (user.user_id, user.display_name)
            )
            logger.info(f"Created user: {user.user_id}")
            return user
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object if found, None otherwise
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT user_id, display_name FROM users WHERE user_id = ?",
                (user_id,)
            )
            if results:
                row = results[0]
                return User(user_id=row['user_id'], display_name=row['display_name'])
            return None
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    def get_or_create_user(self, user_id: str, display_name: str) -> User:
        """Get existing user or create new one.
        
        Args:
            user_id: User ID
            display_name: User display name
            
        Returns:
            User object
        """
        user = self.get_user(user_id)
        if user is None:
            user = self.create_user(display_name, user_id)
        return user
    
    def update_user(self, user_id: str, display_name: str) -> bool:
        """Update user display name.
        
        Args:
            user_id: User ID
            display_name: New display name
            
        Returns:
            True if updated, False if user not found
        """
        try:
            rows_affected = self.db_manager.execute_update(
                "UPDATE users SET display_name = ? WHERE user_id = ?",
                (display_name, user_id)
            )
            if rows_affected > 0:
                logger.info(f"Updated user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user and all related data.
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted, False if user not found
        """
        try:
            rows_affected = self.db_manager.execute_update(
                "DELETE FROM users WHERE user_id = ?",
                (user_id,)
            )
            if rows_affected > 0:
                logger.info(f"Deleted user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    # AppWindow operations
    
    def create_app_window(self, process_name: str, window_title: str, 
                         window_id: Optional[str] = None) -> AppWindow:
        """Create a new app window.
        
        Args:
            process_name: Process name
            window_title: Window title
            window_id: Optional window ID. If None, generates a UUID.
            
        Returns:
            Created AppWindow object
        """
        if window_id is None:
            window_id = str(uuid.uuid4())
        
        app_window = AppWindow(
            window_id=window_id,
            process_name=process_name,
            window_title=window_title
        )
        
        try:
            self.db_manager.execute_update(
                "INSERT INTO app_windows (window_id, process_name, window_title) VALUES (?, ?, ?)",
                (app_window.window_id, app_window.process_name, app_window.window_title)
            )
            logger.info(f"Created app window: {app_window.window_id}")
            return app_window
        except Exception as e:
            logger.error(f"Failed to create app window: {e}")
            raise
    
    def get_app_window(self, window_id: str) -> Optional[AppWindow]:
        """Get app window by ID.
        
        Args:
            window_id: Window ID
            
        Returns:
            AppWindow object if found, None otherwise
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT window_id, process_name, window_title FROM app_windows WHERE window_id = ?",
                (window_id,)
            )
            if results:
                row = results[0]
                return AppWindow(
                    window_id=row['window_id'],
                    process_name=row['process_name'],
                    window_title=row['window_title']
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get app window {window_id}: {e}")
            raise
    
    def get_or_create_app_window(self, process_name: str, window_title: str) -> AppWindow:
        """Get existing app window or create new one based on process and title.
        
        Args:
            process_name: Process name
            window_title: Window title
            
        Returns:
            AppWindow object
        """
        try:
            # Try to find existing window
            results = self.db_manager.execute_query(
                "SELECT window_id, process_name, window_title FROM app_windows WHERE process_name = ? AND window_title = ?",
                (process_name, window_title)
            )
            if results:
                row = results[0]
                return AppWindow(
                    window_id=row['window_id'],
                    process_name=row['process_name'],
                    window_title=row['window_title']
                )
            
            # Create new window if not found
            return self.create_app_window(process_name, window_title)
        except Exception as e:
            logger.error(f"Failed to get or create app window: {e}")
            raise
    
    def update_app_window(self, window_id: str, process_name: Optional[str] = None, 
                         window_title: Optional[str] = None) -> bool:
        """Update app window information.
        
        Args:
            window_id: Window ID
            process_name: New process name (optional)
            window_title: New window title (optional)
            
        Returns:
            True if updated, False if window not found
        """
        if process_name is None and window_title is None:
            return False
        
        try:
            updates = []
            params = []
            
            if process_name is not None:
                updates.append("process_name = ?")
                params.append(process_name)
            
            if window_title is not None:
                updates.append("window_title = ?")
                params.append(window_title)
            
            params.append(window_id)
            
            query = f"UPDATE app_windows SET {', '.join(updates)} WHERE window_id = ?"
            rows_affected = self.db_manager.execute_update(query, tuple(params))
            
            if rows_affected > 0:
                logger.info(f"Updated app window {window_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update app window {window_id}: {e}")
            raise
    
    def delete_app_window(self, window_id: str) -> bool:
        """Delete app window and all related data.
        
        Args:
            window_id: Window ID
            
        Returns:
            True if deleted, False if window not found
        """
        try:
            rows_affected = self.db_manager.execute_update(
                "DELETE FROM app_windows WHERE window_id = ?",
                (window_id,)
            )
            if rows_affected > 0:
                logger.info(f"Deleted app window {window_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete app window {window_id}: {e}")
            raise
    
    # WindowContext operations
    
    def create_window_context(self, user_id: str, window_id: str, agent_type: str,
                            context_id: Optional[str] = None) -> WindowContext:
        """Create a new window context (session).
        
        Args:
            user_id: User ID
            window_id: Window ID
            agent_type: Agent type
            context_id: Optional context ID. If None, generates a UUID.
            
        Returns:
            Created WindowContext object
        """
        if context_id is None:
            context_id = str(uuid.uuid4())
        
        window_context = WindowContext(
            context_id=context_id,
            user_id=user_id,
            window_id=window_id,
            agent_type=agent_type,
            num_messages=0
        )
        
        try:
            self.db_manager.execute_update(
                "INSERT INTO window_contexts (context_id, user_id, window_id, agent_type, num_messages) VALUES (?, ?, ?, ?, ?)",
                (window_context.context_id, window_context.user_id, window_context.window_id, 
                 window_context.agent_type, window_context.num_messages)
            )
            logger.info(f"Created window context: {window_context.context_id}")
            return window_context
        except Exception as e:
            logger.error(f"Failed to create window context: {e}")
            raise
    
    def get_window_context(self, context_id: str) -> Optional[WindowContext]:
        """Get window context by ID.
        
        Args:
            context_id: Context ID
            
        Returns:
            WindowContext object if found, None otherwise
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT context_id, user_id, window_id, agent_type, num_messages FROM window_contexts WHERE context_id = ?",
                (context_id,)
            )
            if results:
                row = results[0]
                return WindowContext(
                    context_id=row['context_id'],
                    user_id=row['user_id'],
                    window_id=row['window_id'],
                    agent_type=row['agent_type'],
                    num_messages=row['num_messages']
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get window context {context_id}: {e}")
            raise
    
    def get_window_contexts_by_window(self, window_id: str, limit: Optional[int] = None) -> List[WindowContext]:
        """Get window contexts for a specific window.
        
        Args:
            window_id: Window ID
            limit: Optional limit on number of results
            
        Returns:
            List of WindowContext objects
        """
        try:
            query = "SELECT context_id, user_id, window_id, agent_type, num_messages FROM window_contexts WHERE window_id = ? ORDER BY context_id DESC"
            params = (window_id,)
            
            if limit is not None:
                query += " LIMIT ?"
                params = (window_id, limit)
            
            results = self.db_manager.execute_query(query, params)
            return [
                WindowContext(
                    context_id=row['context_id'],
                    user_id=row['user_id'],
                    window_id=row['window_id'],
                    agent_type=row['agent_type'],
                    num_messages=row['num_messages']
                )
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to get window contexts for window {window_id}: {e}")
            raise
    
    def get_window_contexts_by_user(self, user_id: str, limit: Optional[int] = None) -> List[WindowContext]:
        """Get window contexts for a specific user.
        
        Args:
            user_id: User ID
            limit: Optional limit on number of results
            
        Returns:
            List of WindowContext objects
        """
        try:
            query = "SELECT context_id, user_id, window_id, agent_type, num_messages FROM window_contexts WHERE user_id = ? ORDER BY context_id DESC"
            params = (user_id,)
            
            if limit is not None:
                query += " LIMIT ?"
                params = (user_id, limit)
            
            results = self.db_manager.execute_query(query, params)
            return [
                WindowContext(
                    context_id=row['context_id'],
                    user_id=row['user_id'],
                    window_id=row['window_id'],
                    agent_type=row['agent_type'],
                    num_messages=row['num_messages']
                )
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to get window contexts for user {user_id}: {e}")
            raise
    
    def update_window_context_message_count(self, context_id: str) -> bool:
        """Update message count for a window context.
        
        Args:
            context_id: Context ID
            
        Returns:
            True if updated, False if context not found
        """
        try:
            rows_affected = self.db_manager.execute_update(
                "UPDATE window_contexts SET num_messages = (SELECT COUNT(*) FROM messages WHERE context_id = ?) WHERE context_id = ?",
                (context_id, context_id)
            )
            if rows_affected > 0:
                logger.debug(f"Updated message count for context {context_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update message count for context {context_id}: {e}")
            raise
    
    def delete_window_context(self, context_id: str) -> bool:
        """Delete window context and all related messages.
        
        Args:
            context_id: Context ID
            
        Returns:
            True if deleted, False if context not found
        """
        try:
            rows_affected = self.db_manager.execute_update(
                "DELETE FROM window_contexts WHERE context_id = ?",
                (context_id,)
            )
            if rows_affected > 0:
                logger.info(f"Deleted window context {context_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete window context {context_id}: {e}")
            raise
    
    # Message operations
    
    def create_message(self, context_id: str, role: MessageRole, type: MessageType,
                      content: str, message_id: Optional[str] = None) -> Message:
        """Create a new message.
        
        Args:
            context_id: Context ID
            role: Message role
            type: Message type
            content: Message content
            message_id: Optional message ID. If None, generates a UUID.
            
        Returns:
            Created Message object
        """
        if message_id is None:
            message_id = str(uuid.uuid4())
        
        # Get next sequence number
        sequence_number = self._get_next_sequence_number(context_id)
        
        message = Message(
            message_id=message_id,
            context_id=context_id,
            role=role,
            type=type,
            sequence_number=sequence_number,
            content=content,
            timestamp=datetime.now()
        )
        
        try:
            self.db_manager.execute_update(
                "INSERT INTO messages (message_id, context_id, role, type, sequence_number, content, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (message.message_id, message.context_id, message_role_to_string(message.role),
                 message_type_to_string(message.type), message.sequence_number, message.content,
                 message.timestamp.isoformat())
            )
            
            # Update message count in window context
            self.update_window_context_message_count(context_id)
            
            logger.info(f"Created message: {message.message_id}")
            return message
        except Exception as e:
            logger.error(f"Failed to create message: {e}")
            raise
    
    def _get_next_sequence_number(self, context_id: str) -> int:
        """Get next sequence number for a context.
        
        Args:
            context_id: Context ID
            
        Returns:
            Next sequence number
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT COALESCE(MAX(sequence_number), 0) + 1 as next_seq FROM messages WHERE context_id = ?",
                (context_id,)
            )
            return results[0]['next_seq'] if results else 1
        except Exception as e:
            logger.error(f"Failed to get next sequence number for context {context_id}: {e}")
            return 0
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID.
        
        Args:
            message_id: Message ID
            
        Returns:
            Message object if found, None otherwise
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT message_id, context_id, role, type, sequence_number, content, timestamp FROM messages WHERE message_id = ?",
                (message_id,)
            )
            if results:
                row = results[0]
                return Message(
                    message_id=row['message_id'],
                    context_id=row['context_id'],
                    role=message_role_from_string(row['role']),
                    type=message_type_from_string(row['type']),
                    sequence_number=row['sequence_number'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get message {message_id}: {e}")
            raise
    
    def get_messages_by_context(self, context_id: str, limit: Optional[int] = None) -> List[Message]:
        """Get messages for a specific context.
        
        Args:
            context_id: Context ID
            limit: Optional limit on number of results
            
        Returns:
            List of Message objects ordered by sequence number
        """
        try:
            query = "SELECT message_id, context_id, role, type, sequence_number, content, timestamp FROM messages WHERE context_id = ? ORDER BY sequence_number"
            params = (context_id,)
            
            if limit is not None:
                query += " LIMIT ?"
                params = (context_id, limit)
            
            results = self.db_manager.execute_query(query, params)
            return [
                Message(
                    message_id=row['message_id'],
                    context_id=row['context_id'],
                    role=message_role_from_string(row['role']),
                    type=message_type_from_string(row['type']),
                    sequence_number=row['sequence_number'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                )
                for row in results
            ]
        except Exception as e:
            logger.error(f"Failed to get messages for context {context_id}: {e}")
            raise
    
    def get_recent_messages(self, context_id: str, limit: int = 10) -> List[Message]:
        """Get recent messages for a context.
        
        Args:
            context_id: Context ID
            limit: Number of recent messages to retrieve
            
        Returns:
            List of recent Message objects
        """
        try:
            results = self.db_manager.execute_query(
                "SELECT message_id, context_id, role, type, sequence_number, content, timestamp FROM messages WHERE context_id = ? ORDER BY sequence_number DESC LIMIT ?",
                (context_id, limit)
            )
            messages = [
                Message(
                    message_id=row['message_id'],
                    context_id=row['context_id'],
                    role=message_role_from_string(row['role']),
                    type=message_type_from_string(row['type']),
                    sequence_number=row['sequence_number'],
                    content=row['content'],
                    timestamp=datetime.fromisoformat(row['timestamp'])
                )
                for row in results
            ]
            # Reverse to get chronological order
            return list(reversed(messages))
        except Exception as e:
            logger.error(f"Failed to get recent messages for context {context_id}: {e}")
            raise
    
    def delete_message(self, message_id: str) -> bool:
        """Delete a message.
        
        Args:
            message_id: Message ID
            
        Returns:
            True if deleted, False if message not found
        """
        try:
            # Get context_id before deletion for updating count
            message = self.get_message(message_id)
            if message is None:
                return False
            
            rows_affected = self.db_manager.execute_update(
                "DELETE FROM messages WHERE message_id = ?",
                (message_id,)
            )
            
            if rows_affected > 0:
                # Update message count in window context
                self.update_window_context_message_count(message.context_id)
                logger.info(f"Deleted message {message_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete message {message_id}: {e}")
            raise
    
    # Utility methods
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics."""
        return self.db_manager.get_database_info()
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up old data beyond specified days.
        
        Args:
            days_to_keep: Number of days to keep data
            
        Returns:
            Number of records deleted
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            rows_affected = self.db_manager.execute_update(
                "DELETE FROM messages WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            
            logger.info(f"Cleaned up {rows_affected} old messages")
            return rows_affected
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            raise