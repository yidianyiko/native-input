"""
Windows API utilities for clipboard and window management.

This module provides centralized Windows API operations, excluding keyboard
operations which remain in their existing implementations.
"""

import pyperclip
import win32gui
from typing import Optional, Dict, Any
from .loguru_config import get_logger
logger = get_logger()

class ClipboardManager:
    """Simplified clipboard manager using pyperclip for cross-platform compatibility."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def get_text(self) -> Optional[str]:
        """
        Get text from clipboard.
        
        Returns:
            Text from clipboard or None if no text available or error occurred
        """
        try:
            text = pyperclip.paste()
            if text:
                logger.info("Successfully retrieved text from clipboard")
                return text
            else:
                logger.info("No text available in clipboard")
                return None
        except Exception as e:
            logger.error("Failed to get text from clipboard")
            return None
    
    def set_text(self, text: str) -> bool:
        """
        Set text to clipboard.
        
        Args:
            text: Text to set in clipboard
            
        Returns:
            True if successful, False otherwise
        """
        try:
            pyperclip.copy(text)
            logger.info("Successfully set text to clipboard")
            return True
        except Exception as e:
            logger.error("Failed to set text to clipboard")
            return False


class WindowManager:
    """Utility class for Windows window management operations."""
    
    def __init__(self):
        self.logger = get_logger(__name__)
    
    def get_active_window_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the active window.
        
        Returns:
            Dictionary with window information or None if error occurred
            Contains: hwnd, title, class_name
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            window_info = {
                "hwnd": hwnd,
                "title": title,
                "class_name": class_name
            }
            
            logger.info("Retrieved active window info")
            
            return window_info
        except Exception as e:
            logger.error("Failed to get active window info")
            return None
    
    def get_window_rect(self, hwnd: int) -> Optional[Dict[str, int]]:
        """
        Get window rectangle coordinates.
        
        Args:
            hwnd: Window handle
            
        Returns:
            Dictionary with left, top, right, bottom coordinates or None if error
        """
        try:
            rect = win32gui.GetWindowRect(hwnd)
            window_rect = {
                "left": rect[0],
                "top": rect[1], 
                "right": rect[2],
                "bottom": rect[3],
                "width": rect[2] - rect[0],
                "height": rect[3] - rect[1]
            }
            
            logger.info("Retrieved window rectangle")
            
            return window_rect
        except Exception as e:
            logger.error("Failed to get window rectangle")
            return None
    
    def is_window_visible(self, hwnd: int) -> bool:
        """
        Check if a window is visible.
        
        Args:
            hwnd: Window handle
            
        Returns:
            True if window is visible, False otherwise
        """
        try:
            visible = win32gui.IsWindowVisible(hwnd)
            logger.info("Checked window visibility")
            return visible
        except Exception as e:
            logger.error("Failed to check window visibility")
            return False