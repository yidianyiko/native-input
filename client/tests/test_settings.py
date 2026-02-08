import json
from pathlib import Path

import pytest

from config.settings import Settings, get_default_settings, load_settings, save_settings


class TestDefaultSettings:
    def test_default_settings_has_required_keys(self):
        defaults = get_default_settings()
        assert defaults["server_host"] == "localhost"
        assert defaults["server_port"] == 18080
        assert defaults["user_id"] == "default_user"
        assert defaults["hotkey"] == "<ctrl>+<shift>+space"
        assert defaults["window_opacity"] == 0.92

    def test_settings_from_defaults(self):
        s = Settings()
        assert s.server_host == "localhost"
        assert s.server_port == 18080
        assert s.ws_url == "ws://localhost:18080/ws/default_user"


class TestLoadSaveSettings:
    def test_save_and_load_roundtrip(self, tmp_path):
        path = tmp_path / "settings.json"
        s = Settings(server_host="example.com", server_port=9090, user_id="u1")
        save_settings(s, path)
        loaded = load_settings(path)
        assert loaded.server_host == "example.com"
        assert loaded.server_port == 9090
        assert loaded.user_id == "u1"

    def test_load_missing_file_returns_defaults(self, tmp_path):
        path = tmp_path / "nonexistent.json"
        loaded = load_settings(path)
        assert loaded.server_host == "localhost"

    def test_load_corrupt_file_returns_defaults(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json!!!")
        loaded = load_settings(path)
        assert loaded.server_host == "localhost"

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "settings.json"
        save_settings(Settings(), path)
        assert path.exists()
