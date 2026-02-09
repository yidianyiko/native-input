# UI package

# Import the new modular FloatingWindow implementation
from .windows.floating_window.main import ModularFloatingWindow as FloatingWindow
from .widgets.positioning import WindowPositioning, PositionConfig, PositionStrategy, PositionResult
from .system_tray import SystemTray
from .windows.settings.settings_dialog import SettingsDialog

__all__ = [
    "FloatingWindow",
    "WindowPositioning", 
    "PositionConfig", 
    "PositionStrategy", 
    "PositionResult",
    "SystemTray",
    "SettingsDialog"
]
