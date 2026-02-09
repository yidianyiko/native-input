# 前端悬浮窗客户端 - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a cross-platform (Windows + macOS) floating window client that receives AI-generated text from the Agent Service via WebSocket and injects it into the user's active input field on confirmation.

**Architecture:** The client is a PySide6 Qt application running in the system tray. A background thread manages the WebSocket connection, emitting Qt signals to the main thread for UI updates. The floating window is a frameless, always-on-top widget that appears near the cursor on `start` messages, streams text on `chunk` messages, and injects text into the previously-active window on Enter key press. Platform-specific operations (window context capture, text injection) are abstracted behind a common interface with Windows (`ctypes`/`pynput`) and macOS (`pynput`) implementations.

**Tech Stack:** Python 3.11+, PySide6 (LGPL-3.0), pynput (LGPL-3.0), websockets (BSD-3), pyperclip (BSD-3), PyInstaller (GPL-2.0 with bootloader exception)

---

## Project Structure

```
client/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── config/
│   └── settings.py                  # Config load/save (JSON)
├── services/
│   ├── websocket_client.py          # WebSocket + reconnect + signal bridge
│   ├── window_context.py            # Capture/restore active window (platform-abstracted)
│   └── text_injection.py            # Inject text via pynput + clipboard fallback
├── ui/
│   ├── floating_window.py           # Frameless floating window with state machine
│   ├── tray.py                      # System tray icon and menu
│   └── styles.py                    # Style constants
├── utils/
│   ├── hotkey.py                    # Global hotkey (pynput)
│   ├── platform.py                  # Platform detection helpers
│   └── single_instance.py           # Prevent multiple instances
└── tests/
    ├── test_settings.py
    ├── test_websocket_client.py
    ├── test_window_context.py
    ├── test_text_injection.py
    ├── test_floating_window.py
    ├── test_tray.py
    ├── test_hotkey.py
    └── test_single_instance.py
```

---

## Task 1: Project scaffolding and configuration

**Files:**
- Create: `client/requirements.txt`
- Create: `client/config/__init__.py`
- Create: `client/config/settings.py`
- Create: `client/services/__init__.py`
- Create: `client/ui/__init__.py`
- Create: `client/utils/__init__.py`
- Create: `client/utils/platform.py`
- Test: `client/tests/__init__.py`
- Test: `client/tests/test_settings.py`

**Step 1: Create directory structure and requirements.txt**

```
mkdir -p client/{config,services,ui,utils,tests}
touch client/{config,services,ui,utils,tests}/__init__.py
```

`client/requirements.txt`:
```
PySide6>=6.7.0
pynput>=1.7.6
websockets>=13.0
pyperclip>=1.9.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

**Step 2: Write the failing test for settings**

`client/tests/test_settings.py`:
```python
import json
from pathlib import Path

import pytest

from config.settings import Settings, get_default_settings, load_settings, save_settings


class TestDefaultSettings:
    def test_default_settings_has_required_keys(self):
        defaults = get_default_settings()
        assert defaults["server_host"] == "localhost"
        assert defaults["server_port"] == 18080
        assert defaults["user_id"] == "default_user"
        assert defaults["hotkey"] == "<ctrl>+<shift>+space"
        assert defaults["window_opacity"] == 0.92

    def test_settings_from_defaults(self):
        s = Settings()
        assert s.server_host == "localhost"
        assert s.server_port == 18080
        assert s.ws_url == "ws://localhost:18080/ws/default_user"


