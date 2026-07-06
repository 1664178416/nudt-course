"""
LLM client module for the Simple Agent Framework.

This module provides abstract and concrete implementations of LLM clients
for interacting with various language model APIs.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from pydantic import BaseModel, ConfigDict, Field, field_validator

from simple_agent_framework.exceptions import LLMError, ValidationError
from simple_agent_framework.message import Message


class LLMConfig(BaseModel):
    """Configuration model for LLM clients.
    
    Attributes:
        api_key: API key for authentication.
        base_url: Base URL for the API endpoint.
        model: Model name to use for completions.
        max_tokens: Maximum number of tokens to generate.
        temperature: Sampling temperature (0.0 to 2.0).
        top_p: Top-p sampling parameter.
        frequency_penalty: Frequency penalty parameter.
        presence_penalty: Presence penalty parameter.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
    """
    
    model_config = ConfigDict(
        frozen=False,
        arbitrary_types_allowed=False,
        validate_assignment=True,
        extra="ignore"
    )
    
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication. If None, uses OPENAI_API_KEY environment variable."
    )
    base_url: Optional[str] = Field(
        default=None,
        description="Base URL for the API endpoint. If None, uses OpenAI's default."
    )
    model: str = Field(
        default="gpt-3.5-turbo",
        description="Model name to use for completions"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        ge=1,
        le=4096,
        description="Maximum number of tokens to generate"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0 to 2.0)"
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Top-p sampling parameter"
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty parameter"
    )
    presence_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Presence penalty parameter"
    )
    timeout: float = Field(
        default=30.0,
        gt=0,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        description="Maximum number of retry attempts"
    )
    
    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key format.
        
        Args:
            v: API key value
            
        Returns:
            Validated API key
            
        Raises:
            ValueError: If API key is invalid
        """
        if v is not None and not isinstance(v, str):
            raise ValueError(f"api_key must be a string or None, got {type(v)}")
        return v
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate base URL format.
        
        Args:
            v: Base URL value
            
        Returns:
            Validated base URL
            
        Raises:
            ValueError: If base_url format is invalid
        """
        if v is not None:
            if not isinstance(v, str):
                raise ValueError(f"base_url must be a string or None, got {type(v)}")
            if not v.startswith(('http://', 'https://')):
                raise ValueError('base_url must start with http:// or https://')
            return v.rstrip('/')
        return v
    
    @field_validator('model')
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate model name.
        
        Args:
            v: Model name
            
        Returns:
            Validated model name
            
        Raises:
            ValueError: If model name is empty
        """
        if not v or not isinstance(v, str):
            raise ValueError(f"model must be a non-empty string, got {v}")
        return v


