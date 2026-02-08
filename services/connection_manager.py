# services/connection_manager.py
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    def has_connection(self, user_id: str) -> bool:
        return user_id in self._connections

    def get_connection(self, user_id: str) -> WebSocket | None:
        return self._connections.get(user_id)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        # Close existing connection if any
        if user_id in self._connections:
            try:
                await self._connections[user_id].close()
            except Exception:
                pass

        await websocket.accept()
        self._connections[user_id] = websocket

    async def disconnect(self, user_id: str) -> None:
        if user_id in self._connections:
            del self._connections[user_id]

    async def send_start(self, user_id: str, request_id: str) -> None:
        if ws := self._connections.get(user_id):
            await ws.send_json({
                "type": "start",
                "requestId": request_id
            })

    async def send_chunk(self, user_id: str, request_id: str, seq: int, content: str) -> None:
        if ws := self._connections.get(user_id):
            await ws.send_json({
                "type": "chunk",
                "requestId": request_id,
                "seq": seq,
                "content": content
            })

    async def send_done(self, user_id: str, request_id: str) -> None:
        if ws := self._connections.get(user_id):
            await ws.send_json({
                "type": "done",
                "requestId": request_id
            })

    async def send_error(self, user_id: str, request_id: str, code: str, message: str) -> None:
        if ws := self._connections.get(user_id):
            await ws.send_json({
                "type": "error",
                "requestId": request_id,
                "code": code,
                "message": message
            })
