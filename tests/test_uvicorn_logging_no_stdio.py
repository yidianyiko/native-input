import sys

import uvicorn

from main import app


def test_uvicorn_config_does_not_crash_when_stdio_missing(monkeypatch, tmp_path):
    # Simulate PyInstaller windowed mode: sys.stdout/sys.stderr can be None.
    monkeypatch.setattr(sys, "stdout", None, raising=False)
    monkeypatch.setattr(sys, "stderr", None, raising=False)

    # Default uvicorn logging config will crash in this situation.
    # Our ServiceManager will pass a file-based log_config to avoid it.
    from app.service import _build_uvicorn_log_config

    log_config = _build_uvicorn_log_config(tmp_path / "uvicorn.log")

    cfg = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=18080,
        log_level="warning",
        log_config=log_config,
    )

    assert cfg.host == "127.0.0.1"
