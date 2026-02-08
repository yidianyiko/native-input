# Agent Service Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an AI-powered text processing service that receives requests via HTTP, processes them through Agno Agent, and streams results via WebSocket.

**Architecture:** FastAPI server with two endpoints: HTTP POST for receiving process requests, WebSocket for streaming results to clients. Agno framework handles AI agent and memory. YAML config stores prompt templates.

**Tech Stack:** Python 3.11+, FastAPI, Agno, uvicorn, PyYAML, pytest, pytest-asyncio

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `main.py`
- Create: `config/prompts.yaml`

**Step 1: Create requirements.txt**

```txt
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
agno>=2.4.0
pyyaml>=6.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
httpx>=0.27.0
```

**Step 2: Create minimal FastAPI app**

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="Agent Service", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 3: Create initial prompts.yaml**

```yaml
# config/prompts.yaml
roles:
  work_email:
    name: "工作邮件"
    description: "正式商务场景"
  social_chat:
    name: "社交聊天"
    description: "轻松日常对话"
  tech_writing:
    name: "技术写作"
    description: "技术文档和代码相关"

buttons:
  polish:
    name: "润色"
    prompts:
      work_email: "请用正式商务语气润色以下内容，保持专业性：\n\n{text}"
      social_chat: "请用轻松友好的语气润色以下内容：\n\n{text}"
      tech_writing: "请润色以下技术内容，保持准确性和清晰度：\n\n{text}"

  expand:
    name: "扩写"
    prompts:
      work_email: "请扩展以下内容，补充必要的商务细节：\n\n{text}"
      social_chat: "请扩展以下内容，使其更生动有趣：\n\n{text}"
      tech_writing: "请扩展以下技术内容，补充必要的说明和示例：\n\n{text}"

  translate:
    name: "翻译"
    prompts:
      work_email: "请将以下内容翻译成专业的商务英语：\n\n{text}"
      social_chat: "请将以下内容翻译成地道的日常英语：\n\n{text}"
      tech_writing: "请将以下内容翻译成准确的技术英语：\n\n{text}"
```

**Step 4: Install dependencies**

Run: `pip install -r requirements.txt`

**Step 5: Verify server starts**

Run: `uvicorn main:app --host 0.0.0.0 --port 8000 &`
Run: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`
Run: `pkill -f uvicorn`

**Step 6: Commit**

```bash
git add requirements.txt main.py config/prompts.yaml
git commit -m "feat: project setup with FastAPI and config"
```

---

## Task 2: PromptLoader Service

**Files:**
- Create: `services/__init__.py`
- Create: `services/prompt_loader.py`
- Create: `tests/__init__.py`
- Create: `tests/test_prompt_loader.py`

**Step 1: Write the failing test**

```python
# tests/test_prompt_loader.py
import pytest
from services.prompt_loader import PromptLoader


class TestPromptLoader:
    def test_get_prompt_returns_formatted_text(self):
        loader = PromptLoader("config/prompts.yaml")
        result = loader.get_prompt("polish", "work_email", "Hello world")
        assert "Hello world" in result
        assert "正式商务语气" in result

    def test_get_prompt_unknown_button_raises(self):
        loader = PromptLoader("config/prompts.yaml")
        with pytest.raises(KeyError):
            loader.get_prompt("unknown_button", "work_email", "text")

    def test_get_prompt_unknown_role_raises(self):
        loader = PromptLoader("config/prompts.yaml")
        with pytest.raises(KeyError):
            loader.get_prompt("polish", "unknown_role", "text")

    def test_list_roles(self):
        loader = PromptLoader("config/prompts.yaml")
        roles = loader.list_roles()
        assert "work_email" in roles
        assert "social_chat" in roles

    def test_list_buttons(self):
        loader = PromptLoader("config/prompts.yaml")
        buttons = loader.list_buttons()
        assert "polish" in buttons
        assert "expand" in buttons
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_prompt_loader.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'services'"

**Step 3: Write minimal implementation**

```python
# services/__init__.py
```

