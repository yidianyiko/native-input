"""FastAPI service manager."""

import logging
from pathlib import Path
import threading
from typing import Optional

import uvicorn

from app.config import get_app_data_dir


def _build_uvicorn_log_config(log_path: Path) -> dict:
    """File-based uvicorn log config.

    PyInstaller windowed apps on Windows may have sys.stdout/sys.stderr set to None,
    which can break uvicorn's default formatter (it tries to call isatty()).
    Writing logs to a file avoids any dependency on console streams.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(levelprefix)s %(message)s",
                "use_colors": False,
            },
            "access": {
                "format": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',
                "use_colors": False,
            },
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "filename": str(log_path),
                "mode": "a",
                "encoding": "utf-8",
                "formatter": "default",
            },
            "access_file": {
                "class": "logging.FileHandler",
                "filename": str(log_path),
                "mode": "a",
                "encoding": "utf-8",
                "formatter": "access",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["file"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"handlers": ["file"], "level": "INFO", "propagate": False},
            "uvicorn.access": {"handlers": ["access_file"], "level": "INFO", "propagate": False},
        },
        "root": {"handlers": ["file"], "level": "WARNING"},
    }


class ServiceManager:
    """Manages the FastAPI service lifecycle."""

    def __init__(self, host: str = "127.0.0.1", port: int = 18080):
        self.host = host
        self.port = port
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the FastAPI service in a background thread."""
        if self.is_running():
            return

        from main import app

        log_path = get_app_data_dir() / "logs" / "uvicorn.log"
        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="warning",
            log_config=_build_uvicorn_log_config(log_path),
            access_log=False,
        )
        self._server = uvicorn.Server(config)

        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the FastAPI service."""
        if self._server:
            self._server.should_exit = True
            if self._thread:
                self._thread.join(timeout=5)
            self._server = None
            self._thread = None
