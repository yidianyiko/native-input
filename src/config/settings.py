"""
Pydantic settings classes for configuration management.

This module provides structured configuration classes using pydantic-settings
for type-safe configuration management with environment variable support.
"""

from typing import Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class HotkeySettings(BaseModel):
    """Settings for hotkey configurations."""
    
    show_floating_window: str = Field(default="win+alt+o", description="Hotkey for showing floating window")
    translate: str = Field(default="ctrl+shift+t", description="Hotkey for translation")
    polish: str = Field(default="ctrl+shift+p", description="Hotkey for text polishing")
    voice_input: str = Field(default="ctrl+shift+v", description="Hotkey for voice input")
    error_correction: str = Field(default="ctrl+shift+e", description="Hotkey for error correction")
    
    @validator('show_floating_window', 'translate', 'polish', 'voice_input', 'error_correction')
    def validate_hotkey_format(cls, v):
        """Validate hotkey format for pynput compatibility."""
        if not v or not isinstance(v, str):
            raise ValueError("Hotkey must be a non-empty string")
        
        # Basic validation for hotkey format
        parts = v.lower().split('+')
        valid_modifiers = {'ctrl', 'shift', 'alt', 'win', 'cmd'}
        
        # Pynput compatible key names
        valid_keys = set('abcdefghijklmnopqrstuvwxyz0123456789')
        special_keys = {
            'space', 'enter', 'tab', 'esc', 'escape', 'backspace', 'delete',
            'home', 'end', 'page_up', 'page_down', 'insert',
            'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
            'up', 'down', 'left', 'right', 'left_bracket', 'right_bracket',
            'semicolon', 'comma', 'period', 'slash', 'backslash', 'equals', 'minus'
        }
        valid_keys.update(special_keys)
        
        if len(parts) < 2:
            raise ValueError("Hotkey must contain at least one modifier and one key")
        
        # Check modifiers
        modifiers = parts[:-1]
        key = parts[-1]
        
        for modifier in modifiers:
            if modifier not in valid_modifiers:
                raise ValueError(f"Invalid modifier: {modifier}")
        
        if key not in valid_keys:
            raise ValueError(f"Invalid key: {key}")
        
        return v


class AIProviderSettings(BaseModel):
    """Settings for AI provider configurations."""
    
    default_model: str = Field(default="gpt-4", description="Default AI model")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")


class UISettings(BaseModel):
    """Settings for UI configurations."""
    
    window_opacity: float = Field(default=0.9, ge=0.1, le=1.0, description="Window opacity")
    window_stay_on_top: bool = Field(default=True, description="Keep window on top")
    auto_hide_delay: int = Field(default=3000, ge=0, description="Auto hide delay in milliseconds")
    theme: str = Field(default="dark", description="UI theme")
    
    @validator('theme')
    def validate_theme(cls, v):
        """Validate theme selection."""
        valid_themes = {'dark', 'light', 'auto'}
        if v not in valid_themes:
            raise ValueError(f"Theme must be one of: {valid_themes}")
        return v


class LoggingSettings(BaseModel):
    """Settings for logging configurations."""
    
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="json", description="Log format")
    max_file_size: int = Field(default=10485760, ge=1048576, description="Max log file size in bytes")
    backup_count: int = Field(default=5, ge=1, le=20, description="Number of backup log files")
    
    @validator('level')
    def validate_log_level(cls, v):
        """Validate logging level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator('format')
    def validate_log_format(cls, v):
        """Validate log format."""
        valid_formats = {'json', 'text'}
        if v not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v


class AppSettings(BaseSettings):
    """Main application settings combining all configuration sections."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Configuration sections
    hotkeys: HotkeySettings = Field(default_factory=HotkeySettings)
    ai_provider: AIProviderSettings = Field(default_factory=AIProviderSettings)
    ui: UISettings = Field(default_factory=UISettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    # Application settings
    app_name: str = Field(default="AI Input Method", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    config_file: str = Field(default="config.json", description="Configuration file path")
    
    def get_config_path(self) -> Path:
        """Get the full path to the configuration file."""
        return Path(self.config_file).resolve()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary for JSON serialization."""
        return {
            "hotkeys": self.hotkeys.dict(),
            "ai_provider": self.ai_provider.dict(),
            "ui": self.ui.dict(),
            "logging": self.logging.dict(),
            "app_name": self.app_name,
            "version": self.version,
            "config_file": self.config_file,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create settings from dictionary."""
        return cls(**data)