```python
# services/prompt_loader.py
from pathlib import Path
from typing import Any

import yaml


class PromptLoader:
    def __init__(self, config_path: str = "config/prompts.yaml"):
        self._config_path = Path(config_path)
        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        with open(self._config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def get_prompt(self, button_id: str, role_id: str, text: str) -> str:
        buttons = self._config.get("buttons", {})
        if button_id not in buttons:
            raise KeyError(f"Unknown button: {button_id}")

        prompts = buttons[button_id].get("prompts", {})
        if role_id not in prompts:
            raise KeyError(f"Unknown role for button {button_id}: {role_id}")

        template = prompts[role_id]
        return template.format(text=text)

    def list_roles(self) -> list[str]:
        return list(self._config.get("roles", {}).keys())

    def list_buttons(self) -> list[str]:
        return list(self._config.get("buttons", {}).keys())
```

```python
# tests/__init__.py
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_prompt_loader.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/ tests/
git commit -m "feat: add PromptLoader for config loading"
```

---

## Task 3: ConnectionManager Service

**Files:**
- Create: `services/connection_manager.py`
- Create: `tests/test_connection_manager.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_connection_manager.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_connection_manager.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/connection_manager.py tests/test_connection_manager.py
git commit -m "feat: add ConnectionManager for WebSocket handling"
```

---

## Task 4: RequestRegistry Service

**Files:**
- Create: `services/request_registry.py`
- Create: `tests/test_request_registry.py`

**Step 1: Write the failing test**

```python
# tests/test_request_registry.py
import asyncio
import pytest
from services.request_registry import RequestRegistry


@pytest.fixture
def registry():
    return RequestRegistry()


class TestRequestRegistry:
    def test_register_creates_cancel_event(self, registry):
        event = registry.register("user1", "req1")
        assert not event.is_set()
        assert registry.get_active_request("user1") == "req1"

    def test_register_cancels_previous_request(self, registry):
        event1 = registry.register("user1", "req1")
        event2 = registry.register("user1", "req2")

        assert event1.is_set()  # old request cancelled
        assert not event2.is_set()  # new request active
        assert registry.get_active_request("user1") == "req2"

    def test_cancel_sets_event(self, registry):
        event = registry.register("user1", "req1")
        result = registry.cancel("user1", "req1")

        assert result is True
        assert event.is_set()

    def test_cancel_wrong_request_id_returns_false(self, registry):
        registry.register("user1", "req1")
        result = registry.cancel("user1", "wrong_id")

        assert result is False

    def test_cancel_unknown_user_returns_false(self, registry):
        result = registry.cancel("unknown", "req1")
        assert result is False

    def test_complete_clears_request(self, registry):
        registry.register("user1", "req1")
        registry.complete("user1", "req1")

        assert registry.get_active_request("user1") is None

    def test_complete_wrong_request_id_does_nothing(self, registry):
        registry.register("user1", "req1")
        registry.complete("user1", "wrong_id")

        assert registry.get_active_request("user1") == "req1"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_request_registry.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# services/request_registry.py
import asyncio


class RequestRegistry:
    def __init__(self):
        self._active_requests: dict[str, str] = {}  # user_id -> request_id
        self._cancel_events: dict[str, asyncio.Event] = {}  # request_id -> Event

    def get_active_request(self, user_id: str) -> str | None:
        return self._active_requests.get(user_id)

    def register(self, user_id: str, request_id: str) -> asyncio.Event:
        # Cancel existing request for this user
        if old_request_id := self._active_requests.get(user_id):
            if old_event := self._cancel_events.get(old_request_id):
                old_event.set()
            self._cancel_events.pop(old_request_id, None)

        # Create new cancel event
        event = asyncio.Event()
        self._active_requests[user_id] = request_id
        self._cancel_events[request_id] = event
        return event

    def cancel(self, user_id: str, request_id: str) -> bool:
        if self._active_requests.get(user_id) != request_id:
            return False

        if event := self._cancel_events.get(request_id):
            event.set()
            return True
        return False

    def complete(self, user_id: str, request_id: str) -> None:
        if self._active_requests.get(user_id) == request_id:
            del self._active_requests[user_id]
            self._cancel_events.pop(request_id, None)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_request_registry.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/request_registry.py tests/test_request_registry.py
git commit -m "feat: add RequestRegistry for request lifecycle"
```

---

## Task 5: AgentService

**Files:**
- Create: `services/agent_service.py`
- Create: `tests/test_agent_service.py`

**Step 1: Write the failing test**