class TestLoadSaveSettings:
    def test_save_and_load_roundtrip(self, tmp_path):
        path = tmp_path / "settings.json"
        s = Settings(server_host="example.com", server_port=9090, user_id="u1")
        save_settings(s, path)
        loaded = load_settings(path)
        assert loaded.server_host == "example.com"
        assert loaded.server_port == 9090
        assert loaded.user_id == "u1"

    def test_load_missing_file_returns_defaults(self, tmp_path):
        path = tmp_path / "nonexistent.json"
        loaded = load_settings(path)
        assert loaded.server_host == "localhost"

    def test_load_corrupt_file_returns_defaults(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("not json!!!")
        loaded = load_settings(path)
        assert loaded.server_host == "localhost"

    def test_save_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "sub" / "dir" / "settings.json"
        save_settings(Settings(), path)
        assert path.exists()
```

**Step 3: Run test to verify it fails**

Run: `cd client && python -m pytest tests/test_settings.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config.settings'`

**Step 4: Implement settings module**

`client/utils/platform.py`:
```python
import os
import sys
from pathlib import Path

APP_NAME = "AgentServiceClient"


def get_app_data_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / APP_NAME
```

`client/config/settings.py`:
```python
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

from utils.platform import get_app_data_dir

logger = logging.getLogger(__name__)

_SETTINGS_FILE = "settings.json"


def get_default_settings() -> dict:
    return {
        "server_host": "localhost",
        "server_port": 18080,
        "user_id": "default_user",
        "hotkey": "<ctrl>+<shift>+space",
        "window_opacity": 0.92,
    }


@dataclass
class Settings:
    server_host: str = "localhost"
    server_port: int = 18080
    user_id: str = "default_user"
    hotkey: str = "<ctrl>+<shift>+space"
    window_opacity: float = 0.92

    @property
    def ws_url(self) -> str:
        return f"ws://{self.server_host}:{self.server_port}/ws/{self.user_id}"


def load_settings(path: Path | None = None) -> Settings:
    if path is None:
        path = get_app_data_dir() / _SETTINGS_FILE
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        defaults = get_default_settings()
        defaults.update(data)
        return Settings(**{k: v for k, v in defaults.items() if k in Settings.__dataclass_fields__})
    except Exception:
        logger.debug("Failed to load settings from %s, using defaults", path)
        return Settings()


def save_settings(settings: Settings, path: Path | None = None) -> None:
    if path is None:
        path = get_app_data_dir() / _SETTINGS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(settings)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
```

**Step 5: Run test to verify it passes**

Run: `cd client && python -m pytest tests/test_settings.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add client/
git commit -m "feat(client): add project scaffolding and settings module"
```

---

## Task 2: WebSocket client with reconnect and Qt signal bridge

**Files:**
- Create: `client/services/websocket_client.py`
- Test: `client/tests/test_websocket_client.py`

**Step 1: Write the failing tests**

`client/tests/test_websocket_client.py`:
```python
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PySide6.QtCore import QObject, SignalInstance

from services.websocket_client import WebSocketClient, ConnectionState


class TestConnectionState:
    def test_initial_state_is_disconnected(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        assert client.state == ConnectionState.DISCONNECTED

    def test_state_enum_values(self):
        assert ConnectionState.DISCONNECTED.value == "disconnected"
        assert ConnectionState.CONNECTING.value == "connecting"
        assert ConnectionState.CONNECTED.value == "connected"
        assert ConnectionState.RECONNECTING.value == "reconnecting"


class TestBackoffStrategy:
    def test_backoff_doubles_up_to_max(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        delays = []
        for _ in range(8):
            delays.append(client._next_backoff())
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        assert delays[3] == 8.0
        assert delays[4] == 16.0
        assert delays[5] == 30.0  # capped
        assert delays[6] == 30.0
        assert delays[7] == 30.0

    def test_backoff_resets(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        client._next_backoff()
        client._next_backoff()
        client._reset_backoff()
        assert client._next_backoff() == 1.0


class TestMessageParsing:
    def test_parse_start_message(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        msg = {"type": "start", "requestId": "req_abc"}
        msg_type, data = client._parse_message(json.dumps(msg))
        assert msg_type == "start"
        assert data["requestId"] == "req_abc"

    def test_parse_chunk_message(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        msg = {"type": "chunk", "requestId": "req_abc", "seq": 1, "content": "hello"}
        msg_type, data = client._parse_message(json.dumps(msg))
        assert msg_type == "chunk"
        assert data["content"] == "hello"
        assert data["seq"] == 1

    def test_parse_done_message(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        msg = {"type": "done", "requestId": "req_abc"}
        msg_type, data = client._parse_message(json.dumps(msg))
        assert msg_type == "done"

    def test_parse_error_message(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        msg = {"type": "error", "requestId": "req_abc", "code": "ERR", "message": "fail"}
        msg_type, data = client._parse_message(json.dumps(msg))
        assert msg_type == "error"
        assert data["code"] == "ERR"

    def test_parse_invalid_json_returns_none(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        result = client._parse_message("not json")
        assert result is None

    def test_parse_missing_type_returns_none(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        result = client._parse_message(json.dumps({"data": "no type"}))
        assert result is None


class TestSendCancel:
    @pytest.mark.asyncio
    async def test_send_cancel_when_connected(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        mock_ws = AsyncMock()
        client._ws = mock_ws
        client._state = ConnectionState.CONNECTED
        await client.send_cancel("req_123")
        mock_ws.send.assert_called_once()
        sent = json.loads(mock_ws.send.call_args[0][0])
        assert sent == {"type": "cancel", "requestId": "req_123"}

    @pytest.mark.asyncio
    async def test_send_cancel_when_disconnected_does_nothing(self):
        client = WebSocketClient(ws_url="ws://localhost:18080/ws/test")
        client._ws = None
        await client.send_cancel("req_123")  # should not raise
```

**Step 2: Run test to verify it fails**

Run: `cd client && python -m pytest tests/test_websocket_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Implement WebSocket client**

`client/services/websocket_client.py`:
```python
from __future__ import annotations

import asyncio
import json
import logging
from enum import Enum
from threading import Thread
from typing import Any

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class WebSocketClient(QObject):
    """WebSocket client that runs in a background thread and emits Qt signals."""

    # Signals for UI thread
    message_start = Signal(str)       # requestId
    message_chunk = Signal(str, int, str)  # requestId, seq, content
    message_done = Signal(str)        # requestId
    message_error = Signal(str, str, str)  # requestId, code, message
    state_changed = Signal(str)       # ConnectionState.value

    _BACKOFF_INITIAL = 1.0
    _BACKOFF_MAX = 30.0
    _PING_INTERVAL = 20
    _PING_TIMEOUT = 10

    def __init__(self, ws_url: str, parent: QObject | None = None):
        super().__init__(parent)
        self._ws_url = ws_url
        self._state = ConnectionState.DISCONNECTED
        self._ws: Any = None
        self._backoff = self._BACKOFF_INITIAL
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: Thread | None = None
        self._should_stop = False

    @property
    def state(self) -> ConnectionState:
        return self._state

    @property
    def ws_url(self) -> str:
        return self._ws_url

    @ws_url.setter
    def ws_url(self, url: str) -> None:
        self._ws_url = url

    def _set_state(self, state: ConnectionState) -> None:
        self._state = state
        self.state_changed.emit(state.value)

    def _next_backoff(self) -> float:
        delay = self._backoff
        self._backoff = min(self._backoff * 2, self._BACKOFF_MAX)
        return delay

    def _reset_backoff(self) -> None:
        self._backoff = self._BACKOFF_INITIAL

    def _parse_message(self, raw: str) -> tuple[str, dict] | None:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Received invalid JSON: %s", raw[:200])
            return None
        msg_type = data.get("type")
        if not msg_type:
            logger.warning("Message missing 'type' field: %s", raw[:200])
            return None
        return msg_type, data

    def _dispatch_message(self, msg_type: str, data: dict) -> None:
        request_id = data.get("requestId", "")
        if msg_type == "start":
            self.message_start.emit(request_id)
        elif msg_type == "chunk":
            self.message_chunk.emit(request_id, data.get("seq", 0), data.get("content", ""))
        elif msg_type == "done":
            self.message_done.emit(request_id)
        elif msg_type == "error":
            self.message_error.emit(request_id, data.get("code", ""), data.get("message", ""))

    async def send_cancel(self, request_id: str) -> None:
        if self._state != ConnectionState.CONNECTED or self._ws is None:
            return
        try:
            msg = json.dumps({"type": "cancel", "requestId": request_id})
            await self._ws.send(msg)
        except Exception:
            logger.exception("Failed to send cancel for %s", request_id)

    async def _connect_loop(self) -> None:
        import websockets

        while not self._should_stop:
            try:
                self._set_state(ConnectionState.CONNECTING)
                async with websockets.connect(
                    self._ws_url,
                    ping_interval=self._PING_INTERVAL,
                    ping_timeout=self._PING_TIMEOUT,
                ) as ws:
                    self._ws = ws
                    self._set_state(ConnectionState.CONNECTED)
                    self._reset_backoff()
                    logger.info("WebSocket connected to %s", self._ws_url)
                    async for raw in ws:
                        if self._should_stop:
                            break
                        result = self._parse_message(raw)
                        if result:
                            self._dispatch_message(*result)
            except Exception:
                if self._should_stop:
                    break
                logger.exception("WebSocket connection error")
            finally:
                self._ws = None

            if not self._should_stop:
                delay = self._next_backoff()
                self._set_state(ConnectionState.RECONNECTING)
                logger.info("Reconnecting in %.1fs...", delay)
                await asyncio.sleep(delay)

        self._set_state(ConnectionState.DISCONNECTED)

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_loop())
        finally:
            self._loop.close()
            self._loop = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._should_stop = False
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._should_stop = True
        if self._loop and self._ws:
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def send_cancel_threadsafe(self, request_id: str) -> None:
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.send_cancel(request_id), self._loop)
```

**Step 4: Run tests to verify they pass**

Run: `cd client && python -m pytest tests/test_websocket_client.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add client/services/websocket_client.py client/tests/test_websocket_client.py
git commit -m "feat(client): add WebSocket client with reconnect and Qt signals"
```

---

## Task 3: Platform-abstracted window context capture and restore

**Files:**
- Create: `client/services/window_context.py`
- Test: `client/tests/test_window_context.py`

**Step 1: Write the failing tests**

`client/tests/test_window_context.py`:
```python
import sys
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

