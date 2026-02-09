"""Pynput Hotkey Configuration

Configuration management for the pynput-based hotkey manager.
Provides default hotkey mappings, validation, and configuration utilities.
"""

from dataclasses import dataclass
from enum import Enum

from src.utils.loguru_config import get_logger


class HotkeyAction(Enum):
    """Enumeration of available hotkey actions"""

    SHOW_FLOATING_WINDOW = "show_floating_window"


@dataclass
class HotkeyConfig:
    """Configuration for a single hotkey"""

    action: HotkeyAction
    hotkey_string: str
    description: str
    enabled: bool = True
    priority: int = 0  # Higher priority hotkeys are processed first


class PynputHotkeyConfig:
    """Configuration manager for pynput-based hotkeys"""

    # Default hotkey configurations - Only show_floating_window
    DEFAULT_HOTKEYS = {
        HotkeyAction.SHOW_FLOATING_WINDOW: HotkeyConfig(
            action=HotkeyAction.SHOW_FLOATING_WINDOW,
            hotkey_string="win+alt+o",
            description="Show/hide floating input window",
            priority=10,
            enabled=True,
        ),
    }

    # Valid modifier keys (pynput format)
    VALID_MODIFIERS = {"cmd", "ctrl", "alt", "shift", "win"}

    # Valid key names (pynput compatible)
    VALID_KEYS = {
        # Letters
        *[chr(i) for i in range(ord("a"), ord("z") + 1)],
        # Numbers
        *[str(i) for i in range(10)],
        # Special keys
        "space", "enter", "tab", "esc", "escape",
        "'", "quote", "comma", "period", "slash", "backslash",
        "semicolon", "equals", "minus", "left_bracket", "right_bracket",
        # Function keys
        *[f"f{i}" for i in range(1, 13)],
        # Arrow keys
        "up", "down", "left", "right",
        # Other common keys
        "home", "end", "page_up", "page_down", "insert", "delete", "backspace"
    }

    def __init__(self):
        self.logger = get_logger(__name__)
        self._hotkey_configs: dict[HotkeyAction, HotkeyConfig] = (
            self.DEFAULT_HOTKEYS.copy()
        )

    def get_hotkey_config(self, action: HotkeyAction) -> HotkeyConfig | None:
        """Get hotkey configuration for a specific action"""
        return self._hotkey_configs.get(action)

    def get_all_hotkey_configs(self) -> dict[HotkeyAction, HotkeyConfig]:
        """Get all hotkey configurations"""
        return self._hotkey_configs.copy()



    def set_hotkey_config(
        self,
        action: HotkeyAction,
        hotkey_string: str,
        description: str = None,
        enabled: bool = True,
        priority: int = 0,
    ) -> bool:
        """Set hotkey configuration for an action"""
        try:
            if not self.validate_hotkey_string(hotkey_string):
                self.logger.error(f"Invalid hotkey string: {hotkey_string}")
                return False

            # Check for conflicts
            if self.has_hotkey_conflict(hotkey_string, exclude_action=action):
                self.logger.error(f"Hotkey conflict detected for: {hotkey_string}")
                return False

            # Create or update configuration
            if description is None and action in self._hotkey_configs:
                description = self._hotkey_configs[action].description
            elif description is None:
                description = f"Action: {action.value}"

            self._hotkey_configs[action] = HotkeyConfig(
                action=action,
                hotkey_string=hotkey_string,
                description=description,
                enabled=enabled,
                priority=priority,
            )

            self.logger.info(
                f"Updated hotkey config for {action.value}: {hotkey_string}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to set hotkey config for {action.value}: {e}")
            return False

    def set_hotkey(self, action: HotkeyAction, hotkey_string: str) -> bool:
        """Simplified method to set hotkey (for compatibility with settings UI)"""
        return self.set_hotkey_config(action, hotkey_string)

    def disable_hotkey(self, action: HotkeyAction) -> bool:
        """Disable a hotkey without removing its configuration"""
        if action in self._hotkey_configs:
            self._hotkey_configs[action].enabled = False
            self.logger.info(f"Disabled hotkey for {action.value}")
            return True
        return False

    def enable_hotkey(self, action: HotkeyAction) -> bool:
        """Enable a previously disabled hotkey"""
        if action in self._hotkey_configs:
            self._hotkey_configs[action].enabled = True
            self.logger.info(f"Enabled hotkey for {action.value}")
            return True
        return False

    def validate_hotkey_string(self, hotkey_string: str) -> bool:
        """Validate a hotkey string format"""
        try:
            if not hotkey_string or not isinstance(hotkey_string, str):
                return False

            parts = [part.strip().lower() for part in hotkey_string.split("+")]

            if len(parts) < 2:
                self.logger.error(
                    f"Hotkey must have at least modifier+key: {hotkey_string}"
                )
                return False

            # Separate modifiers and key
            modifiers = parts[:-1]
            key = parts[-1]

            # Validate modifiers
            for modifier in modifiers:
                if modifier not in self.VALID_MODIFIERS:
                    self.logger.error(f"Invalid modifier: {modifier}")
                    return False

            # Validate key
            if key not in self.VALID_KEYS:
                self.logger.error(f"Invalid key: {key}")
                return False

            # Check for at least one modifier
            if not modifiers:
                self.logger.error(
                    f"Hotkey must have at least one modifier: {hotkey_string}"
                )

            return True

        except Exception as e:
            self.logger.error(f"Error validating hotkey string {hotkey_string}: {e}")
            return False



    def has_hotkey_conflict(
        self, hotkey_string: str, exclude_action: HotkeyAction = None
    ) -> bool:
        """Check if a hotkey string conflicts with existing configurations"""
        for action, config in self._hotkey_configs.items():
            if exclude_action and action == exclude_action:
                continue
            if config.enabled and config.hotkey_string.lower() == hotkey_string.lower():
                return True
        return False

    def get_hotkey_conflicts(self) -> list[tuple[HotkeyAction, HotkeyAction]]:
        """Get list of conflicting hotkey pairs"""
        conflicts = []
        actions = list(self._hotkey_configs.keys())

        for i, action1 in enumerate(actions):
            config1 = self._hotkey_configs[action1]
            if not config1.enabled:
                continue

            for action2 in actions[i + 1 :]:
                config2 = self._hotkey_configs[action2]
                if not config2.enabled:
                    continue

                if config1.hotkey_string.lower() == config2.hotkey_string.lower():
                    conflicts.append((action1, action2))

        return conflicts



    def load_from_config_manager(self, config_manager) -> bool:
        """Load hotkey configurations from ConfigManager"""
        try:
            hotkey_config = config_manager.get_hotkeys()

            # Map config manager keys to our actions (only supported actions)
            action_mapping = {
                # New format (uppercase)
                "SHOW_FLOATING_WINDOW": HotkeyAction.SHOW_FLOATING_WINDOW,
                # Legacy format (lowercase) for backward compatibility
                "show_floating_window": HotkeyAction.SHOW_FLOATING_WINDOW,
            }

            for config_key, hotkey_string in hotkey_config.items():
                if config_key in action_mapping:
                    action = action_mapping[config_key]
                    if action in self._hotkey_configs:
                        # Update existing configuration
                        existing_config = self._hotkey_configs[action]
                        self.set_hotkey_config(
                            action=action,
                            hotkey_string=hotkey_string,
                            description=existing_config.description,
                            enabled=existing_config.enabled,
                            priority=existing_config.priority,
                        )

            self.logger.info(
                "Successfully loaded hotkey configurations from ConfigManager"
            )
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to load hotkey configurations from ConfigManager: {e}"
            )
            return False



    def reset_to_defaults(self) -> None:
        """Reset all hotkey configurations to defaults"""
        self._hotkey_configs = self.DEFAULT_HOTKEYS.copy()
        self.logger.info("Reset hotkey configurations to defaults")


