"""
Settings Validator
Validation logic for settings with conflict detection and error reporting
"""

import re
from typing import Any, Dict, List, Tuple

from src.utils.loguru_config import logger, get_logger


class SettingsValidator:
    """Settings validation with conflict detection and error reporting"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
    def validate_all_settings(self, settings: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate all settings and detect conflicts
        
        Args:
            settings: Dictionary of all settings to validate
            
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Validate individual settings
            for key, value in settings.items():
                is_valid, error = self._validate_setting(key, value)
                if not is_valid:
                    errors.append(f"{key}: {error}")
                    
            # Check for conflicts
            conflict_errors = self._check_conflicts(settings)
            errors.extend(conflict_errors)
            
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("All settings validation passed")
            else:
                logger.error(f"Settings validation failed: {len(errors)} errors")
                
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"Validation system error: {e}"
            logger.error(f"Settings validation system error: {e}")
            return False, [error_msg]
            
    def _validate_setting(self, key: str, value: Any) -> Tuple[bool, str]:
        """Validate a single setting
        
        Args:
            key: Setting key
            value: Setting value
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # General settings validation
            if key.startswith("ui.floating_window."):
                return self._validate_floating_window_setting(key, value)
            elif key.startswith("ui.system_tray."):
                return self._validate_system_tray_setting(key, value)
            elif key.startswith("hotkeys."):
                return self._validate_hotkey_setting(key, value)
            elif key.startswith("ai."):
                return self._validate_ai_setting(key, value)
            elif key.startswith("system."):
                return self._validate_system_setting(key, value)
            else:
                # Unknown setting - allow but log warning
                logger.info(f"Unknown setting key: {key}")
                return True, ""
                
        except Exception as e:
            return False, f"Validation error: {e}"
            
    def _validate_floating_window_setting(self, key: str, value: Any) -> Tuple[bool, str]:
        """Validate floating window settings"""
        if key == "ui.floating_window.transparency":
            if not isinstance(value, (int, float)) or not (0 <= value <= 100):
                return False, "Transparency must be between 0 and 100"
        elif key == "ui.floating_window.theme":
            if value not in ["dark", "light"]:
                return False, "Theme must be 'dark' or 'light'"
        elif key == "ui.floating_window.font_size":
            if not isinstance(value, int) or not (8 <= value <= 24):
                return False, "Font size must be between 8 and 24"
        elif key == "ui.floating_window.auto_focus" and not isinstance(value, bool):
            return False, "Auto focus must be true or false"
                
        return True, ""
        
    def _validate_system_tray_setting(self, key: str, value: Any) -> Tuple[bool, str]:
        """Validate system tray settings"""
        if key in ["ui.system_tray.minimize_to_tray", "ui.system_tray.show_notifications"] and not isinstance(value, bool):
            return False, "System tray settings must be true or false"
                
        return True, ""
        
    def _validate_hotkey_setting(self, key: str, value: Any) -> Tuple[bool, str]:
        """Validate hotkey settings"""
        if not isinstance(value, str):
            return False, "Hotkey must be a string"
            
        # Basic hotkey format validation
        if not self._is_valid_hotkey_format(value):
            return False, "Invalid hotkey format"
            
        return True, ""
        
    def _validate_ai_setting(self, key: str, value: Any) -> Tuple[bool, str]:
        """Validate AI service settings"""
        if key.endswith(".api_key"):
            if not isinstance(value, str) or len(value.strip()) == 0:
                return False, "API key cannot be empty"
        elif key.endswith(".base_url"):
            if not isinstance(value, str) or not self._is_valid_url(value):
                return False, "Invalid URL format"
        elif key.endswith(".model") and (not isinstance(value, str) or len(value.strip()) == 0):
            return False, "Model name cannot be empty"
                
        return True, ""
        
    def _validate_system_setting(self, key: str, value: Any) -> Tuple[bool, str]:
        """Validate system settings"""
        # Only validate system.auto_start; do not validate system.debug_mode or system.log_level anymore
        if key == "system.auto_start" and not isinstance(value, bool):
            return False, "System settings must be true or false"
                
        return True, ""
        
    def _check_conflicts(self, settings: Dict[str, Any]) -> List[str]:
        """Check for conflicts between settings
        
        Args:
            settings: All settings to check
            
        Returns:
            List of conflict error messages
        """
        conflicts = []
        
        try:
            # Check hotkey conflicts
            hotkey_conflicts = self._check_hotkey_conflicts(settings)
            conflicts.extend(hotkey_conflicts)
            
            # Check AI service conflicts
            ai_conflicts = self._check_ai_service_conflicts(settings)
            conflicts.extend(ai_conflicts)
            
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}")
            conflicts.append(f"Conflict detection error: {e}")
            
        return conflicts
        
    def _check_hotkey_conflicts(self, settings: Dict[str, Any]) -> List[str]:
        """Check for hotkey conflicts"""
        conflicts = []
        hotkeys = {}
        
        # Collect all hotkey settings
        for key, value in settings.items():
            if key.startswith("hotkeys.") and isinstance(value, str):
                action = key.replace("hotkeys.", "")
                if value in hotkeys:
                    conflicts.append(
                        f"Hotkey conflict: '{value}' is assigned to both '{action}' and '{hotkeys[value]}'"
                    )
                else:
                    hotkeys[value] = action
                    
        return conflicts
        
    def _check_ai_service_conflicts(self, settings: Dict[str, Any]) -> List[str]:
        """Check for AI service conflicts"""
        conflicts = []
        
        # Check if multiple providers are configured with same base URL
        base_urls = {}
        for key, value in settings.items():
            if key.endswith(".base_url") and isinstance(value, str):
                provider = key.split(".")[1]  # Extract provider name
                if value in base_urls:
                    conflicts.append(
                        f"Base URL conflict: '{value}' is used by both '{provider}' and '{base_urls[value]}'"
                    )
                else:
                    base_urls[value] = provider
                    
        return conflicts
        
    def _is_valid_hotkey_format(self, hotkey: str) -> bool:
        """Validate hotkey format"""
        if not hotkey or not isinstance(hotkey, str):
            return False
            
        # Basic validation - should contain at least one key
        # More sophisticated validation can be added based on actual hotkey format
        return len(hotkey.strip()) > 0
        
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False
            
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
        , re.IGNORECASE)
        
        return re.match(url_pattern, url) is not None