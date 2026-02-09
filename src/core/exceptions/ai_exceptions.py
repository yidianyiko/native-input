"""Core AI exceptions.

Defines custom exceptions for AI-related operations.
"""


class AIException(Exception):
    """Base exception for AI-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class ModelException(AIException):
    """Exception for model-related errors."""


class ModelNotFoundError(ModelException):
    """Exception raised when a requested model is not found."""
    
    def __init__(self, model_id: str):
        super().__init__(
            f"Model '{model_id}' not found",
            error_code="MODEL_NOT_FOUND",
            details={"model_id": model_id}
        )
        self.model_id = model_id


class ModelInitializationError(ModelException):
    """Exception raised when model initialization fails."""
    
    def __init__(self, model_id: str, reason: str = None):
        message = f"Failed to initialize model '{model_id}'"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message,
            error_code="MODEL_INIT_FAILED",
            details={"model_id": model_id, "reason": reason}
        )
        self.model_id = model_id
        self.reason = reason


class AgentException(AIException):
    """Exception for agent-related errors."""


class AgentNotFoundError(AgentException):
    """Exception raised when a requested agent is not found."""
    
    def __init__(self, agent_name: str):
        super().__init__(
            f"Agent '{agent_name}' not found",
            error_code="AGENT_NOT_FOUND",
            details={"agent_name": agent_name}
        )
        self.agent_name = agent_name


class AgentInitializationError(AgentException):
    """Exception raised when agent initialization fails."""
    
    def __init__(self, agent_name: str, reason: str = None):
        message = f"Failed to initialize agent '{agent_name}'"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message,
            error_code="AGENT_INIT_FAILED",
            details={"agent_name": agent_name, "reason": reason}
        )
        self.agent_name = agent_name
        self.reason = reason


class ProcessingException(AIException):
    """Exception for text processing errors."""


class ProcessingTimeoutError(ProcessingException):
    """Exception raised when text processing times out."""
    
    def __init__(self, timeout_seconds: int, agent_name: str = None):
        message = f"Processing timed out after {timeout_seconds} seconds"
        if agent_name:
            message += f" (agent: {agent_name})"
        
        super().__init__(
            message,
            error_code="PROCESSING_TIMEOUT",
            details={"timeout_seconds": timeout_seconds, "agent_name": agent_name}
        )
        self.timeout_seconds = timeout_seconds
        self.agent_name = agent_name


class ProcessingValidationError(ProcessingException):
    """Exception raised when processing request validation fails."""
    
    def __init__(self, validation_error: str, field: str = None):
        message = f"Processing validation failed: {validation_error}"
        if field:
            message += f" (field: {field})"
        
        super().__init__(
            message,
            error_code="PROCESSING_VALIDATION_FAILED",
            details={"validation_error": validation_error, "field": field}
        )
        self.validation_error = validation_error
        self.field = field


class CredentialException(AIException):
    """Exception for credential-related errors."""


class CredentialNotFoundError(CredentialException):
    """Exception raised when credentials are not found."""
    
    def __init__(self, provider: str):
        super().__init__(
            f"Credentials not found for provider '{provider}'",
            error_code="CREDENTIALS_NOT_FOUND",
            details={"provider": provider}
        )
        self.provider = provider


class CredentialValidationError(CredentialException):
    """Exception raised when credential validation fails."""
    
    def __init__(self, provider: str, reason: str = None):
        message = f"Invalid credentials for provider '{provider}'"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message,
            error_code="CREDENTIALS_INVALID",
            details={"provider": provider, "reason": reason}
        )
        self.provider = provider
        self.reason = reason


class ConnectionException(AIException):
    """Exception for connection-related errors."""


class ConnectionTimeoutError(ConnectionException):
    """Exception raised when connection times out."""
    
    def __init__(self, provider: str, timeout_seconds: int):
        super().__init__(
            f"Connection to '{provider}' timed out after {timeout_seconds} seconds",
            error_code="CONNECTION_TIMEOUT",
            details={"provider": provider, "timeout_seconds": timeout_seconds}
        )
        self.provider = provider
        self.timeout_seconds = timeout_seconds


class ConnectionRefusedError(ConnectionException):
    """Exception raised when connection is refused."""
    
    def __init__(self, provider: str, reason: str = None):
        message = f"Connection to '{provider}' was refused"
        if reason:
            message += f": {reason}"
        
        super().__init__(
            message,
            error_code="CONNECTION_REFUSED",
            details={"provider": provider, "reason": reason}
        )
        self.provider = provider
        self.reason = reason