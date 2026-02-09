"""
Single Instance Application Manager
Ensures only one instance of the application runs and handles inter-process communication
"""

import json
import threading
import time
from typing import Optional, Callable, Any

try:
    import win32event
    import win32api
    import win32pipe
    import win32file
    import pywintypes
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from src.utils.loguru_config import logger, get_logger


class SingleInstanceManager:
    """Manages single instance application with named pipe communication"""
    
    def __init__(self, app_name: str = "AIInputMethod"):
        self.logger = get_logger()
        self.app_name = app_name
        self.mutex_name = f"Global\\{app_name}_Mutex"
        self.pipe_name = rf'\\.\pipe\{app_name}_AuthCallback'
        
        # State
        self.mutex: Optional[Any] = None
        self.pipe_server: Optional[Any] = None
        self.is_server_running = False
        self.callback_handler: Optional[Callable[[str, str, Optional[str]], None]] = None
        
        # Check if win32 is available
        if not WIN32_AVAILABLE:
            logger.error("win32 modules not available - single instance not supported")

    def is_already_running(self) -> bool:
        """Check if another instance is already running"""
        if not WIN32_AVAILABLE:
            return False
            
        try:
            self.mutex = win32event.CreateMutex(None, False, self.mutex_name)
            last_error = win32api.GetLastError()
            
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                logger.info("Another instance is already running")
                return True
            
            logger.info("First instance - mutex acquired")
            return False
            
        except Exception as e:
            logger.error(f"Error checking instance: {e}")
            return False

    def start_callback_server(self, callback_handler: Callable[[str, str, Optional[str]], None]) -> bool:
        """Start named pipe server for receiving authentication callbacks"""
        if not WIN32_AVAILABLE:
            logger.error("Cannot start callback server - win32 not available")
            return False
            
        self.callback_handler = callback_handler
        
        try:
            # Start server in background thread
            server_thread = threading.Thread(target=self._run_pipe_server, daemon=True)
            server_thread.start()
            
            logger.info(f"Callback server started on pipe: {self.pipe_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start callback server: {e}")
            return False

    def _run_pipe_server(self) -> None:
        """Run the named pipe server loop"""
        self.is_server_running = True
        
        while self.is_server_running:
            try:
                # Create named pipe
                pipe = win32pipe.CreateNamedPipe(
                    self.pipe_name,
                    win32pipe.PIPE_ACCESS_INBOUND,
                    win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_READMODE_MESSAGE | win32pipe.PIPE_WAIT,
                    1,  # Max instances
                    65536,  # Out buffer size
                    65536,  # In buffer size
                    0,  # Default timeout
                    None  # Security attributes
                )
                
                if pipe == -1:
                    logger.error("Failed to create named pipe")
                    break
                
                logger.info("Waiting for callback connection...")
                
                # Wait for client connection
                win32pipe.ConnectNamedPipe(pipe, None)
                logger.info(" Client connected to callback pipe")
                
                try:
                    # Read data from client
                    result, data = win32file.ReadFile(pipe, 65536)
                    
                    if result == 0:  # Success
                        # Parse callback data
                        callback_data = json.loads(data.decode('utf-8'))
                        
                        api_key = callback_data.get('api_key')
                        username = callback_data.get('username')
                        email = callback_data.get('email')
                        
                        logger.info(f"Received callback for user: {username}")
                        
                        # Process callback
                        if self.callback_handler and api_key and username:
                            self.callback_handler(api_key, username, email)
                            logger.info("Callback processed successfully")
                        else:
                            logger.error("Invalid callback data or no handler")
                    
                except Exception as read_error:
                    logger.error(f"Error reading from pipe: {read_error}")
                
                finally:
                    # Close pipe
                    win32file.CloseHandle(pipe)
                    
            except pywintypes.error as pipe_error:
                if pipe_error.winerror == 109:  # ERROR_BROKEN_PIPE
                    logger.info("Client disconnected")
                else:
                    logger.error(f"Pipe error: {pipe_error}")
                    break
            except Exception as e:
                logger.error(f"Unexpected error in pipe server: {e}")
                break
        
        logger.info("Callback server stopped")

    def send_callback_to_existing_instance(self, api_key: str, username: str, email: Optional[str] = None) -> bool:
        """Send authentication callback to existing instance via named pipe"""
        if not WIN32_AVAILABLE:
            logger.error("Cannot send callback - win32 not available")
            return False
            
        try:
            logger.info(f"Sending callback to existing instance for user: {username}")
            
            # Prepare callback data
            callback_data = {
                'api_key': api_key,
                'username': username,
                'email': email,
                'timestamp': time.time()
            }
            
            data_bytes = json.dumps(callback_data).encode('utf-8')
            
            # Connect to named pipe with timeout
            timeout_ms = 5000  # 5 seconds
            
            try:
                # Wait for pipe to be available
                win32pipe.WaitNamedPipe(self.pipe_name, timeout_ms)
                
                # Open pipe
                pipe = win32file.CreateFile(
                    self.pipe_name,
                    win32file.GENERIC_WRITE,
                    0,  # No sharing
                    None,  # Security attributes
                    win32file.OPEN_EXISTING,
                    0,  # Flags
                    None  # Template
                )
                
                # Send data
                win32file.WriteFile(pipe, data_bytes)
                win32file.CloseHandle(pipe)
                
                logger.info("Callback sent successfully")
                return True
                
            except pywintypes.error as pipe_error:
                if pipe_error.winerror == 2:  # ERROR_FILE_NOT_FOUND
                    logger.error("Named pipe not found - main instance may not be running")
                elif pipe_error.winerror == 121:  # ERROR_SEM_TIMEOUT
                    logger.error("Timeout waiting for pipe connection")
                else:
                    logger.error(f"Pipe connection error: {pipe_error}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send callback: {e}")
            return False

    def activate_existing_instance(self) -> bool:
        """Activate existing instance window (bring to front)"""
        if not WIN32_AVAILABLE:
            return False
            
        try:
            import win32gui
            import win32con
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if "AI Input Method" in window_text or "reInput" in window_text:
                        windows.append(hwnd)
                return True
            
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            if windows:
                # Activate the first matching window
                hwnd = windows[0]
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                logger.info("Activated existing instance window")
                return True
            else:
                logger.info("No visible windows found to activate")
                return False
                
        except Exception as e:
            logger.error(f"Failed to activate existing instance: {e}")
            return False

    def stop_callback_server(self) -> None:
        """Stop the callback server"""
        self.is_server_running = False
        logger.info("Stopping callback server...")

    def cleanup(self) -> None:
        """Clean up resources"""
        try:
            self.stop_callback_server()
            
            if self.mutex:
                win32api.CloseHandle(self.mutex)
                self.mutex = None
                
            logger.info("Single instance manager cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")