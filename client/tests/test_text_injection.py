from unittest.mock import MagicMock, call, patch

import pytest

from services.text_injection import inject_text, _inject_via_clipboard, _inject_via_keyboard


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

