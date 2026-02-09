"""
Trigger Manager Module
Handles intelligent processing triggers with debouncing and priority management
"""

import time
from typing import Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer

from src.utils.loguru_config import logger, get_logger


class TriggerManager(QObject):
    """Manages intelligent processing triggers with debouncing"""
    
    # Signals
    processing_triggered = Signal(str, str, str)  # trigger_type, text, agent_name
    trigger_cancelled = Signal(str)  # trigger_type
    
    def __init__(self, debounce_ms: int = 800):
        super().__init__()
        self.logger = get_logger()
        
        # Debounce settings
        self.debounce_ms = debounce_ms
        
        # Timers for different trigger types
        self._text_change_timer = QTimer()
        self._text_change_timer.setSingleShot(True)
        self._text_change_timer.timeout.connect(self._on_text_change_timeout)
        
        # Current trigger state
        self._pending_text = ""
        self._pending_agent = ""
        self._is_processing = False
        self._last_trigger_time = 0.0
        
        # Trigger statistics
        self._trigger_counts: Dict[str, int] = {
            "text_change": 0,
            "enter_key": 0,
            "agent_switch": 0,
            "manual": 0,
            "immediate": 0
        }
        
        logger.info(f" TriggerManager initialized with {debounce_ms}ms debounce")
    
    def on_text_changed(self, text: str, agent_name: str):
        """Handle text change with debouncing"""
        try:
            if self._is_processing:
                # Skip if already processing
                logger.info("Processing in progress")
                return
            
            # Skip if text is empty
            if not text.strip():
                logger.info("Empty text")
                return
            
            self._pending_text = text
            self._pending_agent = agent_name
            
            # Restart debounce timer
            self._text_change_timer.start(self.debounce_ms)
            
            logger.info(f" Text change detected")
            
        except Exception as e:
            logger.error(f" Error handling text change: {e}")
    
    def _on_text_change_timeout(self):
        """Handle debounced text change"""
        try:
            if not self._pending_text.strip() or self._is_processing:
                return
            
            # Trigger processing
            self._trigger_processing("text_change", self._pending_text, self._pending_agent)
            
        except Exception as e:
            logger.error(f" Error in text change timeout: {e}")
    
    def on_enter_key_pressed(self, text: str, agent_name: str):
        """Handle Enter key press - immediate trigger"""
        try:
            # Cancel any pending text change triggers
            self._text_change_timer.stop()
            
            if text.strip():
                self._trigger_processing("enter_key", text, agent_name)
            
        except Exception as e:
            logger.error(f" Error handling Enter key: {e}")
    
    def on_agent_switched(self, agent_name: str, text: str):
        """Handle agent switch - immediate trigger if text exists"""
        try:
            # Cancel any pending triggers
            self._text_change_timer.stop()
            
            if text.strip():
                self._trigger_processing("agent_switch", text, agent_name)
            
        except Exception as e:
            logger.error(f" Error handling agent switch: {e}")
    
    def trigger_manual(self, text: str, agent_name: str):
        """Manually trigger processing"""
        try:
            # Cancel any pending triggers
            self._text_change_timer.stop()
            
            if text.strip():
                self._trigger_processing("manual", text, agent_name)
            
        except Exception as e:
            logger.error(f" Error in manual trigger: {e}")
    
    def trigger_immediate(self, text: str, agent_name: str):
        """Immediately trigger processing (highest priority)"""
        try:
            # Cancel any pending triggers
            self._text_change_timer.stop()
            
            if text.strip():
                self._trigger_processing("immediate", text, agent_name)
            
        except Exception as e:
            logger.error(f" Error in immediate trigger: {e}")
    
    def _trigger_processing(self, trigger_type: str, text: str, agent_name: str):
        """Internal method to trigger processing"""
        try:
            # Update statistics
            self._trigger_counts[trigger_type] = self._trigger_counts.get(trigger_type, 0) + 1
            self._last_trigger_time = time.time()
            
            # Emit processing signal
            self.processing_triggered.emit(trigger_type, text, agent_name)
            
            logger.info(f" Processing triggered: {trigger_type}")
            
        except Exception as e:
            logger.error(f" Error triggering processing: {e}")
    
    def set_processing_state(self, is_processing: bool):
        """Set processing state to prevent duplicate triggers"""
        try:
            self._is_processing = is_processing
            
            if is_processing:
                # Cancel any pending triggers when processing starts
                self._text_change_timer.stop()
            
            logger.info(f" Processing state: {'active' if is_processing else 'idle'}")
            
        except Exception as e:
            logger.error(f" Error setting processing state: {e}")
    
    def cancel_pending_triggers(self):
        """Cancel all pending triggers"""
        try:
            # Stop all timers
            self._text_change_timer.stop()
            
            # Emit cancellation signal if there was a pending trigger
            if self._text_change_timer.isActive():
                self.trigger_cancelled.emit("text_change")
            
            logger.info(" All pending triggers cancelled")
            
        except Exception as e:
            logger.error(f" Error cancelling triggers: {e}")
    
    def set_debounce_time(self, ms: int):
        """Set debounce time in milliseconds"""
        try:
            self.debounce_ms = max(100, min(ms, 5000))  # Clamp between 100ms and 5s
            
            logger.info(f" Debounce time set to: {self.debounce_ms}ms")
            
        except Exception as e:
            logger.error(f" Error setting debounce time: {e}")
    
    def get_trigger_statistics(self) -> Dict[str, Any]:
        """Get trigger statistics"""
        return {
            "trigger_counts": self._trigger_counts.copy(),
            "total_triggers": sum(self._trigger_counts.values()),
            "last_trigger_time": self._last_trigger_time,
            "debounce_ms": self.debounce_ms,
            "is_processing": self._is_processing,
            "has_pending_triggers": self._text_change_timer.isActive()
        }
    
    def reset_statistics(self):
        """Reset trigger statistics"""
        try:
            self._trigger_counts = {key: 0 for key in self._trigger_counts}
            self._last_trigger_time = 0.0
            
            logger.info(" Trigger statistics reset")
            
        except Exception as e:
            logger.error(f" Error resetting statistics: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            # Stop all timers
            self._text_change_timer.stop()
            
            logger.info(" TriggerManager cleanup completed")
            
        except Exception as e:
            logger.error(f" TriggerManager cleanup failed: {e}")