import pytest

from services.window_context import WindowContext, capture_window_context, restore_window_focus


class TestWindowContext:
    def test_window_context_fields(self):
        ctx = WindowContext(handle="hwnd_123", title="Notepad", process_name="notepad.exe")
        assert ctx.handle == "hwnd_123"
        assert ctx.title == "Notepad"
        assert ctx.process_name == "notepad.exe"

    def test_window_context_defaults(self):
        ctx = WindowContext()
        assert ctx.handle is None
        assert ctx.title == ""
        assert ctx.process_name == ""

    def test_window_context_is_valid(self):
        ctx = WindowContext(handle="hwnd_123")
        assert ctx.is_valid

    def test_window_context_is_not_valid_when_no_handle(self):
        ctx = WindowContext(handle=None)
        assert not ctx.is_valid


class TestCaptureWindowContext:
    @patch("services.window_context.sys")
    def test_capture_returns_context_object(self, mock_sys):
        mock_sys.platform = "win32"
        with patch("services.window_context._capture_windows") as mock_cap:
            mock_cap.return_value = WindowContext(handle=12345, title="Test", process_name="test.exe")
            ctx = capture_window_context()
            assert ctx.is_valid
            assert ctx.title == "Test"

    def test_capture_returns_empty_on_failure(self):
        with patch("services.window_context._capture_current_platform", side_effect=Exception("fail")):
            ctx = capture_window_context()
            assert not ctx.is_valid


class TestRestoreWindowFocus:
    def test_restore_with_invalid_context_returns_false(self):
        ctx = WindowContext(handle=None)
        assert not restore_window_focus(ctx)
```

**Step 2: Run test to verify it fails**

Run: `cd client && python -m pytest tests/test_window_context.py -v`
Expected: FAIL

**Step 3: Implement window context module**

`client/services/window_context.py`:
```python
from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WindowContext:
    handle: Any = None
    title: str = ""
    process_name: str = ""

    @property
    def is_valid(self) -> bool:
        return self.handle is not None


def capture_window_context() -> WindowContext:
    try:
        return _capture_current_platform()
    except Exception:
        logger.exception("Failed to capture window context")
        return WindowContext()


def restore_window_focus(ctx: WindowContext) -> bool:
    if not ctx.is_valid:
        return False
    try:
        return _restore_current_platform(ctx)
    except Exception:
        logger.exception("Failed to restore window focus")
        return False


def _capture_current_platform() -> WindowContext:
    if sys.platform == "win32":
        return _capture_windows()
    elif sys.platform == "darwin":
        return _capture_macos()
    else:
        logger.warning("Unsupported platform: %s", sys.platform)
        return WindowContext()


def _restore_current_platform(ctx: WindowContext) -> bool:
    if sys.platform == "win32":
        return _restore_windows(ctx)
    elif sys.platform == "darwin":
        return _restore_macos(ctx)
    else:
        return False


def _capture_windows() -> WindowContext:
    import ctypes
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return WindowContext()
    buf = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buf, 256)
    title = buf.value
    return WindowContext(handle=hwnd, title=title, process_name="")


def _restore_windows(ctx: WindowContext) -> bool:
    import ctypes
    user32 = ctypes.windll.user32
    result = user32.SetForegroundWindow(ctx.handle)
    return bool(result)


