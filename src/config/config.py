"""
Simplified Configuration Management using Dynaconf
Clean and minimal configuration system.
"""

from pathlib import Path
from typing import Any, Dict, Optional
from dynaconf import Dynaconf
from src.utils.loguru_config import logger, get_logger
from src.core.business.configuration import ConfigurationBusinessLogic


class ConfigManager:
    """Simplified configuration manager using Dynaconf."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.logger = get_logger(__name__)
        
        # Default config directory
        if config_dir is None:
            config_dir = Path.cwd()
        
        self.config_dir = Path(config_dir)
        
        # 跟踪运行时修改的值
        self._pending_changes = {}
        
        # Initialize core business logic
        self.core_config = ConfigurationBusinessLogic()
        self._setup_core_sections()
        
        # Initialize Dynaconf (use settings.toml as primary config)
        toml_config = self.config_dir / "settings.toml"
        
        self.settings = Dynaconf(
            settings_files=[str(toml_config)] if toml_config.exists() else [],
            environments=False,
            load_dotenv=False,  # 不加载 .env 文件
            merge_enabled=True)
        
        logger.info("Configuration manager initialized")
        
        # Debug: log configuration loading status
        if toml_config.exists():
            logger.info(f"Loading configuration from: {toml_config}")
            # Test reading a key to verify config is loaded
            test_provider = self.get("ai_services.default_provider")
            logger.info(f"Test config read - default_provider: {test_provider}")
        else:
            logger.info(f"Configuration file not found: {toml_config}")
    
    def _setup_core_sections(self) -> None:
        """Setup core configuration sections."""
        # Define standard configuration sections without required keys for development flexibility
        self.core_config.define_section("hotkeys", [])
        self.core_config.define_section("ai_services", [])
        self.core_config.define_section("ui", [])
        self.core_config.define_section("voice", [])
        self.core_config.define_section("llm", [])
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation support."""
        try:
            return self.settings.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get config key '{key}'")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value with change tracking."""
        try:
            # 设置到 Dynaconf (运行时)
            self.settings.set(key, value)
            
            # 跟踪变更以便保存
            self._pending_changes[key] = value
            
            logger.info(f"Set config key '{key}' = {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to set config key '{key}'")
            return False
    
    def reload(self) -> bool:
        """Reload configuration from files."""
        try:
            self.settings.reload()
            logger.info("Configuration reloaded")
            return True
        except Exception as e:
            logger.error("Failed to reload configuration")
            return False
    
    def get_hotkeys(self) -> Dict[str, str]:
        """Get hotkey configuration.
        
        Returns:
            Dict[str, str]: Dictionary mapping hotkey strings to actions
        """
        hotkeys_config = dict(self.settings.get("hotkeys", {}))
        # Convert from {action: hotkey_string} to {hotkey_string: action} format
        return {hotkey_string: action for action, hotkey_string in hotkeys_config.items()}
    

    
    def save(self) -> bool:
        """Save configuration to settings.toml file."""
        try:
            import toml
            
            # 读取当前文件内容
            settings_file = self.config_dir / "settings.toml"
            if settings_file.exists():
                with open(settings_file, 'r', encoding='utf-8') as f:
                    current_config = toml.load(f)
            else:
                current_config = {}
            
            # 应用所有待保存的变更
            for key, value in self._pending_changes.items():
                self._set_nested_dict_value(current_config, key, value)
            
            # 保存到文件
            with open(settings_file, 'w', encoding='utf-8') as f:
                toml.dump(current_config, f)
            
            # 清空待保存的变更
            self._pending_changes.clear()
            
            logger.info(f"Configuration saved to {settings_file}")
            return True
        except Exception as e:
            logger.error("Failed to save configuration")
            return False
    
    def _set_nested_dict_value(self, config_dict: dict, key: str, value: Any) -> None:
        """Set a nested value in dictionary using dot notation."""
        keys = key.split('.')
        current = config_dict
        
        # 导航到父级
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置最终值
        current[keys[-1]] = value
    
    def validate(self) -> bool:
        """Basic configuration validation using core business logic."""
        try:
            # Load current configuration into core business logic
            self.core_config.load_from_dict(dict(self.settings))
            
            # Use core business logic for validation
            validation_result = self.core_config.validate_configuration()
            
            if not validation_result.is_valid:
                for error in validation_result.errors:
                    logger.error(f"Configuration validation error: {error}")
                return False
            
            # Log warnings if any
            for warning in validation_result.warnings:
                logger.error(f"Configuration warning: {warning}")
            
            logger.info("Configuration validation passed")
            return True
        except Exception as e:
            logger.error("Configuration validation failed")
            return False
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return dict(self.settings)