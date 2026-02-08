import os

from app import credentials


def test_load_returns_empty_when_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(credentials, "get_app_data_dir", lambda: tmp_path)

    assert credentials.load_deepseek_api_key() == ""


def test_save_then_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(credentials, "get_app_data_dir", lambda: tmp_path)

    credentials.save_deepseek_api_key("k123")
    assert credentials.load_deepseek_api_key() == "k123"


def test_env_overrides_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(credentials, "get_app_data_dir", lambda: tmp_path)
    credentials.save_deepseek_api_key("file_key")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "env_key")
    assert credentials.load_deepseek_api_key() == "env_key"