class LLMClient(ABC):
    """Abstract base class for LLM clients.
    
    This class defines the interface for LLM clients and should be
    subclassed to implement specific LLM provider integrations.
    
    Attributes:
        config: Configuration object for the LLM client.
    """
    
    def __init__(self, config: LLMConfig) -> None:
        """Initialize the LLM client with configuration.
        
        Args:
            config: Configuration object for the LLM client.
            
        Raises:
            ValidationError: If configuration is invalid.
        """
        if not isinstance(config, LLMConfig):
            raise ValidationError(
                f"config must be an instance of LLMConfig, got {type(config)}"
            )
        
        self.config = config
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate a chat completion from a list of messages.
        
        Args:
            messages: List of Message objects representing the conversation history.
            **kwargs: Additional parameters to override default configuration.
            
        Returns:
            Dictionary containing the completion response.
            
        Raises:
            LLMError: If there's an error generating the completion.
        """
        pass
    
    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a chat completion from a list of messages.
        
        Args:
            messages: List of Message objects representing the conversation history.
            **kwargs: Additional parameters to override default configuration.
            
        Yields:
            Dictionary chunks from the streaming response.
            
        Raises:
            LLMError: If there's an error generating the completion.
        """
        pass
    
    def _prepare_messages_for_api(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert Message objects to API-compatible format.
        
        Args:
            messages: List of Message objects.
            
        Returns:
            List of dictionaries in API-compatible format.
        """
        api_messages: List[Dict[str, Any]] = []
        for msg in messages:
            api_msg: Dict[str, Any] = {
                "role": msg.role,
                "content": msg.content
            }
            # Add agent_name as 'name' field if available (OpenAI API supports this)
            if msg.agent_name:
                api_msg["name"] = msg.agent_name
            api_messages.append(api_msg)
        return api_messages
    
    @abstractmethod
    async def close(self) -> None:
        """Close the underlying client resources.
        
        This method should be called when the client is no longer needed
        to clean up resources properly.
        """
        pass
    
    async def __aenter__(self) -> LLMClient:
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()


class OpenAIClient(LLMClient):
    """OpenAI API client implementation.
    
    This class implements the LLMClient interface for the OpenAI API.
    
    Attributes:
        config: Configuration object for the OpenAI client.
        _client: Internal OpenAI async client instance.
    """
    
    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        **kwargs: Any
    ) -> None:
        """Initialize the OpenAI client.
        
        Args:
            config: Configuration object for the OpenAI client.
                If None, a default config will be created using kwargs.
            **kwargs: Configuration parameters for creating LLMConfig.
            
        Examples:
            >>> # Using config object
            >>> config = LLMConfig(api_key="sk-...", model="gpt-4")
            >>> client = OpenAIClient(config)
            
            >>> # Using direct parameters
            >>> client = OpenAIClient(
            ...     api_key="sk-...",
            ...     model="gpt-4",
            ...     temperature=0.7
            ... )
        """
        if config is None:
            config = LLMConfig(**kwargs)
        elif kwargs:
            # Update config with provided kwargs using Pydantic's model_copy
            config = config.model_copy(update=kwargs)
        
        super().__init__(config)
        self._client: Optional[AsyncOpenAI] = None
    
    @property
    def client(self) -> AsyncOpenAI:
        """Get or create the OpenAI async client.
        
        Returns:
            AsyncOpenAI client instance.
        """
        if self._client is None:
            client_kwargs: Dict[str, Any] = {
                "api_key": self.config.api_key,
                "timeout": self.config.timeout,
                "max_retries": self.config.max_retries
            }
            
            if self.config.base_url:
                client_kwargs["base_url"] = self.config.base_url
            
            self._client = AsyncOpenAI(**client_kwargs)
        
        return self._client
    
    async def chat_completion(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Generate a chat completion using OpenAI API.
        
        Args:
            messages: List of Message objects representing the conversation history.
            **kwargs: Additional parameters to override default configuration.
            
        Returns:
            Dictionary containing the completion response from OpenAI.
            
        Raises:
            LLMError: If there's an error calling the OpenAI API.
        """
        try:
            # Prepare messages for API
            api_messages = self._prepare_messages_for_api(messages)
            
            # Prepare completion parameters
            completion_params = self._prepare_completion_params(stream=False, **kwargs)
            
            # Convert to ChatCompletionMessageParam format expected by OpenAI
            chat_messages: List[ChatCompletionMessageParam] = [
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    **({"name": msg["name"]} if "name" in msg else {})
                }
                for msg in api_messages
            ]
            
            # Create chat completion
            response: ChatCompletion = await self.client.chat.completions.create(
                messages=chat_messages,
                **completion_params
            )
            
            # Convert response to dictionary
            return response.model_dump()
            
        except Exception as e:
            raise LLMError(f"OpenAI API error: {str(e)}")
    
    async def chat_completion_stream(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a chat completion using OpenAI API.
        
        Args:
            messages: List of Message objects representing the conversation history.
            **kwargs: Additional parameters to override default configuration.
            
        Yields:
            Dictionary chunks from the streaming response.
            
        Raises:
            LLMError: If there's an error calling the OpenAI API.
        """
        try:
            # Prepare messages for API
            api_messages = self._prepare_messages_for_api(messages)
            
            # Prepare completion parameters
            completion_params = self._prepare_completion_params(stream=True, **kwargs)
            
            # Convert to ChatCompletionMessageParam format expected by OpenAI
            chat_messages: List[ChatCompletionMessageParam] = [
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    **({"name": msg["name"]} if "name" in msg else {})
                }
                for msg in api_messages
            ]
            
            # Create streaming chat completion
            stream = await self.client.chat.completions.create(
                messages=chat_messages,
                **completion_params
            )
            
            # Yield each chunk
            async for chunk in stream:
                yield chunk.model_dump()
                
        except Exception as e:
            raise LLMError(f"OpenAI API streaming error: {str(e)}")
    
    def _prepare_completion_params(
        self,
        stream: bool,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Prepare completion parameters for OpenAI API.
        
        Args:
            stream: Whether to stream the response.
            **kwargs: Additional parameters to override defaults.
            
        Returns:
            Dictionary of completion parameters.
        """
        # Start with config defaults
        params: Dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            "stream": stream
        }
        
        # Add max_tokens if specified in config
        if self.config.max_tokens is not None:
            params["max_tokens"] = self.config.max_tokens
        
        # Override with any provided kwargs (only allowed keys)
        allowed_keys = {
            "model", "temperature", "top_p", "frequency_penalty", 
            "presence_penalty", "max_tokens", "stop", "user", "n",
            "logprobs", "top_logprobs", "seed"
        }
        
        for key, value in kwargs.items():
            if key in allowed_keys:
                params[key] = value
        
        # Filter out None values as OpenAI API may not accept them
        return {k: v for k, v in params.items() if v is not None}
    
    async def close(self) -> None:
        """Close the underlying OpenAI client.
        
        Note: The AsyncOpenAI client doesn't have an explicit close method
        in the current OpenAI library version. We clean up the reference
        to allow proper garbage collection.
        """
        self._client = None
