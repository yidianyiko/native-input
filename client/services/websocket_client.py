from __future__ import annotations

import asyncio
import json
import logging
from enum import Enum
from threading import Thread
from typing import Any

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class WebSocketClient(QObject):
    """WebSocket client that runs in a background thread and emits Qt signals."""

    # Signals for UI thread
    message_start = Signal(str)       # requestId
    message_chunk = Signal(str, int, str)  # requestId, seq, content
    message_done = Signal(str)        # requestId
    message_error = Signal(str, str, str)  # requestId, code, message
    state_changed = Signal(str)       # ConnectionState.value

    _BACKOFF_INITIAL = 1.0
    _BACKOFF_MAX = 30.0
    _PING_INTERVAL = 20
    _PING_TIMEOUT = 10

    def __init__(self, ws_url: str, parent: QObject | None = None):
        super().__init__(parent)
        self._ws_url = ws_url
        self._state = ConnectionState.DISCONNECTED
        self._ws: Any = None
        self._backoff = self._BACKOFF_INITIAL
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: Thread | None = None
        self._should_stop = False

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def ws_url(self) -> str:
        return self._ws_url

    @ws_url.setter
    def ws_url(self, url: str) -> None:
        self._ws_url = url

    def _set_state(self, state: ConnectionState) -> None:
        self._state = state
        self.state_changed.emit(state.value)

    def _next_backoff(self) -> float:
        delay = self._backoff
        self._backoff = min(self._backoff * 2, self._BACKOFF_MAX)
        return delay

    def _reset_backoff(self) -> None:
        self._backoff = self._BACKOFF_INITIAL

    def _parse_message(self, raw: str) -> tuple[str, dict] | None:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Received invalid JSON: %s", raw[:200])
            return None
        msg_type = data.get("type")
        if not msg_type:
            logger.warning("Message missing 'type' field: %s", raw[:200])
            return None
        return msg_type, data

    def _dispatch_message(self, msg_type: str, data: dict) -> None:
        request_id = data.get("requestId", "")
        if msg_type == "start":
            self.message_start.emit(request_id)
        elif msg_type == "chunk":
            self.message_chunk.emit(
                request_id, data.get("seq", 0), data.get("content", "")
            )
        elif msg_type == "done":
            self.message_done.emit(request_id)
        elif msg_type == "error":
            self.message_error.emit(
                request_id, data.get("code", ""), data.get("message", "")
            )

    async def send_cancel(self, request_id: str) -> None:
        if self._state != ConnectionState.CONNECTED or self._ws is None:
            return
        try:
            msg = json.dumps({"type": "cancel", "requestId": request_id})
            await self._ws.send(msg)
        except Exception:
            logger.exception("Failed to send cancel for %s", request_id)

    async def _connect_loop(self) -> None:
        import websockets

        while not self._should_stop:
            try:
                self._set_state(ConnectionState.CONNECTING)
                async with websockets.connect(
                    self._ws_url,
                    ping_interval=self._PING_INTERVAL,
                    ping_timeout=self._PING_TIMEOUT,
                ) as ws:
                    self._ws = ws
                    self._set_state(ConnectionState.CONNECTED)
                    self._reset_backoff()
                    logger.info("WebSocket connected to %s", self._ws_url)
                    async for raw in ws:
                        if self._should_stop:
                            break
                        result = self._parse_message(raw)
                        if result:
                            self._dispatch_message(*result)
            except Exception:
                if self._should_stop:
                    break
                logger.exception("WebSocket connection error")
            finally:
                self._ws = None

            if not self._should_stop:
                delay = self._next_backoff()
                self._set_state(ConnectionState.RECONNECTING)
                logger.info("Reconnecting in %.1fs...", delay)
                await asyncio.sleep(delay)

        self._set_state(ConnectionState.DISCONNECTED)

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_loop())
        finally:
            self._loop.close()
            self._loop = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._should_stop = False
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._should_stop = True
        if self._loop and self._ws:
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def send_cancel_threadsafe(self, request_id: str) -> None:
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.send_cancel(request_id), self._loop
            )
