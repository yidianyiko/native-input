"""Application configuration.

Loads configuration from environment variables and .env file.
For production builds, set DEEPSEEK_API_KEY environment variable before compilation.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# API Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Server Configuration
HOST = "127.0.0.1"
PORT = 18080

# Application Info
APP_NAME = "AgentService"
APP_VERSION = "1.0.0"


def get_app_data_dir() -> Path:
    """Get platform-specific app data directory."""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:  # Mac/Linux
        base = Path.home() / "Library" / "Application Support"

    app_dir = base / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


# Database path (for Agno memory)
DB_PATH = get_app_data_dir() / "agent_memory.db"