def _capture_macos() -> WindowContext:
    try:
        import subprocess
        result = subprocess.run(
            ["osascript", "-e",
             'tell application "System Events" to get {name, unix id} of first process whose frontmost is true'],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0:
            parts = result.stdout.strip().split(", ")
            name = parts[0] if parts else ""
            pid = int(parts[1]) if len(parts) > 1 else 0
            return WindowContext(handle=pid, title=name, process_name=name)
    except Exception:
        logger.exception("macOS capture failed")
    return WindowContext()


def _restore_macos(ctx: WindowContext) -> bool:
    try:
        import subprocess
        title = ctx.title
        result = subprocess.run(
            ["osascript", "-e",
             f'tell application "{title}" to activate'],
            capture_output=True, text=True, timeout=2,
        )
        return result.returncode == 0
    except Exception:
        logger.exception("macOS restore failed")
        return False
```

**Step 4: Run tests to verify they pass**

Run: `cd client && python -m pytest tests/test_window_context.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add client/services/window_context.py client/tests/test_window_context.py
git commit -m "feat(client): add platform-abstracted window context capture/restore"
```

---

## Task 4: Text injection service (pynput + clipboard fallback)

**Files:**
- Create: `client/services/text_injection.py`
- Test: `client/tests/test_text_injection.py`

**Step 1: Write the failing tests**

`client/tests/test_text_injection.py`:
```python
import sys
from unittest.mock import patch, MagicMock, call

import pytest

from services.text_injection import inject_text, _inject_via_keyboard, _inject_via_clipboard


class TestInjectViaKeyboard:
    @patch("services.text_injection.Controller")
    def test_keyboard_injection_calls_type(self, mock_ctrl_cls):
        mock_ctrl = MagicMock()
        mock_ctrl_cls.return_value = mock_ctrl
        result = _inject_via_keyboard("hello")
        mock_ctrl.type.assert_called_once_with("hello")
        assert result is True

    @patch("services.text_injection.Controller")
    def test_keyboard_injection_returns_false_on_error(self, mock_ctrl_cls):
        mock_ctrl = MagicMock()
        mock_ctrl.type.side_effect = Exception("fail")
        mock_ctrl_cls.return_value = mock_ctrl
        result = _inject_via_keyboard("hello")
        assert result is False


class TestInjectViaClipboard:
    @patch("services.text_injection.Controller")
    @patch("services.text_injection.pyperclip")
    def test_clipboard_injection_pastes_text(self, mock_clip, mock_ctrl_cls):
        mock_ctrl = MagicMock()
        mock_ctrl_cls.return_value = mock_ctrl
        mock_clip.paste.return_value = "original"
        result = _inject_via_clipboard("new text")
        mock_clip.copy.assert_any_call("new text")
        assert result is True

    @patch("services.text_injection.Controller")
    @patch("services.text_injection.pyperclip")
    def test_clipboard_injection_restores_original(self, mock_clip, mock_ctrl_cls):
        mock_ctrl = MagicMock()
        mock_ctrl_cls.return_value = mock_ctrl
        mock_clip.paste.return_value = "original"
        _inject_via_clipboard("new text")
        # Last call to copy should restore original
        copy_calls = mock_clip.copy.call_args_list
        assert copy_calls[-1] == call("original")


class TestInjectText:
    @patch("services.text_injection._inject_via_clipboard")
    @patch("services.text_injection._inject_via_keyboard")
    def test_uses_keyboard_first(self, mock_kb, mock_clip):
        mock_kb.return_value = True
        inject_text("hello")
        mock_kb.assert_called_once_with("hello")
        mock_clip.assert_not_called()

    @patch("services.text_injection._inject_via_clipboard")
    @patch("services.text_injection._inject_via_keyboard")
    def test_falls_back_to_clipboard(self, mock_kb, mock_clip):
        mock_kb.return_value = False
        mock_clip.return_value = True
        result = inject_text("hello")
        mock_kb.assert_called_once()
        mock_clip.assert_called_once_with("hello")
        assert result is True

    def test_empty_text_returns_false(self):
        assert inject_text("") is False

    def test_none_text_returns_false(self):
        assert inject_text(None) is False
```

**Step 2: Run test to verify it fails**

Run: `cd client && python -m pytest tests/test_text_injection.py -v`
Expected: FAIL

**Step 3: Implement text injection**

`client/services/text_injection.py`:
```python
from __future__ import annotations

import logging
import sys
import time

import pyperclip
from pynput.keyboard import Controller, Key

logger = logging.getLogger(__name__)


def inject_text(text: str | None) -> bool:
    if not text:
        return False
    if _inject_via_keyboard(text):
        return True
    logger.info("Keyboard injection failed, falling back to clipboard")
    return _inject_via_clipboard(text)


def _inject_via_keyboard(text: str) -> bool:
    try:
        ctrl = Controller()
        ctrl.type(text)
        return True
    except Exception:
        logger.exception("Keyboard injection failed")
        return False


def _inject_via_clipboard(text: str) -> bool:
    try:
        original = pyperclip.paste()
    except Exception:
        original = ""
    try:
        ctrl = Controller()
        pyperclip.copy(text)
        time.sleep(0.05)
        paste_key = Key.cmd if sys.platform == "darwin" else Key.ctrl
        with ctrl.pressed(paste_key):
            ctrl.press("v")
            ctrl.release("v")
        time.sleep(0.05)
        return True
    except Exception:
        logger.exception("Clipboard injection failed")
        return False
    finally:
        try:
            time.sleep(0.1)
            pyperclip.copy(original)
        except Exception:
            pass
```

**Step 4: Run tests to verify they pass**

Run: `cd client && python -m pytest tests/test_text_injection.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add client/services/text_injection.py client/tests/test_text_injection.py
git commit -m "feat(client): add text injection with keyboard and clipboard fallback"
```

---

## Task 5: Single instance lock

**Files:**
- Create: `client/utils/single_instance.py`
- Test: `client/tests/test_single_instance.py`

**Step 1: Write the failing tests**

`client/tests/test_single_instance.py`:
```python
import pytest

from utils.single_instance import SingleInstance


class TestSingleInstance:
    def test_acquire_succeeds_first_time(self, tmp_path):
        lock = SingleInstance(lock_dir=tmp_path)
        assert lock.acquire() is True
        lock.release()

    def test_double_acquire_fails(self, tmp_path):
        lock1 = SingleInstance(lock_dir=tmp_path)
        lock2 = SingleInstance(lock_dir=tmp_path)
        assert lock1.acquire() is True
        assert lock2.acquire() is False
        lock1.release()

    def test_release_allows_reacquire(self, tmp_path):
        lock1 = SingleInstance(lock_dir=tmp_path)
        assert lock1.acquire() is True
        lock1.release()
        lock2 = SingleInstance(lock_dir=tmp_path)
        assert lock2.acquire() is True
        lock2.release()

    def test_context_manager(self, tmp_path):
        with SingleInstance(lock_dir=tmp_path) as acquired:
            assert acquired is True
```

**Step 2: Run test to verify it fails**

Run: `cd client && python -m pytest tests/test_single_instance.py -v`
Expected: FAIL

**Step 3: Implement single instance**

`client/utils/single_instance.py`:
```python
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from utils.platform import get_app_data_dir

logger = logging.getLogger(__name__)

_LOCK_NAME = "client.lock"


class SingleInstance:
    def __init__(self, lock_dir: Path | None = None):
        self._lock_dir = lock_dir or get_app_data_dir()
        self._lock_file = self._lock_dir / _LOCK_NAME
        self._handle = None
        self._acquired = False

    def acquire(self) -> bool:
        if self._acquired:
            return True
        self._lock_dir.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                return self._acquire_windows()
            else:
                return self._acquire_posix()
        except Exception:
            logger.exception("Failed to acquire single instance lock")
            return False

    def _acquire_windows(self) -> bool:
        try:
            # Try to create the file exclusively
            self._handle = open(self._lock_file, "x")
            self._handle.write(str(os.getpid()))
            self._handle.flush()
            self._acquired = True
            return True
        except FileExistsError:
            # Check if the process that created the lock is still alive
            try:
                pid = int(self._lock_file.read_text().strip())
                import ctypes
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
                if handle:
                    kernel32.CloseHandle(handle)
                    return False  # Process still alive
                # Stale lock
                self._lock_file.unlink()
                return self._acquire_windows()
            except Exception:
                return False

    def _acquire_posix(self) -> bool:
        import fcntl
        self._handle = open(self._lock_file, "w")
        try:
            fcntl.flock(self._handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._handle.write(str(os.getpid()))
            self._handle.flush()
            self._acquired = True
            return True
        except (IOError, OSError):
            self._handle.close()
            self._handle = None
            return False

    def release(self) -> None:
        if not self._acquired:
            return
        try:
            if self._handle:
                self._handle.close()
                self._handle = None
            if self._lock_file.exists():
                self._lock_file.unlink()
        except Exception:
            logger.exception("Failed to release lock")
        self._acquired = False

    def __enter__(self) -> bool:
        return self.acquire()

    def __exit__(self, *args) -> None:
        self.release()
```

**Step 4: Run tests to verify they pass**

Run: `cd client && python -m pytest tests/test_single_instance.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add client/utils/single_instance.py client/tests/test_single_instance.py
git commit -m "feat(client): add single instance lock mechanism"
```

---

## Task 6: Global hotkey registration

**Files:**
- Create: `client/utils/hotkey.py`
- Test: `client/tests/test_hotkey.py`

**Step 1: Write the failing tests**

`client/tests/test_hotkey.py`:
```python
from unittest.mock import patch, MagicMock

import pytest

from utils.hotkey import HotkeyManager


class TestHotkeyManager:
    @patch("utils.hotkey.keyboard")
    def test_register_creates_listener(self, mock_kb):
        mock_listener = MagicMock()
        mock_kb.GlobalHotKeys.return_value = mock_listener
        callback = MagicMock()

        mgr = HotkeyManager()
        mgr.register("<ctrl>+<shift>+space", callback)

        mock_kb.GlobalHotKeys.assert_called_once()
        mock_listener.start.assert_called_once()

    @patch("utils.hotkey.keyboard")
    def test_stop_stops_listener(self, mock_kb):
        mock_listener = MagicMock()
        mock_kb.GlobalHotKeys.return_value = mock_listener
        callback = MagicMock()

        mgr = HotkeyManager()
        mgr.register("<ctrl>+<shift>+space", callback)
        mgr.stop()

        mock_listener.stop.assert_called_once()

    @patch("utils.hotkey.keyboard")
    def test_register_replaces_previous(self, mock_kb):
        mock_listener1 = MagicMock()
        mock_listener2 = MagicMock()
        mock_kb.GlobalHotKeys.side_effect = [mock_listener1, mock_listener2]
        callback = MagicMock()

        mgr = HotkeyManager()
        mgr.register("<ctrl>+a", callback)
        mgr.register("<ctrl>+b", callback)

        mock_listener1.stop.assert_called_once()
        mock_listener2.start.assert_called_once()
```

**Step 2: Run test to verify it fails**

Run: `cd client && python -m pytest tests/test_hotkey.py -v`
Expected: FAIL

**Step 3: Implement hotkey manager**

`client/utils/hotkey.py`:
```python
from __future__ import annotations

import logging
from typing import Callable

from pynput import keyboard

logger = logging.getLogger(__name__)


class HotkeyManager:
    def __init__(self):
        self._listener: keyboard.GlobalHotKeys | None = None

    def register(self, hotkey_str: str, callback: Callable[[], None]) -> None:
        self.stop()
        try:
            self._listener = keyboard.GlobalHotKeys({hotkey_str: callback})
            self._listener.daemon = True
            self._listener.start()
            logger.info("Registered global hotkey: %s", hotkey_str)
        except Exception:
            logger.exception("Failed to register hotkey: %s", hotkey_str)

    def stop(self) -> None:
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None
```

**Step 4: Run tests to verify they pass**

Run: `cd client && python -m pytest tests/test_hotkey.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add client/utils/hotkey.py client/tests/test_hotkey.py
git commit -m "feat(client): add global hotkey manager"
```

---

## Task 7: Floating window UI with state machine

**Files:**
- Create: `client/ui/styles.py`
- Create: `client/ui/floating_window.py`
- Test: `client/tests/test_floating_window.py`

**Step 1: Write the failing tests**

`client/tests/test_floating_window.py`:
```python
from unittest.mock import MagicMock, patch
from enum import Enum

import pytest

from ui.floating_window import FloatingWindowState


class TestFloatingWindowState:
    def test_states_exist(self):
        assert FloatingWindowState.HIDDEN.value == "hidden"
        assert FloatingWindowState.STREAMING.value == "streaming"
        assert FloatingWindowState.READY.value == "ready"
        assert FloatingWindowState.INJECTING.value == "injecting"

    def test_all_states_count(self):
        assert len(FloatingWindowState) == 4
```

Note: The floating window widget itself requires a running QApplication and is difficult to unit test in isolation. The state enum and logic will be tested here; integration testing of the window will be done manually and via Task 9.

**Step 2: Run test to verify it fails**

Run: `cd client && python -m pytest tests/test_floating_window.py -v`
Expected: FAIL

**Step 3: Implement styles**

`client/ui/styles.py`:
```python
# Visual constants for the floating window

WINDOW_BG_COLOR = "rgba(30, 30, 30, {alpha})"
WINDOW_BG_ALPHA = 235  # 0-255
WINDOW_BORDER_RADIUS = 10
WINDOW_MIN_WIDTH = 400
WINDOW_MAX_WIDTH = 600
WINDOW_MIN_HEIGHT = 60
WINDOW_MAX_HEIGHT = 300
WINDOW_PADDING = 12

SHADOW_BLUR_RADIUS = 20
SHADOW_OFFSET = 2
SHADOW_COLOR = "rgba(0, 0, 0, 150)"

TEXT_COLOR = "#E0E0E0"
TEXT_FONT_SIZE = 14
TEXT_FONT_FAMILY = "Segoe UI, SF Pro Text, Helvetica Neue, sans-serif"

STATUS_COLOR_STREAMING = "#4FC3F7"  # light blue
STATUS_COLOR_READY = "#81C784"      # light green
STATUS_COLOR_ERROR = "#EF5350"      # light red

CURSOR_OFFSET_X = 10
CURSOR_OFFSET_Y = -10
```

**Step 4: Implement floating window**

`client/ui/floating_window.py`:
```python
from __future__ import annotations

import logging
from enum import Enum

from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtGui import QCursor, QFont, QKeyEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel,
    QGraphicsDropShadowEffect, QApplication,
)

from ui.styles import (
    WINDOW_BG_COLOR, WINDOW_BG_ALPHA, WINDOW_BORDER_RADIUS,
    WINDOW_MIN_WIDTH, WINDOW_MAX_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_MAX_HEIGHT,
    WINDOW_PADDING, SHADOW_BLUR_RADIUS, SHADOW_OFFSET, SHADOW_COLOR,
    TEXT_COLOR, TEXT_FONT_SIZE, TEXT_FONT_FAMILY,
    STATUS_COLOR_STREAMING, STATUS_COLOR_READY, STATUS_COLOR_ERROR,
    CURSOR_OFFSET_X, CURSOR_OFFSET_Y,
)

logger = logging.getLogger(__name__)


class FloatingWindowState(Enum):
    HIDDEN = "hidden"
    STREAMING = "streaming"
    READY = "ready"
    INJECTING = "injecting"


class FloatingWindow(QWidget):
    """Frameless floating window for displaying and confirming AI-generated text."""

    confirm_text = Signal(str)  # emitted with final text on Enter
    cancel_request = Signal(str)  # emitted with requestId on Escape during streaming
    dismissed = Signal()  # emitted when window is closed without confirming

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._state = FloatingWindowState.HIDDEN
        self._request_id = ""
        self._accumulated_text = ""

        self._setup_window()
        self._setup_ui()
        self._setup_shadow()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(WINDOW_MIN_WIDTH)
        self.setMaximumWidth(WINDOW_MAX_WIDTH)
        self.setMinimumHeight(WINDOW_MIN_HEIGHT)
        self.setMaximumHeight(WINDOW_MAX_HEIGHT)

    def _setup_ui(self) -> None:
        self._container = QWidget(self)
        self._container.setStyleSheet(
            f"background-color: {WINDOW_BG_COLOR.format(alpha=WINDOW_BG_ALPHA)};"
            f"border-radius: {WINDOW_BORDER_RADIUS}px;"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(WINDOW_PADDING, WINDOW_PADDING, WINDOW_PADDING, WINDOW_PADDING)

        # Status indicator
        self._status_label = QLabel("")
        self._status_label.setStyleSheet(f"color: {STATUS_COLOR_STREAMING}; font-size: 11px; background: transparent;")
        layout.addWidget(self._status_label)

        # Text area (editable after generation completes)
        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setStyleSheet(
            f"color: {TEXT_COLOR}; background: transparent; border: none;"
            f"font-size: {TEXT_FONT_SIZE}px; font-family: {TEXT_FONT_FAMILY};"
            f"selection-background-color: rgba(100, 100, 255, 100);"
        )
        self._text_edit.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._text_edit.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self._text_edit)

        # Container layout
        container_layout = QVBoxLayout(self._container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        self._container.setLayout(container_layout)

    def _setup_shadow(self) -> None:
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(SHADOW_BLUR_RADIUS)
        shadow.setOffset(SHADOW_OFFSET)
        shadow.setColor(Qt.GlobalColor.black)
        self.setGraphicsEffect(shadow)

    @property
    def state(self) -> FloatingWindowState:
        return self._state

    @property
    def request_id(self) -> str:
        return self._request_id

    def show_at_cursor(self) -> None:
        cursor_pos = QCursor.pos()
        screen = QApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        x = cursor_pos.x() + CURSOR_OFFSET_X
        y = cursor_pos.y() + CURSOR_OFFSET_Y

        # Boundary detection
        if x + self.width() > screen_rect.right():
            x = screen_rect.right() - self.width()
        if y + self.height() > screen_rect.bottom():
            y = cursor_pos.y() - self.height() - abs(CURSOR_OFFSET_Y)
        if x < screen_rect.left():
            x = screen_rect.left()
        if y < screen_rect.top():
            y = screen_rect.top()

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def on_start(self, request_id: str) -> None:
        self._request_id = request_id
        self._accumulated_text = ""
        self._text_edit.clear()
        self._text_edit.setReadOnly(True)
        self._state = FloatingWindowState.STREAMING
        self._status_label.setText("Generating...")
        self._status_label.setStyleSheet(
            f"color: {STATUS_COLOR_STREAMING}; font-size: 11px; background: transparent;"
        )
        self.show_at_cursor()

    def on_chunk(self, request_id: str, seq: int, content: str) -> None:
        if request_id != self._request_id:
            return
        if self._state != FloatingWindowState.STREAMING:
            return
        self._accumulated_text += content
        self._text_edit.setPlainText(self._accumulated_text)
        # Scroll to bottom
        scrollbar = self._text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.adjustSize()

    def on_done(self, request_id: str) -> None:
        if request_id != self._request_id:
            return
        self._state = FloatingWindowState.READY
        self._text_edit.setReadOnly(False)
        self._status_label.setText("Ready — press Enter to insert")
        self._status_label.setStyleSheet(
            f"color: {STATUS_COLOR_READY}; font-size: 11px; background: transparent;"
        )
        self._text_edit.setFocus()

    def on_error(self, request_id: str, code: str, message: str) -> None:
        if request_id != self._request_id:
            return
        self._state = FloatingWindowState.READY  # allow dismiss
        self._text_edit.setPlainText(f"Error [{code}]: {message}")
        self._text_edit.setReadOnly(True)
        self._status_label.setText("Error")
        self._status_label.setStyleSheet(
            f"color: {STATUS_COLOR_ERROR}; font-size: 11px; background: transparent;"
        )

    def dismiss(self) -> None:
        if self._state == FloatingWindowState.STREAMING:
            self.cancel_request.emit(self._request_id)
        self._state = FloatingWindowState.HIDDEN
        self.hide()
        self.dismissed.emit()

    def _confirm(self) -> None:
        if self._state != FloatingWindowState.READY:
            return
        text = self._text_edit.toPlainText()
        self._state = FloatingWindowState.INJECTING
        self.hide()
        self.confirm_text.emit(text)
        self._state = FloatingWindowState.HIDDEN

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                self._confirm()
            else:
                # Shift+Enter, Ctrl+Enter etc. pass through for newline editing
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event) -> None:
        # Dismiss when clicking outside
        if self._state in (FloatingWindowState.STREAMING, FloatingWindowState.READY):
            QTimer.singleShot(100, self._check_focus_lost)
        super().focusOutEvent(event)

    def _check_focus_lost(self) -> None:
        if not self.isActiveWindow() and self._state != FloatingWindowState.HIDDEN:
            self.dismiss()

    def resizeEvent(self, event) -> None:
        self._container.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)
