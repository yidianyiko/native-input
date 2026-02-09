"""Database models for reInput AI input method.

This module defines the data models corresponding to the database tables
as specified in the ER diagram.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class MessageRole(Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(Enum):
    """Message type enumeration."""
    USER_INPUT = "user_input"
    AI_OUTPUT = "ai_output"


@dataclass
class User:
    """User model representing a user in the system."""
    user_id: str
    display_name: str

    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.display_name or not self.display_name.strip():
            raise ValueError("display_name cannot be empty")


@dataclass
class AppWindow:
    """AppWindow model representing an application window."""
    window_id: str
    process_name: str
    window_title: str

    def __post_init__(self):
        """Validate app window data after initialization."""
        if not self.window_id or not self.window_id.strip():
            raise ValueError("window_id cannot be empty")
        if not self.process_name or not self.process_name.strip():
            raise ValueError("process_name cannot be empty")
        if not self.window_title or not self.window_title.strip():
            raise ValueError("window_title cannot be empty")


@dataclass
class WindowContext:
    """WindowContext model representing a conversation session in a window."""
    context_id: str
    user_id: str
    window_id: str
    agent_type: str
    num_messages: int = 0

    def __post_init__(self):
        """Validate window context data after initialization."""
        if not self.context_id or not self.context_id.strip():
            raise ValueError("context_id cannot be empty")
        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not self.window_id or not self.window_id.strip():
            raise ValueError("window_id cannot be empty")
        if not self.agent_type or not self.agent_type.strip():
            raise ValueError("agent_type cannot be empty")
        if self.num_messages < 0:
            raise ValueError("num_messages cannot be negative")


@dataclass
class Message:
    """Message model representing a conversation message."""
    message_id: str
    context_id: str
    role: MessageRole
    type: MessageType
    sequence_number: int
    content: str
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Validate message data after initialization."""
        if not self.message_id or not self.message_id.strip():
            raise ValueError("message_id cannot be empty")
        if not self.context_id or not self.context_id.strip():
            raise ValueError("context_id cannot be empty")
        if not isinstance(self.role, MessageRole):
            raise ValueError("role must be a MessageRole enum")
        if not isinstance(self.type, MessageType):
            raise ValueError("type must be a MessageType enum")
        if self.sequence_number < 0:
            raise ValueError("sequence_number cannot be negative")
        if not self.content or not self.content.strip():
            raise ValueError("content cannot be empty")
        if self.timestamp is None:
            self.timestamp = datetime.now()


# Helper functions for model conversion

def message_role_from_string(role_str: str) -> MessageRole:
    """Convert string to MessageRole enum."""
    try:
        return MessageRole(role_str.lower())
    except ValueError:
        raise ValueError(f"Invalid message role: {role_str}")


def message_type_from_string(type_str: str) -> MessageType:
    """Convert string to MessageType enum."""
    try:
        return MessageType(type_str.lower())
    except ValueError:
        raise ValueError(f"Invalid message type: {type_str}")


def message_role_to_string(role: MessageRole) -> str:
    """Convert MessageRole enum to string."""
    return role.value


def message_type_to_string(type: MessageType) -> str:
    """Convert MessageType enum to string."""
    return type.value