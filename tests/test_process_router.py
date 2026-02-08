# tests/test_process_router.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.process import router, get_connection_manager, get_request_registry, get_prompt_loader, get_agent_service
from services.connection_manager import ConnectionManager
from services.request_registry import RequestRegistry
from services.prompt_loader import PromptLoader


@pytest.fixture
def mock_connection_manager():
    cm = MagicMock(spec=ConnectionManager)
    cm.has_connection = MagicMock(return_value=True)
    cm.send_start = AsyncMock()
    cm.send_chunk = AsyncMock()
    cm.send_done = AsyncMock()
    cm.send_error = AsyncMock()
    return cm


@pytest.fixture
def mock_request_registry():
    rr = MagicMock(spec=RequestRegistry)
    rr.register = MagicMock(return_value=MagicMock())
    rr.complete = MagicMock()
    return rr


@pytest.fixture
def mock_prompt_loader():
    pl = MagicMock(spec=PromptLoader)
    pl.get_prompt = MagicMock(return_value="Formatted prompt: test")
    return pl


@pytest.fixture
def mock_agent_service():
    async def mock_stream(*args, **kwargs):
        yield "Hello "
        yield "World"

    agent = MagicMock()
    agent.process_stream = mock_stream
    return agent


@pytest.fixture
def app(mock_connection_manager, mock_request_registry, mock_prompt_loader, mock_agent_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_connection_manager] = lambda: mock_connection_manager
    app.dependency_overrides[get_request_registry] = lambda: mock_request_registry
    app.dependency_overrides[get_prompt_loader] = lambda: mock_prompt_loader
    app.dependency_overrides[get_agent_service] = lambda: mock_agent_service
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestProcessRouter:
    def test_process_returns_ok(self, client):
        response = client.post("/api/process", json={
            "text": "Hello",
            "buttonId": "polish",
            "roleId": "work_email",
            "userId": "user123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "requestId" in data

    def test_process_no_connection_returns_409(self, client, mock_connection_manager):
        mock_connection_manager.has_connection = MagicMock(return_value=False)

        response = client.post("/api/process", json={
            "text": "Hello",
            "buttonId": "polish",
            "roleId": "work_email",
            "userId": "user123"
        })
        assert response.status_code == 409

    def test_process_invalid_button_returns_404(self, client, mock_prompt_loader):
        mock_prompt_loader.get_prompt = MagicMock(side_effect=KeyError("Unknown button"))

        response = client.post("/api/process", json={
            "text": "Hello",
            "buttonId": "invalid",
            "roleId": "work_email",
            "userId": "user123"
        })
        assert response.status_code == 404
