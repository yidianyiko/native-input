# Desktop Packaging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Package the Agent Service as a standalone desktop application with system tray support for Windows and Mac.

**Architecture:** Create a tray application wrapper around the existing FastAPI service. The tray app manages service lifecycle, auto-start configuration, and provides a menu for user interaction. PyInstaller bundles everything into a single executable, built via GitHub Actions.

**Tech Stack:** PyInstaller, pystray, Pillow, GitHub Actions

---

## Task 1: Add Desktop Dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1: Update requirements.txt**

Add to the end of `requirements.txt`:

```txt
# Desktop app dependencies
pystray>=0.19.0
Pillow>=10.0.0
```

**Step 2: Install new dependencies**

Run: `source venv/bin/activate && pip install pystray Pillow`

**Step 3: Verify installation**

Run: `python -c "import pystray; import PIL; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add desktop app dependencies (pystray, Pillow)"
```

---

## Task 2: Create App Configuration

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`

**Step 1: Create app package**

```python
# app/__init__.py
"""Desktop application package."""
```

**Step 2: Create configuration module**

```python
# app/config.py
"""Application configuration."""
import os
from pathlib import Path

# API Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Server Configuration
HOST = "127.0.0.1"
PORT = 18080

# Application Info
APP_NAME = "AgentService"
APP_VERSION = "1.0.0"

# Paths
def get_app_data_dir() -> Path:
    """Get platform-specific app data directory."""
    if os.name == "nt":  # Windows
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:  # Mac/Linux
        base = Path.home() / "Library" / "Application Support"

    app_dir = base / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

# Database path (for Agno memory)
DB_PATH = get_app_data_dir() / "agent_memory.db"
```

**Step 3: Commit**

```bash
git add app/
git commit -m "feat: add app configuration module"
```

---

## Task 3: Create Service Manager

**Files:**
- Create: `app/service.py`
- Create: `tests/test_service.py`

**Step 1: Write the test**

```python
# tests/test_service.py
import pytest
import time
import requests
from unittest.mock import patch, MagicMock
from app.service import ServiceManager


class TestServiceManager:
    def test_service_starts_and_stops(self):
        manager = ServiceManager(port=18099)  # Use different port for testing

        # Start service
        manager.start()
        time.sleep(1)  # Give it time to start

        assert manager.is_running()

        # Verify health endpoint
        try:
            response = requests.get("http://127.0.0.1:18099/health", timeout=2)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.fail("Service not responding")

        # Stop service
        manager.stop()
        time.sleep(0.5)

        assert not manager.is_running()

    def test_service_not_running_initially(self):
        manager = ServiceManager(port=18098)
        assert not manager.is_running()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_service.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'app.service'"

**Step 3: Write implementation**

```python
# app/service.py
"""FastAPI service manager."""
import threading
import uvicorn
from typing import Optional


class ServiceManager:
    """Manages the FastAPI service lifecycle."""

    def __init__(self, host: str = "127.0.0.1", port: int = 18080):
        self.host = host
        self.port = port
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None

    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Start the FastAPI service in a background thread."""
        if self.is_running():
            return

        from main import app

        config = uvicorn.Config(
            app=app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)

        self._thread = threading.Thread(target=self._server.run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the FastAPI service."""
        if self._server:
            self._server.should_exit = True
            if self._thread:
                self._thread.join(timeout=5)
            self._server = None
            self._thread = None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_service.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add app/service.py tests/test_service.py
git commit -m "feat: add ServiceManager for FastAPI lifecycle"
```

---

## Task 4: Create Auto-Start Manager

**Files:**
- Create: `app/autostart.py`
- Create: `tests/test_autostart.py`

**Step 1: Write the test**

