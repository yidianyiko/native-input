"""
Authentication Callback Handler
Handles URL callback parsing and authentication flow
"""

import sys
import winreg
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass

try:
    from src.utils.loguru_config import logger
    from src.platform_integration.single_instance import SingleInstanceManager
except ImportError:
    # Fallback for PyInstaller
    from utils.loguru_config import logger
    from platform_integration.single_instance import SingleInstanceManager

# Constants
URL_CALLBACK_FLAG = '--url-callback'
REINPUT_URL_SCHEME = 'reinput'
AUTH_CALLBACK_PATH = '/auth/callback'
REINPUT_URL_PREFIX = f'{REINPUT_URL_SCHEME}://auth/callback'
MIN_CALLBACK_ARGS = 3
SUCCESS_EXIT_CODE = 0
ERROR_EXIT_CODE = 1


@dataclass
class AuthCallbackData:
    """Data structure for authentication callback parameters"""
    api_key: Optional[str]
    username: Optional[str]
    email: Optional[str]
    
    @property
    def is_valid(self) -> bool:
        """Check if callback data has required fields"""
        return bool(self.api_key and self.username)


class AuthCallbackHandler:
    """
    Handles authentication callback URL parsing and processing
    """
    
    def __init__(self):
        self.logger = logger
        logger.info("AuthCallbackHandler initialized")
    
    def parse_callback_url(self, url: str) -> Optional[AuthCallbackData]:
        """
        Parse authentication callback URL and extract parameters with security validation
        
        Args:
            url: The callback URL to parse
            
        Returns:
            AuthCallbackData if URL is valid and secure, None otherwise
        """
        try:
            # Strict URL validation
            if not url.startswith(REINPUT_URL_PREFIX):
                return None
                
            parsed_url = urlparse(url)
            
            # Validate scheme and path - handle both netloc and path variations
            if parsed_url.scheme != REINPUT_URL_SCHEME:
                return None
            
            # Support both forms:
            # 1) reinput://auth/callback (netloc='auth', path='/callback')
            # 2) reinput:///auth/callback (path='/auth/callback')
            valid_path = (parsed_url.path == '/callback' and parsed_url.netloc == 'auth') or \
                        (parsed_url.path == AUTH_CALLBACK_PATH)
            
            if not valid_path:
                return None
                
            query_params = parse_qs(parsed_url.query)
            
            # Extract parameters with validation
            api_key = query_params.get('api_key', [None])[0]
            username = query_params.get('username', [None])[0]
            email = query_params.get('email', [None])[0]
            
            # Basic parameter validation
            if api_key and len(api_key.strip()) == 0:
                api_key = None
            if username and len(username.strip()) == 0:
                username = None
                
            return AuthCallbackData(
                api_key=api_key,
                username=username,
                email=email
            )
        except Exception:
            return None
    
    def handle_url_callback(self) -> int:
        """Handle URL callback in separate process"""
        if len(sys.argv) < MIN_CALLBACK_ARGS:
            return ERROR_EXIT_CODE
        
        url_arg = sys.argv[2]  # argv[1] is --url-callback, argv[2] is the URL
        
        # Parse and validate URL
        callback_data = self.parse_callback_url(url_arg)
        if not callback_data or not callback_data.is_valid:
            return ERROR_EXIT_CODE
        
        try:
            # Send callback to existing instance
            single_instance = SingleInstanceManager()
            success = single_instance.send_callback_to_existing_instance(
                callback_data.api_key, callback_data.username, callback_data.email
            )
            return SUCCESS_EXIT_CODE if success else ERROR_EXIT_CODE
            
        except Exception as e:
            # Log critical errors in callback handler
            logger.error(f"Critical error in URL callback handler: {e}")
            return ERROR_EXIT_CODE
    
    def handle_existing_instance_url(self, single_instance: SingleInstanceManager, url_arg: str) -> int:
        """Handle URL callback when instance already exists"""
        callback_data = self.parse_callback_url(url_arg)
        if callback_data and callback_data.is_valid:
            try:
                single_instance.send_callback_to_existing_instance(
                    callback_data.api_key, callback_data.username, callback_data.email
                )
            except Exception as e:
                # Log error but don't fail - this is a secondary process
                logger.error(f"Failed to send callback to existing instance: {e}")
        return SUCCESS_EXIT_CODE
    
    def register_url_scheme(self) -> None:
        """Register Windows URL scheme for authentication callbacks"""
        try:
            logger.info("Registering URL scheme for authentication callbacks")
            
            exe_path = self._get_executable_path()
            if not exe_path:
                logger.error("Could not determine executable path for URL scheme")
                return
            
            # Registry keys for URL scheme
            scheme_key = r"SOFTWARE\Classes\reinput"
            command_key = r"SOFTWARE\Classes\reinput\shell\open\command"
            
            # Create main scheme key
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, scheme_key) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:reInput Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # Create command key
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'{exe_path} "%1"')
            
            logger.info(f"URL scheme registered successfully: scheme=reinput, exe_path={exe_path}")
                
        except OSError as os_error:
            logger.error(f"Registry access denied for URL scheme registration: {os_error}")
        except Exception as e:
            logger.error(f"Error in URL scheme registration: {e}")
    
    def _get_executable_path(self) -> Optional[str]:
        """Get the current executable path for URL scheme registration"""
        try:
            if hasattr(sys, 'frozen'):
                # Running as compiled executable
                return f'"{sys.executable}" --url-callback'
            else:
                # Running as Python script - prefer pythonw to avoid console window
                python_exe = sys.executable.replace('python.exe', 'pythonw.exe')
                if not Path(python_exe).exists():
                    python_exe = sys.executable
                
                main_script = Path(__file__).resolve().parent.parent.parent / "main.py"
                return f'"{python_exe}" "{main_script}" --url-callback'
                
        except Exception as e:
            logger.error(f"Error determining executable path: {e}")
            return None
    
    def handle_auth_callback(self, api_key: str, username: str, email: Optional[str] = None) -> None:
        """
        Handle authentication callback from named pipe
        
        Args:
            api_key: API key from authentication
            username: Username from authentication
            email: Optional email from authentication
        """
        try:
            logger.info(f"Processing authentication callback for user: {username}")
            
            # For now, just log the callback - this can be extended later
            # to handle the actual authentication logic
            logger.info(f"Received auth callback: api_key={'*' * len(api_key) if api_key else None}, username={username}, email={email}")
            
            # TODO: Implement actual authentication handling logic here
            # This might involve:
            # - Storing credentials securely
            # - Updating authentication state
            # - Notifying other components
            
        except Exception as e:
            logger.error(f"Error processing authentication callback: {e}")


def create_auth_callback_handler() -> AuthCallbackHandler:
    """Create and initialize auth callback handler"""
    return AuthCallbackHandler()