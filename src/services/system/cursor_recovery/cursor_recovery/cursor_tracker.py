"""
Cursor Tracker for precise cursor position detection and management.

This module provides functionality for tracking and managing cursor position
within text controls using Windows APIs.
"""

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QObject

from src.utils.loguru_config import logger, get_logger
from .models import CaretInfo

# Windows API constants
EM_GETSEL = 0x00B0
EM_SETSEL = 0x00B1
EM_GETLINECOUNT = 0x00BA
EM_LINEFROMCHAR = 0x00C9
EM_LINEINDEX = 0x00BB

WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E

# Control class names that support text operations
TEXT_CONTROL_CLASSES = {
    "Edit",
    "RichEdit",
    "RichEdit20A",
    "RichEdit20W",
    "RichEdit50W",
    "RICHEDIT60W",
    "Scintilla",
    "SciTEWindow",
}


class CursorTracker(QObject):
    """
    Tracks and manages cursor position within text controls.

    This class provides functionality for:
    - Getting current caret position using Windows APIs
    - Setting caret position in text controls
    - Detecting different types of text controls
    - Getting screen cursor position as fallback
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__name__)

        # Load Windows API functions
        self._load_windows_apis()

        logger.info(" CursorTracker initialized")

    def _load_windows_apis(self):
        """Load required Windows API functions"""
        try:
            # User32.dll functions
            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32

            # Define function signatures
            self.user32.GetCaretPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
            self.user32.GetCaretPos.restype = wintypes.BOOL

            self.user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
            self.user32.GetCursorPos.restype = wintypes.BOOL

            self.user32.SendMessageW.argtypes = [
                wintypes.HWND,
                wintypes.UINT,
                wintypes.WPARAM,
                wintypes.LPARAM,
            ]
            self.user32.SendMessageW.restype = ctypes.c_long

            self.user32.GetClassNameW.argtypes = [
                wintypes.HWND,
                wintypes.LPWSTR,
                ctypes.c_int,
            ]
            self.user32.GetClassNameW.restype = ctypes.c_int

            self.user32.GetFocus.argtypes = []
            self.user32.GetFocus.restype = wintypes.HWND

            self.user32.ClientToScreen.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(wintypes.POINT),
            ]
            self.user32.ClientToScreen.restype = wintypes.BOOL

        except Exception as e:
            logger.error(f" Failed to load Windows APIs: {str(e)}",
                extra={"error": str(e)})

    def get_caret_position(self, hwnd: int) -> int | None:
        """
        Get the current text caret position within a text control.

        Args:
            hwnd: Handle to the window/control

        Returns:
            Text position (character index) if successful, None otherwise
        """
        # Performance monitoring removed during loguru migration
        try:
                if not self.is_text_control(hwnd):
                    logger.warning(f" Window {hwnd} is not a recognized text control")
                    return None

                # Try to get selection range (caret position is start of selection)
                result = self.user32.SendMessageW(hwnd, EM_GETSEL, 0, 0)

                if result != 0:
                    # Extract start and end positions from result
                    start_pos = result & 0xFFFF
                    end_pos = (result >> 16) & 0xFFFF

                    logger.info(f" Caret position retrieved: {start_pos}")

                    return start_pos
                else:
                    logger.warning(f" Failed to get selection from control {hwnd}")
                    return None

        except Exception as e:
            logger.error(f" Failed to get caret position: {str(e)}",
                extra={"hwnd": hwnd, "error": str(e)})
            return None

    def set_caret_position(self, hwnd: int, position: int) -> bool:
        """
        Set the caret position within a text control.

        Args:
            hwnd: Handle to the window/control
            position: Character index to set caret to

        Returns:
            True if successful, False otherwise
        """
        # Performance monitoring removed during loguru migration
        try:
            if not self.is_text_control(hwnd):
                logger.warning(f" Window {hwnd} is not a recognized text control")
                return False

            if position < 0:
                logger.warning(f" Invalid position {position}")
                return False

            # Set selection to position (start and end are the same for caret)
            result = self.user32.SendMessageW(hwnd, EM_SETSEL, position, position)

            if result == 0:  # 0 indicates success for EM_SETSEL
                logger.info(f" Caret position set to {position}")
                return True
            else:
                logger.warning(" Failed to set caret position}")
                return False

        except Exception as e:
            logger.error(f" Failed to set caret position: {str(e)}",
                extra={"hwnd": hwnd, "position": position, "error": str(e)})
            return False

    def get_cursor_screen_position(self) -> tuple[int, int]:
        """
        Get the current cursor position on screen as fallback.

        Returns:
            Tuple of (x, y) screen coordinates
        """
        try:
            point = wintypes.POINT()
            if self.user32.GetCursorPos(ctypes.byref(point)):
                logger.info(f" Screen cursor position: ({point.x}, {point.y})",
                    extra={"x": point.x, "y": point.y})
                return (point.x, point.y)
            else:
                logger.error(" Failed to get cursor screen position")
                return (0, 0)

        except Exception as e:
            logger.error(f" Failed to get cursor screen position: {str(e)}",
                extra={"error": str(e)})
            return (0, 0)

    def get_caret_screen_position(self, hwnd: int) -> tuple[int, int] | None:
        """
        Get the caret position in screen coordinates.

        Args:
            hwnd: Handle to the window/control

        Returns:
            Tuple of (x, y) screen coordinates if successful, None otherwise
        """
        try:
            # Get caret position in client coordinates
            caret_point = wintypes.POINT()
            if not self.user32.GetCaretPos(ctypes.byref(caret_point)):
                logger.warning(f" Failed to get caret position for window {hwnd}")
                return None

            # Convert to screen coordinates
            if self.user32.ClientToScreen(hwnd, ctypes.byref(caret_point)):
                logger.info(f" Caret screen position: ({caret_point.x}, {caret_point.y})",
                    extra={"hwnd": hwnd, "x": caret_point.x, "y": caret_point.y})
                return (caret_point.x, caret_point.y)
            else:
                logger.warning(" Failed to convert caret position to screen coordinates")
                return None

        except Exception as e:
            logger.error(f" Failed to get caret screen position: {str(e)}",
                extra={"hwnd": hwnd, "error": str(e)})
            return None

    def is_text_control(self, hwnd: int) -> bool:
        """
        Check if a window is a text control that supports caret operations.

        Args:
            hwnd: Handle to the window/control

        Returns:
            True if it's a recognized text control, False otherwise
        """
        try:
            # Get window class name
            class_name_buffer = ctypes.create_unicode_buffer(256)
            length = self.user32.GetClassNameW(hwnd, class_name_buffer, 256)

            if length > 0:
                class_name = class_name_buffer.value
                is_text_control = class_name in TEXT_CONTROL_CLASSES

                logger.info(f" Window class check: {class_name} -> {is_text_control}")

                return is_text_control
            else:
                logger.warning(f" Failed to get class name for window {hwnd}")
                return False

        except Exception as e:
            logger.error(f" Failed to check if window is text control: {str(e)}",
                extra={"hwnd": hwnd, "error": str(e)})
            return False

    def get_text_selection(self, hwnd: int) -> tuple[int, int] | None:
        """
        Get the current text selection range.

        Args:
            hwnd: Handle to the window/control

        Returns:
            Tuple of (start, end) positions if successful, None otherwise
        """
        try:
            if not self.is_text_control(hwnd):
                return None

            result = self.user32.SendMessageW(hwnd, EM_GETSEL, 0, 0)

            if result != 0:
                start_pos = result & 0xFFFF
                end_pos = (result >> 16) & 0xFFFF

                logger.info(f" Text selection: ({start_pos}, {end_pos})",
                    extra={"hwnd": hwnd, "start": start_pos, "end": end_pos})

                return (start_pos, end_pos)
            else:
                return None

        except Exception as e:
            logger.error(f" Failed to get text selection: {str(e)}",
                extra={"hwnd": hwnd, "error": str(e)})
            return None

    def get_focused_control(self) -> int | None:
        """
        Get the currently focused control handle.

        Returns:
            Window handle of focused control if available, None otherwise
        """
        try:
            focused_hwnd = self.user32.GetFocus()
            if focused_hwnd:
                logger.info(f" Focused control: {focused_hwnd}")
                return focused_hwnd
            else:
                logger.warning(" No focused control found")
                return None

        except Exception as e:
            logger.error(f" Failed to get focused control: {str(e)}",
                extra={"error": str(e)})
            return None

    def create_caret_info(self, hwnd: int) -> CaretInfo | None:
        """
        Create a comprehensive CaretInfo object for the given window.

        Args:
            hwnd: Handle to the window/control

        Returns:
            CaretInfo object if successful, None otherwise
        """
        # Performance monitoring removed during loguru migration
        try:
                # Get screen cursor position as fallback
                screen_x, screen_y = self.get_cursor_screen_position()

                # Try to get more precise caret information
                text_position = None
                selection_start = None
                selection_end = None
                control_hwnd = None

                if hwnd and self.is_text_control(hwnd):
                    control_hwnd = hwnd
                    text_position = self.get_caret_position(hwnd)

                    # Get selection range
                    selection = self.get_text_selection(hwnd)
                    if selection:
                        selection_start, selection_end = selection

                    # Try to get more precise screen position from caret
                    caret_screen_pos = self.get_caret_screen_position(hwnd)
                    if caret_screen_pos:
                        screen_x, screen_y = caret_screen_pos

                caret_info = CaretInfo(
                    screen_x=screen_x,
                    screen_y=screen_y,
                    text_position=text_position,
                    selection_start=selection_start,
                    selection_end=selection_end,
                    control_hwnd=control_hwnd)

                logger.info(f" CaretInfo created: screen=({screen_x}, {screen_y}), text_pos={text_position}",
                    extra={
                        "hwnd": hwnd,
                        "screen_x": screen_x,
                        "screen_y": screen_y,
                        "text_position": text_position,
                        "has_selection": caret_info.has_selection(),
                    })

                return caret_info

        except Exception as e:
            logger.error(f" Failed to create caret info: {str(e)}",
                extra={"hwnd": hwnd, "error": str(e)})
            return None
