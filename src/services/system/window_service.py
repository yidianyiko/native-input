"""
Window Service
Handles window management operations for Windows platform
"""

import sys
from dataclasses import dataclass
from typing import Optional

from PySide6.QtCore import QObject, Signal

try:
    from src.utils.loguru_config import logger
    from src.utils.windows_utils import WindowManager
except ImportError:
    # Fallback for PyInstaller
    from utils.loguru_config import logger
    from utils.windows_utils import WindowManager

# Platform check
if sys.platform != "win32":
    raise ImportError("WindowService is only supported on Windows")

try:
    import win32api
    import win32con
    import win32gui
    import win32process
    PLATFORM_SUPPORTED = True
except ImportError:
    PLATFORM_SUPPORTED = False


@dataclass
class WindowInfo:
    """Information about a window"""
    hwnd: int
    title: str
    class_name: str
    process_id: int
    process_name: str
    is_active: bool = False


class WindowService(QObject):
    """
    Service for window management operations
    """
    
    # Signals
    window_changed = Signal(object)  # WindowInfo
    
    def __init__(self):
        super().__init__()
        self.logger = logger
        
        if not PLATFORM_SUPPORTED:
            logger.error("Platform not supported")
            raise RuntimeError("Windows platform required")
        
        # Utility managers
        self.window_manager = WindowManager()
        
        # Current window tracking
        self.current_window: Optional[WindowInfo] = None
        
        logger.info("WindowService initialized")
    
    def get_active_window_info(self) -> Optional[WindowInfo]:
        """
        Get information about the currently active window
        
        Returns:
            WindowInfo object with window details or None if failed
        """
        try:
            # Get foreground window handle
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            # Get window title
            title = win32gui.GetWindowText(hwnd)
            
            # Get window class name
            class_name = win32gui.GetClassName(hwnd)
            
            # Get process ID and name
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process_handle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION, False, process_id
                )
                process_name = win32process.GetModuleFileNameEx(
                    process_handle, 0
                ).split("\\")[-1]
                win32api.CloseHandle(process_handle)
            except:
                process_name = "Unknown"
            
            window_info = WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                process_id=process_id,
                process_name=process_name,
                is_active=True,
            )
            
            # Update current window tracking
            if not self.current_window or self.current_window.hwnd != hwnd:
                self.current_window = window_info
                self.window_changed.emit(window_info)
                logger.info(f"Active window changed: {title} ({process_name})")
            
            return window_info
        
        except Exception as e:
            logger.error(f"Failed to get active window info: {e}")
            return None
    
    def focus_window(self, window_info: WindowInfo) -> bool:
        """Focus the specified window"""
        try:
            if not window_info or not window_info.hwnd:
                return False
            
            # Bring window to foreground
            win32gui.SetForegroundWindow(window_info.hwnd)
            logger.info(f"Focused window: {window_info.title}")
            return True
        
        except Exception as e:
            logger.error(f"Exception focusing window: {e}")
            return False
    
    def is_window_responsive(self, window_info: WindowInfo, timeout: float = 1.0) -> bool:
        """Check if window is responsive"""
        try:
            if not window_info or not window_info.hwnd:
                return False
            
            # Send a test message with timeout
            result = win32gui.SendMessageTimeout(
                window_info.hwnd,
                win32con.WM_NULL,
                0,
                0,
                win32con.SMTO_ABORTIFHUNG,
                int(timeout * 1000),  # Convert to milliseconds
            )
            
            return result != (0, 0)
        
        except Exception as e:
            logger.error(f"Failed to check window responsiveness: {e}")
            return False
    
    def get_cursor_position(self) -> tuple[int, int]:
        """Get current cursor position"""
        try:
            x, y = win32api.GetCursorPos()
            return (x, y)
        except Exception as e:
            logger.error(f"Failed to get cursor position: {e}")
            return (0, 0)
    
    def get_window_by_title(self, title: str) -> Optional[WindowInfo]:
        """Find window by title"""
        try:
            # This is a simplified implementation
            # For a full implementation, you would enumerate all windows
            current_window = self.get_active_window_info()
            if current_window and title.lower() in current_window.title.lower():
                return current_window
            return None
        except Exception as e:
            logger.error(f"Failed to find window by title: {e}")
            return None
    
    def get_window_by_process_name(self, process_name: str) -> Optional[WindowInfo]:
        """Find window by process name"""
        try:
            # This is a simplified implementation
            # For a full implementation, you would enumerate all windows
            current_window = self.get_active_window_info()
            if current_window and process_name.lower() in current_window.process_name.lower():
                return current_window
            return None
        except Exception as e:
            logger.error(f"Failed to find window by process name: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up WindowService")
            # Any cleanup needed for Windows API resources
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_window_service() -> Optional[WindowService]:
    """Create and initialize window service"""
    try:
        return WindowService()
    except Exception as e:
        logger.error(f"Failed to create WindowService: {e}")
        return None