```python
# tests/test_agent_service.py
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.agent_service import AgentService


@pytest.fixture
def agent_service():
    return AgentService()


class TestAgentService:
    @pytest.mark.asyncio
    async def test_process_stream_yields_chunks(self, agent_service):
        cancel_event = asyncio.Event()
        chunks = []

        with patch.object(agent_service, '_create_agent') as mock_create:
            # Mock the agent to return predictable chunks
            mock_agent = MagicMock()
            mock_stream = [
                MagicMock(event="run_content", content="Hello "),
                MagicMock(event="run_content", content="World"),
            ]
            mock_agent.run = MagicMock(return_value=iter(mock_stream))
            mock_create.return_value = mock_agent

            async for chunk in agent_service.process_stream(
                text="test",
                prompt_template="Process: {text}",
                user_id="user1",
                request_id="req1",
                cancel_event=cancel_event
            ):
                chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0] == "Hello "
        assert chunks[1] == "World"

    @pytest.mark.asyncio
    async def test_process_stream_stops_on_cancel(self, agent_service):
        cancel_event = asyncio.Event()
        chunks = []

        with patch.object(agent_service, '_create_agent') as mock_create:
            mock_agent = MagicMock()

            def slow_stream():
                yield MagicMock(event="run_content", content="First")
                cancel_event.set()  # Cancel after first chunk
                yield MagicMock(event="run_content", content="Second")

            mock_agent.run = MagicMock(return_value=slow_stream())
            mock_create.return_value = mock_agent

            async for chunk in agent_service.process_stream(
                text="test",
                prompt_template="Process: {text}",
                user_id="user1",
                request_id="req1",
                cancel_event=cancel_event
            ):
                chunks.append(chunk)

        assert len(chunks) == 1
        assert chunks[0] == "First"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent_service.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# services/agent_service.py
import asyncio
from collections.abc import AsyncGenerator
from typing import Any

from agno.agent import Agent, RunEvent
from agno.models.anthropic import Claude
from agno.db.sqlite import SqliteDb


class AgentService:
    def __init__(self, db_path: str = "agent_memory.db"):
        self._db_path = db_path
        self._db = SqliteDb(db_file=db_path)

    def _create_agent(self, user_id: str) -> Agent:
        return Agent(
            model=Claude(id="claude-sonnet-4-5"),
            db=self._db,
            add_history_to_context=True,
            num_history_runs=5,
            markdown=True,
        )

    async def process_stream(
        self,
        text: str,
        prompt_template: str,
        user_id: str,
        request_id: str,
        cancel_event: asyncio.Event,
    ) -> AsyncGenerator[str, None]:
        prompt = prompt_template.format(text=text)
        agent = self._create_agent(user_id)

        # Use session_id to scope memory by user
        stream = agent.run(prompt, session_id=user_id, stream=True)

        for chunk in stream:
            if cancel_event.is_set():
                break

            if hasattr(chunk, 'event') and chunk.event == RunEvent.run_content:
                if chunk.content:
                    yield chunk.content
            elif hasattr(chunk, 'content') and chunk.content:
                # Fallback for simpler response format
                yield chunk.content

            # Allow other tasks to run
            await asyncio.sleep(0)
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_agent_service.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/agent_service.py tests/test_agent_service.py
git commit -m "feat: add AgentService for Agno integration"
```

---

## Task 6: WebSocket Router

**Files:**
- Create: `routers/__init__.py`
- Create: `routers/websocket.py`
- Create: `tests/test_websocket_router.py`

**Step 1: Write the failing test**

```python
# tests/test_websocket_router.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.websocket import router, get_connection_manager
from services.connection_manager import ConnectionManager


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


class TestWebSocketRouter:
    def test_websocket_connects(self, app, connection_manager):
        app.dependency_overrides[get_connection_manager] = lambda: connection_manager

        with TestClient(app) as client:
            with client.websocket_connect("/ws/user123") as websocket:
                assert connection_manager.has_connection("user123")

    def test_websocket_disconnects_on_close(self, app, connection_manager):
        app.dependency_overrides[get_connection_manager] = lambda: connection_manager

        with TestClient(app) as client:
            with client.websocket_connect("/ws/user123") as websocket:
                pass  # Connection closes when exiting context

        assert not connection_manager.has_connection("user123")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_websocket_router.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# routers/__init__.py
```

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_websocket_router.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add routers/ tests/test_websocket_router.py
git commit -m "feat: add WebSocket router for client connections"
```

---

## Task 7: Process Router

**Files:**
- Create: `routers/process.py`
- Create: `tests/test_process_router.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_process_router.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# routers/process.py
import asyncio
import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from services.connection_manager import ConnectionManager
from services.request_registry import RequestRegistry
from services.prompt_loader import PromptLoader
from services.agent_service import AgentService

