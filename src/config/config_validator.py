"""Configuration validation utilities for security and correctness."""

import re
from urllib.parse import urlparse
from typing import List, Tuple, Optional
from src.utils.loguru_config import logger, get_logger


class ConfigValidator:
    """Validates configuration for security and correctness."""
    
    def __init__(self):
        self.logger = get_logger()
        

    
    def validate_config_manager(self, config_manager) -> List[Tuple[str, str]]:
        """
        Validate configuration using ConfigManager instance.
        
        Args:
            config_manager: ConfigManager instance to validate
            
        Returns:
            List of (severity, message) tuples for any issues found
        """
        issues = []
        
        # Validate provider API keys
        for provider in ["openai", "deepseek"]:
            api_key = config_manager.get(f"providers.{provider}.api_key")
            if api_key:
                issues.extend(self._validate_api_key(f"providers.{provider}.api_key", str(api_key)))
            
        # Validate auth frontend URL
        auth_url = config_manager.get("auth.frontend_url")
        if auth_url:
            issues.extend(self._validate_auth_url(auth_url))
            
        return issues
    
    def _validate_api_key(self, key_name: str, key_value: str) -> List[Tuple[str, str]]:
        """Validate API key format and security."""
        issues = []
        
        # Check for placeholder values
        placeholder_patterns = [
            "your_", "REPLACE_WITH", "example", "test", "demo", "placeholder"
        ]
        
        if any(pattern in key_value.lower() for pattern in placeholder_patterns):
            issues.append(("ERROR", f"{key_name} contains placeholder value"))
            return issues
            
        # Check minimum length (most API keys are at least 20 characters)
        if len(key_value) < 20:
            issues.append(("WARNING", f"{key_name} seems too short for a valid API key"))
            
        # Check for common weak patterns
        if key_value.lower() in ["password", "secret", "key", "token"]:
            issues.append(("ERROR", f"{key_name} contains obviously fake value"))
            
        return issues
    
    def _validate_auth_url(self, url: str) -> List[Tuple[str, str]]:
        """Validate authentication URL."""
        issues = []
        
        try:
            parsed = urlparse(url)
            
            # Check protocol for auth URLs
            if parsed.scheme == "http" and parsed.hostname not in ["localhost", "127.0.0.1"]:
                issues.append(("ERROR", "AUTH_FRONTEND_URL must use HTTPS in production"))
                
        except Exception as e:
            issues.append(("ERROR", f"Invalid AUTH_FRONTEND_URL format: {e}"))
            
        return issues
    
    def _is_internal_ip(self, hostname: Optional[str]) -> bool:
        """Check if hostname is an internal IP address."""
        if not hostname:
            return False
            
        # Common internal IP ranges
        internal_patterns = [
            r'^10\.',                    # 10.0.0.0/8
            r'^172\.(1[6-9]|2[0-9]|3[01])\.',  # 172.16.0.0/12
            r'^192\.168\.',              # 192.168.0.0/16
            r'^100\.(6[4-9]|[7-9][0-9]|1[0-1][0-9]|12[0-7])\.',  # 100.64.0.0/10 (CGNAT)
        ]
        
        return any(re.match(pattern, hostname) for pattern in internal_patterns)
    
    def log_validation_results(self, issues: List[Tuple[str, str]]) -> bool:
        """Log validation results and return True if no critical issues."""
        has_errors = False
        
        for severity, message in issues:
            if severity == "ERROR":
                logger.error(f"Configuration Error: {message}")
                has_errors = True
            elif severity == "WARNING":
                logger.warning(f"Configuration Warning: {message}")
                
        if not issues:
            logger.info("Configuration validation passed")
            
        return not has_errors


def validate_startup_config(config_manager) -> bool:
    """
    Validate configuration at startup.
    
    Args:
        config_manager: ConfigManager instance to use for validation
    
    Returns:
        True if configuration is valid, False if critical issues found
    """
    validator = ConfigValidator()
    issues = validator.validate_config_manager(config_manager)
    return validator.log_validation_results(issues)