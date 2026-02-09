"""Dependency Injection Container

Provides a simple dependency injection container for managing
business logic instances and their dependencies.
"""

from typing import Any, Dict, Type, TypeVar, Callable, Optional
from src.core.interfaces import (
    IBusinessLogicContainer,
    IConfigurationManager,
    ITextProcessingBusinessLogic,
    IDatabaseService,
)
from src.core.business.configuration import ConfigurationBusinessLogic
from src.core.business.text_processing import TextProcessingBusinessLogic
from src.services.database import DatabaseService

T = TypeVar('T')


class BusinessLogicContainer(IBusinessLogicContainer):
    """Simple dependency injection container for business logic"""
    
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._transients: Dict[Type, Callable] = {}
        self._setup_default_registrations()
    
    def _setup_default_registrations(self):
        """Setup default business logic registrations"""
        # Register configuration business logic as singleton
        self.register_singleton(
            IConfigurationManager,
            ConfigurationBusinessLogic()
        )
        
        # Register text processing business logic as singleton
        self.register_singleton(
            ITextProcessingBusinessLogic,
            TextProcessingBusinessLogic()
        )
        
        # Register database service as singleton
        self.register_singleton(
            IDatabaseService,
            DatabaseService()
        )
    
    def register_singleton(self, interface_type: Type[T], implementation: T) -> None:
        """Register singleton instance"""
        self._singletons[interface_type] = implementation
    
    def register_transient(self, interface_type: Type[T], factory: Callable[[], T]) -> None:
        """Register transient factory"""
        self._transients[interface_type] = factory
    
    def resolve(self, interface_type: Type[T]) -> T:
        """Resolve instance by interface type"""
        # Check singletons first
        if interface_type in self._singletons:
            return self._singletons[interface_type]
        
        # Check transients
        if interface_type in self._transients:
            factory = self._transients[interface_type]
            return factory()
        
        # Try to resolve by concrete type
        if hasattr(interface_type, '__init__'):
            try:
                return interface_type()
            except Exception:
                pass
        
        raise ValueError(f"No registration found for type: {interface_type}")
    
    def is_registered(self, interface_type: Type) -> bool:
        """Check if interface type is registered"""
        return (
            interface_type in self._singletons or 
            interface_type in self._transients
        )
    
    def get_configuration_manager(self) -> IConfigurationManager:
        """Get configuration manager instance"""
        return self.resolve(IConfigurationManager)
    
    def get_text_processing_logic(self) -> ITextProcessingBusinessLogic:
        """Get text processing business logic instance"""
        return self.resolve(ITextProcessingBusinessLogic)
    
    def get_database_service(self) -> IDatabaseService:
        """Get database service instance"""
        return self.resolve(IDatabaseService)


# Global container instance
_container: Optional[BusinessLogicContainer] = None


def get_container() -> BusinessLogicContainer:
    """Get global container instance"""
    global _container
    if _container is None:
        _container = BusinessLogicContainer()
    return _container


def set_container(container: BusinessLogicContainer) -> None:
    """Set global container instance"""
    global _container
    _container = container


def resolve(interface_type: Type[T]) -> T:
    """Resolve instance from global container"""
    return get_container().resolve(interface_type)


def get_configuration_manager() -> IConfigurationManager:
    """Get configuration manager from global container"""
    return get_container().get_configuration_manager()


def get_text_processing_logic() -> ITextProcessingBusinessLogic:
    """Get text processing business logic from global container"""
    return get_container().get_text_processing_logic()


def get_database_service() -> IDatabaseService:
    """Get database service from global container"""
    return get_container().get_database_service()