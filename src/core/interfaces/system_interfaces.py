"""System Service Interfaces

Defines abstract interfaces for system services to provide
clear contracts and enable dependency injection.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass
from enum import Enum


class ServiceStatus(Enum):
    """Service status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """Service information"""
    name: str
    status: ServiceStatus
    version: Optional[str] = None
    description: Optional[str] = None
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class IService(ABC):
    """Base interface for all services"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get service name"""
    
    @property
    @abstractmethod
    def status(self) -> ServiceStatus:
        """Get current service status"""
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the service"""
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the service"""
    
    @abstractmethod
    def get_info(self) -> ServiceInfo:
        """Get service information"""
    
    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if service is healthy"""


class IServiceManager(ABC):
    """Interface for service management"""
    
    @abstractmethod
    def register_service(self, service: IService) -> bool:
        """Register a service"""
    
    @abstractmethod
    def unregister_service(self, _service_name: str) -> bool:
        """Unregister a service"""
    
    @abstractmethod
    def get_service(self, _service_name: str) -> Optional[IService]:
        """Get service by name"""
    
    @abstractmethod
    def get_all_services(self) -> List[IService]:
        """Get all registered services"""
    
    @abstractmethod
    async def start_service(self, _service_name: str) -> bool:
        """Start a specific service"""
    
    @abstractmethod
    async def stop_service(self, _service_name: str) -> bool:
        """Stop a specific service"""
    
    @abstractmethod
    async def start_all_services(self) -> bool:
        """Start all registered services"""
    
    @abstractmethod
    async def stop_all_services(self) -> bool:
        """Stop all registered services"""
    
    @abstractmethod
    def get_service_status(self, _service_name: str) -> Optional[ServiceStatus]:
        """Get service status"""
    
    @abstractmethod
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""


class IEventBus(ABC):
    """Interface for event bus system"""
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: callable) -> bool:
        """Subscribe to an event type"""
    
    @abstractmethod
    def unsubscribe(self, event_type: str, handler: callable) -> bool:
        """Unsubscribe from an event type"""
    
    @abstractmethod
    def publish(self, event_type: str, data: Any = None) -> bool:
        """Publish an event"""
    
    @abstractmethod
    def get_subscribers(self, event_type: str) -> List[callable]:
        """Get all subscribers for an event type"""


class ILogger(Protocol):
    """Logger protocol interface"""
    
    def debug(self, message: str, *_args, **_kwargs) -> None:
        """Log debug message"""
        ...
    
    def info(self, message: str, *_args, **_kwargs) -> None:
        """Log info message"""
        ...
    
    def warning(self, message: str, *_args, **_kwargs) -> None:
        """Log warning message"""
        ...
    
    def error(self, message: str, *_args, **_kwargs) -> None:
        """Log error message"""
        ...
    
    def critical(self, message: str, *_args, **_kwargs) -> None:
        """Log critical message"""
        ...