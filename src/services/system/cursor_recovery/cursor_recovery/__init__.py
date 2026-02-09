"""
Cursor Position Recovery Module

This module provides functionality for capturing, preserving, and restoring
cursor position and window context when using the AI floating window.
"""

from .cursor_tracker import CursorTracker
from .models import CaretInfo, FocusChain, WindowContext
from .window_context_manager import WindowContextManager

__all__ = [
    "WindowContext",
    "CaretInfo",
    "FocusChain",
    "WindowContextManager",
    "CursorTracker",
]
