"""
Signal Bridge for HTTP Server

Thread-safe bridge between the HTTP server background thread and the Qt main thread.
Uses Qt signals to safely deliver data across thread boundaries.
"""

from PySide6.QtCore import QObject, Signal


class HttpSignalBridge(QObject):
    """Thread-safe bridge: HTTP server thread -> Qt main thread."""

    # Emitted when POST /api/input receives text.
    # Payload: (text, button_number, role_number)
    text_received = Signal(str, int, int)
