# services/prompt_loader.py
import sys
from pathlib import Path
from typing import Any

import yaml


def _resolve_config_path(config_path: str) -> Path:
    """Resolve config path for both dev runs and PyInstaller-frozen builds.

    In PyInstaller one-file builds, data files are extracted under `sys._MEIPASS`,
    so relative paths like `config/prompts.yaml` won't exist relative to CWD.
    """
    p = Path(config_path)

    # Absolute path: use directly.
    if p.is_absolute():
        return p

    # Relative path: prefer CWD when it exists (dev runs).
    if p.exists():
        return p.resolve()

    # PyInstaller: data files live under sys._MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidate = Path(meipass) / p
        if candidate.exists():
            return candidate

    # Fallback: resolve relative to repository root (services/ -> repo root).
    candidate = Path(__file__).resolve().parents[1] / p
    if candidate.exists():
        return candidate

    # Last resort: keep original for a clear FileNotFoundError path.
    return p


class PromptLoader:
    def __init__(self, config_path: str = "config/prompts.yaml"):
        self._config_path = _resolve_config_path(config_path)
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def get_prompt(self, button_id: str, role_id: str, text: str) -> str:
        buttons = self._config.get("buttons", {})
        if button_id not in buttons:
            raise KeyError(f"Unknown button: {button_id}")

        prompts = buttons[button_id].get("prompts", {})
        if role_id not in prompts:
            raise KeyError(f"Unknown role for button {button_id}: {role_id}")

        template = prompts[role_id]
        return template.format(text=text)

    def list_roles(self) -> list[str]:
        return list(self._config.get("roles", {}).keys())

    def list_buttons(self) -> list[str]:
        return list(self._config.get("buttons", {}).keys())
