"""
Window Context Module
Captures and manages window context information for hotkey triggers
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime
import json

from src.utils.loguru_config import logger, get_logger


@dataclass
class WindowContext:
    """
    Persistent window context information captured at hotkey trigger time.
    
    This class stores all necessary information to identify and restore
    focus to the original window after processing.
    """
    
    # Window identification
    hwnd: int  # Window handle (unique identifier)
    title: str  # Window title
    class_name: str  # Window class name
    
    # Process information
    process_id: int  # Process ID
    process_name: str  # Process executable name (e.g., "chrome.exe")
    
    # Window state
    is_visible: bool  # Whether window was visible
    is_active: bool  # Whether window was active/foreground
    
    # Position information (optional, for future use)
    position: Optional[Dict[str, int]] = None  # {x, y, width, height}
    
    # Metadata
    timestamp: str = ""  # When context was captured
    trigger_source: str = ""  # Which hotkey triggered this (e.g., "QUICK_TRANSLATE")
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WindowContext':
        """Create WindowContext from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'WindowContext':
        """Create WindowContext from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def is_same_window(self, other: 'WindowContext') -> bool:
        """
        Check if this context represents the same window as another.
        
        Uses multiple criteria for robustness:
        1. Same hwnd (most reliable)
        2. Same process_id + class_name (if hwnd changed)
        3. Same process_name + title (fallback)
        """
        if not other:
            return False
        
        # Primary: Same window handle
        if self.hwnd == other.hwnd and self.hwnd != 0:
            return True
        
        # Secondary: Same process and class
        if (self.process_id == other.process_id and 
            self.class_name == other.class_name and
            self.process_id != 0):
            return True
        
        # Tertiary: Same process name and title (less reliable)
        if (self.process_name == other.process_name and 
            self.title == other.title and
            self.process_name != "Unknown"):
            return True
        
        return False
    
    def is_valid(self) -> bool:
        """Check if this context has valid window information"""
        return (
            self.hwnd != 0 and
            self.process_id != 0 and
            self.process_name != "Unknown" and
            bool(self.title or self.class_name)
        )
    
    def get_display_name(self) -> str:
        """Get a human-readable display name for this window"""
        if self.title:
            return f"{self.title} ({self.process_name})"
        return f"{self.class_name} ({self.process_name})"
    
    def __str__(self) -> str:
        """String representation for logging"""
        return (
            f"WindowContext(hwnd={self.hwnd}, "
            f"title='{self.title[:30]}...', "
            f"process={self.process_name}, "
            f"pid={self.process_id})"
        )
    
    def __repr__(self) -> str:
        """Detailed representation"""
        return self.__str__()


class WindowContextManager:
    """
    Manages window context capture and restoration.
    
    This manager works with WindowService to capture window information
    at hotkey trigger time and restore focus later.
    """
    
    def __init__(self, window_service):
        """
        Initialize window context manager.
        
        Args:
            window_service: WindowService instance for window operations
        """
        self.logger = get_logger(__name__)
        self.window_service = window_service
        
        # Current context
        self.current_context: Optional[WindowContext] = None
        
        self.logger.info("WindowContextManager initialized")
    
    def capture_context(self, trigger_source: str = "") -> Optional[WindowContext]:
        """
        Capture current window context.
        
        Args:
            trigger_source: Identifier of what triggered the capture (e.g., hotkey name)
            
        Returns:
            WindowContext object or None if capture failed
        """
        try:
            self.logger.info(f"Capturing window context (trigger: {trigger_source})")
            
            # Get active window info from WindowService
            window_info = self.window_service.get_active_window_info()
            if not window_info:
                self.logger.error("Failed to get active window info")
                return None
            
            # Get window position (optional)
            position = None
            try:
                from src.utils.windows_utils import WindowManager
                win_manager = WindowManager()
                rect = win_manager.get_window_rect(window_info.hwnd)
                if rect:
                    position = {
                        "x": rect["left"],
                        "y": rect["top"],
                        "width": rect["width"],
                        "height": rect["height"]
                    }
            except Exception as e:
                self.logger.warning(f"Failed to get window position: {e}")
            
            # Check if window is visible
            is_visible = True
            try:
                from src.utils.windows_utils import WindowManager
                win_manager = WindowManager()
                is_visible = win_manager.is_window_visible(window_info.hwnd)
            except Exception as e:
                self.logger.warning(f"Failed to check window visibility: {e}")
            
            # Create context
            context = WindowContext(
                hwnd=window_info.hwnd,
                title=window_info.title,
                class_name=window_info.class_name,
                process_id=window_info.process_id,
                process_name=window_info.process_name,
                is_visible=is_visible,
                is_active=window_info.is_active,
                position=position,
                trigger_source=trigger_source
            )
            
            # Validate context
            if not context.is_valid():
                self.logger.warning(f"Captured context is invalid: {context}")
                return None
            
            # Store context
            self.current_context = context
            
            self.logger.info(f"Window context captured: {context.get_display_name()}")
            self.logger.debug(f"Context details: {context}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to capture window context: {e}")
            return None
    
    def restore_context(self, context: Optional[WindowContext] = None) -> bool:
        """
        Restore focus to a previously captured window context.
        
        Args:
            context: WindowContext to restore, or None to use current_context
            
        Returns:
            True if restoration successful, False otherwise
        """
        try:
            # Use provided context or current context
            target_context = context or self.current_context
            if not target_context:
                self.logger.warning("No context to restore")
                return False
            
            self.logger.info(f"Restoring window context: {target_context.get_display_name()}")
            
            # Verify window still exists and is valid
            current_window = self.window_service.get_active_window_info()
            if current_window and current_window.hwnd == target_context.hwnd:
                self.logger.info("Target window is already active")
                return True
            
            # Create WindowInfo object for focus operation
            from src.services.system.window_service import WindowInfo
            window_info = WindowInfo(
                hwnd=target_context.hwnd,
                title=target_context.title,
                class_name=target_context.class_name,
                process_id=target_context.process_id,
                process_name=target_context.process_name,
                is_active=False
            )
            
            # Attempt to focus the window
            success = self.window_service.focus_window(window_info)
            
            if success:
                self.logger.info("Window context restored successfully")
            else:
                self.logger.error("Failed to restore window context")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to restore window context: {e}")
            return False
    
    def get_current_context(self) -> Optional[WindowContext]:
        """Get the current window context"""
        return self.current_context
    
    def clear_current_context(self):
        """Clear the current context"""
        self.current_context = None
        self.logger.debug("Current context cleared")


def create_window_context_manager(window_service) -> Optional[WindowContextManager]:
    """
    Factory function to create WindowContextManager.
    
    Args:
        window_service: WindowService instance
        
    Returns:
        WindowContextManager instance or None if creation failed
    """
    try:
        return WindowContextManager(window_service)
    except Exception as e:
        logger.error(f"Failed to create WindowContextManager: {e}")
        return None
