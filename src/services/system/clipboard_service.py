"""
Clipboard Service
Handles clipboard operations and text selection capture
"""

import time
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

try:
    from src.services.system.cursor_recovery.cursor_recovery.cursor_tracker import (
        get_focused_control,
        get_text_selection,
    )
except ImportError:
    get_focused_control = None
    get_text_selection = None


class ClipboardService(QObject):
    """
    Service for clipboard operations and text selection capture
    """
    
    # Signals
    clipboard_changed = Signal(str)  # new_content
    
    def __init__(self):
        super().__init__()
        self.logger = logger
        
        # Utility managers
        self.clipboard_manager = ClipboardManager()
        
        # Current clipboard tracking
        self.clipboard_content: str = ""
        
        logger.info("ClipboardService initialized")
    
    def capture_selected_text(self, timeout: float = 0.5) -> Optional[str]:
        """
        Capture currently selected text from active application
        Enhanced version with better error handling and validation
        
        Args:
            timeout: Maximum time to wait for clipboard operation
            
        Returns:
            Selected text or None if no text is selected
        """
        try:
            logger.info("Starting to capture selected text")
            
            # Check if there's text selection before attempting clipboard capture
            selection_detected = self._check_text_selection()
            logger.info(f"Text selection detection result: {selection_detected}")
            
            if not selection_detected:
                logger.info("No text selection detected, skip clipboard capture")
                return None
            
            # Save current clipboard content
            logger.info("Save original clipboard content")
            original_clipboard = self.get_text()
            logger.info(f"Original clipboard content: {repr(original_clipboard)[:100] if original_clipboard else 'None'}")
            
            # Clear clipboard to detect if new content is copied
            logger.info("Clear clipboard")
            clear_success = self.clear()
            logger.info(f"Clipboard clear result: {clear_success}")
            
            # Longer delay to ensure clipboard is fully cleared
            logger.info("Wait for clipboard clearing to complete (0.1s)")
            time.sleep(0.1)
            
            # Verify clipboard is cleared multiple times
            for verify_attempt in range(3):
                after_clear = self.get_text()
                logger.info(f"Verification {verify_attempt + 1} clipboard content after clearing: {repr(after_clear) if after_clear else 'None'}")
                if not after_clear:
                    break
                time.sleep(0.02)
            
            # Send Ctrl+C to copy selected text
            logger.info("Send Ctrl+C key combination (VK route)")
            try:
                keyboard = Controller()
                ctrl_key = Key.ctrl_l
                c_key = KeyCode.from_vk(0x43)  # VK_C
                keyboard.press(ctrl_key)
                time.sleep(0.01)
                keyboard.press(c_key)
                time.sleep(0.01)
                keyboard.release(c_key)
                time.sleep(0.005)
                keyboard.release(ctrl_key)
                key_send_success = True
                logger.info("Ctrl+C sent successfully via VK route")
            except Exception as e:
                logger.error(f"pynput Ctrl+C failed: {e}")
                key_send_success = False
            logger.info(f"Ctrl+C send result: {key_send_success}")
            
            if not key_send_success:
                logger.error("Ctrl+C send failed")
                return None
            
            # Additional delay after sending Ctrl+C
            logger.info("Additional delay after Ctrl+C send (0.1s)")
            time.sleep(0.1)
            
            # Wait for clipboard to be populated
            logger.info(f"Wait for clipboard to be populated (timeout: {timeout}s)")
            start_time = time.time()
            selected_text = None
            check_count = 0
            
            while time.time() - start_time < timeout:
                check_count += 1
                selected_text = self.get_text()
                elapsed = time.time() - start_time
                
                logger.info(f"Clipboard check {check_count} (elapsed: {elapsed:.3f}s): {repr(selected_text)[:100] if selected_text else 'None'}")
                
                if selected_text and selected_text.strip():
                    logger.info("New content detected, exit waiting loop")
                    break
                time.sleep(0.02)
            
            total_elapsed = time.time() - start_time
            logger.info(f"⏱️ Clipboard check completed, total elapsed: {total_elapsed:.3f}s, check count: {check_count}")
            
            # Restore original clipboard content
            logger.info("Restore original clipboard content")
            if original_clipboard:
                restore_success = self.set_text(original_clipboard)
                logger.info(f"Clipboard restore result: {restore_success}")
            elif selected_text:
                # If we got new text, keep it briefly then clear
                logger.info("No original content, briefly retain new content then clear")
                time.sleep(0.1)
                clear_success = self.clear()
                logger.info(f"Final clear result: {clear_success}")
            
            # Final result processing
            if selected_text and selected_text.strip():
                final_text = selected_text.strip()
                logger.info(f"Successfully captured selected text: '{final_text[:50]}...' (length: {len(final_text)})")
                return final_text
            else:
                logger.info("No selected text detected")
                return None
        
        except Exception as e:
            logger.error(f"Exception occurred while capturing selected text: {e}")
            return None
    
    def _check_text_selection(self) -> bool:
        """
        Check if there's currently selected text in the focused control
        
        Returns:
            True if text is selected, False otherwise
        """
        try:
            # Check if cursor tracker functions are available
            if get_focused_control is None or get_text_selection is None:
                logger.info("Cursor tracking function unavailable, skip text selection check")
                return True  # Assume there is selection, continue with clipboard method
            
            # Get the currently focused control
            focused_hwnd = get_focused_control()
            if not focused_hwnd:
                logger.info("No focused control found")
                return False
            
            logger.info(f"Check text selection status of focused control: {focused_hwnd}")
            
            # Get text selection range
            selection = get_text_selection(focused_hwnd)
            if selection is None:
                logger.info("Unable to get text selection information")
                return False
            
            start, end = selection
            has_selection = start != end
            
            logger.info(f"Text selection range: start={start}, end={end}, has_selection={has_selection}")
            
            return has_selection
        
        except Exception as e:
            logger.error(f"Failed to check text selection status: {e}")
            return False  # If check fails, assume no selection, continue with clipboard method
    
    def get_text(self) -> Optional[str]:
        """Get text from clipboard"""
        return self.clipboard_manager.get_text()
    
    def set_text(self, text: str) -> bool:
        """Set text to clipboard"""
        if not text:
            logger.info("Attempting to set empty text to clipboard")
            return False
        
        return self.clipboard_manager.set_text(text)
    
    def clear(self) -> bool:
        """Clear clipboard content"""
        logger.info("Clearing clipboard content")
        return self.clipboard_manager.set_text("")  # Clear by setting empty text
    
    def monitor_changes(self, callback: callable) -> bool:
        """
        Monitor clipboard changes (basic implementation)
        For full implementation, would need a separate thread with clipboard viewer chain
        """
        try:
            current_content = self.get_text()
            if current_content != self.clipboard_content:
                self.clipboard_content = current_content or ""
                if callback:
                    callback(self.clipboard_content)
                self.clipboard_changed.emit(self.clipboard_content)
            return True
        except Exception as e:
            logger.error(f"Failed to monitor clipboard: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleaning up ClipboardService")
            # Any cleanup needed
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def create_clipboard_service() -> Optional[ClipboardService]:
    """Create and initialize clipboard service"""
    try:
        return ClipboardService()
    except Exception as e:
        logger.error(f"Failed to create ClipboardService: {e}")
        return None