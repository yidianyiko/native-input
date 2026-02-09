import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, SignalInstance

from services.websocket_client import WebSocketClient, ConnectionState


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure a QApplication exists for the test session."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    yield app


class TestConnectionState:
    def test_initial_state_is_disconnected(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        assert client.state == ConnectionState.DISCONNECTED

    def test_state_enum_values(self):
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.RECONNECTING.value == "reconnecting"


class TestBackoffStrategy:
    def test_backoff_doubles_up_to_max(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        delays = []
        for _ in range(8):
            delays.append(client._next_backoff())
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        assert delays[3] == 8.0
        assert delays[4] == 16.0
        assert delays[5] == 30.0  # capped
        assert delays[6] == 30.0
        assert delays[7] == 30.0

    def test_backoff_resets(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        client._next_backoff()
        client._next_backoff()
        client._reset_backoff()
        assert client._next_backoff() == 1.0


class TestMessageParsing:
    def test_parse_start_message(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        msg = {"type": "start", "requestId": "req_abc"}
        msg_type, data = client._parse_message(json.dumps(msg))
        assert msg_type == "start"
        assert data["requestId"] == "req_abc"

    def test_parse_chunk_message(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        msg = {"type": "chunk", "requestId": "req_abc", "seq": 1, "content": "hello"}
        msg_type, data = client._parse_message(json.dumps(msg))
        assert msg_type == "chunk"
        assert data["content"] == "hello"
        assert data["seq"] == 1

    def test_parse_done_message(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        msg = {"type": "done", "requestId": "req_abc"}
        msg_type, data = client._parse_message(json.dumps(msg))
        assert msg_type == "done"

    def test_parse_error_message(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        msg = {"type": "error", "requestId": "req_abc", "code": "ERR", "message": "fail"}
        msg_type, data = client._parse_message(json.dumps(msg))
        assert msg_type == "error"
        assert data["code"] == "ERR"

    def test_parse_invalid_json_returns_none(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        result = client._parse_message("not json")
        assert result is None

    def test_parse_missing_type_returns_none(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        result = client._parse_message(json.dumps({"data": "no type"}))
        assert result is None


class TestSendCancel:
    @pytest.mark.asyncio
    async def test_send_cancel_when_connected(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        mock_ws = AsyncMock()
        client._ws = mock_ws
        client._state = ConnectionState.CONNECTED
        await client.send_cancel("req_123")
        mock_ws.send.assert_called_once()
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent == {"type": "cancel", "requestId": "req_123"}

    @pytest.mark.asyncio
    async def test_send_cancel_when_disconnected_does_nothing(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        client._ws = None
        await client.send_cancel("req_123")  # should not raise
