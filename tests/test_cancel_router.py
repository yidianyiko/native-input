# tests/test_cancel_router.py
import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.cancel import router, get_request_registry
from services.request_registry import RequestRegistry


@pytest.fixture
def mock_registry():
    rr = MagicMock(spec=RequestRegistry)
    rr.cancel = MagicMock(return_value=True)
    return rr


@pytest.fixture
def app(mock_registry):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_request_registry] = lambda: mock_registry
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestCancelRouter:
    def test_cancel_returns_ok(self, client, mock_registry):
        response = client.post("/api/cancel", json={
            "userId": "user123",
            "requestId": "req_abc123"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        mock_registry.cancel.assert_called_once_with("user123", "req_abc123")

    def test_cancel_not_found_returns_404(self, client, mock_registry):
        mock_registry.cancel = MagicMock(return_value=False)

        response = client.post("/api/cancel", json={
            "userId": "user123",
            "requestId": "req_notfound"
        })
        assert response.status_code == 404
