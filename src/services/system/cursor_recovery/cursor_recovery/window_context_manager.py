"""
Window Context Manager for cursor position recovery.

This module manages the capture, validation, and restoration of window context
when the floating window is invoked via hotkey.
"""

import time

from PySide6.QtCore import QObject

from ...platform_integration.system_integration import SystemIntegrationService
from src.utils.loguru_config import logger, get_logger
from .models import ContextValidationResult, WindowContext, WindowInfo


class WindowContextManager(QObject):
    """
    Manages window context capture and restoration for cursor position recovery.

    This class is responsible for:
    - Capturing the current window context when floating window is invoked
    - Validating that captured context is still valid
    - Restoring focus and context when text insertion is complete
    """

    def __init__(self, system_service: SystemIntegrationService):
        super().__init__()
        self.logger = get_logger(__name__)
        self.system_service = system_service

        logger.info("WindowContextManager initialized")

    def capture_context(self) -> WindowContext | None:
        """
        Capture the current window context including active window and cursor position.

        Returns:
            WindowContext if successful, None if capture failed
        """
        # Performance monitoring removed during loguru migration
        try:
                # Get active window information
                window_info = self.system_service.get_active_window_info()
                if not window_info:
                    logger.error("Failed to get active window info")
                    return None

                # Convert SystemIntegrationService WindowInfo to our WindowInfo model
                context_window_info = self._convert_window_info(window_info)

                # Create window context
                context = WindowContext(
                    window_info=context_window_info, timestamp=time.time()
                )

                logger.info(f" Context captured for window: {window_info.title[:30]}...")

                return context

        except Exception as e:
            logger.error(f"Context capture failed: {str(e)}",
                extra={"error": str(e)})
            return None

    def validate_context(self, context: WindowContext) -> ContextValidationResult:
        """
        Validate that the captured context is still valid.

        Args:
            context: The WindowContext to validate

        Returns:
            ContextValidationResult indicating validation status
        """
        if not context:
            return ContextValidationResult.INVALID

        # First check basic validation (expiration, etc.)
        basic_result = context.validate_basic()
        if basic_result != ContextValidationResult.VALID:
            return basic_result

        try:
            # Check if window still exists and is responsive
            if not self._is_window_still_valid(context.window_info):
                context.invalidate(ContextValidationResult.WINDOW_CLOSED)
                return ContextValidationResult.WINDOW_CLOSED

            # Check if window properties have changed significantly
            current_window = self.system_service.get_active_window_info()
            if current_window and current_window.hwnd != context.window_info.hwnd:
                # Window focus has changed - this might be expected behavior
                logger.info("Active window changed during processing")
                # Don't invalidate - we can still restore to original window

            return ContextValidationResult.VALID

        except Exception as e:
            logger.error(f"Context validation failed: {str(e)}",
                extra={"error": str(e)})
            context.invalidate(ContextValidationResult.INVALID)
            return ContextValidationResult.INVALID

    def restore_context(self, context: WindowContext) -> bool:
        """
        Restore the window context by focusing the original window.

        Args:
            context: The WindowContext to restore

        Returns:
            True if restoration was successful, False otherwise
        """
        if not context or not context.is_valid:
            logger.warning("Cannot restore invalid context")
            return False

        # Performance monitoring removed during loguru migration
        try:
                # Validate context before restoration
                validation_result = self.validate_context(context)
                if validation_result != ContextValidationResult.VALID:
                    logger.warning(f"Context validation failed: {validation_result.value}")

                    # Try to restore anyway if window still exists
                    if validation_result != ContextValidationResult.WINDOW_CLOSED:
                        return self._attempt_restoration(context)
                    return False

                return self._attempt_restoration(context)

        except Exception as e:
            logger.error(f"Context restoration failed: {str(e)}",
                extra={"error": str(e)})
            return False

    def _attempt_restoration(self, context: WindowContext) -> bool:
        """
        Attempt to restore window focus and context.

        Args:
            context: The WindowContext to restore

        Returns:
            True if restoration was successful, False otherwise
        """
        try:
            # Convert our WindowInfo back to SystemIntegrationService WindowInfo
            system_window_info = self._convert_to_system_window_info(
                context.window_info
            )

            # Focus the original window
            focus_success = self.system_service.focus_window(system_window_info)

            if focus_success:
                logger.info(f" Context restored for window: {context.window_info.title[:30]}...")
                return True
            else:
                logger.warning(f"Failed to focus window: {context.window_info.title[:30]}...")
                return False

        except Exception as e:
            logger.error(f"Restoration attempt failed: {str(e)}",
                extra={"error": str(e)})
            return False

    def _is_window_still_valid(self, window_info: WindowInfo) -> bool:
        """
        Check if a window is still valid and accessible.

        Args:
            window_info: The WindowInfo to check

        Returns:
            True if window is still valid, False otherwise
        """
        try:
            # Convert to system window info for validation
            system_window_info = self._convert_to_system_window_info(window_info)

            # Use system service to check if window is responsive
            return self.system_service.is_window_responsive(system_window_info)

        except Exception as e:
            logger.error(f"Window validation failed: {str(e)}",
                extra={"hwnd": window_info.hwnd, "error": str(e)})
            return False

    def _convert_window_info(self, system_window_info) -> WindowInfo:
        """
        Convert SystemIntegrationService WindowInfo to our WindowInfo model.

        Args:
            system_window_info: WindowInfo from SystemIntegrationService

        Returns:
            Our WindowInfo model instance
        """
        # Get window rectangle (we'll need to call Windows API for this)
        try:
            import win32gui

            rect = win32gui.GetWindowRect(system_window_info.hwnd)
        except:
            rect = (0, 0, 0, 0)  # Default if we can't get rect

        return WindowInfo(
            hwnd=system_window_info.hwnd,
            title=system_window_info.title,
            class_name=system_window_info.class_name,
            process_id=system_window_info.process_id,
            thread_id=0,  # We don't have thread_id in system service, will need to get it
            rect=rect,
            is_visible=True,  # Assume visible if it's active
            is_enabled=True,  # Assume enabled if it's active
        )

    def _convert_to_system_window_info(self, window_info: WindowInfo):
        """
        Convert our WindowInfo model to SystemIntegrationService WindowInfo.

        Args:
            window_info: Our WindowInfo model instance

        Returns:
            SystemIntegrationService WindowInfo instance
        """
        from ...platform_integration.system_integration import (
            WindowInfo as SystemWindowInfo)

        return SystemWindowInfo(
            hwnd=window_info.hwnd,
            title=window_info.title,
            class_name=window_info.class_name,
            process_id=window_info.process_id,
            process_name="",  # We don't store process name, system service can get it
            is_active=False,  # Will be determined by system service
        )