router = APIRouter()

# Global instances
_connection_manager: ConnectionManager | None = None
_request_registry: RequestRegistry | None = None
_prompt_loader: PromptLoader | None = None
_agent_service: AgentService | None = None


def init_dependencies(
    cm: ConnectionManager,
    rr: RequestRegistry,
    pl: PromptLoader,
    agent: AgentService
) -> None:
    global _connection_manager, _request_registry, _prompt_loader, _agent_service
    _connection_manager = cm
    _request_registry = rr
    _prompt_loader = pl
    _agent_service = agent


def get_connection_manager() -> ConnectionManager:
    if _connection_manager is None:
        raise RuntimeError("ConnectionManager not initialized")
    return _connection_manager


def get_request_registry() -> RequestRegistry:
    if _request_registry is None:
        raise RuntimeError("RequestRegistry not initialized")
    return _request_registry


def get_prompt_loader() -> PromptLoader:
    if _prompt_loader is None:
        raise RuntimeError("PromptLoader not initialized")
    return _prompt_loader


def get_agent_service() -> AgentService:
    if _agent_service is None:
        raise RuntimeError("AgentService not initialized")
    return _agent_service


class ProcessRequest(BaseModel):
    text: str
    buttonId: str
    roleId: str
    userId: str


class ProcessResponse(BaseModel):
    status: str
    requestId: str
    message: str


async def process_task(
    request: ProcessRequest,
    request_id: str,
    prompt: str,
    cancel_event: asyncio.Event,
    cm: ConnectionManager,
    rr: RequestRegistry,
    agent: AgentService,
):
    try:
        await cm.send_start(request.userId, request_id)

        seq = 0
        async for chunk in agent.process_stream(
            text=request.text,
            prompt_template=prompt,
            user_id=request.userId,
            request_id=request_id,
            cancel_event=cancel_event,
        ):
            if cancel_event.is_set():
                break
            seq += 1
            await cm.send_chunk(request.userId, request_id, seq, chunk)

        if not cancel_event.is_set():
            await cm.send_done(request.userId, request_id)

    except Exception as e:
        await cm.send_error(request.userId, request_id, "PROCESSING_ERROR", str(e))
    finally:
        rr.complete(request.userId, request_id)


