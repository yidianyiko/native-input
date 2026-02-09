"""
Window Manager Module - Extracted from FloatingWindow
Handles core window lifecycle and state management.
"""

from enum import Enum
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt

from src.utils.loguru_config import logger, get_logger


class WindowState(Enum):
    """Three-state window system states"""
    INITIAL = "initial"    # 581×120px - Initial state with input area only
    INPUT = "input"        # 581×184px - Input state with separator visible  
    COMPLETE = "complete"   # 581×232px - Complete state with result area visible


class WindowManager(QObject):
    """Manages core window lifecycle and properties."""
    
    # Signals
    state_changed = Signal(object)  # WindowState
    
    def __init__(self, window: QWidget, config_manager):
        super().__init__()
        self.window = window
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self.current_state = WindowState.INITIAL
        
        logger.info(" WindowManager initialized")
    
    def setup_window_flags(self):
        """Setup window properties and flags."""
        try:
            # Set window flags for floating behavior
            self.window.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint |
                Qt.WindowType.Tool
            )
            
            # Set window attributes
            self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            # Avoid suppressing activation so first show can get focus
            self.window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, False)
            
            # Set window title and icon
            self.window.setWindowTitle("AI Input Method Tool")
            
            # Try to set window icon
            from PySide6.QtGui import QIcon
            from pathlib import Path
            
            icon_path = Path(__file__).parent.parent.parent.parent.parent / "resources" / "icons" / "icon.png"
            if icon_path.exists():
                window_icon = QIcon(str(icon_path))
                self.window.setWindowIcon(window_icon)
            
            logger.info(" Window flags configured")
            return True
            
        except Exception as e:
            self.logger.error(f" Failed to setup window flags: {e}")
            return False
    
    def set_state(self, new_state: WindowState):
        """Change window state."""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_changed.emit(new_state)
            
            logger.info(f" State changed: {old_state.value} → {new_state.value}")
    
    def get_state(self) -> WindowState:
        """Get current window state."""
        return self.current_state
    
    def show_window(self):
        """Show the window."""
        try:
            self.window.show()
            self.window.raise_()
            logger.info(" Window shown")
            
        except Exception as e:
            self.logger.error(f" Failed to show window: {e}")
    
    def hide_window(self):
        """Hide the window."""
        try:
            self.window.hide()
            logger.info(" Window hidden")
            
        except Exception as e:
            self.logger.error(f" Failed to hide window: {e}")
    
    def cleanup(self):
        """Clean up window manager resources."""
        try:
            logger.info(" WindowManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f" WindowManager cleanup failed: {e}")