```

**Step 5: Run tests to verify they pass**

Run: `cd client && python -m pytest tests/test_floating_window.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add client/ui/styles.py client/ui/floating_window.py client/tests/test_floating_window.py
git commit -m "feat(client): add floating window with state machine and cursor positioning"
```

---

## Task 8: System tray with connection status

**Files:**
- Create: `client/ui/tray.py`
- Test: `client/tests/test_tray.py`

**Step 1: Write the failing tests**

`client/tests/test_tray.py`:
```python
from unittest.mock import MagicMock

import pytest

from ui.tray import TrayManager


class TestTrayManager:
    def test_status_text_disconnected(self):
        mgr = TrayManager.__new__(TrayManager)
        mgr._connection_state = "disconnected"
        assert mgr._format_status() == "Status: Disconnected"

    def test_status_text_connected(self):
        mgr = TrayManager.__new__(TrayManager)
        mgr._connection_state = "connected"
        assert mgr._format_status() == "Status: Connected"

    def test_status_text_reconnecting(self):
        mgr = TrayManager.__new__(TrayManager)
        mgr._connection_state = "reconnecting"
        assert mgr._format_status() == "Status: Reconnecting..."
```

**Step 2: Run test to verify it fails**

Run: `cd client && python -m pytest tests/test_tray.py -v`
Expected: FAIL

**Step 3: Implement tray manager**

`client/ui/tray.py`:
```python
from __future__ import annotations