@router.post("/api/process", response_model=ProcessResponse)
async def process(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    cm: ConnectionManager = Depends(get_connection_manager),
    rr: RequestRegistry = Depends(get_request_registry),
    pl: PromptLoader = Depends(get_prompt_loader),
    agent: AgentService = Depends(get_agent_service),
):
    # Check WebSocket connection exists
    if not cm.has_connection(request.userId):
        raise HTTPException(
            status_code=409,
            detail=f"No WebSocket connection for user {request.userId}"
        )

    # Get prompt template
    try:
        prompt = pl.get_prompt(request.buttonId, request.roleId, "{text}")
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Generate request ID and register
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    cancel_event = rr.register(request.userId, request_id)

    # Start background processing
    background_tasks.add_task(
        process_task,
        request,
        request_id,
        prompt,
        cancel_event,
        cm,
        rr,
        agent,
    )

    return ProcessResponse(
        status="ok",
        requestId=request_id,
        message="Processing started"
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_process_router.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add routers/process.py tests/test_process_router.py
git commit -m "feat: add process router for HTTP requests"
```

---

## Task 8: Cancel Router

**Files:**
- Create: `routers/cancel.py`
- Create: `tests/test_cancel_router.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_cancel_router.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

```python
# routers/cancel.py
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException

from services.request_registry import RequestRegistry

router = APIRouter()

_request_registry: RequestRegistry | None = None


def init_dependencies(rr: RequestRegistry) -> None:
    global _request_registry
    _request_registry = rr


def get_request_registry() -> RequestRegistry:
    if _request_registry is None:
        raise RuntimeError("RequestRegistry not initialized")
    return _request_registry


class CancelRequest(BaseModel):
    userId: str
    requestId: str


class CancelResponse(BaseModel):
    status: str


@router.post("/api/cancel", response_model=CancelResponse)
async def cancel(
    request: CancelRequest,
    rr: RequestRegistry = Depends(get_request_registry),
):
    if not rr.cancel(request.userId, request.requestId):
        raise HTTPException(
            status_code=404,
            detail=f"Request {request.requestId} not found for user {request.userId}"
        )

    return CancelResponse(status="ok")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_cancel_router.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add routers/cancel.py tests/test_cancel_router.py
git commit -m "feat: add cancel router for request cancellation"
```

---

## Task 9: Wire Up Main Application

**Files:**
- Modify: `main.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main.py -v`
Expected: FAIL (missing routes)

**Step 3: Update main.py**

```python
# main.py
from fastapi import FastAPI

from services.connection_manager import ConnectionManager
from services.request_registry import RequestRegistry
from services.prompt_loader import PromptLoader
from services.agent_service import AgentService

from routers import websocket as ws_router
from routers import process as process_router
from routers import cancel as cancel_router

app = FastAPI(title="Agent Service", version="0.1.0")

# Initialize shared dependencies
connection_manager = ConnectionManager()
request_registry = RequestRegistry()
prompt_loader = PromptLoader()
agent_service = AgentService()

# Inject dependencies into routers
ws_router.init_dependencies(connection_manager, request_registry)
process_router.init_dependencies(connection_manager, request_registry, prompt_loader, agent_service)
cancel_router.init_dependencies(request_registry)

# Include routers
app.include_router(ws_router.router)
app.include_router(process_router.router)
app.include_router(cancel_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: wire up all routers in main application"
```

---

## Task 10: Integration Test

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

```python
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
```

**Step 2: Run integration test**

Run: `pytest tests/test_integration.py -v`
Expected: All tests PASS

**Step 3: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for full flow"
```

---

## Task 11: Create pytest.ini and Final Cleanup

**Files:**
- Create: `pytest.ini`
- Create: `.env.example`

**Step 1: Create pytest.ini**

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

**Step 2: Create .env.example**

```
# .env.example
# Copy to .env and fill in values

# Anthropic API Key for Claude
ANTHROPIC_API_KEY=your_api_key_here

# Server configuration
HOST=0.0.0.0
PORT=8000
```

**Step 3: Run all tests**

Run: `pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add pytest.ini .env.example
git commit -m "chore: add pytest config and env example"
```

---

## Task 12: Final Verification

**Step 1: Verify project structure**

Run: `find . -type f -name "*.py" | head -20`

Expected structure:
```
./main.py
./services/__init__.py
./services/prompt_loader.py
./services/connection_manager.py
./services/request_registry.py
./services/agent_service.py
./routers/__init__.py
./routers/websocket.py
./routers/process.py
./routers/cancel.py
./tests/__init__.py
./tests/test_prompt_loader.py
./tests/test_connection_manager.py
./tests/test_request_registry.py
./tests/test_agent_service.py
./tests/test_websocket_router.py
./tests/test_process_router.py
./tests/test_cancel_router.py
./tests/test_main.py
./tests/test_integration.py
```

**Step 2: Run full test suite**

Run: `pytest -v --tb=short`
Expected: All tests PASS

**Step 3: Start server and test manually**

Run: `uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1`

Test health:
Run: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`

**Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete Agent Service MVP implementation"
```

---

## Summary

This plan implements:

1. **PromptLoader** - Loads and renders prompt templates from YAML
2. **ConnectionManager** - Manages WebSocket connections by userId
3. **RequestRegistry** - Tracks active requests and handles cancellation
4. **AgentService** - Wraps Agno Agent for streaming text generation
5. **WebSocket Router** - `/ws/{userId}` for client connections
6. **Process Router** - `/api/process` for triggering generation
7. **Cancel Router** - `/api/cancel` for stopping requests
8. **Integration Tests** - Full flow verification

Total: 12 tasks, ~60 steps, TDD throughout.
