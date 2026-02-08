# tests/test_main.py
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestMainApp:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_process_endpoint_exists(self, client):
        # Should return 409 (no WS connection) not 404
        response = client.post("/api/process", json={
            "text": "test",
            "buttonId": "polish",
            "roleId": "work_email",
            "userId": "test_user"
        })
        assert response.status_code == 409

    def test_cancel_endpoint_exists(self, client):
        response = client.post("/api/cancel", json={
            "userId": "test_user",
            "requestId": "req_123"
        })
        # Should return 404 (request not found) not 405
        assert response.status_code == 404
