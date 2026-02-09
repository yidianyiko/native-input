# tests/test_websocket_router.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.websocket import router, get_connection_manager, get_request_registry
from services.connection_manager import ConnectionManager
from services.request_registry import RequestRegistry


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def connection_manager():
    return ConnectionManager()


@pytest.fixture
def request_registry():
    return RequestRegistry()


class TestWebSocketRouter:
    def test_websocket_connects(self, app, connection_manager, request_registry):
        app.dependency_overrides[get_connection_manager] = lambda: connection_manager
        app.dependency_overrides[get_request_registry] = lambda: request_registry

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                assert connection_manager.has_connection("default")

    def test_websocket_disconnects_on_close(self, app, connection_manager, request_registry):
        app.dependency_overrides[get_connection_manager] = lambda: connection_manager
        app.dependency_overrides[get_request_registry] = lambda: request_registry

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                pass  # Connection closes when exiting context

        assert not connection_manager.has_connection("default")
