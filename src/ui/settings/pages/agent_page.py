"""
Agent Settings Page
AI agents configuration UI with agent management and testing
"""

from typing import Any, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger

from .base_page import BaseSettingsPage


class AgentSettingsPage(BaseSettingsPage):
    """Agent settings page with agent configuration and testing"""

    def __init__(self, config_manager: ConfigManager, ai_service_manager: Any = None, parent=None):
        self.ai_service_manager = ai_service_manager
        super().__init__(config_manager, parent)

    def _setup_ui(self) -> None:
        """Setup the UI components for agent settings"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Agent Configuration
        agents_group = QGroupBox("AI Agents Configuration")
        agents_layout = QVBoxLayout(agents_group)

        # Agent selection
        agent_selection_layout = QHBoxLayout()

        agent_selection_layout.addWidget(QLabel("Select Agent:"))

        self.agent_combo = QComboBox()
        self._populate_agent_combo()
        self.agent_combo.currentTextChanged.connect(self._on_agent_changed)
        agent_selection_layout.addWidget(self.agent_combo)

        agent_selection_layout.addStretch()

        agents_layout.addLayout(agent_selection_layout)

        # Agent settings
        agent_settings_layout = QFormLayout()

        # Enable/disable agent
        self.agent_enabled_cb = QCheckBox("Enable this agent")
        self.agent_enabled_cb.stateChanged.connect(self._on_agent_enabled_changed)
        agent_settings_layout.addRow("Status:", self.agent_enabled_cb)

        # Agent prompt
        self.agent_prompt_text = QTextEdit()
        self.agent_prompt_text.setMaximumHeight(120)
        self.agent_prompt_text.setPlaceholderText(
            "Enter the system prompt for this agent..."
        )
        self.agent_prompt_text.textChanged.connect(self._on_agent_prompt_changed)
        agent_settings_layout.addRow("System Prompt:", self.agent_prompt_text)

        # Temperature setting
        self.agent_temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.agent_temperature_slider.setRange(0, 100)
        self.agent_temperature_slider.setValue(30)
        self.agent_temperature_slider.valueChanged.connect(self._on_temperature_changed)

        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.agent_temperature_slider)
        self.temperature_label = QLabel("0.3")
        self.temperature_label.setMinimumWidth(30)
        temp_layout.addWidget(self.temperature_label)

        agent_settings_layout.addRow("Temperature:", temp_layout)

        # Max tokens
        self.agent_max_tokens_spin = QSpinBox()
        self.agent_max_tokens_spin.setRange(100, 4000)
        self.agent_max_tokens_spin.setValue(1000)
        self.agent_max_tokens_spin.valueChanged.connect(self._on_max_tokens_changed)
        agent_settings_layout.addRow("Max Tokens:", self.agent_max_tokens_spin)

        agents_layout.addLayout(agent_settings_layout)

        layout.addWidget(agents_group)

        # Agent Testing
        test_group = QGroupBox("Agent Testing")
        test_layout = QVBoxLayout(test_group)

        # Test input
        self.agent_test_input = QTextEdit()
        self.agent_test_input.setMaximumHeight(60)
        self.agent_test_input.setPlaceholderText("Enter test text here...")
        test_layout.addWidget(QLabel("Test Input:"))
        test_layout.addWidget(self.agent_test_input)

        # Test button
        test_button_layout = QHBoxLayout()
        self.test_agent_btn = QPushButton("Test Agent")
        self.test_agent_btn.clicked.connect(self._test_current_agent)
        test_button_layout.addWidget(self.test_agent_btn)
        test_button_layout.addStretch()
        test_layout.addLayout(test_button_layout)

        # Test output
        self.agent_test_output = QTextEdit()
        self.agent_test_output.setMaximumHeight(80)
        self.agent_test_output.setReadOnly(True)
        self.agent_test_output.setPlaceholderText(
            "Agent test results will appear here..."
        )
        test_layout.addWidget(QLabel("Test Output:"))
        test_layout.addWidget(self.agent_test_output)

        layout.addWidget(test_group)
        layout.addStretch()

    def _populate_agent_combo(self) -> None:
        """Populate agent selection combo box from AI Service Manager"""
        try:
            self.agent_combo.clear()

            if self.ai_service_manager and hasattr(
                self.ai_service_manager, "get_available_agents"
            ):
                # Get agents from AI Service Manager
                available_agents = self.ai_service_manager.get_available_agents()

                # Get agent configuration for display names
                agents_config = self.config_manager.get("agents", {})

                # Add to combo box
                for agent_key in available_agents:
                    agent_config = agents_config.get(agent_key, {})

                    # Get friendly display name
                    display_name = agent_config.get("name")
                    if not display_name:
                        name_map = {
                            "translation": "Translation",
                            "polish": "Polish",
                            "correction": "Correction",
                        }
                        display_name = name_map.get(
                            agent_key, agent_key.replace("_", " ").title()
                        )

                    self.agent_combo.addItem(display_name)
                    self.agent_combo.setItemData(
                        self.agent_combo.count() - 1, agent_key
                    )

                logger.info(f"Populated agent combo with {len(available_agents)} agents")
            else:
                # Fallback: load from configuration
                agents_config = self.config_manager.get("agents", {})

                # Add all enabled agents from configuration
                for agent_key, agent_config in agents_config.items():
                    if not isinstance(agent_config, dict):
                        continue
                    
                    # Check if enabled and has prompt
                    enabled = agent_config.get("enabled", True)
                    prompt = agent_config.get("prompt", "").strip()
                    
                    if enabled and prompt:
                        display_name = agent_config.get("name", agent_key.replace("_", " ").title())
                        self.agent_combo.addItem(display_name)
                        self.agent_combo.setItemData(
                            self.agent_combo.count() - 1, agent_key
                        )
                        logger.info(f"Added agent to combo: {agent_key} ({display_name})")
                    elif not prompt:
                        logger.warning(f"Agent {agent_key} has empty prompt, skipping")
                    elif not enabled:
                        logger.info(f"Agent {agent_key} is disabled, skipping")

                logger.info("Populated agent combo from configuration as fallback")

        except Exception as e:
            logger.error(f"Failed to populate agent combo: {e}")

    def _load_settings(self) -> None:
        """Load current agent settings from configuration"""
        try:
            # Load settings for the first agent if available
            if self.agent_combo.count() > 0:
                self.agent_combo.setCurrentIndex(0)
                self._load_agent_settings()

            logger.info("Agent settings loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load agent settings: {e}")

    def _load_agent_settings(self) -> None:
        """Load settings for the currently selected agent"""
        try:
            current_agent = self._get_current_agent_key()
            if not current_agent:
                return

            agents_config = self.config_manager.get("agents", {})
            agent_config = agents_config.get(current_agent, {})

            # Load agent enabled status
            enabled = agent_config.get("enabled", True)
            self.agent_enabled_cb.setChecked(enabled)

            # Load agent prompt
            prompt = agent_config.get("prompt", "")
            self.agent_prompt_text.setPlainText(prompt)

            # Load temperature
            temperature = agent_config.get("temperature", 0.3)
            temperature_value = int(temperature * 100)
            self.agent_temperature_slider.setValue(temperature_value)
            self.temperature_label.setText(f"{temperature:.1f}")

            # Load max tokens
            max_tokens = agent_config.get("max_tokens", 1000)
            self.agent_max_tokens_spin.setValue(max_tokens)

        except Exception as e:
            logger.error(f"Failed to load agent settings for {current_agent}: {e}")

    def _get_current_agent_key(self) -> str:
        """Get the key of the currently selected agent"""
        current_index = self.agent_combo.currentIndex()
        if current_index >= 0:
            return self.agent_combo.itemData(current_index) or "translation"
        return "translation"

    def apply_settings(self) -> bool:
        """Apply pending agent settings changes
        
        Returns:
            bool: True if all settings applied successfully
        """
        try:
            success = True
            
            for config_key, value in self.pending_changes.items():
                try:
                    # Apply the setting to config manager
                    self.config_manager.set(config_key, value)
                    
                    logger.info(f"Applied agent setting: {config_key} = {value}")
                    
                except Exception as e:
                    logger.error(f"Failed to apply agent setting {config_key}: {e}")
                    success = False
                    
            if success:
                # Save configuration
                self.config_manager.save()
                self.status_update.emit("Agent settings applied successfully", "green")
            else:
                self.status_update.emit("Some agent settings failed to apply", "orange")
                
            return success
            
        except Exception as e:
            logger.error(f"Error applying agent settings: {e}")
            self.status_update.emit("Error applying agent settings", "red")
            return False

    def validate_settings(self) -> Tuple[bool, List[str]]:
        """Validate current agent settings
        
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        try:
            current_agent = self._get_current_agent_key()
            
            # Validate temperature
            temperature = self.agent_temperature_slider.value() / 100.0
            if not (0.0 <= temperature <= 1.0):
                errors.append(f"Temperature for {current_agent} must be between 0.0 and 1.0")
                
            # Validate max tokens
            max_tokens = self.agent_max_tokens_spin.value()
            if not (100 <= max_tokens <= 4000):
                errors.append(f"Max tokens for {current_agent} must be between 100 and 4000")
                
            # Validate prompt (should not be empty if agent is enabled)
            if self.agent_enabled_cb.isChecked():
                prompt = self.agent_prompt_text.toPlainText().strip()
                if not prompt:
                    errors.append(f"System prompt for {current_agent} cannot be empty when agent is enabled")
                    
            is_valid = len(errors) == 0
            
            if is_valid:
                logger.info("Agent settings validation passed")
            else:
                logger.error(f"Agent settings validation failed: {errors}")
                
            return is_valid, errors
            
        except Exception as e:
            error_msg = f"Agent settings validation error: {e}"
            logger.error(f"Agent settings validation error: {e}")
            return False, [error_msg]

    def _reset_to_defaults_impl(self) -> None:
        """Reset agent settings to default values"""
        try:
            # Reset to default values
            self.agent_enabled_cb.setChecked(True)
            self.agent_prompt_text.setPlainText("")
            self.agent_temperature_slider.setValue(30)
            self.temperature_label.setText("0.3")
            self.agent_max_tokens_spin.setValue(1000)
            
            # Clear test areas
            self.agent_test_input.setPlainText("")
            self.agent_test_output.setPlainText("")
            
            # Clear pending changes
            self.clear_pending_changes()
            
            logger.info("Agent settings reset to defaults")
            
        except Exception as e:
            logger.error(f"Failed to reset agent settings to defaults: {e}")

    def _on_agent_changed(self, agent_name: str) -> None:
        """Handle agent selection change"""
        try:
            # Save current agent settings if there are pending changes
            self._save_current_agent_settings()

            # Load settings for new agent
            self._load_agent_settings()

        except Exception as e:
            logger.error(f"Error changing agent: {e}")

    def _save_current_agent_settings(self) -> None:
        """Save current agent settings to pending changes"""
        try:
            current_agent = self._get_current_agent_key()
            if not current_agent:
                return

            # Save all current settings
            enabled = self.agent_enabled_cb.isChecked()
            prompt = self.agent_prompt_text.toPlainText()
            temperature = self.agent_temperature_slider.value() / 100.0
            max_tokens = self.agent_max_tokens_spin.value()

            self._mark_change(f"agents.{current_agent}.enabled", enabled)
            self._mark_change(f"agents.{current_agent}.prompt", prompt)
            self._mark_change(f"agents.{current_agent}.temperature", temperature)
            self._mark_change(f"agents.{current_agent}.max_tokens", max_tokens)

        except Exception as e:
            logger.error(f"Error saving current agent settings: {e}")

    def _on_agent_enabled_changed(self) -> None:
        """Handle agent enabled checkbox change"""
        try:
            current_agent = self._get_current_agent_key()
            enabled = self.agent_enabled_cb.isChecked()
            self._mark_change(f"agents.{current_agent}.enabled", enabled)

        except Exception as e:
            logger.error(f"Error handling agent enabled change: {e}")

    def _on_agent_prompt_changed(self) -> None:
        """Handle agent prompt text change"""
        try:
            current_agent = self._get_current_agent_key()
            prompt = self.agent_prompt_text.toPlainText()
            self._mark_change(f"agents.{current_agent}.prompt", prompt)

        except Exception as e:
            logger.error(f"Error handling agent prompt change: {e}")

    def _on_temperature_changed(self, value: int) -> None:
        """Handle temperature slider change"""
        try:
            temperature = value / 100.0
            self.temperature_label.setText(f"{temperature:.1f}")

            current_agent = self._get_current_agent_key()
            self._mark_change(f"agents.{current_agent}.temperature", temperature)

        except Exception as e:
            logger.error(f"Error changing temperature: {e}")

    def _on_max_tokens_changed(self, value: int) -> None:
        """Handle max tokens spinbox change"""
        try:
            current_agent = self._get_current_agent_key()
            self._mark_change(f"agents.{current_agent}.max_tokens", value)

        except Exception as e:
            logger.error(f"Error changing max tokens: {e}")

    def _test_current_agent(self) -> None:
        """Test current agent with sample input"""
        try:
            if not self.ai_service_manager:
                self.agent_test_output.setPlainText("AI service manager not available")
                return

            test_input = self.agent_test_input.toPlainText().strip()
            if not test_input:
                self.agent_test_output.setPlainText("Please enter test input")
                return

            current_agent = self._get_current_agent_key()

            self.status_update.emit(f"Testing {current_agent} agent...", "blue")

            # Process text with current agent
            if hasattr(self.ai_service_manager, "process_text"):
                result = self.ai_service_manager.process_text(test_input, current_agent)

                if result:
                    self.agent_test_output.setPlainText(result)
                    self.status_update.emit("Agent test completed", "green")
                else:
                    self.agent_test_output.setPlainText(
                        "Agent test failed - no result returned"
                    )
                    self.status_update.emit("Agent test failed", "red")
            else:
                self.agent_test_output.setPlainText(
                    "Agent testing not supported by current AI service manager"
                )
                self.status_update.emit("Agent testing not available", "orange")

        except Exception as e:
            self.agent_test_output.setPlainText(f"Agent test error: {str(e)}")
            self.status_update.emit("Agent test error", "red")
            logger.error(f"Agent test failed: {e}")