"""
Credential Management System
Handles per-provider API keys with direct official endpoints
"""

from typing import Optional, Tuple, Dict
from dataclasses import dataclass

from src.core.business.configuration import ConfigurationBusinessLogic
from src.utils.loguru_config import logger, get_logger


@dataclass
class ProviderConfig:
    """Provider configuration with API credentials"""
    name: str
    base_url: str
    api_key: Optional[str] = None
    enabled: bool = True


class CredentialManager:
    """Manages per-provider API credentials using official endpoints"""
    
    # Official provider base URLs
    PROVIDER_URLS = {
        "deepseek": "https://api.deepseek.com",
        "openai": "https://api.openai.com/v1", 
        "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    }
    
    def __init__(self, config_manager, auth_manager=None):
        self.logger = get_logger(__name__)
        self.config_manager = config_manager
        self.auth_manager = auth_manager
        
        # Core business logic
        self.core_config = ConfigurationBusinessLogic()
        self._setup_credential_configuration()
        
        logger.info("Credential manager initialized")
    
    def get_provider_credentials(self, provider: str) -> Tuple[Optional[str], Optional[str]]:
        """Get credentials for a specific provider using its official API endpoint"""
        try:
            provider_lower = provider.lower()
            
            # Read from config (set via settings UI)
            config_key = self.config_manager.get(f"providers.{provider_lower}.api_key")
            if config_key and str(config_key).strip():
                base_url = self.PROVIDER_URLS.get(provider_lower)
                if base_url:
                    logger.info(f"Using config credentials for {provider}")
                    return base_url, str(config_key).strip()
            
            logger.info(f"No provider credentials for {provider}")
            return None, None
            
        except Exception as e:
            logger.error(f"Error getting {provider} credentials: {e}")
            return None, None
    
    def get_best_credentials(self, provider: str) -> Tuple[Optional[str], Optional[str], str]:
        """Get the best available credentials for a provider"""
        try:
            provider_url, provider_key = self.get_provider_credentials(provider)
            if provider_url and provider_key:
                return provider_url, provider_key, "provider"
            
            logger.warning(f"No credentials available for {provider}")
            return None, None, "none"
            
        except Exception as e:
            logger.error(f"Error getting best credentials for {provider}: {e}")
            return None, None, "error"
    
    def validate_provider_credentials(self, provider: str) -> bool:
        """Check if valid credentials exist for a provider"""
        try:
            url, key, source = self.get_best_credentials(provider)
            return url is not None and key is not None
        except Exception as e:
            logger.error(f"Error validating {provider} credentials: {e}")
            return False
    
    def get_available_providers(self) -> Dict[str, ProviderConfig]:
        """Get all available provider configurations"""
        providers = {}
        
        for provider_name in self.PROVIDER_URLS:
            url, key, source = self.get_best_credentials(provider_name)
            providers[provider_name] = ProviderConfig(
                name=provider_name,
                base_url=url or self.PROVIDER_URLS[provider_name],
                api_key=key,
                enabled=key is not None
            )
        
        return providers
    
    def has_any_credentials(self) -> bool:
        """Check if any provider credentials are available"""
        for provider in self.PROVIDER_URLS:
            if self.validate_provider_credentials(provider):
                return True
        
        return False

    def refresh_credentials(self) -> None:
        """Refresh credentials - re-read from config"""
        try:
            logger.info("Credentials refreshed")
        except Exception as e:
            logger.error(f"Error refreshing credentials: {e}")

    def update_settings(self, settings: dict) -> bool:
        """Update credential settings"""
        try:
            self.refresh_credentials()
            
            if "providers" in settings:
                logger.info("Provider credentials updated")
            
            return True
        except Exception as e:
            logger.error(f"Failed to update credential settings: {e}")
            return False
    
    def get_missing_credentials_info(self) -> Dict[str, str]:
        """Get info about missing credentials for user prompts"""
        info = {}
        
        missing_providers = []
        for provider in self.PROVIDER_URLS:
            if not self.validate_provider_credentials(provider):
                missing_providers.append(provider)
        
        if missing_providers:
            info["providers"] = f"Missing provider credentials: {', '.join(missing_providers)}"
        
        return info
    
    def _setup_credential_configuration(self):
        """Setup credential configuration sections in core business logic."""
        # Setup providers section
        providers_section = self.core_config.define_section(
            "providers",
            required_keys=[]
        )
        
        # Set default provider configurations
        for provider_name, base_url in self.PROVIDER_URLS.items():
            provider_subsection = self.core_config.define_section(
                f"providers.{provider_name}",
                required_keys=["api_key"]
            )
            provider_subsection.set_value("base_url", base_url)
            provider_subsection.set_value("enabled", True)