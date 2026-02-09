"""
General Settings Page
General settings UI with language and theme options management
"""

from typing import Any, List, Tuple

from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QVBoxLayout,
)

from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger

from .base_page import BaseSettingsPage


class GeneralSettingsPage(BaseSettingsPage):
    """General settings page with application-wide options"""

    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(config_manager, parent)

    def _setup_ui(self) -> None:
        """Setup the UI components for general settings"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Application Settings group
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout(app_group)

        # Auto-start (Implemented - requires restart)
        self.auto_start_cb = QCheckBox("Start with Windows")
        self.auto_start_cb.setToolTip(
            "Automatically start the application when Windows starts (Requires restart)"
        )
        self.auto_start_cb.stateChanged.connect(
            lambda: self._mark_change(
                "system.auto_start",
                self.auto_start_cb.isChecked(),
                restart_required=True,
            )
        )
        app_layout.addRow("Startup:", self.auto_start_cb)

        # Minimize to tray (Implemented - immediate effect)
        self.minimize_tray_cb = QCheckBox("Minimize to system tray")
        self.minimize_tray_cb.setToolTip(
            "Hide window to system tray instead of closing (Immediate effect)"
        )
        self.minimize_tray_cb.stateChanged.connect(
            lambda: self._mark_change(
                "ui.system_tray.minimize_to_tray", self.minimize_tray_cb.isChecked()
            )
        )
        app_layout.addRow("System Tray:", self.minimize_tray_cb)

        # Show notifications - 默认开启，不需要用户选择

        layout.addWidget(app_group)
        layout.addStretch()

    def _load_settings(self) -> None:
        """Load current general settings from configuration"""
        try:
            # Load auto-start setting
            auto_start = self.config_manager.get("system.auto_start", False)
            self.auto_start_cb.setChecked(auto_start)

            # Load minimize to tray setting
            minimize_tray = self.config_manager.get("ui.system_tray.minimize_to_tray", True)
            self.minimize_tray_cb.setChecked(minimize_tray)

            # Show notifications - 默认开启，不需要用户选择
            # These settings are now handled automatically by the system

            logger.info("General settings loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load general settings: {e}")

    def apply_settings(self) -> bool:
        """Apply pending general settings changes
        
        Returns:
            bool: True if all settings applied successfully
        """
        try:
            success = True
            
            for config_key, value in self.pending_changes.items():
                try:
                    # Apply the setting to config manager
                    self.config_manager.set(config_key, value)
                    
                    # Apply immediate changes if not restart required
                    if config_key not in self.restart_required_changes:
                        self._apply_immediate_change(config_key, value)
                        
                    logger.info(f"Applied general setting: {config_key} = {value}")
                    
                except Exception as e:
                    logger.error(f"Failed to apply general setting {config_key}: {e}")
                    success = False
                    
            if success:
                # Save configuration
                self.config_manager.save()
                self.status_update.emit("General settings applied successfully", "green")
            else:
                self.status_update.emit("Some general settings failed to apply", "orange")
                
            return success
            
        except Exception as e:
            logger.error(f"Error applying general settings: {e}")
            self.status_update.emit("Error applying general settings", "red")
            return False

    def _apply_immediate_change(self, config_key: str, value: Any) -> None:
        """Apply configuration change immediately to running components
        
        Args:
            config_key: Configuration key
            value: New value
        """
        try:
            # System tray changes are usually applied automatically
            # since the system tray reads from config manager directly
            if config_key.startswith("ui.system_tray."):
                # Get system tray from parent application
                parent = self.parent()
                while parent and not hasattr(parent, "system_tray"):
                    parent = parent.parent()
                    
                if parent and hasattr(parent, "system_tray") and parent.system_tray:
                    # System tray will automatically pick up config changes
                    pass
                    
        except Exception as e:
            logger.error(f"Error applying immediate change for {config_key}: {e}")

    def validate_settings(self) -> Tuple[bool, List[str]]:
        """Validate current general settings
        
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Validate auto-start setting
            auto_start = self.auto_start_cb.isChecked()
            if not isinstance(auto_start, bool):
                errors.append("Auto-start setting must be true or false")
                
            # Validate minimize to tray setting
            minimize_tray = self.minimize_tray_cb.isChecked()
            if not isinstance(minimize_tray, bool):
                errors.append("Minimize to tray setting must be true or false")
                
            # Show notifications are now handled automatically
            # No validation needed as they are not user-configurable
                
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("General settings validation passed")
            else:
                logger.error(f"General settings validation failed: {errors}")
                
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"General settings validation error: {e}"
            logger.error(f"General settings validation error: {e}")
            return False, [error_msg]

    def _reset_to_defaults_impl(self) -> None:
        """Reset general settings to default values"""
        try:
            # Reset to default values
            self.auto_start_cb.setChecked(False)
            self.minimize_tray_cb.setChecked(True)
            # Show notifications are handled automatically
            
            # Clear pending changes
            self.clear_pending_changes()
            
            logger.info("General settings reset to defaults")
            
        except Exception as e:
            logger.error(f"Failed to reset general settings to defaults: {e}")