"""
Settings Dialog Manager
Main dialog coordination with tab management and settings application logic
"""

from typing import Any, Dict

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget)

from src.config.hotkey_config import PynputHotkeyConfig
from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger
from .pages import AgentSettingsPage, AuthSettingsPage, GeneralSettingsPage, HotkeySettingsPage, ProviderKeysSettingsPage
from .validator import SettingsValidator


class SettingsDialogManager(QDialog):
    """Main settings dialog with tab management and coordination"""

    settings_changed = Signal(dict)
    hotkey_changed = Signal(str, str)  # action, new_hotkey
    model_changed = Signal(str)  # new_model_id

    def __init__(
        self,
        config_manager: ConfigManager,
        ai_service_manager: Any = None,
        auth_manager: Any = None,
        parent: QWidget = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._config_manager = config_manager
        self.ai_service_manager = ai_service_manager
        self.auth_manager = auth_manager

        # Hotkey configuration manager
        self._hotkey_config = PynputHotkeyConfig()
        self._hotkey_config.load_from_config_manager(self._config_manager)

        # Settings validator and configuration manager
        self.validator = SettingsValidator()
        self.configuration_manager = self._config_manager  # Use the config manager directly

        # UI state
        self.pending_changes: Dict[str, Any] = {}
        self.restart_required_changes: set[str] = set()
        self.connection_test_results: Dict[str, Any] = {}

        # Settings pages
        self.settings_pages: Dict[str, Any] = {}

        self.setWindowTitle("AI Input Method - Settings")
        self.setModal(True)
        self.resize(800, 600)
        self.setMinimumSize(700, 500)
        
        # Set window icon
        from PySide6.QtGui import QIcon
        from pathlib import Path
        
        icon_path = Path(__file__).parent.parent.parent.parent / "resources" / "icons" / "icon.png"
        if icon_path.exists():
            settings_icon = QIcon(str(icon_path))
            self.setWindowIcon(settings_icon)

        self._setup_validation_timer()
        self._setup_ui()
        self._setup_pages()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup main dialog UI structure"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        layout.addWidget(self.tab_widget)

        # Status bar
        self._create_status_bar()
        layout.addWidget(self.status_frame)

        # Buttons
        self._create_buttons()
        layout.addLayout(self.button_layout)

    def _setup_pages(self) -> None:
        """Setup settings pages"""
        try:
            # General settings page
            self.general_page = GeneralSettingsPage(self._config_manager, self)
            self.settings_pages["general"] = self.general_page
            self.tab_widget.addTab(self.general_page, "General")

            # Authentication settings page
            self.auth_page = AuthSettingsPage(self._config_manager, self.auth_manager, self)
            self.settings_pages["auth"] = self.auth_page
            self.tab_widget.addTab(self.auth_page, "Authentication")

            # Hotkey settings page
            self.hotkey_page = HotkeySettingsPage(
                self._config_manager, self._hotkey_config, self
            )
            self.settings_pages["hotkeys"] = self.hotkey_page
            self.tab_widget.addTab(self.hotkey_page, "Hotkeys")

            # Agent settings page
            self.agent_page = AgentSettingsPage(
                self._config_manager, self.ai_service_manager, self
            )
            self.settings_pages["agents"] = self.agent_page
            self.tab_widget.addTab(self.agent_page, "Agents")

            # Provider Keys settings page
            self.provider_keys_page = ProviderKeysSettingsPage(
                self._config_manager, self.ai_service_manager, self
            )
            self.settings_pages["provider_keys"] = self.provider_keys_page
            self.tab_widget.addTab(self.provider_keys_page, "Provider Keys")

            logger.info("Settings pages initialized")

        except Exception as e:
            logger.exception(f"Failed to setup settings pages: {e}")

    def _connect_signals(self) -> None:
        """Connect signals from settings pages"""
        for page_name, page in self.settings_pages.items():
            if hasattr(page, "settings_changed"):
                page.settings_changed.connect(self._on_page_settings_changed)
            if hasattr(page, "validation_error"):
                page.validation_error.connect(self._on_validation_error)
            if hasattr(page, "status_update"):
                page.status_update.connect(self._update_status)

    def _setup_validation_timer(self) -> None:
        """Setup timer for real-time validation"""
        self.validation_timer = QTimer()
        self.validation_timer.setSingleShot(True)
        self.validation_timer.timeout.connect(self._validate_current_settings)

    def _create_status_bar(self) -> None:
        """Create status bar for feedback"""
        self.status_frame = QFrame()
        self.status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self.status_frame.setMaximumHeight(30)

        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(10, 5, 10, 5)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #666;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumWidth(200)
        status_layout.addWidget(self.progress_bar)

    def _create_buttons(self) -> None:
        """Create dialog buttons"""
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()

        # Reset to defaults button
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        self.button_layout.addWidget(self.reset_btn)

        self.button_layout.addStretch()

        # Standard buttons
        self.apply_btn = QPushButton("Apply")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")

        self.apply_btn.clicked.connect(self._apply_settings)
        self.ok_btn.clicked.connect(self._ok_clicked)
        self.cancel_btn.clicked.connect(self.reject)

        self.button_layout.addWidget(self.apply_btn)
        self.button_layout.addWidget(self.ok_btn)
        self.button_layout.addWidget(self.cancel_btn)

        # Set initial button states
        self.apply_btn.setEnabled(False)

    def _on_page_settings_changed(self, config_key: str, value: Any) -> None:
        """Handle settings change from a page"""
        try:
            # Collect all pending changes from all pages
            self._collect_pending_changes()

            # Update apply button state
            self._update_apply_button()

            # Emit signal for external listeners
            self.settings_changed.emit(self.pending_changes)

        except Exception as e:
            logger.exception(f"Error handling page settings change: {e}")

    def _collect_pending_changes(self) -> None:
        """Collect pending changes from all pages"""
        self.pending_changes.clear()
        self.restart_required_changes.clear()

        for page in self.settings_pages.values():
            if hasattr(page, "get_pending_changes"):
                page_changes = page.get_pending_changes()
                self.pending_changes.update(page_changes)

            if hasattr(page, "has_restart_required_changes") and page.has_restart_required_changes() and hasattr(page, "restart_required_changes"):
                self.restart_required_changes.update(page.restart_required_changes)

    def _update_apply_button(self) -> None:
        """Update apply button state based on pending changes"""
        has_changes = bool(self.pending_changes)
        self.apply_btn.setEnabled(has_changes)

    def _on_validation_error(self, field_name: str, error_message: str) -> None:
        """Handle validation error from a page"""
        self._update_status(f"Validation error in {field_name}: {error_message}", "red")

    def _update_status(self, message: str, color: str = "#666") -> None:
        """Update status bar message"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color};")

    def _validate_current_settings(self) -> None:
        """Validate all current settings"""
        try:
            is_valid, errors = self.validator.validate_all_settings(self.pending_changes)

            if is_valid:
                self._update_status("All settings are valid", "green")
            else:
                error_summary = f"{len(errors)} validation errors"
                self._update_status(error_summary, "red")

        except Exception as e:
            logger.exception(f"Error during settings validation: {e}")
            self._update_status("Validation error", "red")

    def _apply_settings(self) -> None:
        """Apply all pending settings"""
        try:
            # Performance monitoring removed during loguru migration
                # Validate before applying
                is_valid, errors = self.validator.validate_all_settings(self.pending_changes)
                if not is_valid:
                    error_msg = "Cannot apply settings:\n" + "\n".join(errors)
                    QMessageBox.warning(self, "Validation Error", error_msg)
                    return

                # Apply settings in each page
                success_count = 0
                total_pages = len(self.settings_pages)

                for page_name, page in self.settings_pages.items():
                    if hasattr(page, "apply_settings"):
                        if page.apply_settings():
                            success_count += 1
                        else:
                            logger.error(f"Failed to apply settings for {page_name}")

                # Update status
                if success_count == total_pages:
                    self._update_status("All settings applied successfully", "green")
                    self.apply_btn.setEnabled(False)

                    # Emit settings changed signal to notify main application
                    if self.pending_changes:
                        logger.info(f"Emitting settings_changed signal with {len(self.pending_changes)} changes")
                        self.settings_changed.emit(self.pending_changes.copy())

                    # Check if restart is required
                    if self.restart_required_changes:
                        restart_msg = (
                            "Some changes require application restart to take effect:\n"
                            + "\n".join(self.restart_required_changes)
                        )
                        QMessageBox.information(self, "Restart Required", restart_msg)

                    # Clear pending changes
                    for page in self.settings_pages.values():
                        if hasattr(page, "clear_pending_changes"):
                            page.clear_pending_changes()

                    self.pending_changes.clear()
                    self.restart_required_changes.clear()

                else:
                    self._update_status(
                        f"Applied {success_count}/{total_pages} page settings", "orange"
                    )

        except Exception as e:
            logger.exception(f"Error applying settings: {e}")
            self._update_status("Error applying settings", "red")

    def _reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        try:
            reply = QMessageBox.question(
                self,
                "Reset to Defaults",
                "Are you sure you want to reset all settings to defaults?\n"
                "This action cannot be undone.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                for page in self.settings_pages.values():
                    if hasattr(page, "reset_to_defaults"):
                        page.reset_to_defaults()

                self._update_status("Settings reset to defaults", "green")
                logger.info("All settings reset to defaults")

        except Exception as e:
            logger.exception(f"Error resetting to defaults: {e}")



    def _ok_clicked(self) -> None:
        """Handle OK button click"""
        if self.pending_changes:
            self._apply_settings()
        self.accept()

    def get_current_settings(self) -> Dict[str, Any]:
        """Get current settings from all pages"""
        current_settings = {}
        for page in self.settings_pages.values():
            if hasattr(page, "get_pending_changes"):
                current_settings.update(page.get_pending_changes())
        return current_settings

    @property
    def config_manager(self):
        """Get the configuration manager"""
        return self._config_manager

    @property
    def hotkey_config(self):
        """Get the hotkey configuration"""
        return self._hotkey_config