"""FastAPI service manager."""

import threading
from typing import Optional

import uvicorn


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

        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="warning",
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
