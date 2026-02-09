"""Configuration Interfaces

Defines abstract interfaces for configuration management to provide
clear contracts and enable dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of configuration validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class IConfigurationSection(ABC):
    """Interface for configuration sections"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get section name"""
    
    @property
    @abstractmethod
    def data(self) -> Dict[str, Any]:
        """Get section data"""
    
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get value from section"""
    
    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """Set value in section"""
    
    @abstractmethod
    def is_valid(self) -> bool:
        """Check if section has all required keys"""


class IConfigurationManager(ABC):
    """Interface for configuration management"""
    
    @abstractmethod
    def get_section(self, name: str) -> Optional[IConfigurationSection]:
        """Get configuration section by name"""
    
    @abstractmethod
    def create_section(self, name: str, required_keys: Optional[List[str]] = None) -> IConfigurationSection:
        """Create new configuration section"""
    
    @abstractmethod
    def validate_configuration(self) -> ValidationResult:
        """Validate all configuration sections"""
    
    @abstractmethod
    def load_configuration(self, _config_path: Optional[str] = None) -> bool:
        """Load configuration from file"""
    
    @abstractmethod
    def save_configuration(self, _config_path: Optional[str] = None) -> bool:
        """Save configuration to file"""
    
    @abstractmethod
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (section.key)"""
    
    @abstractmethod
    def set_value(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation (section.key)"""
