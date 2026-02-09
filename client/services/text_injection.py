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

