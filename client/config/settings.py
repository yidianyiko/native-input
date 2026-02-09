from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from utils.platform import get_app_data_dir

logger = logging.getLogger(__name__)

_SETTINGS_FILE = "settings.json"


def get_default_settings() -> dict:
    return {
        "server_host": "localhost",
        "server_port": 18080,
        "user_id": "default_user",
        "hotkey": "<ctrl>+<shift>+space",
        "window_opacity": 0.92,
    }


@dataclass
class Settings:
    server_host: str = "localhost"
    server_port: int = 18080
    user_id: str = "default_user"
    hotkey: str = "<ctrl>+<shift>+space"
    window_opacity: float = 0.92

    @property
    def ws_url(self) -> str:
        return f"ws://{self.server_host}:{self.server_port}/ws/{self.user_id}"


def load_settings(path: Path | None = None) -> Settings:
    if path is None:
        path = get_app_data_dir() / _SETTINGS_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        defaults = get_default_settings()
        defaults.update(data)
        return Settings(**{k: v for k, v in defaults.items() if k in Settings.__dataclass_fields__})
    except Exception:
        logger.debug("Failed to load settings from %s, using defaults", path)
        return Settings()


def save_settings(settings: Settings, path: Path | None = None) -> None:
    if path is None:
        path = get_app_data_dir() / _SETTINGS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(settings)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
