# tests/test_connection_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from services.connection_manager import ConnectionManager


@pytest.fixture
def manager():
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestConnectionManager:
    @pytest.mark.asyncio
    async def test_connect_stores_connection(self, manager, mock_websocket):
        await manager.connect("user1", mock_websocket)
        assert manager.has_connection("user1")
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self, manager, mock_websocket):
        await manager.connect("user1", mock_websocket)
        await manager.disconnect("user1")
        assert not manager.has_connection("user1")

    @pytest.mark.asyncio
    async def test_send_chunk(self, manager, mock_websocket):
        await manager.connect("user1", mock_websocket)
        await manager.send_chunk("user1", "req123", 1, "hello")
        mock_websocket.send_json.assert_called_with({
            "type": "chunk",
            "requestId": "req123",
            "seq": 1,
            "content": "hello"
        })

    @pytest.mark.asyncio
    async def test_send_start(self, manager, mock_websocket):
        await manager.connect("user1", mock_websocket)
        await manager.send_start("user1", "req123")
        mock_websocket.send_json.assert_called_with({
            "type": "start",
            "requestId": "req123"
        })

    @pytest.mark.asyncio
    async def test_send_done(self, manager, mock_websocket):
        await manager.connect("user1", mock_websocket)
        await manager.send_done("user1", "req123")
        mock_websocket.send_json.assert_called_with({
            "type": "done",
            "requestId": "req123"
        })

    @pytest.mark.asyncio
    async def test_send_error(self, manager, mock_websocket):
        await manager.connect("user1", mock_websocket)
        await manager.send_error("user1", "req123", "ERR_CODE", "error message")
        mock_websocket.send_json.assert_called_with({
            "type": "error",
            "requestId": "req123",
            "code": "ERR_CODE",
            "message": "error message"
        })

    @pytest.mark.asyncio
    async def test_new_connection_replaces_old(self, manager, mock_websocket):
        old_ws = AsyncMock()
        old_ws.accept = AsyncMock()
        old_ws.close = AsyncMock()

        await manager.connect("user1", old_ws)
        await manager.connect("user1", mock_websocket)

        old_ws.close.assert_called_once()
        assert manager.has_connection("user1")