```python
# tests/test_autostart.py
import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from app.autostart import AutoStartManager


class TestAutoStartManager:
    @pytest.fixture
    def manager(self, tmp_path):
        # Use temp path for testing
        with patch('app.autostart.AutoStartManager._get_executable_path') as mock_exe:
            mock_exe.return_value = "/path/to/AgentService"
            mgr = AutoStartManager()
            # Override paths for testing
            if sys.platform == "darwin":
                mgr._plist_path = tmp_path / "com.agentservice.plist"
            return mgr

    def test_is_enabled_returns_false_initially(self, manager):
        # Should return False when not configured
        assert manager.is_enabled() == False

    @pytest.mark.skipif(sys.platform == "win32", reason="Mac-specific test")
    def test_enable_creates_plist_on_mac(self, manager, tmp_path):
        if sys.platform != "darwin":
            pytest.skip("Mac-specific test")

        manager.enable()
        assert manager._plist_path.exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="Mac-specific test")
    def test_disable_removes_plist_on_mac(self, manager, tmp_path):
        if sys.platform != "darwin":
            pytest.skip("Mac-specific test")

        manager.enable()
        manager.disable()
        assert not manager._plist_path.exists()
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_autostart.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write implementation**

```python
# app/autostart.py
"""Auto-start manager for Windows and Mac."""
import os
import sys
import plistlib
from pathlib import Path
from typing import Optional

from app.config import APP_NAME


class AutoStartManager:
    """Manages auto-start configuration for the application."""

    def __init__(self):
        self._plist_path: Optional[Path] = None
        if sys.platform == "darwin":
            self._plist_path = (
                Path.home() / "Library" / "LaunchAgents" / f"com.{APP_NAME.lower()}.plist"
            )

    def _get_executable_path(self) -> str:
        """Get the path to the current executable."""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return sys.executable
        else:
            # Running as script
            return sys.executable

    def is_enabled(self) -> bool:
        """Check if auto-start is enabled."""
        if sys.platform == "win32":
            return self._is_enabled_windows()
        elif sys.platform == "darwin":
            return self._is_enabled_mac()
        return False

    def enable(self) -> None:
        """Enable auto-start."""
        if sys.platform == "win32":
            self._enable_windows()
        elif sys.platform == "darwin":
            self._enable_mac()

    def disable(self) -> None:
        """Disable auto-start."""
        if sys.platform == "win32":
            self._disable_windows()
        elif sys.platform == "darwin":
            self._disable_mac()

    # Windows implementation
    def _is_enabled_windows(self) -> bool:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, APP_NAME)
                return True
            except FileNotFoundError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception:
            return False

    def _enable_windows(self) -> None:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, self._get_executable_path())
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to enable auto-start: {e}")

    def _disable_windows(self) -> None:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Failed to disable auto-start: {e}")

    # Mac implementation
    def _is_enabled_mac(self) -> bool:
        return self._plist_path is not None and self._plist_path.exists()

    def _enable_mac(self) -> None:
        if self._plist_path is None:
            return

        plist_content = {
            "Label": f"com.{APP_NAME.lower()}",
            "ProgramArguments": [self._get_executable_path()],
            "RunAtLoad": True,
            "KeepAlive": False,
        }

        self._plist_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._plist_path, "wb") as f:
            plistlib.dump(plist_content, f)

    def _disable_mac(self) -> None:
        if self._plist_path and self._plist_path.exists():
            self._plist_path.unlink()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_autostart.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add app/autostart.py tests/test_autostart.py
git commit -m "feat: add AutoStartManager for Windows/Mac"
```

---

## Task 5: Create Tray Icon

**Files:**
- Create: `app/icon.py`
- Create: `app/assets/icon.png`

**Step 1: Create a simple icon programmatically**

```python
# app/icon.py
"""Tray icon generation."""
from PIL import Image, ImageDraw
from pathlib import Path


def create_default_icon(size: int = 64) -> Image.Image:
    """Create a simple default tray icon."""
    # Create a simple colored circle icon
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw a filled circle (green for "running")
    margin = size // 8
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(46, 204, 113, 255),  # Green color
        outline=(39, 174, 96, 255),
        width=2
    )

    # Draw "A" in the center
    font_size = size // 2
    text = "A"
    # Get text bounding box for centering
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - margin
    draw.text((x, y), text, fill=(255, 255, 255, 255))

    return image


