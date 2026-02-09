"""
Asynchronous Text Processor
Handles non-blocking AI text processing operations
"""

import time
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass
from PySide6.QtCore import Signal, QThread

from src.services.ai.ai_service import AIService
from src.utils.loguru_config import logger, get_logger


class RequestPriority(Enum):
    """Processing request priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    IMMEDIATE = 4


@dataclass
class ProcessingRequest:
    """Text processing request"""
    request_id: int
    text: str
    agent_name: str
    priority: RequestPriority
    timestamp: float
    window_context: Optional[Dict[str, Any]] = None  # Window context information
    
    def __lt__(self, other):
        """Compare requests for priority queue ordering"""
        if self.priority.value != other.priority.value:
            return self.priority.value > other.priority.value  # Higher priority first
        return self.timestamp < other.timestamp  # Earlier timestamp first


class AsyncProcessor(QThread):
    """Asynchronous text processor using Qt threading"""
    
    # Signals
    processing_started = Signal(int, str)  # request_id, agent_name
    processing_completed = Signal(int, str, str)  # request_id, agent_name, result
    processing_failed = Signal(int, str, str)  # request_id, agent_name, error
    processing_cancelled = Signal(int, str)  # request_id, agent_name
    
    def __init__(self, ai_service_manager: AIService):
        super().__init__()
        self.ai_service_manager = ai_service_manager
        self.logger = get_logger(__name__)
        
        # Request management
        self._request_queue: list[ProcessingRequest] = []
        self._current_request: Optional[ProcessingRequest] = None
        self._request_counter = 0
        self._is_running = False
        self._stop_requested = False
        
        # Performance tracking
        self._processing_times: Dict[int, float] = {}
        
        logger.info("AsyncProcessor initialized")
    
    def submit_request(self, text: str, agent_name: str, priority: RequestPriority = RequestPriority.NORMAL, 
                      window_context: Optional[Dict[str, Any]] = None) -> int:
        """Submit a text processing request
        
        Args:
            text: Text to process
            agent_name: Name of the agent to use
            priority: Request priority level
            window_context: Optional window context information (title, process_name, etc.)
        """
        try:
            self._request_counter += 1
            request_id = self._request_counter
            
            request = ProcessingRequest(
                request_id=request_id,
                text=text,
                agent_name=agent_name,
                priority=priority,
                timestamp=time.time(),
                window_context=window_context
            )
            
            # Add to priority queue
            self._request_queue.append(request)
            self._request_queue.sort()  # Sort by priority and timestamp
            
            if window_context:
                logger.info(f"Request submitted: ID={request_id} with context: {window_context.get('window_title', 'Unknown')}")
            else:
                logger.info(f"Request submitted: ID={request_id}")
            
            return request_id
            
        except Exception as e:
            logger.error(f"Failed to submit request: {e}")
            return -1
    
    def run(self):
        """Main processing loop"""
        try:
            self._is_running = True
            logger.info("AsyncProcessor started")
            
            while not self._stop_requested:
                try:
                    # Check for pending requests
                    if self._request_queue:
                        # Get highest priority request
                        request = self._request_queue.pop(0)
                        self._process_request(request)
                    else:
                        # No requests, sleep briefly
                        self.msleep(50)  # 50ms sleep
                        
                except Exception as e:
                    logger.error(f"Error in processing loop: {e}")
                    self.msleep(100)  # Longer sleep on error
            
            logger.info("AsyncProcessor stopped")
            
        except Exception as e:
            logger.error(f"Fatal error in AsyncProcessor: {e}")
        finally:
            self._is_running = False
    
    def _process_request(self, request: ProcessingRequest):
        """Process a single request"""
        try:
            self._current_request = request
            start_time = time.time()
            
            # Emit processing started signal
            self.processing_started.emit(request.request_id, request.agent_name)
            
            logger.info(f"Processing request ID={request.request_id}: {request.text[:50]}...")
            
            # Process text with AI service
            if self.ai_service_manager:
                result = self.ai_service_manager.process_text(
                    request.text, 
                    request.agent_name,
                    window_context=request.window_context
                )
                
                if result and result.strip():
                    # Record processing time
                    processing_time = time.time() - start_time
                    self._processing_times[request.request_id] = processing_time
                    
                    # Emit success signal
                    self.processing_completed.emit(request.request_id, request.agent_name, result)
                    
                    logger.info(f"Request completed: ID={request.request_id}")
                else:
                    # Empty result
                    error_msg = "AI processing returned empty result"
                    self.processing_failed.emit(request.request_id, request.agent_name, error_msg)
                    
                    logger.error(f"Request failed: ID={request.request_id}")
            else:
                # AI service not available
                error_msg = "AI service manager not available"
                self.processing_failed.emit(request.request_id, request.agent_name, error_msg)
                
                logger.error(f"Request failed: ID={request.request_id}")
                
        except Exception as e:
            # Processing error
            error_msg = f"Processing exception: {str(e)}"
            self.processing_failed.emit(request.request_id, request.agent_name, error_msg)
            
            logger.error(f"Request failed: ID={request.request_id}")
        finally:
            self._current_request = None
    
    def stop_processing(self):
        """Stop the processing thread"""
        try:
            logger.info("Stopping AsyncProcessor...")
            self._stop_requested = True
            
            # Cancel current request if any
            if self._current_request:
                self.processing_cancelled.emit(
                    self._current_request.request_id,
                    self._current_request.agent_name
                )
            
            # Clear pending requests
            cancelled_count = len(self._request_queue)
            for request in self._request_queue:
                self.processing_cancelled.emit(request.request_id, request.agent_name)
            
            self._request_queue.clear()
            
            if cancelled_count > 0:
                logger.info(f"Cancelled {cancelled_count} pending requests")
            
        except Exception as e:
            logger.error(f"Error stopping AsyncProcessor: {e}")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return len(self._request_queue)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        if not self._processing_times:
            return {
                "total_requests": 0,
                "average_time": 0.0,
                "min_time": 0.0,
                "max_time": 0.0
            }
        
        times = list(self._processing_times.values())
        return {
            "total_requests": len(times),
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "queue_size": self.get_queue_size(),
            "is_running": self._is_running
        }
    
    def is_processing(self) -> bool:
        """Check if currently processing a request"""
        return self._current_request is not None
    
    def clear_queue(self):
        """Clear all pending requests"""
        try:
            cancelled_count = len(self._request_queue)
            
            for request in self._request_queue:
                self.processing_cancelled.emit(request.request_id, request.agent_name)
            
            self._request_queue.clear()
            
            logger.info(f"Cleared {cancelled_count} pending requests")
            
        except Exception as e:
            logger.error(f"Error clearing queue: {e}")