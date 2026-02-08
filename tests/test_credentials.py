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
