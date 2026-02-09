"""Core AI models and data structures.

Defines the core data models used throughout the AI system.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class ModelProvider(Enum):
    """AI model providers."""
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    GATEWAY = "gateway"


class ModelStatus(Enum):
    """Model availability status."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    TESTING = "testing"


@dataclass
class ModelInfo:
    """Information about an AI model."""
    id: str
    name: str
    provider: ModelProvider
    description: Optional[str] = None
    max_tokens: Optional[int] = None
    supports_streaming: bool = True
    cost_per_token: Optional[float] = None
    status: ModelStatus = ModelStatus.AVAILABLE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderCredentials:
    """Credentials for an AI provider."""
    provider: ModelProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """Check if credentials are valid (have required fields)."""
        return bool(self.api_key and self.api_key.strip())


@dataclass
class ModelConfiguration:
    """Configuration for a specific model."""
    model_info: ModelInfo
    credentials: Optional[ProviderCredentials] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def is_usable(self) -> bool:
        """Check if model can be used (has valid credentials)."""
        return (
            self.model_info.status == ModelStatus.AVAILABLE and
            self.credentials is not None and
            self.credentials.is_valid()
        )


@dataclass
class AgentConfiguration:
    """Configuration for an AI agent."""
    name: str
    display_name: str
    prompt: str
    enabled: bool = True
    model_requirements: Optional[List[str]] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    
    def supports_model(self, model_id: str) -> bool:
        """Check if agent supports a specific model."""
        if not self.model_requirements:
            return True  # No specific requirements
        return model_id in self.model_requirements


@dataclass
class ConnectionTestResult:
    """Result of a connection test."""
    provider: ModelProvider
    model_id: Optional[str]
    success: bool
    response_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    test_timestamp: Optional[str] = None
    
    def __str__(self) -> str:
        status = "Success" if self.success else "Failed"
        if self.model_id:
            return f"{status} - {self.provider.value}/{self.model_id}"
        return f"{status} - {self.provider.value}"