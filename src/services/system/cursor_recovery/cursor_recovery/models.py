"""
Core data models for cursor position recovery functionality.

This module defines the data structures used to capture, store, and validate
window context, cursor position, and focus chain information.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.utils.loguru_config import logger, get_logger

logger = get_logger(__name__)


class ContextValidationResult(Enum):
    """Results of context validation checks"""

    VALID = "valid"
    EXPIRED = "expired"
    WINDOW_CLOSED = "window_closed"
    WINDOW_CHANGED = "window_changed"
    INVALID = "invalid"


@dataclass
class WindowInfo:
    """Information about a window"""

    hwnd: int
    title: str
    class_name: str
    process_id: int
    thread_id: int
    rect: tuple[int, int, int, int]  # left, top, right, bottom
    is_visible: bool = True
    is_enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "hwnd": self.hwnd,
            "title": self.title,
            "class_name": self.class_name,
            "process_id": self.process_id,
            "thread_id": self.thread_id,
            "rect": self.rect,
            "is_visible": self.is_visible,
            "is_enabled": self.is_enabled,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WindowInfo":
        """Create from dictionary"""
        return cls(**data)


@dataclass
class CaretInfo:
    """Information about cursor/caret position"""

    screen_x: int
    screen_y: int
    text_position: int | None = None
    selection_start: int | None = None
    selection_end: int | None = None
    control_hwnd: int | None = None
    timestamp: float = field(default_factory=time.time)

    def has_selection(self) -> bool:
        """Check if there is text selection"""
        return (
            self.selection_start is not None
            and self.selection_end is not None
            and self.selection_start != self.selection_end
        )

    def selection_length(self) -> int:
        """Get length of selected text"""
        if self.has_selection():
            return abs(self.selection_end - self.selection_start)
        return 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "screen_x": self.screen_x,
            "screen_y": self.screen_y,
            "text_position": self.text_position,
            "selection_start": self.selection_start,
            "selection_end": self.selection_end,
            "control_hwnd": self.control_hwnd,
            "timestamp": self.timestamp,
        }


@dataclass
class FocusChain:
    """Information about window focus chain"""

    active_window: int
    focused_control: int | None = None
    foreground_window: int = 0
    timestamp: float = field(default_factory=time.time)

    def is_expired(self, max_age_seconds: float = 30.0) -> bool:
        """Check if focus chain is expired"""
        return time.time() - self.timestamp > max_age_seconds

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "active_window": self.active_window,
            "focused_control": self.focused_control,
            "foreground_window": self.foreground_window,
            "timestamp": self.timestamp,
        }


@dataclass
class WindowContext:
    """Complete context of the original window and cursor state"""

    window_info: WindowInfo
    caret_info: CaretInfo | None = None
    focus_chain: FocusChain | None = None
    selected_text: str | None = None
    timestamp: float = field(default_factory=time.time)
    is_valid: bool = True
    validation_result: ContextValidationResult = ContextValidationResult.VALID

    def is_expired(self, max_age_seconds: float = 30.0) -> bool:
        """Check if context is expired based on timestamp"""
        return time.time() - self.timestamp > max_age_seconds

    def invalidate(
        self, reason: ContextValidationResult = ContextValidationResult.INVALID
    ) -> None:
        """Mark context as invalid with reason"""
        self.is_valid = False
        self.validation_result = reason
        logger.info(f" Context invalidated: {reason.value}")

    def validate_basic(self) -> ContextValidationResult:
        """Perform basic validation checks without Windows API calls"""
        if not self.is_valid:
            return self.validation_result

        if self.is_expired():
            self.invalidate(ContextValidationResult.EXPIRED)
            return ContextValidationResult.EXPIRED

        return ContextValidationResult.VALID

    def get_cursor_screen_position(self) -> tuple[int, int] | None:
        """Get cursor screen position if available"""
        if self.caret_info:
            return (self.caret_info.screen_x, self.caret_info.screen_y)
        return None

    def get_text_position(self) -> int | None:
        """Get text cursor position if available"""
        if self.caret_info:
            return self.caret_info.text_position
        return None

    def has_text_selection(self) -> bool:
        """Check if there is selected text"""
        return (
            self.selected_text is not None
            and len(self.selected_text) > 0
            and self.caret_info is not None
            and self.caret_info.has_selection()
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "window_info": self.window_info.to_dict(),
            "caret_info": self.caret_info.to_dict() if self.caret_info else None,
            "focus_chain": self.focus_chain.to_dict() if self.focus_chain else None,
            "selected_text": self.selected_text,
            "timestamp": self.timestamp,
            "is_valid": self.is_valid,
            "validation_result": self.validation_result.value,
        }

    def to_json(self) -> str:
        """Convert to JSON string for logging/debugging"""
        try:
            return json.dumps(self.to_dict(), indent=2)
        except Exception as e:
            logger.exception(" Failed to serialize WindowContext to JSON")
            return f"<WindowContext hwnd={self.window_info.hwnd} valid={self.is_valid}>"

    def __str__(self) -> str:
        """String representation for debugging"""
        return (
            f"WindowContext(hwnd={self.window_info.hwnd}, "
            f"title='{self.window_info.title[:30]}...', "
            f"valid={self.is_valid}, "
            f"has_caret={self.caret_info is not None}, "
            f"has_selection={self.has_text_selection()}"
        )


# Validation helper functions
def validate_hwnd(hwnd: int) -> bool:
    """Basic validation for window handle"""
    return isinstance(hwnd, int) and hwnd > 0


def validate_screen_coordinates(x: int, y: int) -> bool:
    """Basic validation for screen coordinates"""
    return (
        isinstance(x, int)
        and isinstance(y, int)
        and -32768 <= x <= 32767
        and -32768 <= y <= 32767
    )


def validate_text_position(position: int) -> bool:
    """Basic validation for text position"""
    return isinstance(position, int) and position >= 0
