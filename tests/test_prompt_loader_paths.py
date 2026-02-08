import sys
from pathlib import Path

import pytest


def test_prompt_loader_finds_config_under_meipass(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "prompts.yaml").write_text("roles: {}\nbuttons: {}\n", encoding="utf-8")

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    monkeypatch.chdir(run_dir)

    # Simulate PyInstaller extraction dir
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    from services.prompt_loader import PromptLoader

    loader = PromptLoader()  # default config path
    assert loader.list_roles() == []
    assert loader.list_buttons() == []
