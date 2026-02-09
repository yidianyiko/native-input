"""
HTTP Server Service

Runs a FastAPI/uvicorn server in a daemon thread so that external clients
can POST text input to the reInput application.
"""

import threading
from typing import Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.utils.loguru_config import logger
from .routes import router, set_text_callback
from .signal_bridge import HttpSignalBridge


class HttpServerService:
    """Embedded HTTP server that accepts external text input via POST."""

    def __init__(self, host: str = "127.0.0.1", port: int = 18599):
        self.host = host
        self.port = port
        self.bridge = HttpSignalBridge()
        self.server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

        # Build FastAPI app
        self.app = FastAPI(title="reInput API", version="0.1.0")

        # Allow cross-origin requests from any local client
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.app.include_router(router)

        # Wire the route callback to emit the Qt signal
        set_text_callback(self._on_text_received)

    def _on_text_received(self, text: str, button_number: int, role_number: int) -> None:
        """Called from the async route handler; emits a thread-safe Qt signal."""
        logger.info(f"HTTP server received text: {text[:80]}... button={button_number} role={role_number}")
        self.bridge.text_received.emit(text, button_number, role_number)

    def start(self) -> None:
        """Start the uvicorn server in a background daemon thread."""
        try:
            config = uvicorn.Config(
                self.app,
                host=self.host,
                port=self.port,
                log_level="warning",
            )
            self.server = uvicorn.Server(config)
            self._thread = threading.Thread(
                target=self.server.run,
                name="http-server",
                daemon=True,
            )
            self._thread.start()
            logger.info(f"HTTP server started on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")

    def stop(self) -> None:
        """Signal the uvicorn server to shut down gracefully."""
        try:
            if self.server:
                self.server.should_exit = True
                logger.info("HTTP server shutdown requested")
        except Exception as e:
            logger.error(f"Error stopping HTTP server: {e}")
