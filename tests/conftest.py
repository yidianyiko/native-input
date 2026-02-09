"""
Pytest configuration and fixtures for refactoring tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock
from pathlib import Path
import sys

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_qt_application():
    """Mock Qt application for UI testing."""
    mock_app = Mock()
    mock_app.exec = Mock(return_value=0)
    mock_app.quit = Mock()
    return mock_app


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    logger.debug = Mock()
    return logger


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        'window': {
            'opacity': 0.9,
            'always_on_top': True,
            'follow_cursor': True,
            'theme': 'dark'
        },
        'hotkeys': {
            'trigger_key': 'F1',
            'modifier_keys': ['ctrl', 'shift']
        },
        'ai': {
            'provider': 'openai',
            'model': 'gpt-4',
            'api_key': 'test-key'
        }
    }


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_audio_device():
    """Mock audio device for testing."""
    device = Mock()
    device.start_recording = Mock()
    device.stop_recording = Mock()
    device.get_audio_data = Mock(return_value=b'mock_audio_data')
    return device


@pytest.fixture
def mock_windows_api():
    """Mock Windows API functions for testing."""
    api = Mock()
    api.GetForegroundWindow = Mock(return_value=12345)
    api.GetWindowText = Mock(return_value="Test Window")
    api.SetWindowsHookEx = Mock(return_value=1)
    return api


@pytest.fixture
def mock_pynput_keyboard():
    """Mock pynput keyboard for testing."""
    keyboard = Mock()
    keyboard.press = Mock()
    keyboard.release = Mock()
    keyboard.type = Mock()
    keyboard.pressed = Mock()
    return keyboard


@pytest.fixture
def mock_pynput_listener():
    """Mock pynput hotkey listener for testing."""
    listener = Mock()
    listener.start = Mock()
    listener.stop = Mock()
    listener.join = Mock()
    listener.running = True
    return listener


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "refactoring: marks tests as refactoring-related"
    )
    config.addinivalue_line(
        "markers", "ui_module: marks tests for UI module refactoring"
    )
    config.addinivalue_line(
        "markers", "audio_module: marks tests for audio module refactoring"
    )
    config.addinivalue_line(
        "markers", "system_module: marks tests for system integration module refactoring"
    )