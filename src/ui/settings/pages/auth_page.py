"""
Authentication Settings Page
Handles user authentication status and login/logout functionality
"""


from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger

from .base_page import BaseSettingsPage


class AuthSettingsPage(BaseSettingsPage):
    """Authentication settings page for login/logout management"""

    def __init__(self, config_manager: ConfigManager, auth_manager=None, parent: QWidget = None):
        self.auth_manager = auth_manager
        super().__init__(config_manager, parent)

    def _setup_ui(self) -> None:
        """Setup authentication settings UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Authentication Status Group
        self._create_auth_status_group()
        layout.addWidget(self.auth_status_group)

        # Authentication Actions Group
        self._create_auth_actions_group()
        layout.addWidget(self.auth_actions_group)

        layout.addStretch()

    def _create_auth_status_group(self) -> None:
        """Create authentication status display group"""
        self.auth_status_group = QGroupBox("Authentication Status")
        layout = QVBoxLayout(self.auth_status_group)

        # Status display
        self.status_label = QLabel()
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.status_label)

        # User info display
        self.user_info_widget = QWidget()
        self.user_info_layout = QVBoxLayout(self.user_info_widget)
        self.user_info_layout.setContentsMargins(20, 10, 0, 0)

        self.username_label = QLabel()
        self.email_label = QLabel()
        self.login_time_label = QLabel()

        self.user_info_layout.addWidget(self.username_label)
        self.user_info_layout.addWidget(self.email_label)
        self.user_info_layout.addWidget(self.login_time_label)

        layout.addWidget(self.user_info_widget)

    def _create_auth_actions_group(self) -> None:
        """Create authentication actions group"""
        self.auth_actions_group = QGroupBox("Authentication Actions")
        layout = QVBoxLayout(self.auth_actions_group)

        # Button layout
        button_layout = QHBoxLayout()

        self.auth_button = QPushButton()
        self.auth_button.setMinimumHeight(35)
        self.auth_button.clicked.connect(self._on_auth_button_clicked)

        button_layout.addWidget(self.auth_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Info text
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(self.info_label)

    def _load_settings(self) -> None:
        """Load current authentication settings"""
        self._update_auth_display()

    def _update_auth_display(self) -> None:
        """Update authentication status display"""
        try:
            if not self.auth_manager:
                self._show_no_auth_manager()
                return

            is_authenticated = self.auth_manager.is_authenticated()

            if is_authenticated:
                self._show_authenticated_state()
            else:
                self._show_unauthenticated_state()

        except Exception as e:
            logger.error(f"Error updating auth display: {e}")
            self._show_error_state()

    def _show_authenticated_state(self) -> None:
        """Show authenticated user state"""
        user_info = self.auth_manager.get_user_info()
        
        # Status
        self.status_label.setText("Logged In")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #28a745;")

        # User info
        if user_info:
            self.username_label.setText(f"Username: {user_info.username}")
            self.username_label.setVisible(True)

            if user_info.email:
                self.email_label.setText(f"Email: {user_info.email}")
                self.email_label.setVisible(True)
            else:
                self.email_label.setVisible(False)

            if user_info.login_time:
                login_time_str = user_info.login_time.strftime("%Y-%m-%d %H:%M:%S")
                self.login_time_label.setText(f"Login Time: {login_time_str}")
                self.login_time_label.setVisible(True)
            else:
                self.login_time_label.setVisible(False)
        else:
            self.username_label.setText("Username: Unknown")
            self.email_label.setVisible(False)
            self.login_time_label.setVisible(False)

        self.user_info_widget.setVisible(True)

        # Button
        self.auth_button.setText("Logout")
        self.auth_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")

        # Info
        self.info_label.setText("You are currently logged in. Your API key is being used for AI services.")

    def _show_unauthenticated_state(self) -> None:
        """Show unauthenticated state"""
        # Status
        self.status_label.setText("Not Logged In")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #dc3545;")

        # Hide user info
        self.user_info_widget.setVisible(False)

        # Button
        self.auth_button.setText("Login")
        self.auth_button.setStyleSheet("QPushButton { background-color: #007bff; color: white; }")

        # Info
        self.info_label.setText("Click Login to authenticate and get your API key. This will open your browser for secure login.")

    def _show_no_auth_manager(self) -> None:
        """Show state when auth manager is not available"""
        # Status
        self.status_label.setText("Authentication Not Available")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffc107;")

        # Hide user info
        self.user_info_widget.setVisible(False)

        # Button
        self.auth_button.setText("Login")
        self.auth_button.setEnabled(False)
        self.auth_button.setStyleSheet("")

        # Info
        self.info_label.setText("Authentication manager is not available. Please check your configuration.")

    def _show_error_state(self) -> None:
        """Show error state"""
        # Status
        self.status_label.setText("Authentication Error")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #dc3545;")

        # Hide user info
        self.user_info_widget.setVisible(False)

        # Button
        self.auth_button.setText("Retry")
        self.auth_button.setStyleSheet("")

        # Info
        self.info_label.setText("An error occurred while checking authentication status.")

    def _on_auth_button_clicked(self) -> None:
        """Handle authentication button click"""
        try:
            if not self.auth_manager:
                logger.error("Auth manager not available")
                return

            is_authenticated = self.auth_manager.is_authenticated()

            if is_authenticated:
                # Logout
                logger.info("Logout requested from settings")
                self.auth_manager.logout()
                self.status_update.emit("Logged out successfully", "#28a745")
            else:
                # Login
                logger.info("Login requested from settings")
                if self.auth_manager.login():
                    self.status_update.emit("Browser opened for login", "#007bff")
                else:
                    self.status_update.emit("Failed to start login process", "#dc3545")

            # Update display
            self._update_auth_display()

        except Exception as e:
            logger.error(f"Error handling auth button click: {e}")
            self.status_update.emit(f"Authentication error: {str(e)}", "#dc3545")

    def refresh_auth_status(self) -> None:
        """Refresh authentication status (called externally)"""
        self._update_auth_display()

    def set_auth_manager(self, auth_manager) -> None:
        """Set authentication manager reference"""
        self.auth_manager = auth_manager
        self._update_auth_display()

    def get_pending_changes(self) -> dict:
        """Get pending changes (authentication doesn't have config changes)"""
        return {}

    def apply_settings(self) -> bool:
        """Apply settings (authentication doesn't have config changes)"""
        return True
    
    def validate_settings(self) -> tuple[bool, list[str]]:
        """Validate settings (authentication doesn't need validation)"""
        return True, []
    
    def _reset_to_defaults_impl(self) -> None:
        """Reset to defaults (authentication doesn't have defaults)"""

    def reset_to_defaults(self) -> None:
        """Reset to defaults (authentication doesn't have defaults)"""

    def validate_settings(self) -> tuple[bool, list[str]]:
        """Validate settings (authentication doesn't need validation)"""
        return True, []