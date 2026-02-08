from unittest.mock import MagicMock

from app.tray import TrayApp


def test_set_api_key_saves_and_updates_menu(monkeypatch):
    app = TrayApp()
    app._icon = MagicMock()

    saved = {}

    def fake_save(key: str) -> None:
        saved["key"] = key

    monkeypatch.setattr("app.tray.save_deepseek_api_key", fake_save)

    app._save_api_key("k999")

    assert saved["key"] == "k999"
    app._icon.update_menu.assert_called()
