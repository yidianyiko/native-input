from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WindowContext:
    handle: Any = None
    title: str = ""
    process_name: str = ""

    @property
    def is_valid(self) -> bool:
        return self.handle is not None


def capture_window_context() -> WindowContext:
    try:
        return _capture_current_platform()
    except Exception:
        logger.exception("Failed to capture window context")
        return WindowContext()


def restore_window_focus(ctx: WindowContext) -> bool:
    if not ctx.is_valid:
        return False
    try:
        return _restore_current_platform(ctx)
    except Exception:
        logger.exception("Failed to restore window focus")
        return False


def _capture_current_platform() -> WindowContext:
    if sys.platform == "win32":
        return _capture_windows()
    if sys.platform == "darwin":
        return _capture_macos()
    logger.warning("Unsupported platform: %s", sys.platform)
    return WindowContext()


def _restore_current_platform(ctx: WindowContext) -> bool:
    if sys.platform == "win32":
        return _restore_windows(ctx)
    if sys.platform == "darwin":
        return _restore_macos(ctx)
    return False


def _capture_windows() -> WindowContext:
    import ctypes

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return WindowContext()
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    title = buf.value
    return WindowContext(handle=hwnd, title=title, process_name="")


def _restore_windows(ctx: WindowContext) -> bool:
    import ctypes

    user32 = ctypes.windll.user32
    result = user32.SetForegroundWindow(ctx.handle)
    return bool(result)


def _capture_macos() -> WindowContext:
    try:
        import subprocess

        result = subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to get {name, unix id} of first process whose frontmost is true',
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            name = parts[0] if parts else ""
            pid = int(parts[1]) if len(parts) > 1 else 0
            return WindowContext(handle=pid, title=name, process_name=name)
    except Exception:
        logger.exception("macOS capture failed")
    return WindowContext()


def _restore_macos(ctx: WindowContext) -> bool:
    try:
        import subprocess

        title = ctx.title
        result = subprocess.run(
            ["osascript", "-e", f'tell application "{title}" to activate'],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.returncode == 0
    except Exception:
        logger.exception("macOS restore failed")
        return False

