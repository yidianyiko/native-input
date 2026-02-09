"""
Output Buffer Module
Handles independent result display and state management
"""

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QLabel

from src.utils.loguru_config import logger, get_logger


class OutputBuffer(QObject):
    """Independent output buffer for result display"""
    
    # Signals
    content_updated = Signal(str)  # Emitted when content is updated
    state_changed = Signal(str)  # Emitted when state changes
    display_cleared = Signal()  # Emitted when display is cleared
    
    def __init__(self, result_widget: QLabel):
        super().__init__()
        self.result_widget = result_widget
        self.logger = get_logger(__name__)
        
        # Buffer state
        self._content = ""
        self._state = "idle"  # idle, processing, success, error, cancelled
        self._processing_agent = ""
        
        # Animation timer for processing indicator
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_processing_animation)
        self._animation_dots = 0
        
        logger.info("OutputBuffer initialized")
    
    def set_content(self, content: str):
        """Set output content"""
        try:
            self._content = content
            self._state = "success"
            
            # Update result widget if available
            if self.result_widget:
                self.result_widget.setText(content)
            
            # Stop processing animation
            self._stop_processing_animation()
            
            # Emit signals
            self.content_updated.emit(content)
            self.state_changed.emit(self._state)
            
            logger.info(f"Content updated: {len(content)} chars")
            
        except Exception as e:
            logger.error(f"Error setting content: {e}")
    
    def clear(self):
        """Clear output content"""
        try:
            self._content = ""
            self._state = "idle"
            self._processing_agent = ""
            
            # Clear result widget if available
            if self.result_widget:
                self.result_widget.clear()
            
            # Stop processing animation
            self._stop_processing_animation()
            
            # Emit signals
            self.display_cleared.emit()
            self.state_changed.emit(self._state)
            
            logger.info("Content cleared")
            
        except Exception as e:
            logger.error(f"Error clearing content: {e}")
    
    def start_processing(self, agent_name: str):
        """Start processing state with animation"""
        try:
            self._state = "processing"
            self._processing_agent = agent_name
            self._animation_dots = 0
            
            # Start processing animation
            self._start_processing_animation()
            
            # Emit state change
            self.state_changed.emit(self._state)
            
            logger.info(f"Processing started with agent: {agent_name}")
            
        except Exception as e:
            logger.error(f"Error starting processing: {e}")
    
    def complete_processing(self, result: str):
        """Complete processing with result"""
        try:
            self.set_content(result)
            
            logger.info(f"Processing completed: {len(result)} chars")
            
        except Exception as e:
            logger.error(f"Error completing processing: {e}")
    
    def error_processing(self, error_message: str):
        """Handle processing error"""
        try:
            self._state = "error"
            self._content = f"Error: {error_message}"
            
            # Update result widget
            if self.result_widget:
                self.result_widget.setText(self._content)
            
            # Stop processing animation
            self._stop_processing_animation()
            
            # Emit signals
            self.content_updated.emit(self._content)
            self.state_changed.emit(self._state)
            
            logger.error(f"Processing error: {error_message}")
            
        except Exception as e:
            logger.error(f"Error handling processing error: {e}")
    
    def cancel_processing(self):
        """Cancel processing"""
        try:
            self._state = "cancelled"
            self._content = "Processing cancelled"
            
            # Update result widget
            if self.result_widget:
                self.result_widget.setText(self._content)
            
            # Stop processing animation
            self._stop_processing_animation()
            
            # Emit signals
            self.content_updated.emit(self._content)
            self.state_changed.emit(self._state)
            
            logger.info("Processing cancelled")
            
        except Exception as e:
            logger.error(f"Error cancelling processing: {e}")
    
    def _start_processing_animation(self):
        """Start processing animation"""
        try:
            self._animation_timer.start(500)  # Update every 500ms
            self._update_processing_animation()
            
        except Exception as e:
            logger.error(f"Error starting animation: {e}")
    
    def _stop_processing_animation(self):
        """Stop processing animation"""
        try:
            self._animation_timer.stop()
            
        except Exception as e:
            logger.error(f"Error stopping animation: {e}")
    
    def _update_processing_animation(self):
        """Update processing animation"""
        try:
            if self._state != "processing":
                return
            
            # Cycle through dots (0, 1, 2, 3)
            self._animation_dots = (self._animation_dots + 1) % 4
            dots = "." * self._animation_dots
            
            # Update display
            processing_text = f"Processing with {self._processing_agent}{dots}"
            
            if self.result_widget:
                self.result_widget.setText(processing_text)
            
        except Exception as e:
            logger.error(f"Error updating animation: {e}")
    
    def get_content(self) -> str:
        """Get current content"""
        return self._content
    
    def get_state(self) -> str:
        """Get current state"""
        return self._state
    
    def is_processing(self) -> bool:
        """Check if currently processing"""
        return self._state == "processing"
    
    def is_empty(self) -> bool:
        """Check if buffer is empty"""
        return not self._content.strip()
    
    def get_processing_agent(self) -> str:
        """Get current processing agent"""
        return self._processing_agent
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop animation timer
            if self._animation_timer:
                self._animation_timer.stop()
            
            logger.info("OutputBuffer cleanup completed")
            
        except Exception as e:
            logger.error(f"OutputBuffer cleanup failed: {e}")