import logging
from typing import Callable

from PySide6.QtGui import QIcon, QPixmap, QAction, QPainter, QColor, QFont
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PySide6.QtCore import QObject, Slot, QSize

logger = logging.getLogger(__name__)

_STATUS_LABELS = {
    "disconnected": "Status: Disconnected",
    "connecting": "Status: Connecting...",
    "connected": "Status: Connected",
    "reconnecting": "Status: Reconnecting...",
}


class TrayManager(QObject):
    def __init__(
        self,
        on_quit: Callable[[], None],
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._on_quit = on_quit
        self._connection_state = "disconnected"
        self._tray = QSystemTrayIcon(self)
        self._tray.setIcon(self._create_icon())
        self._tray.setToolTip("Agent Service Client")
        self._menu = QMenu()
        self._build_menu()
        self._tray.setContextMenu(self._menu)
        self._tray.show()

    def _create_icon(self) -> QIcon:
        size = 64
        pixmap = QPixmap(QSize(size, size))
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(46, 204, 113))
        painter.setPen(QColor(39, 174, 96))
        painter.drawEllipse(4, 4, size - 8, size - 8)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Arial", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), 0x0084, "A")  # AlignCenter
        painter.end()
        return QIcon(pixmap)

    def _build_menu(self) -> None:
        self._menu.clear()
        self._status_action = QAction(self._format_status())
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)
        self._menu.addSeparator()
        quit_action = QAction("Quit")
        quit_action.triggered.connect(self._on_quit)
        self._menu.addAction(quit_action)

    def _format_status(self) -> str:
        return _STATUS_LABELS.get(self._connection_state, f"Status: {self._connection_state}")

    @Slot(str)
    def on_connection_state_changed(self, state: str) -> None:
        self._connection_state = state
        self._status_action.setText(self._format_status())
