"""
Base Settings Page
Base class for all settings pages with common functionality
"""

from abc import ABC, ABCMeta, abstractmethod
from typing import Any, Dict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger


class QWidgetABCMeta(type(QWidget), ABCMeta):
    """Metaclass that combines QWidget and ABC metaclasses"""


class BaseSettingsPage(QWidget, ABC, metaclass=QWidgetABCMeta):
    """Base class for settings pages with common functionality"""
    
    # Signals for settings changes
    settings_changed = Signal(str, object)  # config_key, value
    validation_error = Signal(str, str)     # field_name, error_message
    status_update = Signal(str, str)        # message, color
    
    def __init__(self, config_manager: ConfigManager, parent: QWidget = None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        
        # Track pending changes
        self.pending_changes: Dict[str, Any] = {}
        self.restart_required_changes: set[str] = set()
        
        self._setup_ui()
        self._load_settings()
        
    @abstractmethod
    def _setup_ui(self) -> None:
        """Setup the UI components for this settings page"""
        
    @abstractmethod
    def _load_settings(self) -> None:
        """Load current settings from configuration"""
        
    @abstractmethod
    def apply_settings(self) -> bool:
        """Apply pending settings changes
        
        Returns:
            bool: True if all settings applied successfully
        """
        
    @abstractmethod
    def validate_settings(self) -> tuple[bool, list[str]]:
        """Validate current settings
        
        Returns:
            tuple: (is_valid, error_messages)
        """
        
    def reset_to_defaults(self) -> None:
        """Reset settings to default values"""
        try:
            self._reset_to_defaults_impl()
            self._load_settings()
            logger.info(f"Reset {self.__class__.__name__} to defaults")
        except Exception as e:
            logger.error(f"Failed to reset {self.__class__.__name__} to defaults: {e}")
            
    @abstractmethod
    def _reset_to_defaults_impl(self) -> None:
        """Implementation-specific reset logic"""
        
    def has_pending_changes(self) -> bool:
        """Check if there are pending changes"""
        return bool(self.pending_changes)
        
    def has_restart_required_changes(self) -> bool:
        """Check if any pending changes require restart"""
        return bool(self.restart_required_changes)
        
    def get_pending_changes(self) -> Dict[str, Any]:
        """Get all pending changes"""
        return self.pending_changes.copy()
        
    def clear_pending_changes(self) -> None:
        """Clear all pending changes"""
        self.pending_changes.clear()
        self.restart_required_changes.clear()
        
    def _mark_change(self, config_key: str, value: Any, restart_required: bool = False) -> None:
        """Mark a configuration change
        
        Args:
            config_key: Configuration key (e.g., 'ui.floating_window.transparency')
            value: New value
            restart_required: Whether this change requires application restart
        """
        try:
            # Store the change
            self.pending_changes[config_key] = value
            
            if restart_required:
                self.restart_required_changes.add(config_key)
                
            # Emit signal
            self.settings_changed.emit(config_key, value)
            
            # Update status
            if restart_required:
                self.status_update.emit(
                    f"Change marked (restart required): {config_key}", "orange"
                )
            else:
                self.status_update.emit(f"Change marked: {config_key}", "blue")
                
            logger.info(f"Marked change: {config_key} = {value} (restart: {restart_required})")
            
        except Exception as e:
            logger.error(f"Error marking change for {config_key}: {e}")
            
    def _validate_field(self, field_name: str, value: Any, validator_func) -> bool:
        """Validate a single field
        
        Args:
            field_name: Name of the field being validated
            value: Value to validate
            validator_func: Function to perform validation
            
        Returns:
            bool: True if validation passed
        """
        try:
            is_valid, error_message = validator_func(value)
            if not is_valid:
                self.validation_error.emit(field_name, error_message)
                return False
            return True
        except Exception as e:
            error_msg = f"Validation error: {e}"
            self.validation_error.emit(field_name, error_msg)
            logger.error(f"Validation error for {field_name}: {e}")
            return False