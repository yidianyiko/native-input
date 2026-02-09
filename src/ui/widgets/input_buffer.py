"""
Input Buffer Module
Handles non-blocking input text management and change detection
"""
import contextlib

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QTextEdit

from src.utils.loguru_config import logger, get_logger


class InputBuffer(QObject):
    """Non-blocking input buffer for immediate text response"""
    
    # Signals
    text_changed = Signal(str)  # Emitted when text changes
    content_cleared = Signal()  # Emitted when content is cleared
    content_processed = Signal(str)  # Emitted when content is marked as processed
    
    def __init__(self, text_widget: QTextEdit):
        super().__init__()
        self.text_widget = text_widget
        self.logger = get_logger(__name__)
        
        # Buffer state
        self._content = ""
        self._is_processed = False
        self._last_change_time = 0.0
        
        # Change detection
        self._change_timer = QTimer()
        self._change_timer.setSingleShot(True)
        self._change_timer.timeout.connect(self._on_change_timeout)
        self._debounce_ms = 100  # 100ms debounce
        
        # Connect to text widget
        if self.text_widget:
            self.text_widget.textChanged.connect(self._on_text_changed)
        
        logger.info("InputBuffer initialized")
    
    def _on_text_changed(self):
        """Handle text widget changes with debouncing"""
        try:
            import time
            
            # Get current text
            current_text = self.text_widget.toPlainText() if self.text_widget else ""
            
            # Update internal state
            self._content = current_text
            self._is_processed = False
            self._last_change_time = time.time()
            
            # Restart debounce timer
            self._change_timer.start(self._debounce_ms)
            
        except Exception as e:
            logger.error(f"Error handling text change: {e}")
    
    def _on_change_timeout(self):
        """Handle debounced text change"""
        try:
            # Emit text changed signal after debounce
            self.text_changed.emit(self._content)
            
            logger.info(f"Text changed: {len(self._content)} chars")
            
        except Exception as e:
            logger.error(f"Error in change timeout: {e}")
    
    def get_content(self) -> str:
        """Get current buffer content"""
        return self._content
    
    def set_content(self, text: str):
        """Set buffer content programmatically"""
        try:
            self._content = text
            self._is_processed = False
            
            # Update text widget if available
            if self.text_widget:
                # Temporarily disconnect to avoid recursive signals
                self.text_widget.textChanged.disconnect(self._on_text_changed)
                self.text_widget.setPlainText(text)
                self.text_widget.textChanged.connect(self._on_text_changed)
            
            # Emit change signal
            self.text_changed.emit(text)
            
            logger.info(f"Content set programmatically: {len(text)} chars")
            
        except Exception as e:
            logger.error(f"Error setting content: {e}")
    
    def clear(self):
        """Clear buffer content"""
        try:
            self._content = ""
            self._is_processed = False
            
            # Clear text widget if available
            if self.text_widget:
                # Temporarily disconnect to avoid recursive signals
                self.text_widget.textChanged.disconnect(self._on_text_changed)
                self.text_widget.clear()
                self.text_widget.textChanged.connect(self._on_text_changed)
            
            # Emit cleared signal
            self.content_cleared.emit()
            
            logger.info("Content cleared")
            
        except Exception as e:
            logger.error(f"Error clearing content: {e}")
    
    def mark_processed(self):
        """Mark current content as processed"""
        try:
            self._is_processed = True
            self.content_processed.emit(self._content)
            
            logger.info(f"Content marked as processed: {len(self._content)} chars")
            
        except Exception as e:
            logger.error(f"Error marking as processed: {e}")
    
    def is_processed(self) -> bool:
        """Check if current content is processed"""
        return self._is_processed
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return not self._content.strip()
    
    def get_word_count(self) -> int:
        """Get word count of current content"""
        return len(self._content.split()) if self._content else 0
    
    def get_char_count(self) -> int:
        """Get character count of current content"""
        return len(self._content)
    
    def set_debounce_time(self, ms: int):
        """Set debounce time in milliseconds"""
        self._debounce_ms = max(50, min(ms, 1000))  # Clamp between 50ms and 1s
        logger.info(f"Debounce time set to: {self._debounce_ms}ms")
    
    def get_last_change_time(self) -> float:
        """Get timestamp of last change"""
        return self._last_change_time
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop timer
            if self._change_timer:
                self._change_timer.stop()
            
            # Disconnect from text widget
            if self.text_widget:
                with contextlib.suppress(RuntimeError):
                    self.text_widget.textChanged.disconnect(self._on_text_changed)
            
            logger.info("InputBuffer cleanup completed")
            
        except Exception as e:
            logger.error(f"InputBuffer cleanup failed: {e}")