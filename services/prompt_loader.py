# services/prompt_loader.py
from pathlib import Path
from typing import Any

import yaml


class PromptLoader:
    def __init__(self, config_path: str = "config/prompts.yaml"):
        self._config_path = Path(config_path)
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
