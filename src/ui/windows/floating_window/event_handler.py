"""
Event Handler Module - Extracted from FloatingWindow
Handles keyboard and mouse events, hotkey processing.
"""

from typing import Optional, Dict, Callable
from PySide6.QtCore import QObject, Signal, QEvent, Qt
from PySide6.QtGui import QKeyEvent, QMouseEvent, QFocusEvent
from PySide6.QtWidgets import QWidget, QTextEdit

from src.utils.loguru_config import logger, get_logger


class EventHandler(QObject):
    """Handles all event processing for the floating window."""
    
    # Signals
    key_pressed = Signal(str)  # key_name
    mouse_clicked = Signal(int, int)  # x, y
    escape_pressed = Signal()
    enter_pressed = Signal()
    ctrl_enter_pressed = Signal()
    
    def __init__(self, window: QWidget):
        super().__init__()
        self.window = window
        self.logger = get_logger()
        
        # Event tracking
        self._key_modifiers = Qt.KeyboardModifier.NoModifier
        self._mouse_pressed = False
        self._monitored_widgets: Dict[QWidget, bool] = {}
        
        # Event callbacks for complex processing
        self._enter_callback: Optional[Callable[[str], None]] = None
        self._ctrl_enter_callback: Optional[Callable[[], None]] = None
        
        logger.info("EventHandler initialized")
    
    def install_event_filter(self, widget: QWidget) -> None:
        """Install event filter on a widget for monitoring."""
        widget.installEventFilter(self)
        self._monitored_widgets[widget] = True
        logger.info(f"Event filter installed on {widget.__class__.__name__}")
    
    def remove_event_filter(self, widget: QWidget) -> None:
        """Remove event filter from a widget."""
        if widget in self._monitored_widgets:
            widget.removeEventFilter(self)
            del self._monitored_widgets[widget]
            logger.info(f"Event filter removed from {widget.__class__.__name__}")
    
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Qt event filter - main entry point for all events."""
        try:
            # Handle key press events
            if event.type() == QEvent.Type.KeyPress:
                return self.handle_key_event(event)
            
            # Handle mouse events
            elif event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
                return self.handle_mouse_event(event)
            
            # Handle focus events
            elif event.type() == QEvent.Type.FocusOut:
                return self.handle_focus_event(event)
            
            return False  # Let other handlers process
            
        except Exception as e:
            logger.error(f"Event filter failed: {e}")
            return False
    
    def handle_key_event(self, event: QKeyEvent) -> bool:
        """Handle keyboard events."""
        try:
            key = event.key()
            modifiers = event.modifiers()
            self._key_modifiers = modifiers
            
            # Handle special key combinations
            if key == Qt.Key.Key_Escape:
                self.escape_pressed.emit()
                logger.info("Escape key pressed")
                return True
                
            elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
                if modifiers & Qt.KeyboardModifier.ControlModifier:
                    self.ctrl_enter_pressed.emit()
                    # Execute callback if registered
                    if self._ctrl_enter_callback:
                        try:
                            self._ctrl_enter_callback()
                        except Exception as e:
                            logger.error(f"Ctrl+Enter callback failed: {e}")
                    logger.info("Ctrl+Enter pressed")
                else:
                    self.enter_pressed.emit()
                    # Execute callback if registered
                    if self._enter_callback:
                        try:
                            # Get text from the focused widget if it's a text widget
                            text = ""
                            if isinstance(event.source(), QTextEdit):
                                text = event.source().toPlainText()
                            self._enter_callback(text)
                        except Exception as e:
                            logger.error(f"Enter callback failed: {e}")
                    logger.info("Enter pressed")
                return True
            
            # Emit general key press signal
            key_name = self._get_key_name(key, modifiers)
            self.key_pressed.emit(key_name)
            
            return False  # Let other handlers process
            
        except Exception as e:
            logger.error(f"Key event handling failed: {e}")
            return False
    
    def set_enter_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for Enter key processing."""
        self._enter_callback = callback
        logger.info("Enter callback registered")
    
    def set_ctrl_enter_callback(self, callback: Callable[[], None]) -> None:
        """Set callback for Ctrl+Enter key processing."""
        self._ctrl_enter_callback = callback
        logger.info("Ctrl+Enter callback registered")
    
    def install_on_widget(self, widget: QWidget) -> None:
        """Install event filter on a specific widget."""
        self.install_event_filter(widget)
    
    def get_monitored_widgets(self) -> list[QWidget]:
        """Get list of monitored widgets."""
        return list(self._monitored_widgets.keys())
    
    def handle_focus_event(self, event: QFocusEvent) -> bool:
        """Handle focus out events."""
        try:
            if event.type() == QEvent.Type.FocusOut:
                logger.info(" Focus lost from monitored widget")
                # Could trigger window hiding or other focus-related actions
                return False  # Don't consume the event
            
            return False
            
        except Exception as e:
            logger.error(f" Focus event handling failed: {e}")
            return False
    
    def handle_mouse_event(self, event: QMouseEvent) -> bool:
        """Handle mouse events."""
        try:
            if event.type() == QEvent.Type.MouseButtonPress:
                self._mouse_pressed = True
                pos = event.position().toPoint()
                self.mouse_clicked.emit(pos.x(), pos.y())
                
                logger.info(f"🖱️ Mouse clicked at ({pos.x()}, {pos.y()})")
                return True
                
            elif event.type() == QEvent.Type.MouseButtonRelease:
                self._mouse_pressed = False
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"🖱️ Mouse event handling failed: {e}")
            return False
    
    # Class-level key mapping for performance
    _KEY_MAP = {
        Qt.Key.Key_A: "A", Qt.Key.Key_B: "B", Qt.Key.Key_C: "C",
        Qt.Key.Key_D: "D", Qt.Key.Key_E: "E", Qt.Key.Key_F: "F",
        Qt.Key.Key_G: "G", Qt.Key.Key_H: "H", Qt.Key.Key_I: "I",
        Qt.Key.Key_J: "J", Qt.Key.Key_K: "K", Qt.Key.Key_L: "L",
        Qt.Key.Key_M: "M", Qt.Key.Key_N: "N", Qt.Key.Key_O: "O",
        Qt.Key.Key_P: "P", Qt.Key.Key_Q: "Q", Qt.Key.Key_R: "R",
        Qt.Key.Key_S: "S", Qt.Key.Key_T: "T", Qt.Key.Key_U: "U",
        Qt.Key.Key_V: "V", Qt.Key.Key_W: "W", Qt.Key.Key_X: "X",
        Qt.Key.Key_Y: "Y", Qt.Key.Key_Z: "Z",
        Qt.Key.Key_Space: "Space", Qt.Key.Key_Tab: "Tab",
        Qt.Key.Key_Backspace: "Backspace", Qt.Key.Key_Delete: "Delete",
        Qt.Key.Key_F1: "F1", Qt.Key.Key_F2: "F2", Qt.Key.Key_F3: "F3",
        Qt.Key.Key_F4: "F4", Qt.Key.Key_F5: "F5", Qt.Key.Key_F6: "F6",
        Qt.Key.Key_F7: "F7", Qt.Key.Key_F8: "F8", Qt.Key.Key_F9: "F9",
        Qt.Key.Key_F10: "F10", Qt.Key.Key_F11: "F11", Qt.Key.Key_F12: "F12",
    }
    
    def _get_key_name(self, key: int, modifiers: Qt.KeyboardModifier) -> str:
        """Convert key and modifiers to readable string."""
        key_parts = []
        
        # Use bitwise operations for better performance
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            key_parts.append("Ctrl")
        if modifiers & Qt.KeyboardModifier.AltModifier:
            key_parts.append("Alt")
        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            key_parts.append("Shift")
        
        # Use class-level mapping for better performance
        key_name = self._KEY_MAP.get(key, f"Key_{key}")
        key_parts.append(key_name)
        
        return "+".join(key_parts)
    
    def is_mouse_pressed(self) -> bool:
        """Check if mouse is currently pressed."""
        return self._mouse_pressed
    
    def get_current_modifiers(self) -> Qt.KeyboardModifier:
        """Get current keyboard modifiers."""
        return self._key_modifiers
    
    def cleanup(self):
        """Clean up event handler resources."""
        try:
            # Remove event filters from all monitored widgets
            for widget in list(self._monitored_widgets.keys()):
                self.remove_event_filter(widget)
            
            # Clear callbacks
            self._enter_callback = None
            self._ctrl_enter_callback = None
            
            # Reset state
            self._mouse_pressed = False
            self._key_modifiers = Qt.KeyboardModifier.NoModifier
            
            logger.info("EventHandler cleanup completed")
            
        except Exception as e:
            logger.error(f"EventHandler cleanup failed: {e}")