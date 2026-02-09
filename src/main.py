#!/usr/bin/env python3
"""
AI Input Method Tool - Main Application Entry Point
Simplified entry point that delegates to specialized modules
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSystemTrayIcon
from PySide6.QtGui import QIcon

from src.utils.loguru_config import logger
from src.platform_integration.single_instance import SingleInstanceManager
from src.services.auth.auth_callback_handler import AuthCallbackHandler
from src.core.app_initializer import AppInitializer
from src.core.app_lifecycle import AppLifecycleManager

# Constants
URL_CALLBACK_FLAG = '--url-callback'
REINPUT_URL_SCHEME = 'reinput'
SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1


def get_config_directory() -> str:
    """
    Get the configuration directory, handling both development and packaged environments.
    
    Returns:
        str: Path to configuration directory
    """
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # Running as PyInstaller executable
            exe_dir = Path(sys.executable).parent
            
            # Check if config.json exists in exe directory
            if (exe_dir / "config.json").exists():
                logger.info(f"Using exe directory for config: {exe_dir}")
                return str(exe_dir)
            
            # Fallback: check parent directories for config
            current_dir = exe_dir
            for _ in range(3):  # Check up to 3 levels up
                if (current_dir / "config.json").exists():
                    logger.info(f"Found config in parent directory: {current_dir}")
                    return str(current_dir)
                current_dir = current_dir.parent
            
            # If no config found, use exe directory (will create default)
            logger.info(f"No config found, using exe directory: {exe_dir}")
            return str(exe_dir)
        else:
            # Development environment - use current working directory
            cwd = Path.cwd()
            logger.info(f"Development mode, using cwd: {cwd}")
            return str(cwd)
            
    except Exception as e:
        logger.error(f"Error determining config directory: {e}")
        # Fallback to current working directory
        return str(Path.cwd())


def handle_url_callback() -> int:
    """Handle URL callback in separate process"""
    auth_handler = AuthCallbackHandler()
    return auth_handler.handle_url_callback()


def handle_existing_instance_url(single_instance: SingleInstanceManager, url_arg: str) -> int:
    """Handle URL callback when instance already exists"""
    auth_handler = AuthCallbackHandler()
    return auth_handler.handle_existing_instance_url(single_instance, url_arg)


def setup_qt_application() -> QApplication:
    """Setup Qt application with proper configuration"""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running in system tray
    
    # Set application icon
    icon_path = Path(__file__).parent.parent / "resources" / "icons" / "icon.png"
    if icon_path.exists():
        app_icon = QIcon(str(icon_path))
        app.setWindowIcon(app_icon)
        # Also set as default icon for all windows
        QApplication.setWindowIcon(app_icon)
    
    # Set application metadata
    app.setApplicationName("AI Input Method Tool")
    app.setApplicationDisplayName("AI智能输入法工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AI Input Method")
    
    return app


def main() -> int:
    """Main entry point with improved structure and error handling"""
    # Handle URL callback in separate process
    if len(sys.argv) >= 2 and sys.argv[1] == URL_CALLBACK_FLAG:
        return handle_url_callback()
    
    # Check for single instance
    single_instance = SingleInstanceManager()
    
    if single_instance.is_already_running():
        # Handle URL callback to existing instance
        if len(sys.argv) >= 2 and sys.argv[1].startswith(f'{REINPUT_URL_SCHEME}://'):
            return handle_existing_instance_url(single_instance, sys.argv[1])
        else:
            # Normal startup but instance exists - activate existing window
            single_instance.activate_existing_instance()
            return SUCCESS_EXIT_CODE
    
    # First instance - start application
    return start_application()


def start_application() -> int:
    """
    Start the main application instance with proper initialization sequence
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        # Create Qt application first to enable proper logging
        app = setup_qt_application()
        
        # Setup basic logging for debugging
        logger.info("Qt Application created successfully")
        
        # Check system tray availability early
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.error("System tray is not available on this system")
            print("System tray is not available on this system")
            return ERROR_EXIT_CODE
        
        # Determine config directory
        config_dir = get_config_directory()
        
        # Create app initializer
        logger.info("Creating AppInitializer instance")
        app_initializer = AppInitializer()
        
        # Create auth callback handler for lifecycle manager
        auth_handler = AuthCallbackHandler()
        
        # Initialize application components
        logger.info("Running application initialization")
        if not app_initializer.initialize(config_dir, auth_handler.handle_auth_callback):
            logger.error("Application initialization failed")
            return ERROR_EXIT_CODE
        
        # Get initialized components
        components = app_initializer.get_components()
        
        # Create lifecycle manager
        logger.info("Creating AppLifecycleManager instance")
        lifecycle_manager = AppLifecycleManager(components)
        
        # Start application runtime
        logger.info("Starting application runtime")
        result = lifecycle_manager.start_application()
        
        if result == 0:
            logger.info("Application initialized successfully, starting Qt event loop")
            # Setup shutdown handler for graceful cleanup
            app.aboutToQuit.connect(lifecycle_manager.shutdown)
            # Run Qt event loop
            result = app.exec()
        else:
            logger.error(f"Application startup failed with code: {result}")
        
        return result
        
    except Exception as e:
        logger.error(f"Critical error starting application: {e}")
        return ERROR_EXIT_CODE


if __name__ == "__main__":
    sys.exit(main())