def get_icon() -> Image.Image:
    """Get the tray icon, creating default if needed."""
    # Try to load from assets first
    asset_path = Path(__file__).parent / "assets" / "icon.png"
    if asset_path.exists():
        return Image.open(asset_path)

    # Fall back to generated icon
    return create_default_icon()
```

**Step 2: Create assets directory**

```bash
mkdir -p app/assets
```

**Step 3: Test icon generation**

Run: `python -c "from app.icon import get_icon; img = get_icon(); print(f'Icon size: {img.size}')"`
Expected: `Icon size: (64, 64)`

**Step 4: Commit**

```bash
git add app/icon.py app/assets/
git commit -m "feat: add tray icon generation"
```

---

## Task 6: Create Tray Application

**Files:**
- Create: `app/tray.py`

**Step 1: Write tray application**

```python
# app/tray.py
"""System tray application."""
import pystray
from pystray import MenuItem as Item
import threading
from typing import Optional

from app.config import APP_NAME, PORT, HOST
from app.service import ServiceManager
from app.autostart import AutoStartManager
from app.icon import get_icon


class TrayApp:
    """System tray application for Agent Service."""

    def __init__(self):
        self.service = ServiceManager(host=HOST, port=PORT)
        self.autostart = AutoStartManager()
        self._icon: Optional[pystray.Icon] = None

    def _create_menu(self) -> pystray.Menu:
        """Create the tray menu."""
        return pystray.Menu(
            Item(
                f"状态: {'运行中' if self.service.is_running() else '已停止'}",
                None,
                enabled=False
            ),
            Item(
                f"端口: {PORT}",
                None,
                enabled=False
            ),
            pystray.Menu.SEPARATOR,
            Item(
                "开机启动",
                self._toggle_autostart,
                checked=lambda item: self.autostart.is_enabled()
            ),
            pystray.Menu.SEPARATOR,
            Item("退出", self._quit),
        )

    def _toggle_autostart(self, icon: pystray.Icon, item: Item) -> None:
        """Toggle auto-start setting."""
        if self.autostart.is_enabled():
            self.autostart.disable()
        else:
            self.autostart.enable()
        # Update menu
        icon.update_menu()

    def _quit(self, icon: pystray.Icon, item: Item) -> None:
        """Quit the application."""
        self.service.stop()
        icon.stop()

    def run(self) -> None:
        """Run the tray application."""
        # Start the service
        self.service.start()

        # Enable auto-start by default on first run
        if not self.autostart.is_enabled():
            self.autostart.enable()

        # Create and run the tray icon
        self._icon = pystray.Icon(
            APP_NAME,
            get_icon(),
            APP_NAME,
            menu=self._create_menu()
        )

        self._icon.run()


def main():
    """Main entry point for the tray application."""
    app = TrayApp()
    app.run()


if __name__ == "__main__":
    main()
```

**Step 2: Test tray app imports**

Run: `python -c "from app.tray import TrayApp; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add app/tray.py
git commit -m "feat: add TrayApp for system tray interface"
```

---

## Task 7: Create PyInstaller Spec

**Files:**
- Create: `build/agent_service.spec`

**Step 1: Create build directory and spec file**

```python
# build/agent_service.spec
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Get the project root
ROOT = Path(SPECPATH).parent

# Collect all data files
datas = [
    (str(ROOT / 'config'), 'config'),
    (str(ROOT / 'app' / 'assets'), 'app/assets'),
]

a = Analysis(
    [str(ROOT / 'app' / 'tray.py')],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'main',
        'routers.websocket',
        'routers.process',
        'routers.cancel',
        'services.connection_manager',
        'services.request_registry',
        'services.prompt_loader',
        'services.agent_service',
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AgentService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'build' / 'assets' / 'icon.ico') if sys.platform == 'win32' else None,
)

