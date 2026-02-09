"""
Application Initializer
Handles application initialization and component setup
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QSystemTrayIcon

try:
    from src.utils.loguru_config import logger
    from src.config.config import ConfigManager
    from src.config.config_validator import validate_startup_config
    from src.services.ai.ai_service import AIService
    from src.services.system.pynput_hotkey_manager import PynputHotkeyManager as HotkeyManager
    from src.services.auth.simple_auth_manager import SimpleAuthManager
    from src.ui import FloatingWindow
    from src.ui.windows.settings.settings_dialog import SettingsDialog
    from src.ui.system_tray import SystemTray
    from src.ui.dialogs.credentials_dialog import CredentialsErrorDialog
    from src.platform_integration.single_instance import SingleInstanceManager
    from src.core import (
        set_container,
        BusinessLogicContainer,
        get_configuration_manager,
        get_text_processing_logic
    )
    from src.core.interfaces import (
        IConfigurationManager,
        ITextProcessingBusinessLogic
    )
    from src.services.http_server.http_server import HttpServerService
except ImportError as e:
    logger.error(f"Import error in app_initializer: {e}")
    raise


class AppInitializer(QObject):
    """
    Handles application initialization and component setup
    """
    
    # Signals
    initialization_progress = Signal(str, int)  # message, progress_percentage
    initialization_complete = Signal(bool)  # success
    
    def __init__(self):
        super().__init__()
        self.logger = logger
        
        # Core components
        self.config_manager: Optional[ConfigManager] = None
        self.floating_window: Optional[FloatingWindow] = None
        self.system_tray: Optional[SystemTray] = None
        self.settings_dialog: Optional[SettingsDialog] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.ai_service_manager: Optional[AIService] = None
        self.auth_manager: Optional[SimpleAuthManager] = None
        self.single_instance: Optional[SingleInstanceManager] = None
        self.http_server_service: Optional[HttpServerService] = None
        
        # Core business logic interfaces
        self.configuration_logic: Optional[IConfigurationManager] = None
        self.text_processing_logic: Optional[ITextProcessingBusinessLogic] = None
        
        logger.info("AppInitializer created")
    
    def initialize(self, config_dir: str, auth_callback_handler) -> bool:
        """
        Initialize all application components
        
        Args:
            config_dir: Configuration directory path
            auth_callback_handler: Authentication callback handler function
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("System initializing...")
            
            # Step 1: Initialize core business logic
            self.initialization_progress.emit("Initializing core business logic...", 10)
            if not self._initialize_core_business_logic():
                return False
            
            # Step 2: Initialize configuration
            self.initialization_progress.emit("Loading configuration...", 20)
            if not self._initialize_configuration(config_dir):
                return False
            
            # Step 3: Initialize authentication manager
            self.initialization_progress.emit("Initializing authentication...", 30)
            if not self._initialize_auth_manager():
                return False
            
            # Step 4: Initialize AI service manager
            self.initialization_progress.emit("Initializing AI services...", 40)
            if not self._initialize_ai_service_manager():
                return False
            
            # Step 5: Initialize floating window
            self.initialization_progress.emit("Initializing floating window...", 50)
            if not self._initialize_floating_window():
                return False
            
            # Step 5.5: Initialize HTTP server for external input
            self.initialization_progress.emit("Initializing HTTP server...", 55)
            if not self._initialize_http_server():
                # Non-critical: continue without HTTP server
                logger.warning("HTTP server initialization failed, continuing without it")
            
            # Step 6: Initialize system tray
            self.initialization_progress.emit("Initializing system tray...", 60)
            if not self._initialize_system_tray():
                return False
            
            # Step 7: Initialize hotkey manager
            self.initialization_progress.emit("Initializing hotkey manager...", 70)
            if not self._initialize_hotkey_manager():
                return False
            
            # Step 8: Initialize single instance manager
            self.initialization_progress.emit("Initializing single instance manager...", 80)
            if not self._initialize_single_instance_manager(auth_callback_handler):
                return False
            
            # Step 9: Register URL scheme
            self.initialization_progress.emit("Registering URL scheme...", 90)
            self._register_url_scheme()
            
            # Step 10: Complete initialization
            self.initialization_progress.emit("Initialization complete", 100)
            logger.info("Application initialized successfully")
            self.initialization_complete.emit(True)
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            self.initialization_complete.emit(False)
            return False
    
    def _initialize_core_business_logic(self) -> bool:
        """Initialize core business logic components"""
        try:
            # Create and configure the container
            container = BusinessLogicContainer()
            set_container(container)
            
            # Get business logic instances from container
            self.configuration_logic = get_configuration_manager()
            self.text_processing_logic = get_text_processing_logic()
            
            logger.info("Core business logic initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize core business logic: {e}")
            return False
    
    def _initialize_configuration(self, config_dir: str) -> bool:
        """Initialize configuration manager"""
        try:
            self.config_manager = ConfigManager(config_dir)
            
            # Validate configuration for security issues
            if not validate_startup_config(self.config_manager):
                logger.error("Configuration validation failed - check .env file")
                return False
            
            # New config system auto-loads, just validate
            if not self.config_manager.validate():
                logger.error("Configuration validation failed")
                return False
            
            logger.info("Configuration loaded and validated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize configuration: {e}")
            return False
    
    def _initialize_auth_manager(self) -> bool:
        """Initialize authentication manager"""
        try:
            self.auth_manager = SimpleAuthManager(config_manager=self.config_manager)
            logger.info("Authentication manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize authentication manager: {e}")
            return False
    
    def _initialize_ai_service_manager(self) -> bool:
        """Initialize AI service manager"""
        try:
            self.ai_service_manager = AIService(self.config_manager, self.auth_manager)
            
            if not self.ai_service_manager.initialize():
                logger.error("Failed to initialize AI service manager, continuing with limited functionality")
                # Continue initialization even if AI service fails
            
            logger.info("AI service manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI service manager: {e}")
            return False
    
    def _initialize_floating_window(self) -> bool:
        """Initialize floating window"""
        try:
            self.floating_window = FloatingWindow(
                config_manager=self.config_manager,
                ai_service_manager=self.ai_service_manager
            )
            
            # Pre-initialize floating window for better first-time focus
            self._pre_initialize_floating_window()
            
            logger.info("Floating window initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize floating window: {e}")
            return False
    
    def _initialize_http_server(self) -> bool:
        """Initialize embedded HTTP server for external input"""
        try:
            enabled = self.config_manager.get("http_server.enabled", False)
            if not enabled:
                logger.info("HTTP server is disabled in configuration")
                return True  # Not an error, just disabled
            
            host = self.config_manager.get("http_server.host", "127.0.0.1")
            port = int(self.config_manager.get("http_server.port", 18599))
            
            self.http_server_service = HttpServerService(host=host, port=port)
            
            # Connect signal: when text arrives via HTTP, show it in the floating window
            if self.floating_window:
                self.http_server_service.bridge.text_received.connect(
                    self.floating_window.receive_external_input
                )
            
            self.http_server_service.start()
            logger.info(f"HTTP server initialized on {host}:{port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize HTTP server: {e}")
            return False
    
    def _initialize_system_tray(self) -> bool:
        """Initialize system tray"""
        try:
            # Check system tray availability
            if not QSystemTrayIcon.isSystemTrayAvailable():
                logger.error("System tray is not available on this system")
                return False
            
            self.system_tray = SystemTray(
                config_manager=self.config_manager,
                floating_window=self.floating_window,
                ai_service_manager=self.ai_service_manager,
                auth_manager=self.auth_manager
            )
            
            logger.info("System tray initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize system tray: {e}")
            return False
    
    def _initialize_hotkey_manager(self) -> bool:
        """Initialize hotkey manager"""
        try:
            logger.info("Initializing hotkey manager...")
            
            # Initialize WindowService for context capture
            window_service = None
            try:
                from src.services.system.window_service import create_window_service
                window_service = create_window_service()
                if window_service:
                    logger.info("WindowService initialized for hotkey context capture")
                else:
                    logger.warning("Failed to initialize WindowService, context capture disabled")
            except Exception as e:
                logger.warning(f"WindowService initialization failed: {e}")
            
            self.hotkey_manager = HotkeyManager(
                config_manager=self.config_manager,
                floating_window=self.floating_window,
                window_service=window_service
            )
            logger.info("Hotkey manager instance created")
            
            # Integrate window context with floating window
            if window_service and self.floating_window:
                try:
                    from src.ui.windows.floating_window.context_integration import add_context_integration_to_window
                    if add_context_integration_to_window(self.floating_window, self.hotkey_manager):
                        logger.info("Window context integration added to floating window")
                    else:
                        logger.warning("Failed to add window context integration")
                except Exception as e:
                    logger.warning(f"Window context integration failed: {e}")
            
            # Enable the PowerToys-style hook
            logger.info("Enabling hotkey manager...")
            if not self.hotkey_manager.enable():
                logger.error("Failed to enable hotkey manager")
                return False
            logger.info("Hotkey manager enabled successfully")
            
            # Register configured hotkeys
            logger.info("Registering hotkeys...")
            hotkey_config = self.config_manager.get_hotkeys()
            if not self.hotkey_manager.register_hotkeys(hotkey_config):
                logger.error("Failed to register hotkeys")
                return False
            logger.info("Hotkeys registered successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize hotkey manager: {e}")
            return False
    
    def _initialize_single_instance_manager(self, auth_callback_handler) -> bool:
        """Initialize single instance manager"""
        try:
            self.single_instance = SingleInstanceManager()
            if not self.single_instance.start_callback_server(auth_callback_handler):
                logger.error("Failed to start callback server")
                # Continue without callback server - not critical for basic functionality
            
            logger.info("Single instance manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize single instance manager: {e}")
            return False
    
    def _register_url_scheme(self):
        """Register URL scheme for authentication callbacks"""
        try:
            # This would be handled by the auth callback handler
            # For now, just log that it should be done
            logger.info("URL scheme registration should be handled by auth callback handler")
            
        except Exception as e:
            logger.error(f"Failed to register URL scheme: {e}")
    
    def _pre_initialize_floating_window(self):
        """Pre-initialize floating window to ensure proper focus behavior on first show"""
        try:
            logger.info("Starting floating window pre-initialization")
            
            if not self.floating_window:
                logger.error("Floating window not available for pre-initialization")
                return
            
            # Show window briefly to initialize all Qt components and focus system
            self.floating_window.show()
            self.floating_window.raise_()
            self.floating_window.activateWindow()
            
            # Allow Qt event loop to process the show event
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QApplication
            
            # Process events to ensure window is fully initialized
            QApplication.processEvents()
            
            # Use a timer to hide the window after a brief moment
            def hide_after_init():
                try:
                    self.floating_window.hide()
                    logger.info("Floating window pre-initialization completed")
                except Exception as e:
                    logger.error(f"Error hiding window after pre-init: {e}")
            
            # Hide window after 50ms to complete the pre-initialization
            QTimer.singleShot(50, hide_after_init)
            
        except Exception as e:
            logger.error(f"Failed to pre-initialize floating window: {e}")
    
    def get_components(self) -> Dict[str, Any]:
        """Get all initialized components"""
        return {
            'config_manager': self.config_manager,
            'floating_window': self.floating_window,
            'system_tray': self.system_tray,
            'settings_dialog': self.settings_dialog,
            'hotkey_manager': self.hotkey_manager,
            'ai_service_manager': self.ai_service_manager,
            'auth_manager': self.auth_manager,
            'single_instance': self.single_instance,
            'http_server_service': self.http_server_service,
            'configuration_logic': self.configuration_logic,
            'text_processing_logic': self.text_processing_logic
        }


def create_app_initializer() -> AppInitializer:
    """Create and return app initializer"""
    return AppInitializer()