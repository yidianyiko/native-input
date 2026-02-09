"""
Simple Authentication Manager
Handles browser-based login with URL scheme callback for API key management
"""

import json
import os
import webbrowser
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.utils.loguru_config import logger, get_logger


@dataclass
class UserInfo:
    """User information data model"""
    username: str
    email: Optional[str] = None
    login_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.login_time:
            data['login_time'] = self.login_time.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'UserInfo':
        """Create UserInfo from dictionary"""
        if 'login_time' in data and data['login_time']:
            data['login_time'] = datetime.fromisoformat(data['login_time'])
        return cls(**data)


class SimpleAuthManager:
    """Core authentication manager for browser login + URL scheme callback"""

    # Configuration constants
    CALLBACK_SCHEME = "reinput://auth/callback"
    CLIENT_IDENTIFIER = "windows"
    SESSION_FILE_NAME = "session.json"

    def __init__(self, login_url: Optional[str] = None, config_manager=None):
        self.logger = get_logger()
        self.config_manager = config_manager
        
        # Get login URL from parameter, config, or default
        if login_url:
            self.login_url = login_url
        elif config_manager:
            self.login_url = config_manager.get('auth.frontend_url')
        else:
            self.login_url = None
            
        if not self.login_url:
            logger.error("auth.frontend_url not configured")
            self.login_url = None
        
        # Session storage - use user data directory for better permissions
        self.session_file = self._get_session_file_path()
        
        # Current session data
        self._api_key: Optional[str] = None
        self._user_info: Optional[UserInfo] = None
        
        # Load existing session on initialization
        self._load_session()

    def _get_session_file_path(self) -> Path:
        """Get the session file path in user data directory"""
        try:
            # Use Windows AppData directory for better permissions
            import os
            app_data = os.getenv('APPDATA')
            if app_data:
                app_dir = Path(app_data) / "reInput"
                app_dir.mkdir(exist_ok=True)
                return app_dir / self.SESSION_FILE_NAME
            else:
                # Fallback to current directory
                return Path(self.SESSION_FILE_NAME)
        except Exception as e:
            logger.warning(f"Could not create user data directory")
            return Path(self.SESSION_FILE_NAME)

    def _validate_login_url(self) -> bool:
        """Validate login URL configuration"""
        if not self.login_url:
            logger.error("auth.frontend_url not configured")
            return False

        if not self.login_url.startswith(('http://', 'https://')):
            logger.error(f"Invalid auth.frontend_url format: {self.login_url}")
            return False

        return True

    def _construct_login_url(self) -> str:
        """Construct full login URL with parameters"""
        return f"{self.login_url}/login?from={self.CLIENT_IDENTIFIER}&redirect_uri={self.CALLBACK_SCHEME}"

    def login(self) -> bool:
        """Start browser login process"""
        try:
            # Validate configuration
            if not self._validate_login_url():
                return False

            # Construct login URL
            full_login_url = self._construct_login_url()
            
            logger.info("Starting browser login process")
            logger.info(f"Opening browser to: {full_login_url}")
            
            # Open browser to login page
            success = webbrowser.open(full_login_url)
            
            if not success:
                logger.error("Failed to open browser - no suitable browser found")
                return False
            
            logger.info("Browser login initiated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start login process: {e}")
            return False

    def _validate_callback_params(self, api_key: str, username: str) -> bool:
        """Validate callback parameters"""
        if not api_key or not api_key.strip():
            logger.error("Missing or empty API key in callback")
            return False
        
        if not username or not username.strip():
            logger.error("Missing or empty username in callback")
            return False
        
        return True

    def handle_callback(self, api_key: str, username: str, email: Optional[str] = None) -> bool:
        """Handle authentication callback from browser"""
        try:
            # Validate input parameters
            if not self._validate_callback_params(api_key, username):
                return False

            logger.info(f"Processing authentication callback for user: {username}")
            
            # Create user info
            self._user_info = UserInfo(
                username=username,
                email=email,
                login_time=datetime.now()
            )
            
            # Store API key
            self._api_key = api_key
            
            # Save session to file
            if self._save_session():
                logger.info("Authentication successful")
                return True
            else:
                logger.error("Failed to save session")
                return False
                
        except Exception as e:
            logger.error(f"Failed to handle authentication callback: {e}")
            return False

    def logout(self) -> None:
        """Clear authentication data and logout"""
        try:
            logger.info("Logging out user")
            
            # Clear memory data
            self._api_key = None
            self._user_info = None
            
            # Delete session file
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("🗑️ Session file deleted")
            
            logger.info("Logout completed")
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")

    def is_authenticated(self) -> bool:
        """Check if user is currently authenticated"""
        return self._api_key is not None and self._user_info is not None

    def get_api_key(self) -> Optional[str]:
        """Get current API key"""
        return self._api_key

    def get_user_info(self) -> Optional[UserInfo]:
        """Get current user information"""
        return self._user_info

    def _save_session(self) -> bool:
        """Save current session to file"""
        # Performance monitoring removed during loguru migration
        try:
            if not self._api_key or not self._user_info:
                logger.warning("No session data to save")
                return False

            session_data = {
                "api_key": self._api_key,
                "user_info": self._user_info.to_dict()
            }
            
            # Write to file with secure permissions
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
            
            # Set file permissions to be readable only by current user (Windows)
            try:
                os.chmod(self.session_file, 0o600)
            except Exception as e:
                logger.warning(f"Could not set secure file permissions: {e}")
            
            logger.info("Session saved successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False

    def _load_session(self) -> bool:
        """Load session from file"""
        # Performance monitoring removed during loguru migration
        try:
            if not self.session_file.exists():
                logger.info("No existing session file found")
                return False

            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Validate session data structure
            if not isinstance(session_data, dict):
                raise ValueError("Invalid session data format")
            
            api_key = session_data.get('api_key')
            user_info_data = session_data.get('user_info')
            
            if not api_key or not user_info_data:
                raise ValueError("Missing required session data")
            
            # Restore session
            self._api_key = api_key
            self._user_info = UserInfo.from_dict(user_info_data)
            
            logger.info(f"Session loaded for user: {self._user_info.username}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load session")
            
            # Clear corrupted session file
            try:
                if self.session_file.exists():
                    self.session_file.unlink()
                    logger.info("🗑️ Corrupted session file deleted")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup corrupted session: {cleanup_error}")
            
            return False