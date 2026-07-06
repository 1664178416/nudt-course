"""
Exception classes for the Simple Agent Framework.

This module defines the base exception and specific exceptions used throughout
the framework. All framework-specific exceptions should inherit from AgentException.
"""


class AgentException(Exception):
    """Base exception for all agent framework errors.
    
    Attributes:
        message: Error message describing the exception.
    """
    
    def __init__(self, message: str) -> None:
        """Initialize AgentException with an error message.
        
        Args:
            message: Error message describing the exception.
        """
        super().__init__(message)
        self.message = message


class ConfigurationError(AgentException):
    """Raised when there's an error in framework configuration."""
    pass


class LLMError(AgentException):
    """Raised when there's an error in LLM communication or processing."""
    pass


class ToolError(AgentException):
    """Raised when there's an error in tool execution or registration."""
    pass


class MemoryError(AgentException):
    """Raised when there's an error in memory operations."""
    pass


class SessionError(AgentException):
    """Raised when there's an error in session management or execution."""
    pass


class ValidationError(AgentException):
    """Raised when data validation fails."""
    pass
