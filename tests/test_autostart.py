import sys
from unittest.mock import patch

import pytest

from app.autostart import AutoStartManager


class TestAutoStartManager:
    @pytest.fixture
    def manager(self, tmp_path):
        # Use temp path for testing
        with patch("app.autostart.AutoStartManager._get_executable_path") as mock_exe:
            mock_exe.return_value = "/path/to/AgentService"
            mgr = AutoStartManager()
            # Override paths for testing
            if sys.platform == "darwin":
                mgr._plist_path = tmp_path / "com.agentservice.plist"
            return mgr

    def test_is_enabled_returns_false_initially(self, manager):
        # Should return False when not configured
        assert manager.is_enabled() is False

    @pytest.mark.skipif(sys.platform == "win32", reason="Mac-specific test")
    def test_enable_creates_plist_on_mac(self, manager):
        if sys.platform != "darwin":
            pytest.skip("Mac-specific test")

        manager.enable()
        assert manager._plist_path.exists()

    @pytest.mark.skipif(sys.platform == "win32", reason="Mac-specific test")
    def test_disable_removes_plist_on_mac(self, manager):
        if sys.platform != "darwin":
            pytest.skip("Mac-specific test")

        manager.enable()
        manager.disable()
        assert not manager._plist_path.exists()
