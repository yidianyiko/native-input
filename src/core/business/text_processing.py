"""Text processing business logic.

Core business logic for text processing operations.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class ProcessingStatus(Enum):
    """Text processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingRequest:
    """Represents a text processing request."""
    text: str
    agent_name: str
    request_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingResult:
    """Represents a text processing result."""
    request_id: str
    original_text: str
    processed_text: Optional[str]
    agent_name: str
    status: ProcessingStatus
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None


class TextProcessingBusinessLogic:
    """Core business logic for text processing."""
    
    def __init__(self):
        self._processing_history: Dict[str, ProcessingResult] = {}
    
    def create_processing_request(self, text: str, agent_name: str, 
                                model_id: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> ProcessingRequest:
        """Create a new processing request."""
        import uuid
        request_id = str(uuid.uuid4())
        
        if metadata is None:
            metadata = {}
        if model_id:
            metadata['model_id'] = model_id
            
        return ProcessingRequest(
            text=text,
            agent_name=agent_name,
            request_id=request_id,
            metadata=metadata
        )
    
    def validate_processing_request(self, request: ProcessingRequest) -> tuple[bool, Optional[str]]:
        """Validate a processing request.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not request.text or not request.text.strip():
            return False, "Text cannot be empty"
        
        if not request.agent_name:
            return False, "Agent name is required"
        
        if len(request.text) > 10000:  # Reasonable limit
            return False, "Text is too long (max 10000 characters)"
        
        return True, None
    
    def create_processing_result(self, request: ProcessingRequest, 
                               processed_text: Optional[str] = None,
                               status: ProcessingStatus = ProcessingStatus.PENDING,
                               error_message: Optional[str] = None) -> ProcessingResult:
        """Create a processing result from a request."""
        result = ProcessingResult(
            request_id=request.request_id or f"{request.agent_name}_{hash(request.text)}",
            original_text=request.text,
            processed_text=processed_text,
            agent_name=request.agent_name,
            status=status,
            error_message=error_message
        )
        
        # Store in history
        self._processing_history[result.request_id] = result
        return result
    
    def update_processing_result(self, request_id: str, 
                               processed_text: Optional[str] = None,
                               status: Optional[ProcessingStatus] = None,
                               error_message: Optional[str] = None,
                               processing_time_ms: Optional[int] = None) -> Optional[ProcessingResult]:
        """Update an existing processing result."""
        if request_id not in self._processing_history:
            return None
        
        result = self._processing_history[request_id]
        
        if processed_text is not None:
            result.processed_text = processed_text
        if status is not None:
            result.status = status
        if error_message is not None:
            result.error_message = error_message
        if processing_time_ms is not None:
            result.processing_time_ms = processing_time_ms
        
        return result
    
    def get_processing_result(self, request_id: str) -> Optional[ProcessingResult]:
        """Get a processing result by ID."""
        return self._processing_history.get(request_id)
    
    def get_processing_history(self, agent_name: Optional[str] = None) -> Dict[str, ProcessingResult]:
        """Get processing history, optionally filtered by agent."""
        if agent_name is None:
            return self._processing_history.copy()
        
        return {
            request_id: result 
            for request_id, result in self._processing_history.items() 
            if result.agent_name == agent_name
        }
    
    def clear_processing_history(self) -> None:
        """Clear all processing history."""
        self._processing_history.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        total_requests = len(self._processing_history)
        if total_requests == 0:
            return {
                "total_requests": 0,
                "completed_requests": 0,
                "failed_requests": 0,
                "success_rate": 0.0,
                "agents_used": []
            }
        
        completed = sum(1 for r in self._processing_history.values() 
                       if r.status == ProcessingStatus.COMPLETED)
        failed = sum(1 for r in self._processing_history.values() 
                    if r.status == ProcessingStatus.FAILED)
        agents_used = list(set(r.agent_name for r in self._processing_history.values()))
        
        return {
            "total_requests": total_requests,
            "completed_requests": completed,
            "failed_requests": failed,
            "success_rate": completed / total_requests * 100,
            "agents_used": agents_used
        }