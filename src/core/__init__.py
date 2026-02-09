"""Core Package

Provides core business logic, models, and interfaces for the reInput application.
This package contains the domain logic and abstractions that are independent
of external frameworks and UI concerns.
"""

# Import key components for easy access
from .business.configuration import ConfigurationBusinessLogic
from .business.text_processing import TextProcessingBusinessLogic

# Import models
from .models.ai_models import (
    ModelInfo,
    ModelConfiguration,
    ProviderCredentials,
    AgentConfiguration,
    ModelProvider,
    ModelStatus,
    ConnectionTestResult,
)

# Import exceptions
from .exceptions.ai_exceptions import (
    AIException,
    ModelException,
    ModelNotFoundError,
    AgentException,
    ProcessingException,
    CredentialException,
    ConnectionException,
)

# Import container and interfaces
from .container import (
    BusinessLogicContainer,
    get_container,
    set_container,
    resolve,
    get_configuration_manager,
    get_text_processing_logic,
)

__all__ = [
    # Business Logic
    "ConfigurationBusinessLogic",
    "TextProcessingBusinessLogic",
    # Models
    "ModelInfo",
    "ModelConfiguration",
    "ProviderCredentials",
    "AgentConfiguration",
    "ModelProvider",
    "ModelStatus",
    "ConnectionTestResult",
    # Exceptions
    "AIException",
    "ModelException",
    "ModelNotFoundError",
    "AgentException",
    "ProcessingException",
    "CredentialException",
    "ConnectionException",
    # Container
    "BusinessLogicContainer",
    "get_container",
    "set_container",
    "resolve",
    "get_configuration_manager",
    "get_text_processing_logic",
]