```

**Step 4: Run tests to verify they pass**

Run: `cd client && python -m pytest tests/test_tray.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add client/ui/tray.py client/tests/test_tray.py
git commit -m "feat(client): add system tray with connection status display"
```

---

## Task 9: Application entry point (main.py) — wiring everything together

**Files:**
- Create: `client/main.py`

**Step 1: Implement main.py**

`client/main.py`:
```python
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from config.settings import Settings, load_settings, save_settings
from services.websocket_client import WebSocketClient
from services.window_context import capture_window_context, restore_window_focus
from services.text_injection import inject_text
from ui.floating_window import FloatingWindow
from ui.tray import TrayManager
from utils.hotkey import HotkeyManager
from utils.single_instance import SingleInstance
from utils.platform import get_app_data_dir

logger = logging.getLogger(__name__)

_INJECT_DELAY_MS = 100


def _setup_logging() -> None:
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "client.log", encoding="utf-8"),
        ],
    )


class Application:
    def __init__(self) -> None:
        self._settings = load_settings()
        self._window_context = None
        self._app = QApplication(sys.argv)

        # Core components
        self._ws_client = WebSocketClient(ws_url=self._settings.ws_url)
        self._floating_window = FloatingWindow()
        self._tray = TrayManager(on_quit=self._quit)
        self._hotkey_manager = HotkeyManager()

        self._connect_signals()

    def _connect_signals(self) -> None:
        # WebSocket → Floating Window
        self._ws_client.message_start.connect(self._on_start)
        self._ws_client.message_chunk.connect(self._floating_window.on_chunk)
        self._ws_client.message_done.connect(self._floating_window.on_done)
        self._ws_client.message_error.connect(self._floating_window.on_error)

        # WebSocket → Tray
        self._ws_client.state_changed.connect(self._tray.on_connection_state_changed)

        # Floating Window → Actions
        self._floating_window.confirm_text.connect(self._on_confirm)
        self._floating_window.cancel_request.connect(self._on_cancel)

    def _on_start(self, request_id: str) -> None:
        self._window_context = capture_window_context()
        self._floating_window.on_start(request_id)

    def _on_confirm(self, text: str) -> None:
        ctx = self._window_context
        if ctx and ctx.is_valid:
            QTimer.singleShot(_INJECT_DELAY_MS, lambda: self._do_inject(ctx, text))
        else:
            logger.warning("No valid window context, skipping injection")

    def _do_inject(self, ctx, text: str) -> None:
        restore_window_focus(ctx)
        time.sleep(0.05)
        success = inject_text(text)
        if success:
            logger.info("Text injected successfully (%d chars)", len(text))
        else:
            logger.error("Text injection failed")

    def _on_cancel(self, request_id: str) -> None:
        self._ws_client.send_cancel_threadsafe(request_id)

    def _quit(self) -> None:
        self._hotkey_manager.stop()
        self._ws_client.stop()
        self._app.quit()

    def run(self) -> int:
        self._ws_client.start()
        self._hotkey_manager.register(
            self._settings.hotkey,
            lambda: self._floating_window.show_at_cursor(),
        )
        return self._app.exec()


