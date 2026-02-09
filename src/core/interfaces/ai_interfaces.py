"""Core AI interfaces and abstract base classes.

Simplified interfaces for Agno-based AI services.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any, List


class IAIService(ABC):
    """
    Simplified interface for AI service.
    Replaces the complex multi-layer architecture with a single unified interface.
    """
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the AI service."""
    
    @abstractmethod
    def process_text(self, text: str, agent_name: str = "translation") -> Optional[str]:
        """Process text using specified agent."""
    
    @abstractmethod
    def get_available_agents(self) -> List[str]:
        """Get list of available agent names."""
    
    @abstractmethod
    def switch_model(self, model_id: str) -> bool:
        """Switch to a different model."""
    
    @abstractmethod
    def get_current_model(self) -> Optional[str]:
        """Get current model ID."""
    
    @abstractmethod
    def get_available_models(self) -> Dict[str, Any]:
        """Get all available models."""
    
    @abstractmethod
    def test_connection(self, model_or_provider: str) -> bool:
        """Test connection to a model or provider."""
    
    @abstractmethod
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update service settings."""


class ICredentialManager(ABC):
    """Interface for credential management - kept for auth services."""
    
    @abstractmethod
    def get_api_key_for_model(self, model_id: str) -> Optional[str]:
        """Get API key for a specific model."""
    
    @abstractmethod
    def has_credentials(self, provider: str) -> bool:
        """Check if credentials exist for a provider."""
    
    @abstractmethod
    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """Update credential settings."""
