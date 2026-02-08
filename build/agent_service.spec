# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# build/agent_service.spec lives under build/, so project root is parent of SPECPATH.
ROOT = Path(SPECPATH).parent

# Collect all data files
datas = [
    (str(ROOT / "config"), "config"),
    (str(ROOT / "app" / "assets"), "app/assets"),
]

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "main",
    "routers.websocket",
    "routers.process",
    "routers.cancel",
    "services.connection_manager",
    "services.request_registry",
    "services.prompt_loader",
    "services.agent_service",
]

win_icon_path = ROOT / "build" / "assets" / "icon.ico"
mac_icon_path = ROOT / "build" / "assets" / "icon.icns"

win_icon = str(win_icon_path) if win_icon_path.exists() else None
mac_icon = str(mac_icon_path) if mac_icon_path.exists() else None


a = Analysis(
    [str(ROOT / "app" / "tray.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
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
    name="AgentService",
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
    icon=win_icon if sys.platform == "win32" else None,
)

# Mac-specific: create .app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="AgentService.app",
        icon=mac_icon,
        bundle_identifier="com.agentservice",
        info_plist={
            "LSUIElement": True,  # Hide from dock
        },
    )
