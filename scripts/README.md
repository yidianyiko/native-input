# Build Scripts Documentation

This directory contains automation scripts for building and packaging the AI Input Method Tool.

## Scripts Overview

### `build_executable.py`
Creates a standalone Windows executable using PyInstaller.

```bash
# Basic build
python scripts/build_executable.py

# Debug build with verbose output
python scripts/build_executable.py --debug

# Skip cleaning build directories
python scripts/build_executable.py --no-clean

# Validate environment only
python scripts/build_executable.py --validate-only
```

### `build_installer.py`
Creates a Windows installer using NSIS (requires NSIS to be installed).

```bash
# Build installer (requires existing executable)
python scripts/build_installer.py

# Validate prerequisites only
python scripts/build_installer.py --validate-only
```

### `build_and_test.py`
Complete build process including executable, installer, and testing.

```bash
# Full build and test process
python scripts/build_and_test.py

# Build with debug mode
python scripts/build_and_test.py --debug

# Skip installation tests
python scripts/build_and_test.py --skip-tests

# Build executable only
python scripts/build_and_test.py --executable-only

# Build installer only
python scripts/build_and_test.py --installer-only
```

### `test_installation.py`
Tests installation and uninstallation processes.

```bash
python scripts/test_installation.py
```

## Prerequisites

1. **Python 3.10+** with all project dependencies installed
2. **PyInstaller** - Install with: `uv add --dev pyinstaller`
3. **NSIS** (for installer) - Download from https://nsis.sourceforge.io/

## Build Process

1. **Executable Build**: Creates `dist/ai-input-method/ai-input-method.exe`
2. **Installer Build**: Creates `dist/ai-input-method-installer-*.exe`
3. **Testing**: Validates installation/uninstallation
4. **Release Package**: Creates complete release in `dist/release/`

## Output Structure

```
dist/
├── ai-input-method/              # Portable executable
│   ├── ai-input-method.exe
│   └── [dependencies...]
├── ai-input-method-installer-*.exe  # Windows installer
└── release/                      # Complete release package
    ├── ai-input-method-installer-*.exe
    ├── portable/                 # Portable version
    └── RELEASE_NOTES.txt
```

## Troubleshooting

- **PyInstaller errors**: Check dependencies in `build/pyinstaller/ai-input-method.spec`
- **NSIS errors**: Ensure NSIS is installed and `makensis.exe` is in PATH
- **Missing files**: Check that all required resources exist in `resources/` directory