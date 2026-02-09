"""
New Settings Dialog - Modular Implementation
Maintains API compatibility with original SettingsDialog while using modular structure
"""

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger

from ...settings.dialog_manager import SettingsDialogManager


class SettingsDialog(SettingsDialogManager):
    """
    New modular settings dialog that maintains API compatibility with the original.
    
    This class serves as a drop-in replacement for the original SettingsDialog,
    providing the same public interface while using the new modular architecture.
    """

    # Maintain the same signals as the original
    settings_changed = Signal(dict)
    hotkey_changed = Signal(str, str)  # action, new_hotkey
    model_changed = Signal(str)  # new_model_id

    def __init__(
        self,
        config_manager: ConfigManager,
        ai_service_manager: Any = None,
        auth_manager: Any = None,
        parent: QWidget = None) -> None:
        """Initialize the new modular settings dialog
        
        Args:
            config_manager: Configuration manager instance
            ai_service_manager: AI service manager instance (optional)
            auth_manager: Authentication manager instance (optional)
            parent: Parent widget (optional)
        """
        super().__init__(config_manager, ai_service_manager, auth_manager, parent)
        self.logger = get_logger(__name__)
        
        logger.info("New modular SettingsDialog initialized")

    # The following methods maintain compatibility with the original API
    # while delegating to the new modular implementation

    def get_pending_changes(self) -> dict[str, Any]:
        """Get all pending changes (compatibility method)"""
        return self.pending_changes

    def has_pending_changes(self) -> bool:
        """Check if there are pending changes (compatibility method)"""
        return bool(self.pending_changes)

    def apply_changes(self) -> bool:
        """Apply all pending changes (compatibility method)"""
        return self._apply_settings()

    def reset_all_to_defaults(self) -> None:
        """Reset all settings to defaults (compatibility method)"""
        self._reset_to_defaults()

    def validate_all_settings(self) -> tuple[bool, list[str]]:
        """Validate all settings (compatibility method)"""
        return self.validator.validate_all_settings(self.pending_changes)

    # Additional methods that may be expected by existing code
    def _apply_settings(self) -> bool:
        """Apply settings - delegates to parent implementation"""
        try:
            # Call the parent class implementation
            super()._apply_settings()
            return True
        except Exception:
            return False

    def _reset_to_defaults(self) -> None:
        """Reset to defaults - delegates to parent implementation"""
        super()._reset_to_defaults()

    def _test_ai_connection(self) -> None:
        """Test AI connection - delegates to parent implementation"""
        super()._test_ai_connection()

    def _ok_clicked(self) -> None:
        """Handle OK button click - delegates to parent implementation"""
        super()._ok_clicked()

    # Expose configuration manager for backward compatibility
    @property
    def config_manager(self) -> ConfigManager:
        """Get the configuration manager"""
        return self.config_manager

    @property
    def hotkey_config(self):
        """Get the hotkey configuration"""
        return self.hotkey_config

    # Method to get specific page instances (for advanced usage)
    def get_general_page(self):
        """Get the general settings page instance"""
        return self.settings_pages.get("general")

    def get_hotkey_page(self):
        """Get the hotkey settings page instance"""
        return self.settings_pages.get("hotkeys")

    def get_ai_page(self):
        """Get the AI settings page instance"""
        return self.settings_pages.get("ai")

    def get_ui_page(self):
        """Get the UI settings page instance"""
        return self.settings_pages.get("ui")

    def get_agent_page(self):
        """Get the agent settings page instance"""
        return self.settings_pages.get("agents")

    # Validation methods for specific sections
    def validate_general_settings(self) -> tuple[bool, list[str]]:
        """Validate general settings only"""
        general_page = self.get_general_page()
        if general_page and hasattr(general_page, "validate_settings"):
            return general_page.validate_settings()
        return True, []

    def validate_hotkey_settings(self) -> tuple[bool, list[str]]:
        """Validate hotkey settings only"""
        hotkey_page = self.get_hotkey_page()
        if hotkey_page and hasattr(hotkey_page, "validate_settings"):
            return hotkey_page.validate_settings()
        return True, []

    def validate_ai_settings(self) -> tuple[bool, list[str]]:
        """Validate AI settings only"""
        ai_page = self.get_ai_page()
        if ai_page and hasattr(ai_page, "validate_settings"):
            return ai_page.validate_settings()
        return True, []

    def validate_ui_settings(self) -> tuple[bool, list[str]]:
        """Validate UI settings only"""
        ui_page = self.get_ui_page()
        if ui_page and hasattr(ui_page, "validate_settings"):
            return ui_page.validate_settings()
        return True, []

    def validate_agent_settings(self) -> tuple[bool, list[str]]:
        """Validate agent settings only"""
        agent_page = self.get_agent_page()
        if agent_page and hasattr(agent_page, "validate_settings"):
            return agent_page.validate_settings()
        return True, []

    # Configuration backup/restore methods
    def create_config_backup(self, backup_name: str = None) -> str:
        """Create a configuration backup"""
        return self.configuration_manager.create_backup(backup_name)

    def restore_config_backup(self, backup_path: str) -> bool:
        """Restore configuration from backup"""
        success = self.configuration_manager.restore_backup(backup_path)
        if success:
            # Reload all pages with restored settings
            for page in self.settings_pages.values():
                if hasattr(page, "_load_settings"):
                    page._load_settings()
        return success

    def list_config_backups(self) -> list[dict[str, Any]]:
        """List available configuration backups"""
        return self.configuration_manager.list_backups()

    # Advanced configuration methods
    def merge_config(self, override_config: dict[str, Any]) -> None:
        """Merge configuration with override values"""
        current_config = self.config_manager.config
        merged_config = self.configuration_manager.merge_configurations(
            current_config, override_config
        )
        
        # Update config manager
        for key, value in merged_config.items():
            self.config_manager.set(key, value)
            
        # Reload all pages
        for page in self.settings_pages.values():
            if hasattr(page, "_load_settings"):
                page._load_settings()

    def get_default_config(self) -> dict[str, Any]:
        """Get default configuration values"""
        return self.configuration_manager.get_default_configuration()

    def export_config(self, export_path: str) -> bool:
        """Export current configuration to file"""
        try:
            import json
            from pathlib import Path
            
            config_data = self.config_manager.config
            export_file = Path(export_path)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Configuration exported to: {export_path}")
            return True
            
        except Exception as e:
            logger.info(f"Failed to export configuration: {e}")
            return False

    def import_config(self, import_path: str) -> bool:
        """Import configuration from file"""
        try:
            import json
            from pathlib import Path
            
            import_file = Path(import_path)
            if not import_file.exists():
                return False
                
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            # Validate imported configuration
            is_valid, errors = self.configuration_manager.validate_configuration(imported_config)
            if not is_valid:
                logger.info(f"Invalid configuration file: {errors}")
                return False
                
            # Merge with current configuration
            self.merge_config(imported_config)
            
            logger.info(f"Configuration imported from: {import_path}")
            return True
            
        except Exception as e:
            logger.info(f"Failed to import configuration: {e}")
            return False