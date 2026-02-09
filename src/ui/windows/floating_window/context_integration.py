"""
Window Context Integration for Floating Window
Provides methods to integrate window context capture and restoration
"""

from typing import Optional
from src.utils.loguru_config import logger, get_logger


class WindowContextIntegration:
    """
    Mixin class to add window context functionality to FloatingWindow.
    
    This class provides methods to:
    1. Capture window context when floating window is shown
    2. Restore window context when processing is complete
    3. Inject text back to the original window
    """
    
    def __init__(self, hotkey_manager=None):
        """
        Initialize window context integration.
        
        Args:
            hotkey_manager: HotkeyManager instance with window context manager
        """
        self.logger = get_logger(__name__)
        self.hotkey_manager = hotkey_manager
        self._captured_context = None
        
        self.logger.info("WindowContextIntegration initialized")
    
    def get_captured_context(self):
        """
        Get the window context captured by hotkey manager.
        
        Returns:
            WindowContext object or None
        """
        if self.hotkey_manager:
            return self.hotkey_manager.get_current_window_context()
        return None
    
    def capture_current_context(self, trigger_source: str = "manual"):
        """
        Manually capture current window context.
        
        Args:
            trigger_source: Source identifier for the capture
            
        Returns:
            WindowContext object or None
        """
        if self.hotkey_manager and self.hotkey_manager.window_context_manager:
            context = self.hotkey_manager.window_context_manager.capture_context(
                trigger_source=trigger_source
            )
            self._captured_context = context
            return context
        return None
    
    def restore_original_window(self, context=None) -> bool:
        """
        Restore focus to the original window.
        
        Args:
            context: WindowContext to restore, or None to use captured context
            
        Returns:
            True if restoration successful
        """
        try:
            # Use provided context or get from hotkey manager
            target_context = context or self.get_captured_context()
            
            if not target_context:
                self.logger.warning("No window context to restore")
                return False
            
            self.logger.info(f"Restoring focus to: {target_context.get_display_name()}")
            
            # Restore via hotkey manager
            if self.hotkey_manager:
                success = self.hotkey_manager.restore_window_context(target_context)
                if success:
                    self.logger.info("Window focus restored successfully")
                else:
                    self.logger.error("Failed to restore window focus")
                return success
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error restoring window: {e}")
            return False
    
    def inject_to_original_window(self, text: str, restore_focus: bool = True) -> bool:
        """
        Inject text to the original window that triggered the hotkey.
        
        Args:
            text: Text to inject
            restore_focus: Whether to restore focus before injection
            
        Returns:
            True if injection successful
        """
        try:
            if not text:
                self.logger.warning("No text to inject")
                return False
            
            # Get the original window context
            context = self.get_captured_context()
            if not context:
                self.logger.warning("No window context available for injection")
                # Fall back to injecting to current active window
                return self._inject_to_active_window(text)
            
            self.logger.info(f"Injecting text to: {context.get_display_name()}")
            
            # Restore focus to original window if requested
            if restore_focus:
                if not self.restore_original_window(context):
                    self.logger.warning("Failed to restore focus, attempting injection anyway")
                
                # Small delay to ensure window is focused
                import time
                time.sleep(0.1)
            
            # Inject text
            return self._inject_to_active_window(text)
            
        except Exception as e:
            self.logger.error(f"Error injecting to original window: {e}")
            return False
    
    def _inject_to_active_window(self, text: str) -> bool:
        """
        Inject text to the currently active window.
        
        Args:
            text: Text to inject
            
        Returns:
            True if injection successful
        """
        try:
            # Use system service if available
            if hasattr(self, 'system_service') and self.system_service:
                result = self.system_service.inject_text(text)
                return result.success
            
            # Fallback: use pynput directly
            from pynput.keyboard import Controller
            keyboard = Controller()
            keyboard.type(text)
            return True
            
        except Exception as e:
            self.logger.error(f"Text injection failed: {e}")
            return False
    
    def get_context_info(self) -> dict:
        """
        Get information about the current window context.
        
        Returns:
            Dictionary with context information
        """
        context = self.get_captured_context()
        if not context:
            return {"has_context": False}
        
        return {
            "has_context": True,
            "window_title": context.title,
            "process_name": context.process_name,
            "process_id": context.process_id,
            "trigger_source": context.trigger_source,
            "timestamp": context.timestamp,
            "is_valid": context.is_valid()
        }
    
    def clear_context(self):
        """Clear the captured window context"""
        self._captured_context = None
        if self.hotkey_manager and self.hotkey_manager.window_context_manager:
            self.hotkey_manager.window_context_manager.clear_current_context()
        self.logger.debug("Window context cleared")


def add_context_integration_to_window(floating_window, hotkey_manager):
    """
    Add window context integration methods to a FloatingWindow instance.
    
    Args:
        floating_window: FloatingWindow instance
        hotkey_manager: HotkeyManager instance with window context
    """
    try:
        # Create integration instance
        integration = WindowContextIntegration(hotkey_manager)
        
        # Add methods to floating window
        floating_window.get_captured_context = integration.get_captured_context
        floating_window.capture_current_context = integration.capture_current_context
        floating_window.restore_original_window = integration.restore_original_window
        floating_window.inject_to_original_window = integration.inject_to_original_window
        floating_window.get_context_info = integration.get_context_info
        floating_window.clear_context = integration.clear_context
        
        # Store integration instance
        floating_window._context_integration = integration
        
        logger.info("Window context integration added to FloatingWindow")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add context integration: {e}")
        return False
