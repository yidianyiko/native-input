"""Core configuration business logic.

Handles application configuration management and validation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
import json


@dataclass
class ConfigurationSection:
    """Represents a configuration section."""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    required_keys: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if all required keys are present."""
        return all(key in self.data for key in self.required_keys)
    
    def get_missing_keys(self) -> List[str]:
        """Get list of missing required keys."""
        return [key for key in self.required_keys if key not in self.data]
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value with default."""
        return self.data.get(key, default)
    
    def set_value(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.data[key] = value


@dataclass
class ConfigurationValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_sections: List[str] = field(default_factory=list)
    invalid_sections: List[str] = field(default_factory=list)


class ConfigurationBusinessLogic:
    """Core business logic for configuration management."""
    
    def __init__(self):
        self._sections: Dict[str, ConfigurationSection] = {}
        self._config_path: Optional[Path] = None
        self._auto_save = True
    
    def define_section(self, name: str, required_keys: List[str] = None) -> ConfigurationSection:
        """Define a configuration section with required keys."""
        section = ConfigurationSection(
            name=name,
            required_keys=required_keys or []
        )
        self._sections[name] = section
        return section
    
    def get_section(self, name: str) -> Optional[ConfigurationSection]:
        """Get configuration section by name."""
        return self._sections.get(name)
    
    def has_section(self, name: str) -> bool:
        """Check if section exists."""
        return name in self._sections
    
    def get_all_sections(self) -> Dict[str, ConfigurationSection]:
        """Get all configuration sections."""
        return self._sections.copy()
    
    def validate_configuration(self) -> ConfigurationValidationResult:
        """Validate entire configuration."""
        result = ConfigurationValidationResult(is_valid=True)
        
        for name, section in self._sections.items():
            if not section.is_valid():
                result.is_valid = False
                result.invalid_sections.append(name)
                missing_keys = section.get_missing_keys()
                for key in missing_keys:
                    result.errors.append(f"Missing required key '{key}' in section '{name}'")
        
        return result
    
    def validate_section(self, section_name: str) -> ConfigurationValidationResult:
        """Validate specific configuration section."""
        result = ConfigurationValidationResult(is_valid=True)
        
        if section_name not in self._sections:
            result.is_valid = False
            result.missing_sections.append(section_name)
            result.errors.append(f"Section '{section_name}' not found")
            return result
        
        section = self._sections[section_name]
        if not section.is_valid():
            result.is_valid = False
            result.invalid_sections.append(section_name)
            missing_keys = section.get_missing_keys()
            for key in missing_keys:
                result.errors.append(f"Missing required key '{key}' in section '{section_name}'")
        
        return result
    
    def get_value(self, section_name: str, key: str, default: Any = None) -> Any:
        """Get configuration value from section."""
        section = self.get_section(section_name)
        if section is None:
            return default
        return section.get_value(key, default)
    
    def set_value(self, section_name: str, key: str, value: Any, create_section: bool = True) -> bool:
        """Set configuration value in section."""
        section = self.get_section(section_name)
        if section is None:
            if not create_section:
                return False
            section = self.define_section(section_name)
        
        section.set_value(key, value)
        
        if self._auto_save and self._config_path:
            self.save_to_file(self._config_path)
        
        return True
    
    def load_from_dict(self, config_data: Dict[str, Any]) -> bool:
        """Load configuration from dictionary."""
        try:
            for section_name, section_data in config_data.items():
                if isinstance(section_data, dict):
                    section = self.get_section(section_name)
                    if section is None:
                        section = self.define_section(section_name)
                    section.data.update(section_data)
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            name: section.data
            for name, section in self._sections.items()
        }
    
    def load_from_file(self, file_path: Path) -> bool:
        """Load configuration from JSON file."""
        try:
            if not file_path.exists():
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self._config_path = file_path
            return self.load_from_dict(config_data)
        except Exception:
            return False
    
    def save_to_file(self, file_path: Path) -> bool:
        """Save configuration to JSON file."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
            self._config_path = file_path
            return True
        except Exception:
            return False
    
    def set_auto_save(self, enabled: bool) -> None:
        """Enable or disable auto-save."""
        self._auto_save = enabled
    
    def set_config_path(self, file_path: Path) -> None:
        """Set the configuration file path."""
        self._config_path = file_path
    
    def get_config_path(self) -> Optional[Path]:
        """Get the current configuration file path."""
        return self._config_path
    
    def reset_section(self, section_name: str) -> bool:
        """Reset a configuration section to empty state."""
        section = self.get_section(section_name)
        if section is None:
            return False
        
        section.data.clear()
        
        if self._auto_save and self._config_path:
            self.save_to_file(self._config_path)
        
        return True
    
    def remove_section(self, section_name: str) -> bool:
        """Remove a configuration section."""
        if section_name not in self._sections:
            return False
        
        del self._sections[section_name]
        
        if self._auto_save and self._config_path:
            self.save_to_file(self._config_path)
        
        return True
    
    def get_section_names(self) -> List[str]:
        """Get list of all section names."""
        return list(self._sections.keys())
    
    def is_section_valid(self, section_name: str) -> bool:
        """Check if a specific section is valid."""
        section = self.get_section(section_name)
        return section is not None and section.is_valid()