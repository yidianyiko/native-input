# tests/test_integration.py
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app, connection_manager, request_registry


class TestIntegration:
    def test_full_flow_with_websocket(self):
        with TestClient(app) as client:
            # Step 1: Connect WebSocket
            with client.websocket_connect("/ws/integration_user") as websocket:
                # Verify connection
                assert connection_manager.has_connection("integration_user")

                # Step 2: Send process request (will use mock agent)
                with patch('services.agent_service.Agent') as mock_agent_class:
                    # Mock the agent to return test chunks
                    mock_agent = MagicMock()
                    mock_agent.run.return_value = iter([
                        MagicMock(event="run_content", content="Test response")
                    ])
                    mock_agent_class.return_value = mock_agent

                    response = client.post("/api/process", json={
                        "text": "Hello world",
                        "buttonId": "polish",
                        "roleId": "work_email",
                        "userId": "integration_user"
                    })

                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "ok"
                    assert "requestId" in data

                    # Step 3: Receive messages via WebSocket
                    # Give background task time to run
                    import time
                    time.sleep(0.5)

                    # Messages should have been sent
                    # (In real test, we'd receive them via websocket)

    def test_process_without_websocket_fails(self):
        with TestClient(app) as client:
            response = client.post("/api/process", json={
                "text": "Hello",
                "buttonId": "polish",
                "roleId": "work_email",
                "userId": "no_ws_user"
            })
            assert response.status_code == 409

    def test_cancel_flow(self):
        with TestClient(app) as client:
            with client.websocket_connect("/ws/cancel_user") as websocket:
                # Register a request directly
                request_registry.register("cancel_user", "test_req_123")

                # Cancel it
                response = client.post("/api/cancel", json={
                    "userId": "cancel_user",
                    "requestId": "test_req_123"
                })
                assert response.status_code == 200
                assert response.json()["status"] == "ok"
