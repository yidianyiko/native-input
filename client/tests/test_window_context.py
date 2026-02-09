from unittest.mock import patch


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

