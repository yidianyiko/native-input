"""
Provider API Keys Settings Page
Handles configuration of provider-specific API keys (第二类密钥)
"""

from typing import Dict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QFrame
)

from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger
from src.services.auth.credential_manager import CredentialManager

from .base_page import BaseSettingsPage


class ProviderKeyWidget(QWidget):
    """Widget for configuring a single provider's API key"""
    
    key_changed = Signal(str, str)  # provider, key
    test_requested = Signal(str)    # provider
    
    def __init__(self, provider: str, provider_info: dict, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.provider_info = provider_info
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup provider key configuration UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Provider header
        header_layout = QHBoxLayout()
        
        # Provider name and status
        self.name_label = QLabel(f"{self.provider.title()}")
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(self.name_label)
        
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-size: 12px;")
        header_layout.addWidget(self.status_label)
        
        header_layout.addStretch()
        
        # Test button
        self.test_button = QPushButton("Test")
        self.test_button.setMaximumWidth(80)
        self.test_button.clicked.connect(lambda: self.test_requested.emit(self.provider))
        header_layout.addWidget(self.test_button)
        
        layout.addLayout(header_layout)
        
        # API Key input
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API Key:"))
        
        self.key_input = QLineEdit()
        self.key_input.setEchoMode(QLineEdit.Password)
        self.key_input.setPlaceholderText(f"Enter your {self.provider.title()} API key...")
        self.key_input.textChanged.connect(self._on_key_changed)
        key_layout.addWidget(self.key_input)
        
        # Show/Hide button
        self.show_button = QPushButton("👁")
        self.show_button.setMaximumWidth(30)
        self.show_button.setCheckable(True)
        self.show_button.toggled.connect(self._toggle_key_visibility)
        key_layout.addWidget(self.show_button)
        
        layout.addLayout(key_layout)
        
        # Base URL (read-only)
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("Base URL:"))
        
        self.url_label = QLabel(self.provider_info.get('base_url', 'N/A'))
        self.url_label.setStyleSheet("color: #666; font-family: monospace;")
        url_layout.addWidget(self.url_label)
        
        layout.addLayout(url_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #ddd;")
        layout.addWidget(separator)
    
    def _on_key_changed(self):
        """Handle API key change"""
        key = self.key_input.text().strip()
        self.key_changed.emit(self.provider, key)
        self._update_status()
    
    def _toggle_key_visibility(self, show: bool):
        """Toggle API key visibility"""
        if show:
            self.key_input.setEchoMode(QLineEdit.Normal)
            self.show_button.setText("🙈")
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
            self.show_button.setText("👁")
    
    def set_key(self, key: str):
        """Set API key value"""
        self.key_input.setText(key or "")
        self._update_status()
    
    def get_key(self) -> str:
        """Get current API key value"""
        return self.key_input.text().strip()
    
    def _update_status(self):
        """Update provider status"""
        key = self.get_key()
        if key:
            self.status_label.setText("Configured")
            self.status_label.setStyleSheet("color: #28a745; font-size: 12px;")
            self.test_button.setEnabled(True)
        else:
            self.status_label.setText("Not configured")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
            self.test_button.setEnabled(False)
    
    def set_test_result(self, success: bool, message: str = ""):
        """Set test result status"""
        if success:
            self.status_label.setText("Test passed")
            self.status_label.setStyleSheet("color: #28a745; font-size: 12px;")
        else:
            self.status_label.setText(f"Test failed: {message}")
            self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")


class ProviderKeysSettingsPage(BaseSettingsPage):
    """Provider API keys settings page"""
    
    def __init__(self, config_manager: ConfigManager, ai_service_manager=None, parent: QWidget = None):
        self.ai_service_manager = ai_service_manager
        self.credential_manager = CredentialManager(config_manager) if config_manager else None
        self.provider_widgets: Dict[str, ProviderKeyWidget] = {}
        self.pending_keys: Dict[str, str] = {}
        
        super().__init__(config_manager, parent)
    
    def _setup_ui(self) -> None:
        """Setup provider keys settings UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        
        # Header
        header_layout = QVBoxLayout()
        
        title_label = QLabel("Provider API Keys")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header_layout.addWidget(title_label)
        
        info_label = QLabel(
            "Configure API keys for direct provider access. These keys have higher priority than gateway credentials."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-bottom: 15px;")
        header_layout.addWidget(info_label)
        
        main_layout.addLayout(header_layout)
        
        # Scroll area for providers
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        self.providers_layout = QVBoxLayout(scroll_widget)
        self.providers_layout.setSpacing(10)
        
        # Create provider widgets
        self._create_provider_widgets()
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # Action buttons
        self._create_action_buttons()
        main_layout.addLayout(self.action_layout)
    
    def _create_provider_widgets(self):
        """Create widgets for all providers"""
        if not self.credential_manager:
            return
        
        providers = {
            "deepseek": {
                "name": "DeepSeek",
                "base_url": "https://api.deepseek.com",
                "description": "DeepSeek AI models"
            },
            "openai": {
                "name": "OpenAI", 
                "base_url": "https://api.openai.com/v1",
                "description": "GPT models from OpenAI"
            },
            "qwen": {
                "name": "Qwen",
                "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "description": "Qwen models from Alibaba"
            },

        }
        
        for provider_id, provider_info in providers.items():
            widget = ProviderKeyWidget(provider_id, provider_info)
            widget.key_changed.connect(self._on_provider_key_changed)
            widget.test_requested.connect(self._on_test_provider)
            
            self.provider_widgets[provider_id] = widget
            self.providers_layout.addWidget(widget)
    
    def _create_action_buttons(self):
        """Create action buttons"""
        self.action_layout = QHBoxLayout()
        
        # Test all button
        self.test_all_button = QPushButton("Test All")
        self.test_all_button.clicked.connect(self._on_test_all)
        self.action_layout.addWidget(self.test_all_button)
        
        self.action_layout.addStretch()
        
        # Clear all button
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.setStyleSheet("QPushButton { color: #dc3545; }")
        self.clear_all_button.clicked.connect(self._on_clear_all)
        self.action_layout.addWidget(self.clear_all_button)
    
    def _load_settings(self) -> None:
        """Load current provider key settings"""
        if not self.config_manager:
            return
        
        for provider_id, widget in self.provider_widgets.items():
            # Load from config
            key = self.config_manager.get(f"providers.{provider_id}.api_key", "")
            widget.set_key(key)
    
    def _on_provider_key_changed(self, provider: str, key: str):
        """Handle provider key change"""
        self.pending_keys[provider] = key
        logger.info(f"Provider key changed: {provider}")
        
        # Emit signal to notify parent dialog about the change
        config_key = f"providers.{provider}.api_key"
        self.settings_changed.emit(config_key, key)
    
    def _on_test_provider(self, provider: str):
        """Test single provider connection"""
        try:
            if not self.ai_service_manager:
                self.status_update.emit("AI service manager not available", "#dc3545")
                return
            
            widget = self.provider_widgets.get(provider)
            if not widget:
                return
            
            # Get the current API key from the widget
            api_key = widget.get_key()
            if not api_key:
                widget.set_test_result(False, "No API key configured")
                self.status_update.emit(f"{provider.title()} test failed: No API key", "#dc3545")
                return
            
            # Temporarily apply the API key to config for testing
            config_key = f"providers.{provider}.api_key"
            original_value = self.config_manager.get(config_key, "")
            
            # Test connection with the provided API key
            if hasattr(self.ai_service_manager, 'test_provider_with_key'):
                success = self.ai_service_manager.test_provider_with_key(provider, api_key)
            else:
                # Fallback to original method
                try:
                    # Set the API key temporarily
                    self.config_manager.set(config_key, api_key)
                    
                    # Reinitialize the AI service manager to use the new key
                    if hasattr(self.ai_service_manager, 'initialize'):
                        self.ai_service_manager.initialize()
                    
                    # Test connection
                    success = self.ai_service_manager.test_connection(provider)
                    
                finally:
                    # Restore original value
                    self.config_manager.set(config_key, original_value)
            
            if success:
                widget.set_test_result(True)
                self.status_update.emit(f"{provider.title()} connection test passed", "#28a745")
            else:
                widget.set_test_result(False, "Connection failed")
                self.status_update.emit(f"{provider.title()} connection test failed", "#dc3545")
                
        except Exception as e:
            logger.error(f"Error testing {provider}: {e}")
            widget.set_test_result(False, str(e))
            self.status_update.emit(f"Error testing {provider}: {str(e)}", "#dc3545")
    
    def _on_test_all(self):
        """Test all configured providers"""
        configured_providers = [p for p, w in self.provider_widgets.items() if w.get_key()]
        
        if not configured_providers:
            self.status_update.emit("No providers configured to test", "#ffc107")
            return
        
        for provider in configured_providers:
            self._on_test_provider(provider)
    
    def _on_clear_all(self):
        """Clear all provider keys"""
        for widget in self.provider_widgets.values():
            widget.set_key("")
        
        self.pending_keys.clear()
        self.status_update.emit("All provider keys cleared", "#28a745")
    
    def get_pending_changes(self) -> dict:
        """Get pending configuration changes"""
        changes = {}
        
        for provider, key in self.pending_keys.items():
            config_key = f"providers.{provider}.api_key"
            current_value = self.config_manager.get(config_key, "")
            
            if key != current_value:
                changes[config_key] = key
        
        return changes
    
    def apply_settings(self) -> bool:
        """Apply provider key settings"""
        try:
            success = True
            
            for provider, key in self.pending_keys.items():
                config_key = f"providers.{provider}.api_key"
                if not self.config_manager.set(config_key, key):
                    success = False
                    logger.error(f"Failed to save {provider} API key")
            
            if success:
                # Save configuration
                self.config_manager.save()
                self.pending_keys.clear()
                logger.info("Provider API keys saved successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Error applying provider key settings: {e}")
            return False
    
    def validate_settings(self) -> tuple[bool, list[str]]:
        """Validate provider key settings"""
        errors = []
        
        # Basic validation for key formats
        for provider, key in self.pending_keys.items():
            if key:  # Only validate non-empty keys
                if provider == "openai" and not key.startswith("sk-"):
                    errors.append(f"OpenAI API key should start with 'sk-'")
                elif len(key) < 10:
                    errors.append(f"{provider.title()} API key seems too short")
        
        return len(errors) == 0, errors
    
    def _reset_to_defaults_impl(self) -> None:
        """Reset provider keys to defaults (empty)"""
        for widget in self.provider_widgets.values():
            widget.set_key("")
        self.pending_keys.clear()
    
    def set_ai_service_manager(self, ai_service_manager):
        """Set AI service manager reference"""
        self.ai_service_manager = ai_service_manager