# routers/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from services.connection_manager import ConnectionManager
from services.request_registry import RequestRegistry

router = APIRouter()

# Global instances (will be injected in main.py)
_connection_manager: ConnectionManager | None = None
_request_registry: RequestRegistry | None = None


def init_dependencies(cm: ConnectionManager, rr: RequestRegistry) -> None:
    global _connection_manager, _request_registry
    _connection_manager = cm
    _request_registry = rr


def get_connection_manager() -> ConnectionManager:
    if _connection_manager is None:
        raise RuntimeError("ConnectionManager not initialized")
    return _connection_manager


def get_request_registry() -> RequestRegistry:
    if _request_registry is None:
        raise RuntimeError("RequestRegistry not initialized")
    return _request_registry


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str,
    manager: ConnectionManager = Depends(get_connection_manager),
    registry: RequestRegistry = Depends(get_request_registry),
):
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()

            # Handle cancel message from client
            if data.get("type") == "cancel":
                request_id = data.get("requestId")
                if request_id:
                    registry.cancel(user_id, request_id)

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user_id)
