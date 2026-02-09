# HTTP POST Input Server Integration

## Overview

Embed a lightweight HTTP server (FastAPI + uvicorn) into the reInput desktop app. External clients can POST text to the server, which will be displayed in the floating window's input field. If the floating window is not open, it will auto-open.

## Architecture

- **Server runs in a background thread** to avoid blocking the Qt event loop.
- **Qt signal bridge** (`QObject` subclass) allows the HTTP thread to safely communicate with the Qt main thread.
- Reference: `docs/native-input/routers/process.py` for POST structure inspiration.

---

## Step 1: Add Dependencies

**File:** `pyproject.toml`

Add `fastapi` and `uvicorn` to the `dependencies` list:

```toml
"fastapi>=0.115.0",
"uvicorn>=0.34.0",
```

Then run `uv sync` to install.

---

## Step 2: Add Configuration

**File:** `settings.toml`

Replace the existing `[native_input]` section with an `[http_server]` section (or add alongside it):

```toml
[http_server]
enabled = true
host = "127.0.0.1"
port = 18599
```

---

## Step 3: Create the HTTP Server Service

**New file:** `src/services/http_server/__init__.py` (empty)

**New file:** `src/services/http_server/signal_bridge.py`

A `QObject` subclass that acts as a thread-safe bridge between the HTTP server thread and the Qt main thread:

```python
from PySide6.QtCore import QObject, Signal

class HttpSignalBridge(QObject):
    """Thread-safe bridge: HTTP server thread -> Qt main thread."""
    text_received = Signal(str)  # emitted when POST /api/input receives text
```

**New file:** `src/services/http_server/routes.py`

Define the FastAPI routes:

```python
from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter()

class InputRequest(BaseModel):
    text: str

class InputResponse(BaseModel):
    status: str
    message: str

# A callback set by the server at startup
_on_text_received = None

def set_text_callback(callback):
    global _on_text_received
    _on_text_received = callback

@router.post("/api/input", response_model=InputResponse)
async def receive_input(request: InputRequest):
    if not request.text.strip():
        return InputResponse(status="error", message="Empty text")
    if _on_text_received:
        _on_text_received(request.text)
    return InputResponse(status="ok", message="Text received")

@router.get("/health")
async def health():
    return {"status": "ok"}
```

**New file:** `src/services/http_server/http_server.py`

The main service that starts/stops uvicorn in a daemon thread:

```python
import threading, uvicorn
from fastapi import FastAPI
from .routes import router, set_text_callback
from .signal_bridge import HttpSignalBridge

class HttpServerService:
    def __init__(self, host="127.0.0.1", port=18599):
        self.host = host
        self.port = port
        self.bridge = HttpSignalBridge()
        self.server = None
        self._thread = None

        self.app = FastAPI(title="reInput API")
        self.app.include_router(router)
        set_text_callback(self.bridge.text_received.emit)

    def start(self):
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="warning")
        self.server = uvicorn.Server(config)
        self._thread = threading.Thread(target=self.server.run, daemon=True)
        self._thread.start()

    def stop(self):
        if self.server:
            self.server.should_exit = True
```

---

## Step 4: Integrate into App Initialization

**File:** `src/core/app_initializer.py`

1. Add a new instance variable `self.http_server_service` in `__init__`.
2. Add a new initialization step `_initialize_http_server()` after the floating window is initialized (Step 5.5).
3. In `_initialize_http_server()`:
   - Read `http_server.enabled`, `http_server.host`, `http_server.port` from config.
   - Create `HttpServerService(host, port)`.
   - Connect `http_server_service.bridge.text_received` signal to a slot that calls `floating_window.set_text(text)` + `floating_window.show_window()`.
   - Call `http_server_service.start()`.
4. Add `http_server_service` to `get_components()` dict.

---

## Step 5: Wire Shutdown

**File:** `src/core/app_lifecycle.py`

In `shutdown()`, call `self.http_server_service.stop()` if the component exists.

---

## Step 6: Handle Incoming Text in Floating Window

**File:** `src/ui/windows/floating_window/main.py`

Add a new method `receive_external_input(text: str)` that:

1. Calls `self.clear_content()` to reset state.
2. Calls `self.set_text(text)` to populate the input field.
3. If the window is not visible, calls `self.show_window()` to auto-open it.

This method will be connected to the HTTP signal bridge's `text_received` signal.

---

## File Change Summary

| File | Action |
|------|--------|
| `pyproject.toml` | Add fastapi, uvicorn deps |
| `settings.toml` | Add `[http_server]` config section |
| `src/services/http_server/__init__.py` | New (empty) |
| `src/services/http_server/signal_bridge.py` | New - Qt signal bridge |
| `src/services/http_server/routes.py` | New - POST endpoint |
| `src/services/http_server/http_server.py` | New - Server service |
| `src/core/app_initializer.py` | Add HTTP server init step |
| `src/core/app_lifecycle.py` | Add HTTP server shutdown |
| `src/ui/windows/floating_window/main.py` | Add `receive_external_input()` method |