# Mac-specific: create .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='AgentService.app',
        icon=str(ROOT / 'build' / 'assets' / 'icon.icns'),
        bundle_identifier='com.agentservice',
        info_plist={
            'LSUIElement': True,  # Hide from dock
        },
    )
```

**Step 2: Create build assets directory**

```bash
mkdir -p build/assets
```

**Step 3: Commit**

```bash
git add build/
git commit -m "feat: add PyInstaller spec for packaging"
```

---

## Task 8: Create GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/build.yml`

**Step 1: Create workflows directory**

```bash
mkdir -p .github/workflows
```

**Step 2: Create build workflow**

```yaml
# .github/workflows/build.yml
name: Build Desktop App

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      version:
        description: 'Version tag (e.g., v1.0.0)'
        required: false
        default: 'dev'

jobs:
  build:
    strategy:
      matrix:
        include:
          - os: windows-latest
            artifact_name: AgentService.exe
            asset_name: AgentService-windows-x64.exe
          - os: macos-latest
            artifact_name: AgentService.app
            asset_name: AgentService-macos-x64.zip

    runs-on: ${{ matrix.os }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build with PyInstaller
        run: |
          pyinstaller build/agent_service.spec --noconfirm

      - name: Package Mac app
        if: matrix.os == 'macos-latest'
        run: |
          cd dist
          zip -r AgentService-macos-x64.zip AgentService.app

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.asset_name }}
          path: |
            dist/${{ matrix.artifact_name }}
            dist/AgentService-macos-x64.zip
          if-no-files-found: error

      - name: Upload to Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: |
            dist/${{ matrix.asset_name }}
            dist/AgentService-macos-x64.zip
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Step 3: Commit**

```bash
git add .github/
git commit -m "feat: add GitHub Actions workflow for builds"
```

---

## Task 9: Update Main for Embedded API Key

**Files:**
- Modify: `services/agent_service.py`
- Modify: `app/config.py`

**Step 1: Update config with API key placeholder**

In `app/config.py`, the API key is already configured to read from environment variable. For the packaged app, we need to set it.

**Step 2: Create a .env file for local development (not committed)**

```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
echo ".env" >> .gitignore
```

**Step 3: Update agent_service.py to use config**

Modify `services/agent_service.py` to import and use the API key from config:

```python
# At the top of services/agent_service.py, add:
import os
# Set API key from config if available
try:
    from app.config import ANTHROPIC_API_KEY
    if ANTHROPIC_API_KEY:
        os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
except ImportError:
    pass
```

**Step 4: Commit**

```bash
git add services/agent_service.py .gitignore
git commit -m "feat: configure API key from app config"
```

---

## Task 10: Test Local Build

**Step 1: Install PyInstaller**

Run: `pip install pyinstaller`

**Step 2: Test build**

Run: `pyinstaller build/agent_service.spec --noconfirm`

**Step 3: Verify output**

Run: `ls -la dist/`
Expected: `AgentService` executable or `AgentService.app` directory

**Step 4: Test run (optional, may need display)**

Run: `./dist/AgentService` (Linux/Mac) or `dist\AgentService.exe` (Windows)

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete desktop packaging implementation"
```

---

## Task 11: Push and Create Release

**Step 1: Push all changes**

Run: `git push origin main`

**Step 2: Create and push tag**

Run: `git tag v1.0.0 && git push origin v1.0.0`

This will trigger the GitHub Actions workflow to build and create a release.

---

## Summary

This plan implements:

1. **Service Manager** - Controls FastAPI lifecycle in background thread
2. **Auto-Start Manager** - Windows registry / Mac LaunchAgents integration
3. **Tray Icon** - Programmatically generated icon
4. **Tray Application** - pystray-based system tray with menu
5. **PyInstaller Spec** - Cross-platform packaging configuration
6. **GitHub Actions** - Automated builds for Windows and Mac

Total: 11 tasks
