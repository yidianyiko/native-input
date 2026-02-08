"""Application configuration.

Design choice: embed the Anthropic API key in code so end-users don't need to
configure environment variables at runtime.

Do not commit real secrets to the repository; replace the placeholder during a
private build, or inject it at build time.
"""

import os
from pathlib import Path

# API Configuration
# NOTE: Replace this placeholder for production builds.
ANTHROPIC_API_KEY = "sk-ant-REPLACE_ME"

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
