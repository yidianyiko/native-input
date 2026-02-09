"""
Hotkey Settings Page
Hotkey configuration UI with key capture functionality and conflict detection
"""

from typing import Dict, List, Tuple

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QFormLayout,
)

from src.config.hotkey_config import HotkeyAction, PynputHotkeyConfig
from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger

from .base_page import BaseSettingsPage


class HotkeySettingsPage(BaseSettingsPage):
    """Hotkey settings page with conflict detection and validation"""

    def __init__(self, config_manager: ConfigManager, hotkey_config: PynputHotkeyConfig, parent=None):
        self.hotkey_config = hotkey_config
        self.hotkey_inputs: Dict[HotkeyAction, QLineEdit] = {}
        self.hotkey_status_labels: Dict[HotkeyAction, QLabel] = {}
        super().__init__(config_manager, parent)

    def _setup_ui(self) -> None:
        """Setup the UI components for hotkey settings"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Instructions
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet(
            "background-color: #f0f8ff; border: 1px solid #ccc; border-radius: 5px;"
        )
        info_layout = QVBoxLayout(info_frame)

        info_label = QLabel("Configure global hotkeys for quick access to AI features")
        info_label.setFont(QFont("", 9, QFont.Weight.Bold))
        info_layout.addWidget(info_label)

        format_label = QLabel("Format: win+modifier+key (e.g., win+shift+o, win+alt+v)")
        format_label.setStyleSheet("color: #666; font-size: 9pt;")
        info_layout.addWidget(format_label)

        tips_label = QLabel(
            "Tip: Use Windows key combinations to avoid conflicts with other applications"
        )
        tips_label.setStyleSheet("color: #0066cc; font-size: 9pt;")
        info_layout.addWidget(tips_label)

        layout.addWidget(info_frame)

        # Hotkeys configuration
        hotkeys_group = QGroupBox("Global Hotkeys")
        hotkeys_layout = QFormLayout(hotkeys_group)

        # Create hotkey inputs for each action
        hotkey_configs = self.hotkey_config.get_all_hotkey_configs()

        for action, config in hotkey_configs.items():
            # Create horizontal layout for input and status
            input_layout = QHBoxLayout()

            # Hotkey input field
            hotkey_input = QLineEdit()
            hotkey_input.setPlaceholderText(config.hotkey_string)
            hotkey_input.setText(config.hotkey_string)
            hotkey_input.textChanged.connect(
                lambda text, a=action: self._on_hotkey_changed(a, text)
            )
            input_layout.addWidget(hotkey_input)

            # Status label for validation feedback
            status_label = QLabel("✓")
            status_label.setStyleSheet("color: green; font-weight: bold;")
            status_label.setFixedWidth(20)
            status_label.setToolTip("Hotkey is valid")
            input_layout.addWidget(status_label)

            # Store references
            self.hotkey_inputs[action] = hotkey_input
            self.hotkey_status_labels[action] = status_label

            # Add to form layout
            hotkeys_layout.addRow(f"{config.description}:", input_layout)

        layout.addWidget(hotkeys_group)

        # Conflict detection section
        conflicts_group = QGroupBox("Conflict Detection")
        conflicts_layout = QVBoxLayout(conflicts_group)

        self.conflicts_list = QListWidget()
        self.conflicts_list.setMaximumHeight(100)
        self.conflicts_list.setStyleSheet("QListWidget { background-color: #fff5f5; }")
        conflicts_layout.addWidget(self.conflicts_list)

        # Conflict resolution buttons
        conflict_buttons_layout = QHBoxLayout()

        self.auto_resolve_btn = QPushButton("Auto-resolve Conflicts")
        self.auto_resolve_btn.clicked.connect(self._auto_resolve_conflicts)
        self.auto_resolve_btn.setEnabled(False)
        conflict_buttons_layout.addWidget(self.auto_resolve_btn)

        conflict_buttons_layout.addStretch()

        self.reset_hotkeys_btn = QPushButton("Reset to Defaults")
        self.reset_hotkeys_btn.clicked.connect(self._reset_hotkeys_to_defaults)
        conflict_buttons_layout.addWidget(self.reset_hotkeys_btn)

        conflicts_layout.addLayout(conflict_buttons_layout)

        layout.addWidget(conflicts_group)
        layout.addStretch()

    def _load_settings(self) -> None:
        """Load current hotkey settings from configuration"""
        try:
            # Load hotkey configurations from config manager
            self.hotkey_config.load_from_config_manager(self.config_manager)

            # Update UI with loaded hotkeys
            for action, config in self.hotkey_config.get_all_hotkey_configs().items():
                if action in self.hotkey_inputs:
                    self.hotkey_inputs[action].setText(config.hotkey_string)

            # Validate all hotkeys and update status
            self._validate_all_hotkeys()

            logger.info("Hotkey settings loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load hotkey settings: {e}")

    def apply_settings(self) -> bool:
        """Apply pending hotkey settings changes
        
        Returns:
            bool: True if all settings applied successfully
        """
        try:
            success = True
            
            # Validate before applying
            is_valid, errors = self.validate_settings()
            if not is_valid:
                self.status_update.emit(f"Validation failed: {'; '.join(errors)}", "red")
                return False
            
            # Apply hotkey changes
            for action, input_field in self.hotkey_inputs.items():
                hotkey_string = input_field.text().strip()
                config_key = f"hotkeys.{action.value}"
                
                try:
                    # Update hotkey config
                    self.hotkey_config.set_hotkey(action, hotkey_string)
                    
                    # Update config manager
                    self.config_manager.set(config_key, hotkey_string)
                    
                    logger.info(f"Applied hotkey setting: {action.value} = {hotkey_string}")
                    
                except Exception as e:
                    logger.error(f"Failed to apply hotkey setting {action.value}: {e}")
                    success = False
                    
            if success:
                # Save configuration
                self.config_manager.save()
                
                # Apply to hotkey manager if available
                self._apply_to_hotkey_manager()
                
                self.status_update.emit("Hotkey settings applied successfully", "green")
            else:
                self.status_update.emit("Some hotkey settings failed to apply", "orange")
                
            return success
            
        except Exception as e:
            logger.error(f"Error applying hotkey settings: {e}")
            self.status_update.emit("Error applying hotkey settings", "red")
            return False

    def _apply_to_hotkey_manager(self) -> None:
        """Apply hotkey changes to the hotkey manager"""
        try:
            # Get hotkey manager from parent application
            parent = self.parent()
            while parent and not hasattr(parent, "hotkey_manager"):
                parent = parent.parent()
                
            if parent and hasattr(parent, "hotkey_manager") and parent.hotkey_manager:
                hotkey_manager = parent.hotkey_manager
                
                if hasattr(hotkey_manager, "reload_hotkeys"):
                    hotkey_manager.reload_hotkeys()
                    logger.info("Hotkey manager reloaded with new settings")
                    
        except Exception as e:
            logger.error(f"Error applying hotkeys to manager: {e}")

    def validate_settings(self) -> Tuple[bool, List[str]]:
        """Validate current hotkey settings
        
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        try:
            # Check for conflicts
            current_hotkeys = {}
            for action, input_field in self.hotkey_inputs.items():
                text = input_field.text().strip()
                if text:
                    # Validate format
                    if not self.hotkey_config.validate_hotkey_string(text):
                        errors.append(f"Invalid hotkey format for {action.value}: {text}")
                        continue
                        
                    # Check for duplicates
                    if text.lower() in current_hotkeys:
                        other_action = current_hotkeys[text.lower()]
                        errors.append(f"Hotkey conflict: '{text}' is used by both {action.value} and {other_action}")
                    else:
                        current_hotkeys[text.lower()] = action.value
                        
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("Hotkey settings validation passed")
            else:
                logger.error(f"Hotkey settings validation failed: {errors}")
                
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"Hotkey settings validation error: {e}"
            logger.error(f"Hotkey settings validation error: {e}")
            return False, [error_msg]

    def _reset_to_defaults_impl(self) -> None:
        """Reset hotkey settings to default values"""
        try:
            # Reset hotkey config to defaults
            self.hotkey_config.reset_to_defaults()
            
            # Update UI with default values
            for action, config in self.hotkey_config.get_all_hotkey_configs().items():
                if action in self.hotkey_inputs:
                    self.hotkey_inputs[action].setText(config.hotkey_string)
                    
            # Revalidate
            self._validate_all_hotkeys()
            
            # Clear pending changes
            self.clear_pending_changes()
            
            logger.info("Hotkey settings reset to defaults")
            
        except Exception as e:
            logger.error(f"Failed to reset hotkey settings to defaults: {e}")

    def _on_hotkey_changed(self, action: HotkeyAction, text: str) -> None:
        """Handle hotkey input change"""
        try:
            # Validate hotkey format
            is_valid = self.hotkey_config.validate_hotkey_string(text)

            # Check for conflicts
            has_conflict = False
            if is_valid and text.strip():
                has_conflict = self.hotkey_config.has_hotkey_conflict(
                    text, exclude_action=action
                )

            # Update status indicator
            status_label = self.hotkey_status_labels[action]
            if not text.strip():
                status_label.setText("⚠")
                status_label.setStyleSheet("color: orange; font-weight: bold;")
                status_label.setToolTip("Hotkey is empty")
            elif not is_valid:
                status_label.setText("✗")
                status_label.setStyleSheet("color: red; font-weight: bold;")
                status_label.setToolTip("Invalid hotkey format")
            elif has_conflict:
                status_label.setText("⚠")
                status_label.setStyleSheet("color: orange; font-weight: bold;")
                status_label.setToolTip("Hotkey conflict detected")
            else:
                status_label.setText("✓")
                status_label.setStyleSheet("color: green; font-weight: bold;")
                status_label.setToolTip("Hotkey is valid")

            # Mark as changed
            config_key = f"hotkeys.{action.value}"
            self._mark_change(config_key, text)

            # Update conflict list
            self._update_conflicts_list()

        except Exception as e:
            logger.error(f"Error handling hotkey change: {e}")

    def _validate_all_hotkeys(self) -> None:
        """Validate all hotkey inputs"""
        try:
            for action, input_field in self.hotkey_inputs.items():
                self._on_hotkey_changed(action, input_field.text())
        except Exception as e:
            logger.error(f"Error validating hotkeys: {e}")

    def _update_conflicts_list(self) -> None:
        """Update the conflicts list widget"""
        try:
            self.conflicts_list.clear()

            # Get current hotkey values
            current_hotkeys = {}
            for action, input_field in self.hotkey_inputs.items():
                text = input_field.text().strip()
                if text:
                    current_hotkeys[action] = text

            # Find conflicts
            conflicts = []
            actions = list(current_hotkeys.keys())
            for i, action1 in enumerate(actions):
                hotkey1 = current_hotkeys[action1]
                for action2 in actions[i + 1 :]:
                    hotkey2 = current_hotkeys[action2]
                    if hotkey1.lower() == hotkey2.lower():
                        conflicts.append((action1, action2, hotkey1))

            # Display conflicts
            if conflicts:
                for action1, action2, hotkey in conflicts:
                    config1 = self.hotkey_config.get_hotkey_config(action1)
                    config2 = self.hotkey_config.get_hotkey_config(action2)

                    desc1 = config1.description if config1 else action1.value
                    desc2 = config2.description if config2 else action2.value

                    conflict_text = (
                        f"⚠ Conflict: '{hotkey}' used by both '{desc1}' and '{desc2}'"
                    )
                    self.conflicts_list.addItem(conflict_text)

                self.auto_resolve_btn.setEnabled(True)
                self.status_update.emit("Hotkey conflicts detected", "orange")
            else:
                self.conflicts_list.addItem("✓ No conflicts detected")
                self.auto_resolve_btn.setEnabled(False)

        except Exception as e:
            logger.error(f"Error updating conflicts list: {e}")

    def _auto_resolve_conflicts(self) -> None:
        """Automatically resolve hotkey conflicts"""
        try:
            # Simple resolution: append numbers to conflicting hotkeys
            used_hotkeys = set()

            for action, input_field in self.hotkey_inputs.items():
                original_hotkey = input_field.text().strip()
                if not original_hotkey:
                    continue

                resolved_hotkey = original_hotkey
                counter = 1

                while resolved_hotkey.lower() in used_hotkeys:
                    # Try different modifier combinations
                    if counter == 1:
                        resolved_hotkey = original_hotkey.replace("shift", "alt")
                    elif counter == 2:
                        resolved_hotkey = original_hotkey.replace("alt", "ctrl")
                    else:
                        # Append number to key
                        parts = original_hotkey.split("+")
                        if len(parts) > 1:
                            parts[-1] = f"{parts[-1]}{counter - 2}"
                            resolved_hotkey = "+".join(parts)

                    counter += 1
                    if counter > 10:  # Prevent infinite loop
                        break

                input_field.setText(resolved_hotkey)
                used_hotkeys.add(resolved_hotkey.lower())

            # Revalidate all hotkeys
            self._validate_all_hotkeys()

            logger.info("Auto-resolved hotkey conflicts")

        except Exception as e:
            logger.error(f"Error auto-resolving conflicts: {e}")

    def _reset_hotkeys_to_defaults(self) -> None:
        """Reset all hotkeys to default values"""
        self._reset_to_defaults_impl()