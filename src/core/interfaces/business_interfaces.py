"""Business Logic Interfaces

Defines abstract interfaces for business logic components to provide
clear contracts and enable dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ProcessingResult:
    """Result of text processing operation"""
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ITextProcessingBusinessLogic(ABC):
    """Interface for text processing business logic"""
    
    @abstractmethod
    def process_text(self, text: str, agent_name: str, **kwargs) -> ProcessingResult:
        """Process text using specified agent"""
    
    @abstractmethod
    def get_available_processors(self) -> List[str]:
        """Get list of available text processors"""
    
    @abstractmethod
    def validate_processing_request(self, text: str, agent_name: str) -> bool:
        """Validate text processing request"""
    
    @abstractmethod
    def get_processing_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get text processing history"""


class IBusinessLogicFactory(ABC):
    """Factory interface for creating business logic instances"""
    
    @abstractmethod
    def create_configuration_logic(self) -> 'IConfigurationManager':
        """Create configuration business logic instance"""
    
    @abstractmethod
    def create_text_processing_logic(self) -> ITextProcessingBusinessLogic:
        """Create text processing business logic instance"""


class IBusinessLogicContainer(ABC):
    """Container interface for business logic dependency injection"""
    
    @abstractmethod
    def register_singleton(self, interface_type: type, implementation: Any) -> None:
        """Register singleton instance"""
    
    @abstractmethod
    def register_transient(self, interface_type: type, factory: callable) -> None:
        """Register transient factory"""
    
    @abstractmethod
    def resolve(self, interface_type: type) -> Any:
        """Resolve instance by interface type"""
    
    @abstractmethod
    def is_registered(self, interface_type: type) -> bool:
        """Check if interface type is registered"""
