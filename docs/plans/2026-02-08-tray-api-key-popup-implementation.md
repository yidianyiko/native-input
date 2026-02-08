# Tray API Key Popup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow users to set `DEEPSEEK_API_KEY` from the system tray menu via a popup input box, and persist it to an app-data `settings.json`.

**Architecture:** Add a small credentials/settings module that reads key from (1) environment / `.env` and falls back to (2) `settings.json` under the app data directory. The tray app adds a menu action to prompt for the key using `tkinter` and saves it.

**Tech Stack:** `pystray`, `tkinter` (stdlib), `json`, `python-dotenv` (optional dev), PyInstaller.

---

## Task 1: Add Credentials Module (JSON settings)

**Files:**
- Create: `app/credentials.py`
- Test: `tests/test_credentials.py`

**Step 1: Write the failing test**

```python
# tests/test_credentials.py
import os

from app import credentials


def test_load_returns_empty_when_unset(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(credentials, "get_app_data_dir", lambda: tmp_path)

    assert credentials.load_deepseek_api_key() == ""


def test_save_then_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(credentials, "get_app_data_dir", lambda: tmp_path)

    credentials.save_deepseek_api_key("k123")
    assert credentials.load_deepseek_api_key() == "k123"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_credentials.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.credentials'`

**Step 3: Write minimal implementation**

```python
# app/credentials.py
import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

from app.config import get_app_data_dir


def _settings_path() -> Path:
    return get_app_data_dir() / "settings.json"


def load_deepseek_api_key() -> str:
    env = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if env:
        return env

    path = _settings_path()
    if not path.exists():
        return ""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    key = str(data.get("deepseek_api_key", "") or "").strip()
    return key


def save_deepseek_api_key(key: str) -> None:
    key = (key or "").strip()
    path = _settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {"deepseek_api_key": key}

    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

    # Best-effort: restrict permissions on POSIX.
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_credentials.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add app/credentials.py tests/test_credentials.py
git commit -m "feat: persist DeepSeek API key in app settings"
```

---

## Task 2: Wire AgentService to Use Saved Key

**Files:**
- Modify: `services/agent_service.py`
- Test: `tests/test_credentials.py`

**Step 1: Write failing test for env precedence**

Append to `tests/test_credentials.py`:

```python
def test_env_overrides_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(credentials, "get_app_data_dir", lambda: tmp_path)
    credentials.save_deepseek_api_key("file_key")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "env_key")
    assert credentials.load_deepseek_api_key() == "env_key"
```

**Step 2: Run test to verify it fails (if implementation wrong)**

Run: `.venv/bin/pytest tests/test_credentials.py -v`
Expected: FAIL if env precedence not implemented

**Step 3: Update `services/agent_service.py` to import from credentials**

Replace config import block with:

```python
from app.credentials import load_deepseek_api_key

key = load_deepseek_api_key()
if key and not os.getenv("DEEPSEEK_API_KEY"):
    os.environ["DEEPSEEK_API_KEY"] = key
```

**Step 4: Run tests**

Run: `.venv/bin/pytest -q`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add services/agent_service.py tests/test_credentials.py
git commit -m "feat: load DeepSeek API key from saved settings"
```

---

## Task 3: Add Tray Menu Item and Popup

**Files:**
- Modify: `app/tray.py`
- Test: `tests/test_tray_api_key.py`

**Step 1: Write failing test**

```python
# tests/test_tray_api_key.py
from unittest.mock import MagicMock

from app.tray import TrayApp


def test_set_api_key_saves_and_updates_menu(monkeypatch):
    app = TrayApp()
    app._icon = MagicMock()

    saved = {}

    def fake_save(key: str) -> None:
        saved["key"] = key

    monkeypatch.setattr("app.tray.save_deepseek_api_key", fake_save)

    app._save_api_key("k999")

    assert saved["key"] == "k999"
    app._icon.update_menu.assert_called()
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_tray_api_key.py -v`
Expected: FAIL (missing `_save_api_key` or missing import)

**Step 3: Implement tray changes**

In `app/tray.py`:
- Import `save_deepseek_api_key`, `load_deepseek_api_key`.
- Add a disabled status item: `Key: 已配置/未配置`.
- Add menu item: `设置 API Key...`.
- Implement `_save_api_key(self, key: str)` which saves and calls `self._icon.update_menu()`.
- Implement `_prompt_api_key(...)` using `tkinter` in a short-lived thread:
  - `askstring("设置 API Key", "请输入 DeepSeek API Key:", show="*")`
  - If user cancels: do nothing
  - If empty: show error messagebox
  - Else: save + show success messagebox

**Step 4: Run tests**

Run: `.venv/bin/pytest -q`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add app/tray.py tests/test_tray_api_key.py
git commit -m "feat: add tray popup to set and persist API key"
```

---

## Task 4: Smoke Verify Server Still Starts

**Step 1: Run local server health check**

Run:
```bash
.venv/bin/python - <<'PY'
import time
import httpx

from app.service import ServiceManager

m = ServiceManager(port=18080)
m.start()

deadline = time.time() + 5
while time.time() < deadline:
    try:
        r = httpx.get('http://127.0.0.1:18080/health', timeout=0.5)
        print(r.status_code, r.text)
        break
    except Exception:
        time.sleep(0.1)

m.stop()
PY
```
Expected: `200 {"status":"ok"}`

**Step 2: Commit (if any docs updates needed)**

No commit required.
