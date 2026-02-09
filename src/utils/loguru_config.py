"""Loguru configuration for reInput application.

This module provides a simplified logging configuration using loguru,
replacing the complex category-based logging system.
"""

import sys
from pathlib import Path
from loguru import logger
from dynaconf import Dynaconf

# Load settings to get log level
try:
    settings = Dynaconf(
        settings_files=["settings.toml"],
        load_dotenv=True,
    )
    console_log_level = settings.get("logging.level", "INFO") or "INFO"
    file_log_level = settings.get("logging.level", "DEBUG") or "DEBUG"
    print(f"[LOGURU CONFIG] Loaded log levels: console={console_log_level}, file={file_log_level}")
except Exception as e:
    # Fallback if settings can't be loaded
    console_log_level = "INFO"
    file_log_level = "DEBUG"
    print(f"[LOGURU CONFIG] Failed to load settings, using defaults: {e}")

# Ensure log levels are never None
console_log_level = console_log_level or "INFO"
file_log_level = file_log_level or "DEBUG"

# Remove default handler
logger.remove()

# Configure console handler with colors
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=console_log_level,
    colorize=True,
    backtrace=True,
    diagnose=True
)

# Configure file handler
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.add(
    log_dir / "reInput_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level=file_log_level,
    rotation="1 day",
    retention="30 days",
    compression="zip",
    backtrace=True,
    diagnose=True
)

# Configure error file handler
logger.add(
    log_dir / "reInput_errors_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="ERROR",
    rotation="1 day",
    retention="30 days",
    compression="zip",
    backtrace=True,
    diagnose=True
)

def get_logger(name: str = None):
    """Get a logger instance.
    
    Args:
        name: Logger name (optional, for compatibility)
        
    Returns:
        loguru.Logger: Configured logger instance
    """
    return logger

# Export the main logger instance
__all__ = ['logger', 'get_logger']