def main() -> None:
    _setup_logging()
    lock = SingleInstance()
    if not lock.acquire():
        print("Another instance is already running.")
        sys.exit(1)
    try:
        app = Application()
        sys.exit(app.run())
    finally:
        lock.release()


if __name__ == "__main__":
    main()
```

**Step 2: Smoke test manually**

Run: `cd client && python main.py`

Verify:
- Tray icon appears
- WebSocket tries to connect (shows reconnecting if backend isn't running)
- Start backend (`cd .. && uvicorn main:app --port 18080`), verify tray shows "Connected"
- Global hotkey shows floating window at cursor

**Step 3: Commit**

```bash
git add client/main.py
git commit -m "feat(client): add application entry point wiring all components"
```

---

## Task 10: pytest configuration and CI integration

**Files:**
- Create: `client/pytest.ini`
- Modify: `.github/workflows/build.yml` (add client test step)

**Step 1: Create pytest.ini**

`client/pytest.ini`:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

**Step 2: Run the full test suite**

Run: `cd client && python -m pytest tests/ -v`
Expected: All tests pass

**Step 3: Add client test job to CI**

Modify `.github/workflows/build.yml` — add a new job before the build jobs:

```yaml
  test-client:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install client dependencies
        run: |
          pip install -r client/requirements.txt
      - name: Run client tests
        run: |
          cd client && python -m pytest tests/ -v
```

**Step 4: Commit**

```bash
git add client/pytest.ini .github/workflows/build.yml
git commit -m "ci: add client test configuration and CI job"
```

---

## Task 11: PyInstaller spec for client

**Files:**
- Create: `build/agent_client.spec`

**Step 1: Create spec file**

`build/agent_client.spec`:
```python
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

SPECPATH_DIR = Path(SPECPATH)
PROJECT_ROOT = SPECPATH_DIR.parent

a = Analysis(
    [str(PROJECT_ROOT / "client" / "main.py")],
    pathex=[str(PROJECT_ROOT / "client")],
    binaries=[],
    datas=[],
    hiddenimports=[
        "client.config.settings",
        "client.services.websocket_client",
        "client.services.window_context",
        "client.services.text_injection",
        "client.ui.floating_window",
        "client.ui.tray",
        "client.ui.styles",
        "client.utils.hotkey",
        "client.utils.platform",
        "client.utils.single_instance",
        "websockets",
        "pynput",
        "pynput.keyboard",
        "pynput.keyboard._xorg",
        "pynput.keyboard._win32",
        "pynput.keyboard._darwin",
        "pyperclip",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == "win32":
    icon_file = str(PROJECT_ROOT / "build" / "assets" / "icon.ico")
elif sys.platform == "darwin":
    icon_file = str(PROJECT_ROOT / "build" / "assets" / "icon.icns")
else:
    icon_file = None

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="AgentClient",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="AgentClient.app",
        icon=icon_file,
        bundle_identifier="com.agentservice.client",
        info_plist={
            "LSUIElement": True,  # hide from dock
        },
    )
```

**Step 2: Verify build locally**

Run: `pyinstaller build/agent_client.spec --noconfirm`
Expected: Build succeeds, outputs `dist/AgentClient` (or `dist/AgentClient.app` on macOS)

**Step 3: Commit**

```bash
git add build/agent_client.spec
git commit -m "build: add PyInstaller spec for client application"
```

---

## Task Summary

| Task | Description | Test files | Source files |
|------|-------------|------------|-------------|
| 1 | Scaffolding + Settings | `test_settings.py` | `settings.py`, `platform.py`, `requirements.txt` |
| 2 | WebSocket client | `test_websocket_client.py` | `websocket_client.py` |
| 3 | Window context | `test_window_context.py` | `window_context.py` |
| 4 | Text injection | `test_text_injection.py` | `text_injection.py` |
| 5 | Single instance | `test_single_instance.py` | `single_instance.py` |
| 6 | Global hotkey | `test_hotkey.py` | `hotkey.py` |
| 7 | Floating window | `test_floating_window.py` | `floating_window.py`, `styles.py` |
| 8 | System tray | `test_tray.py` | `tray.py` |
| 9 | Main entry point | (manual smoke test) | `main.py` |
| 10 | Test config + CI | — | `pytest.ini`, `build.yml` |
| 11 | PyInstaller build | — | `agent_client.spec` |

**Dependency order:** Tasks 1-6 are independent and can be parallelized. Task 7 depends on styles (created in same task). Task 8 is independent. Task 9 depends on all previous tasks. Tasks 10-11 depend on Task 9.
