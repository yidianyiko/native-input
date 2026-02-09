"""
System Integration Service
Lightweight coordinator that uses specialized service modules
"""

import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PySide6.QtCore import QObject, Signal

try:
    from src.utils.loguru_config import logger
    from src.services.system.text_injection import TextInjectionService, TextInjectionMethod, InjectionResult
    from src.services.system.clipboard_service import ClipboardService
    from src.services.system.window_service import WindowService, WindowInfo
except ImportError:
    # Fallback for PyInstaller
    from utils.loguru_config import logger
    from services.system.text_injection import TextInjectionService, TextInjectionMethod, InjectionResult
    from services.system.clipboard_service import ClipboardService
    from services.system.window_service import WindowService, WindowInfo

# Platform check
if sys.platform != "win32":
    raise ImportError("SystemIntegrationService is only supported on Windows")


class SystemIntegrationService(QObject):
    """
    Lightweight system integration coordinator that delegates to specialized services
    """
    
    # Signals
    text_injected = Signal(str, bool)  # text, success
    window_changed = Signal(object)  # WindowInfo
    clipboard_changed = Signal(str)  # new_content
    
    def __init__(self):
        super().__init__()
        self.logger = logger
        
        # Initialize specialized services
        self.text_injection_service = TextInjectionService()
        self.clipboard_service = ClipboardService()
        self.window_service = WindowService()
        
        # Connect signals from services to our signals
        self.text_injection_service.text_injected.connect(self.text_injected)
        self.window_service.window_changed.connect(self.window_changed)
        self.clipboard_service.clipboard_changed.connect(self.clipboard_changed)
        
        logger.info("SystemIntegrationService initialized with modular services")
    
    def inject_text(self, text: str, target_window: Optional[WindowInfo] = None) -> InjectionResult:
        """
        Inject text using the text injection service
        
        Args:
            text: Text to inject
            target_window: Target window info (None for active window)
            
        Returns:
            InjectionResult with success status and method used
        """
        return self.text_injection_service.inject_text(text, target_window)
    
    def capture_selected_text(self, timeout: float = 0.5) -> Optional[str]:
        """
        Capture currently selected text from active application
        
        Args:
            timeout: Maximum time to wait for clipboard operation
            
        Returns:
            Selected text or None if no text is selected
        """
        return self.clipboard_service.capture_selected_text(timeout)
    
    def get_active_window_info(self) -> Optional[WindowInfo]:
        """
        Get information about the currently active window
        
        Returns:
            WindowInfo object with window details or None if failed
        """
        return self.window_service.get_active_window_info()
    
    def focus_window(self, window_info: WindowInfo) -> bool:
        """Focus the specified window"""
        return self.window_service.focus_window(window_info)
    
    def is_window_responsive(self, window_info: WindowInfo, timeout: float = 1.0) -> bool:
        """Check if window is responsive"""
        return self.window_service.is_window_responsive(window_info, timeout)
    
    def get_cursor_position(self) -> tuple[int, int]:
        """Get current cursor position"""
        return self.window_service.get_cursor_position()
    
    def monitor_clipboard_changes(self, callback: callable) -> bool:
        """
        Monitor clipboard changes
        """
        return self.clipboard_service.monitor_changes(callback)
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up SystemIntegrationService")
            
            # Cleanup specialized services
            if hasattr(self, 'text_injection_service'):
                self.text_injection_service.cleanup()
            
            if hasattr(self, 'clipboard_service'):
                self.clipboard_service.cleanup()
            
            if hasattr(self, 'window_service'):
                self.window_service.cleanup()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_system_integration_service() -> Optional[SystemIntegrationService]:
    """Create and initialize system integration service"""
    try:
        return SystemIntegrationService()
    except Exception as e:
        logger.error(f"Failed to create SystemIntegrationService: {e}")
        return None
