"""Auto-start manager for Windows and Mac."""

import plistlib
import sys
from pathlib import Path
from typing import Optional

from app.config import APP_NAME


class AutoStartManager:
    """Manages auto-start configuration for the application."""

    def __init__(self):
        self._plist_path: Optional[Path] = None
        if sys.platform == "darwin":
            self._plist_path = (
                Path.home() / "Library" / "LaunchAgents" / f"com.{APP_NAME.lower()}.plist"
            )

    def _get_executable_path(self) -> str:
        """Get the path to the current executable."""
        if getattr(sys, "frozen", False):
            return sys.executable
        return sys.executable

    def is_enabled(self) -> bool:
        """Check if auto-start is enabled."""
        if sys.platform == "win32":
            return self._is_enabled_windows()
        if sys.platform == "darwin":
            return self._is_enabled_mac()
        return False

    def enable(self) -> None:
        """Enable auto-start."""
        if sys.platform == "win32":
            self._enable_windows()
        elif sys.platform == "darwin":
            self._enable_mac()

    def disable(self) -> None:
        """Disable auto-start."""
        if sys.platform == "win32":
            self._disable_windows()
        elif sys.platform == "darwin":
            self._disable_mac()

    # Windows implementation
    def _is_enabled_windows(self) -> bool:
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ,
            )
            try:
                winreg.QueryValueEx(key, APP_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def _enable_windows(self) -> None:
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            winreg.SetValueEx(
                key,
                APP_NAME,
                0,
                winreg.REG_SZ,
                self._get_executable_path(),
            )
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to enable auto-start: {e}")

    def _disable_windows(self) -> None:
        try:
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE,
            )
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to disable auto-start: {e}")

    # Mac implementation
    def _is_enabled_mac(self) -> bool:
        return self._plist_path is not None and self._plist_path.exists()

    def _enable_mac(self) -> None:
        if self._plist_path is None:
            return

        plist_content = {
            "Label": f"com.{APP_NAME.lower()}",
            "ProgramArguments": [self._get_executable_path()],
            "RunAtLoad": True,
            "KeepAlive": False,
        }

        self._plist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._plist_path, "wb") as f:
            plistlib.dump(plist_content, f)

    def _disable_mac(self) -> None:
        if self._plist_path and self._plist_path.exists():
            self._plist_path.unlink()
