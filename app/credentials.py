"""Persist and load credentials for the desktop app.

Primary use-case: store DeepSeek API key in app-data settings.json.

Precedence (highest to lowest):
1) Environment / .env (`DEEPSEEK_API_KEY`)
2) settings.json under app data directory
"""

import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # dotenv is optional for production; don't fail import.
    pass

from app.config import get_app_data_dir


def _settings_path() -> Path:
    return get_app_data_dir() / "settings.json"


def load_deepseek_api_key() -> str:
    """Load the DeepSeek API key using precedence rules."""
    env = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if env:
        return env

    path = _settings_path()
    if not path.exists():
        return ""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    return str(data.get("deepseek_api_key", "") or "").strip()


def save_deepseek_api_key(key: str) -> None:
    """Persist the DeepSeek API key to settings.json (best-effort atomic)."""
    key = (key or "").strip()
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {"deepseek_api_key": key}

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

    # Best-effort: restrict permissions on POSIX.
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
