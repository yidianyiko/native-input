"""
System Tray UI Component
Provides system tray integration with menu and notifications
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from src.config.config import ConfigManager
from src.utils.loguru_config import logger, get_logger


class SystemTray(QObject):
    """System tray integration for AI Input Method Tool"""

    # Signals
    show_floating_window_requested = Signal()
    show_settings_requested = Signal()
    exit_requested = Signal()

    def __init__(
        self,
        config_manager: ConfigManager,
        floating_window=None,
        ai_service_manager=None,
        auth_manager=None):
        super().__init__()
        self.logger = get_logger(__name__)
        self.config_manager = config_manager
        self.floating_window = floating_window
        self.ai_service_manager = ai_service_manager
        self.auth_manager = auth_manager

        # System tray icon
        self.tray_icon: QSystemTrayIcon | None = None
        self.tray_menu: QMenu | None = None
        self.model_menu: QMenu | None = None
        self.model_actions = {}  # Store model actions for checkmark updates

        self._setup_tray_icon()
        self._setup_menu()
        self._connect_signals()

    def _setup_tray_icon(self):
        """Setup system tray icon"""
        try:
            # Create tray icon
            self.tray_icon = QSystemTrayIcon()

            # Set icon (use default for now, can be customized later)
            icon = self._create_default_icon()
            self.tray_icon.setIcon(icon)

            # Set tooltip
            self.tray_icon.setToolTip("AI Input Method Tool")

        except Exception as e:
            self.logger.error(f"Failed to setup tray icon: {e}")

    def _create_default_icon(self) -> QIcon:
        """Create default application icon"""
        try:
            # Try to load icon from resources
            icon_path = "resources/icons/icon.png"
            icon = QIcon(icon_path)
            
            # If still null, try absolute path
            if icon.isNull():
                from pathlib import Path
                abs_icon_path = Path(__file__).parent.parent.parent / "resources" / "icons" / "icon.png"
                if abs_icon_path.exists():
                    icon = QIcon(str(abs_icon_path))

            if icon.isNull():
                # Create simple text-based icon as fallback
                from PySide6.QtGui import QColor, QFont, QPainter, QPixmap

                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

                painter = QPainter(pixmap)
                painter.setFont(QFont("Arial", 16, QFont.Weight.Bold))
                painter.setPen(QColor(201, 228, 126))  # Light green color
                painter.drawText(pixmap.rect(), 0, "AI")
                painter.end()

                icon = QIcon(pixmap)

            return icon

        except Exception as e:
            self.logger.error(f"Failed to create icon: {e}")
            return QIcon()  # Empty icon as fallback

    def _setup_menu(self):
        """Setup context menu for tray icon"""
        try:
            self.tray_menu = QMenu()

            # Show Floating Window action
            show_action = QAction("Show Floating Window", self)
            show_action.triggered.connect(self._on_show_floating_window)
            self.tray_menu.addAction(show_action)

            self.tray_menu.addSeparator()

            # Switch Model submenu
            self._setup_model_menu()

            self.tray_menu.addSeparator()

            # Authentication menu - Hidden from users
            # self._setup_auth_menu()

            # self.tray_menu.addSeparator()

            # Settings action
            settings_action = QAction("Settings...", self)
            settings_action.triggered.connect(self._on_show_settings)
            self.tray_menu.addAction(settings_action)

            self.tray_menu.addSeparator()

            self.tray_menu.addSeparator()

            # About action (placeholder for P2)
            about_action = QAction("About", self)
            about_action.triggered.connect(self._on_about)
            about_action.setEnabled(False)  # Disabled for P0
            self.tray_menu.addAction(about_action)

            self.tray_menu.addSeparator()

            # Exit action
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self._on_exit)
            self.tray_menu.addAction(exit_action)

            # Set context menu
            if self.tray_icon:
                self.tray_icon.setContextMenu(self.tray_menu)

        except Exception as e:
            self.logger.error(f"Failed to setup tray menu: {e}")

    def _connect_signals(self):
        """Connect tray icon signals"""
        try:
            if self.tray_icon:
                # Double-click to show floating window
                self.tray_icon.activated.connect(self._on_tray_activated)

        except Exception as e:
            self.logger.error(f"Failed to connect tray signals: {e}")

    def _on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self._on_show_floating_window()

    def _on_show_floating_window(self):
        """Handle show floating window request"""
        try:
            if self.floating_window:
                self.floating_window.show_at_cursor()
            self.show_floating_window_requested.emit()
        except Exception as e:
            self.logger.error(f"Failed to show floating window: {e}")

    def _on_show_settings(self):
        """Handle show settings request"""
        try:
            logger.info("Settings requested from system tray")
            self.show_settings_requested.emit()
        except Exception as e:
            self.logger.error(f"Failed to handle settings request: {e}")

    def _on_about(self):
        """Handle about request (P2 feature)"""
        self.logger.info("About requested (not implemented in P0)")

    def _setup_model_menu(self):
        """Setup model switching submenu with categories"""
        try:
            if not self.ai_service_manager:
                return

            self.model_menu = QMenu("Switch Model", parent=None)
            self.tray_menu.addMenu(self.model_menu)

            # Get all available models
            available_models = self.ai_service_manager.get_available_models()
            current_model = self.ai_service_manager.get_current_model()
            
            # If no models are initialized, show a message
            if not available_models:
                no_models_action = QAction("No models available - Check credentials", self)
                no_models_action.setEnabled(False)
                self.model_menu.addAction(no_models_action)
                return

            self.model_actions.clear()
            
            # Create action group for exclusive selection (single choice)
            from PySide6.QtGui import QActionGroup
            self.model_action_group = QActionGroup(self)

            # Group models by category
            categories = {}
            for model_id, model_info in available_models.items():
                category = model_info.get("category", "other")
                if category not in categories:
                    categories[category] = []
                categories[category].append((model_id, model_info))

            # Create submenus for each category
            category_order = ["chat", "code", "realtime", "instruct", "other"]
            category_names = {
                "chat": "Chat Models",
                "code": "Code Models",
                "realtime": "Realtime Models",
                "instruct": "Instruct Models",
                "other": "Other Models",
            }

            for category in category_order:
                if category not in categories:
                    continue

                models_in_category = categories[category]
                if not models_in_category:
                    continue

                # Create submenu for category
                category_menu = QMenu(
                    category_names.get(category, category.title()), parent=None
                )
                self.model_menu.addMenu(category_menu)

                # Sort models by provider and name
                models_in_category.sort(
                    key=lambda x: (x[1].get("provider", ""), x[1].get("name", ""))
                )

                for model_id, model_info in models_in_category:
                    display_name = model_info.get("name", model_id)
                    provider = model_info.get("provider", "Unknown")

                    # Create action with provider info
                    action_text = f"{display_name} ({provider})"
                    action = QAction(action_text, self)
                    action.setCheckable(True)
                    action.setChecked(model_id == current_model)
                    action.triggered.connect(
                        lambda _, mid=model_id: self._on_model_switch(mid)
                    )

                    # Add tooltip with description
                    description = model_info.get(
                        "description", "No description available"
                    )
                    action.setToolTip(description)

                    # Add to action group for exclusive selection
                    self.model_action_group.addAction(action)
                    category_menu.addAction(action)
                    self.model_actions[model_id] = action

            # Add separator and current model info
            self.model_menu.addSeparator()
            current_info = available_models.get(current_model, {})
            current_display = (
                current_info.get("name", current_model)
                if current_info
                else current_model
            )
            current_action = QAction(f"Current: {current_display}", self)
            current_action.setEnabled(False)
            self.model_menu.addAction(current_action)

        except Exception as e:
            self.logger.error(f"Failed to setup model menu: {e}")

    def _setup_auth_menu(self):
        """Setup authentication menu items - DISABLED FOR USER VERSION"""
        # Authentication menu is hidden from users
        # This method is kept for potential future use or admin versions
        return

    def _on_login_clicked(self):
        """Handle login button click"""
        try:
            if not self.auth_manager:
                logger.error("Auth manager not available")
                return

            logger.info("Login requested from system tray")
            
            if self.auth_manager.login():
                self.show_notification("Login", "Browser opened for login", 2000)
                logger.info("Login process initiated")
            else:
                self.show_notification("Login Failed", "Failed to start login process", 3000)
                logger.error("Failed to start login process")

        except Exception as e:
            logger.error(f"Error handling login click: {e}")
            self.show_notification("Login Error", f"Error: {str(e)}", 3000)

    def _on_logout_clicked(self):
        """Handle logout button click"""
        try:
            if not self.auth_manager:
                logger.error("Auth manager not available")
                return

            logger.info("Logout requested from system tray")
            
            self.auth_manager.logout()
            self.show_notification("Logout", "Successfully logged out", 2000)
            logger.info("Logout completed")
            
            # Update menu to reflect new auth status
            self._update_auth_status(False)

        except Exception as e:
            logger.error(f"Error handling logout click: {e}")
            self.show_notification("Logout Error", f"Error: {str(e)}", 3000)

    def _update_auth_status(self, is_authenticated: bool):
        """Update authentication status in menu - DISABLED FOR USER VERSION"""
        # Authentication status updates are disabled for user version
        # Menu does not include auth components
        try:
            auth_status = "authenticated" if is_authenticated else "not authenticated"
            logger.info(f"Auth status change ignored (user version): {auth_status}")

        except Exception as e:
            logger.error(f"Error in auth status update: {e}")

    def _on_model_switch(self, model_id: str):
        """Handle model switch request"""
        try:
            if not self.ai_service_manager:
                logger.error("AI service manager not available for model switch")
                return

            logger.info(f"Attempting to switch model to: {model_id}")

            # Switch model
            success = self.ai_service_manager.switch_model(model_id)

            if success:
                # Update checkmarks
                self._update_model_checkmarks(model_id)

                # Show notification with model ID (simple and reliable)
                self.show_notification(
                    "Model Switched", f"Successfully switched to {model_id}", 2000
                )

                logger.info(f"Model successfully switched to: {model_id}")

                # Log agent reinitialization
                available_agents = self.ai_service_manager.get_available_agents()
                logger.info(f"Agents reinitialized: {available_agents}",
                    extra={"agents": available_agents, "model": model_id})

            else:
                self.show_notification(
                    "Model Switch Failed", f"Failed to switch to {model_id}", 3000
                )
                logger.error(f"Failed to switch to model: {model_id}")

        except Exception as e:
            logger.error(f"Error switching model to {model_id}: {e}")
            self.show_notification(
                "Model Switch Error", f"Error switching model: {str(e)}", 3000
            )

    def _update_model_checkmarks(self, selected_model_id: str):
        """Update checkmarks for model actions"""
        try:
            # QActionGroup automatically handles exclusive selection,
            # but we still need to update the checked state manually
            if selected_model_id in self.model_actions:
                self.model_actions[selected_model_id].setChecked(True)
        except Exception as e:
            self.logger.error(f"Failed to update model checkmarks: {e}")

    def refresh_model_menu(self):
        """Refresh the model menu (useful when models change)"""
        try:
            if self.model_menu:
                self.model_menu.clear()
                self.model_actions.clear()
                self._setup_model_menu()
        except Exception as e:
            self.logger.error(f"Failed to refresh model menu: {e}")

    def _on_exit(self):
        """Handle exit request"""
        try:
            self.logger.info("Exit requested from system tray")
            self.exit_requested.emit()
            QApplication.quit()
        except Exception as e:
            self.logger.error(f"Failed to handle exit request: {e}")

    def show(self):
        """Show system tray icon"""
        try:
            if self.tray_icon and QSystemTrayIcon.isSystemTrayAvailable():
                self.tray_icon.show()
                self.logger.info("System tray icon shown")
            else:
                self.logger.warning("System tray not available")
        except Exception as e:
            self.logger.error(f"Failed to show system tray: {e}")

    def hide(self):
        """Hide system tray icon"""
        try:
            if self.tray_icon:
                self.tray_icon.hide()
                self.logger.info("System tray icon hidden")
        except Exception as e:
            self.logger.error(f"Failed to hide system tray: {e}")

    def show_notification(self, title: str, message: str, duration: int = 3000):
        """Show system tray notification"""
        try:
            if self.tray_icon and self.config_manager.get(
                "ui.system_tray.show_notifications", True
            ):
                self.tray_icon.showMessage(
                    title, message, QSystemTrayIcon.MessageIcon.Information, duration
                )

        except Exception as e:
            self.logger.error(f"Failed to show notification: {e}")

    def update_tooltip(self, tooltip: str):
        """Update tray icon tooltip"""
        try:
            if self.tray_icon:
                self.tray_icon.setToolTip(tooltip)
        except Exception as e:
            self.logger.error(f"Failed to update tooltip: {e}")

    def update_auth_status(self):
        """Update authentication status (called externally when auth state changes) - DISABLED FOR USER VERSION"""
        # Authentication status updates are disabled for user version
        # No auth-related notifications or UI changes
        try:
            logger.info("External auth status update ignored (user version)")
                
        except Exception as e:
            logger.error(f"Error in auth status update: {e}")
