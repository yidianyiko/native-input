"""
Settings Dialog Module
Modular settings dialog with tabbed interface for different setting categories
"""

from .dialog_manager import SettingsDialogManager
from src.config.config import ConfigManager as ConfigurationManager
from .validator import SettingsValidator

__all__ = [
    "SettingsDialogManager",
    "ConfigurationManager", 
    "SettingsValidator",
]