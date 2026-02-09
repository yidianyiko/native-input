"""
Text Injection Service
Handles text injection using different methods (SendInput, Clipboard)
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from PySide6.QtCore import QObject, Signal
from pynput.keyboard import Controller, Key, KeyCode

try:
    from src.utils.loguru_config import logger
    from src.utils.windows_utils import ClipboardManager
except ImportError:
    # Fallback for PyInstaller
    from utils.loguru_config import logger
    from utils.windows_utils import ClipboardManager


class TextInjectionMethod(Enum):
    """Available text injection methods"""
    CLIPBOARD = "clipboard"


@dataclass
class InjectionResult:
    """Result of text injection operation"""
    success: bool
    method_used: TextInjectionMethod
    error_message: Optional[str] = None
    injection_time: float = 0.0


class TextInjectionService(QObject):
    """
    Service for injecting text into applications using various methods
    """
    
    # Signals
    text_injected = Signal(str, bool)  # text, success
    
    def __init__(self):
        super().__init__()
        self.logger = logger
        
        # Utility managers
        self.clipboard_manager = ClipboardManager()

        # Injection lock to prevent concurrent clipboard operations
        self._is_injecting = False
        self._last_injection_time = 0
        
        logger.info("TextInjectionService initialized")
    
    def inject_text(self, text: str, target_window=None) -> InjectionResult:
        """
        Inject text using the best available method
        
        Args:
            text: Text to inject
            target_window: Target window info (None for active window)
            
        Returns:
            InjectionResult with success status and method used
        """
        if not text:
            return InjectionResult(False, TextInjectionMethod.CLIPBOARD, "Empty text")
        
        # Prevent concurrent injections (especially important for clipboard method)
        if self._is_injecting:
            logger.warning("Injection already in progress, waiting...")
            # Wait for previous injection to complete (max 1 second)
            wait_count = 0
            while self._is_injecting and wait_count < 20:
                time.sleep(0.05)
                wait_count += 1
            
            if self._is_injecting:
                logger.error("Previous injection did not complete in time")
                return InjectionResult(False, TextInjectionMethod.CLIPBOARD, "Injection timeout")
        
        # Also ensure minimum time between injections
        time_since_last = time.time() - self._last_injection_time
        if time_since_last < 0.15:  # Minimum 150ms between injections
            wait_time = 0.15 - time_since_last
            logger.info(f"Waiting {wait_time:.2f}s before next injection")
            time.sleep(wait_time)
        
        self._is_injecting = True
        start_time = time.time()
        
        logger.info(f"Injecting text via clipboard: '{text[:50]}...' to {getattr(target_window, 'title', 'active window')}")
        
        try:
            # Clipboard-only injection
            try:
                if self._inject_via_clipboard(text, target_window):
                    injection_time = time.time() - start_time
                    logger.info("Text injection successful using Clipboard")
                    self.text_injected.emit(text, True)
                    return InjectionResult(True, TextInjectionMethod.CLIPBOARD, injection_time=injection_time)
            except Exception as e:
                logger.error(f"Clipboard injection failed: {e}")
            
            # Injection failed
            injection_time = time.time() - start_time
            error_msg = "Clipboard injection failed"
            logger.error(error_msg)
            self.text_injected.emit(text, False)
            return InjectionResult(False, TextInjectionMethod.CLIPBOARD, error_msg, injection_time)
        
        finally:
            # Always release the lock and update last injection time
            self._is_injecting = False
            self._last_injection_time = time.time()
    
    # Removed keyboard typing injection method; clipboard injection is the only method
    
    def _inject_via_clipboard(self, text: str, target_window=None) -> bool:
        """
        Inject text using clipboard + Ctrl+V (fallback method)
        
        Args:
            text: Text to inject
            target_window: Target window info (if provided, will focus window first)
        """
        try:
            # Focus target window if specified
            if target_window and hasattr(target_window, 'focus'):
                try:
                    target_window.focus()
                    # Longer delay to ensure window is properly focused
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Failed to focus target window: {e}")
                    # Continue with injection even if focus fails
            
            # Set text to clipboard (no need to save/restore original content)
            if not self.clipboard_manager.set_text(text):
                return False
            
            # Verify clipboard content was set correctly
            time.sleep(0.02)  # Small delay to ensure clipboard is updated
            clipboard_content = self.clipboard_manager.get_text()
            if clipboard_content != text:
                logger.warning(f"Clipboard verification failed. Expected: '{text[:50]}...', Got: '{clipboard_content[:50] if clipboard_content else 'None'}...'")
                # Try to set clipboard again
                self.clipboard_manager.set_text(text)
                time.sleep(0.02)
                clipboard_content = self.clipboard_manager.get_text()
                if clipboard_content != text:
                    logger.error("Clipboard content verification failed after retry")
                    return False
            else:
                logger.info(f"Clipboard content verified: '{text[:50]}...'")
            
            # Small delay to ensure clipboard is set
            time.sleep(0.05)
            
            # Send paste keys using robust virtual-key route
            try:
                keyboard = Controller()
                # Use left Ctrl explicitly; IMEs sometimes ignore generic Ctrl state
                ctrl_key = Key.ctrl_l
                # Use VK code for 'V' to guarantee physical key event instead of character packet
                v_key = KeyCode.from_vk(0x56)  # VK_V

                # Press Ctrl+V with small inter-key delays to ensure modifier is engaged
                keyboard.press(ctrl_key)
                time.sleep(0.01)
                keyboard.press(v_key)
                time.sleep(0.01)
                keyboard.release(v_key)
                time.sleep(0.005)
                keyboard.release(ctrl_key)

                logger.info("Paste sent via VK route (Ctrl_l + VK_V)")

                # Small delay to allow paste to complete
                time.sleep(0.1)

                return True
            except Exception as e:
                logger.error(f"pynput Ctrl+V (VK route) failed: {e}")

                # Fallback: try Shift+Insert (common paste alternative)
                try:
                    keyboard.press(Key.shift)
                    time.sleep(0.01)
                    keyboard.press(Key.insert)
                    time.sleep(0.01)
                    keyboard.release(Key.insert)
                    time.sleep(0.005)
                    keyboard.release(Key.shift)
                    logger.info("Paste sent via fallback Shift+Insert")
                    time.sleep(0.1)
                    return True
                except Exception as e2:
                    logger.error(f"Fallback Shift+Insert failed: {e2}")
                    return False
        
        except Exception as e:
            logger.error(f"Clipboard injection failed: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up TextInjectionService")
            # Any cleanup needed
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_text_injection_service() -> Optional[TextInjectionService]:
    """Create and initialize text injection service"""
    try:
        return TextInjectionService()
    except Exception as e:
        logger.error(f"Failed to create TextInjectionService: {e}")
        return None