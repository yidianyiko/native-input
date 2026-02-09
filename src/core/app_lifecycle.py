"""
Application Lifecycle Manager
Handles application runtime, event handling, and shutdown
"""

import sys
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

try:
    from src.utils.loguru_config import logger
    from src.ui.windows.settings.settings_dialog import SettingsDialog
    from src.ui.dialogs.credentials_dialog import CredentialsErrorDialog
    from src.services.auth.auth_callback_handler import AuthCallbackHandler
    from src.platform_integration.single_instance import SingleInstanceManager
except ImportError as e:
    logger.error(f"Import error in app_lifecycle: {e}")
    raise


class AppLifecycleManager(QObject):
    """
    Manages application lifecycle including runtime, event handling, and shutdown
    """
    
    # Signals
    auth_status_changed = Signal()
    shutdown_requested = Signal()
    
    def __init__(self, components: Dict[str, Any]):
        super().__init__()
        self.logger = logger
        
        # Store component references
        self.config_manager = components.get('config_manager')
        self.floating_window = components.get('floating_window')
        self.system_tray = components.get('system_tray')
        self.hotkey_manager = components.get('hotkey_manager')
        self.ai_service_manager = components.get('ai_service_manager')
        self.auth_manager = components.get('auth_manager')
        self.single_instance = components.get('single_instance')
        self.http_server_service = components.get('http_server_service')
        
        # Runtime state
        self.is_running: bool = False
        self.settings_dialog: Optional[SettingsDialog] = None
        
        # Connect internal signals
        self.auth_status_changed.connect(self._update_components_after_auth)
        
        logger.info("AppLifecycleManager initialized")
    
    def start_application(self) -> int:
        """Start the application runtime"""
        try:
            self.is_running = True
            logger.info("AI Input Method Tool started")
            
            # Connect component signals
            self._connect_component_signals()
            
            # Show system tray
            if self.system_tray:
                self.system_tray.show()
            
            return 0
            
        except Exception as e:
            logger.error(f"Application runtime error: {e}")
            return 1
    
    def _connect_component_signals(self):
        """Connect signals between components"""
        try:
            # Connect system tray signals
            if self.system_tray:
                self.system_tray.show_settings_requested.connect(self._show_settings_dialog)
            
            # Connect hotkey manager signals
            if self.hotkey_manager:
                self.hotkey_manager.hotkey_triggered.connect(self._on_hotkey_triggered)
                self.hotkey_manager.show_floating_window.connect(self._on_show_floating_window)
            
            # Connect AI service manager signals
            if self.ai_service_manager:
                self.ai_service_manager.credentials_error.connect(self._on_credentials_error)
            
            logger.info("Component signals connected")
            
        except Exception as e:
            logger.error(f"Failed to connect component signals: {e}")
    
    def _show_settings_dialog(self):
        """Show settings dialog"""
        try:
            if not self.settings_dialog:
                self.settings_dialog = SettingsDialog(
                    config_manager=self.config_manager,
                    ai_service_manager=self.ai_service_manager,
                    auth_manager=self.auth_manager
                )
                
                # Connect settings changed signals
                self.settings_dialog.settings_changed.connect(self._on_settings_changed)
                self.settings_dialog.hotkey_changed.connect(self._on_hotkey_changed)
                self.settings_dialog.model_changed.connect(self._on_model_changed)
            
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()
            
        except Exception as e:
            logger.error(f"Failed to show settings dialog: {e}")
    
    def _on_settings_changed(self, new_settings: Dict[str, Any]) -> None:
        """Handle settings changes"""
        try:
            logger.info("⚙️ Settings changed, applying updates...")
            
            # Reload hotkeys if they changed
            if self.hotkey_manager and "hotkeys" in new_settings:
                # Unregister all existing hotkeys and register new ones
                self.hotkey_manager.unregister_all()
                hotkey_config = self.config_manager.get_hotkeys()
                self.hotkey_manager.register_hotkeys(hotkey_config)
            
            # Update floating window settings if they changed
            if self.floating_window and "ui" in new_settings:
                ui_settings = new_settings.get("ui", {}).get("floating_window", {})
                if ui_settings:
                    self.floating_window.update_settings(ui_settings)
            
            # Update AI service settings if they changed
            if self.ai_service_manager:
                # Collect all AI-related settings
                ai_related_settings = {}
                
                # Include ai_services settings
                if "ai_services" in new_settings:
                    ai_related_settings["ai_services"] = new_settings["ai_services"]
                
                # Include providers settings (for API keys)
                if "providers" in new_settings:
                    ai_related_settings["providers"] = new_settings["providers"]
                
                # Include agents settings
                if "agents" in new_settings:
                    ai_related_settings["agents"] = new_settings["agents"]
                
                if ai_related_settings:
                    self.ai_service_manager.update_settings(ai_related_settings)
            
            logger.info("Settings updates applied successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply settings changes: {e}")
    
    def _on_hotkey_changed(self, action: str, new_hotkey: str):
        """Handle hotkey change from settings dialog"""
        try:
            logger.info(f"Hotkey changed for {action}: {new_hotkey}")
            
            if self.hotkey_manager:
                # Reload hotkeys to apply the change
                self.hotkey_manager.unregister_all()
                hotkey_config = self.config_manager.get_hotkeys()
                self.hotkey_manager.register_hotkeys(hotkey_config)
                
        except Exception as e:
            logger.error(f"Failed to handle hotkey change: {e}")
    
    def _on_hotkey_triggered(self, hotkey_string: str):
        """Handle hotkey triggered signal from hotkey manager"""
        try:
            logger.info(f"Hotkey triggered in main thread: {hotkey_string}")
            
            # Show floating window in main thread
            if self.floating_window:
                self.floating_window.show_window()
                logger.info("Floating window shown from main thread")
            else:
                logger.warning("Floating window not available")
                
        except Exception as e:
            logger.error(f"Error handling hotkey trigger: {e}")
    
    def _on_show_floating_window(self):
        """Handle show floating window signal from hotkey manager"""
        try:
            logger.info(" Show floating window signal received in main thread! ")
            
            # Show floating window in main thread
            if self.floating_window:
                logger.info(" Calling floating_window.show_window()...")
                self.floating_window.show_window()
                logger.info(" Floating window shown from main thread successfully!")
            else:
                logger.warning(" Floating window not available")
                
        except Exception as e:
            logger.error(f"💥 Error handling show floating window signal: {e}")
            logger.exception("💥 Full exception details:")
    
    def _on_model_changed(self, new_model_id: str):
        """Handle AI model change from settings dialog"""
        try:
            logger.info(f"AI model changed to: {new_model_id}")
            
            if self.ai_service_manager:
                # Switch to the new model
                success = self.ai_service_manager.switch_model(new_model_id)
                if success:
                    logger.info(f"Successfully switched to model: {new_model_id}")
                    
                    # Update system tray model menu if available
                    if self.system_tray:
                        self.system_tray.refresh_model_menu()
                else:
                    logger.error(f"Failed to switch to model: {new_model_id}")
                    
        except Exception as e:
            logger.error(f"Failed to handle model change: {e}")
    
    def _on_credentials_error(self, missing_info: dict) -> None:
        """Handle credentials error from AI service manager"""
        try:
            logger.info("Showing credentials error dialog")
            
            # Create and show credentials error dialog
            dialog = CredentialsErrorDialog(missing_info, None)
            
            # Connect dialog signals
            dialog.login_requested.connect(self._on_login_requested)
            dialog.settings_requested.connect(self._on_settings_requested)
            
            # Show dialog
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error showing credentials dialog: {e}")
    
    def _on_login_requested(self) -> None:
        """Handle login request from credentials dialog"""
        try:
            if self.auth_manager:
                logger.info("Login requested from credentials dialog")
                self.auth_manager.login()
            else:
                logger.error("Auth manager not available for login")
        except Exception as e:
            logger.error(f"Error handling login request: {e}")
    
    def _on_settings_requested(self) -> None:
        """Handle settings request from credentials dialog"""
        try:
            logger.info("⚙️ Settings requested from credentials dialog")
            self._show_settings_dialog()
            
            # Switch to provider keys tab if possible
            if self.settings_dialog and hasattr(self.settings_dialog, 'tab_widget'):
                # Find provider keys tab index
                for i in range(self.settings_dialog.tab_widget.count()):
                    if self.settings_dialog.tab_widget.tabText(i) == "Provider Keys":
                        self.settings_dialog.tab_widget.setCurrentIndex(i)
                        break
                        
        except Exception as e:
            logger.error(f"Error handling settings request: {e}")
    
    def _update_components_after_auth(self) -> None:
        """Update all components after successful authentication (thread-safe)"""
        try:
            # Update AI service manager to use new API key
            if self.ai_service_manager and self.auth_manager:
                self.ai_service_manager.set_auth_manager(self.auth_manager)
                if self.ai_service_manager.initialize():
                    logger.info("AI service updated with new API key")
                else:
                    logger.error("Failed to reinitialize AI service with new API key")
            
            # Update UI components (safe to call from main thread via signal)
            if self.system_tray:
                self.system_tray.update_auth_status()
                logger.info("System tray auth status updated")
            
            # Update settings dialog if it's open
            if self.settings_dialog and hasattr(self.settings_dialog, 'auth_page'):
                self.settings_dialog.auth_page.refresh_auth_status()
                logger.info("Settings dialog auth status updated")
                
        except Exception as e:
            logger.error(f"Error updating components after authentication: {e}")
    
    def handle_auth_callback(self, api_key: str, username: str, email: Optional[str] = None) -> None:
        """Handle authentication callback from named pipe"""
        try:
            logger.info(f"Processing authentication callback for user: {username}")
            
            # Initialize auth manager if not already done
            if not self.auth_manager:
                from src.services.auth.simple_auth_manager import SimpleAuthManager
                self.auth_manager = SimpleAuthManager()
            
            # Handle the callback
            callback_success = self.auth_manager.handle_callback(api_key, username, email)
            
            if callback_success:
                logger.info("Authentication callback processed successfully")
                # Emit signal for thread-safe UI updates
                self.auth_status_changed.emit()
            else:
                logger.error(f"Failed to process authentication callback for user: {username}")
                
        except Exception as e:
            logger.error(f"Error processing authentication callback: {e}")
    
    def shutdown(self):
        """Gracefully shutdown the application"""
        try:
            logger.info("Shutting down AI Input Method Tool...")
            self.is_running = False
            
            # Cleanup single instance manager
            if self.single_instance:
                self.single_instance.cleanup()
            
            # Stop HTTP server
            if self.http_server_service:
                self.http_server_service.stop()
            
            # Cleanup components
            if self.hotkey_manager:
                self.hotkey_manager.cleanup()
            
            if self.floating_window:
                self.floating_window.close()
            
            if self.system_tray:
                self.system_tray.hide()
            
            logger.info("Application shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def create_app_lifecycle_manager(components: Dict[str, Any]) -> AppLifecycleManager:
    """Create and return app lifecycle manager"""
    return AppLifecycleManager(components)