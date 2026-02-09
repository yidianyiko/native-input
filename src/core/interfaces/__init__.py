"""Core Interfaces Package

Defines abstract interfaces and contracts for the core layer.
"""

from .ai_interfaces import (
    IAIService,
    ICredentialManager,
)
from .configuration_interfaces import (
    IConfigurationManager,
    IConfigurationSection,
    ValidationResult,
)
from .system_interfaces import (
    IService,
    ServiceStatus,
    ServiceInfo,
    IServiceManager,
    IEventBus,
)
from .business_interfaces import (
    IBusinessLogicContainer,
    ITextProcessingBusinessLogic,
)
from .database_interfaces import (
    IDatabaseService,
    IDatabaseManager,
    IMigrationManager,
)

__all__ = [
    # AI interfaces
    'IAIService',
    'ICredentialManager',
    
    # Configuration interfaces
    'IConfigurationManager',
    'IConfigurationSection',
    'ValidationResult',
    
    # System interfaces
    'IService',
    'ServiceStatus',
    'ServiceInfo',
    'IServiceManager',
    'IEventBus',
    
    # Business interfaces
    'IBusinessLogicContainer',
    'ITextProcessingBusinessLogic',
    
    # Database interfaces
    'IDatabaseService',
    'IDatabaseManager',
    'IMigrationManager',
]