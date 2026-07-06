## simple_agent_framework/agent.py
```python
"""
Agent module for the Simple Agent Framework.

This module defines the core agent classes that interact with LLMs,
manage memory, and utilize tools to perform tasks. The BaseAgent provides
an abstract interface that can be extended to create custom agents.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from simple_agent_framework.exceptions import (
    AgentException,
    LLMError,
    ToolError,
    ValidationError,
)
from simple_agent_framework.llm import LLMClient
from simple_agent_framework.memory import BaseMemory
from simple_agent_framework.message import Message
from simple_agent_framework.tools import (
    Tool,
    ToolRegistry,
    get_default_tool_registry,
)

# Configure module logger
logger = logging.getLogger(__name__)


class AgentConfig(BaseModel):
    """Configuration model for agent instances.

    Attributes:
        name: Unique name identifier for the agent.
        system_prompt: System prompt defining the agent's role and behavior.
        llm_client: LLM client for generating responses.
        memory: Memory instance for storing conversation history.
        tool_registry: Registry for accessing available tools.
        tools: Initial list of tools (function names or Tool instances).
        max_context_length: Maximum number of messages to include in context.
    """

    model_config = ConfigDict(
        frozen=False,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        extra="ignore",
    )

    name: str = Field(
        ...,
        description="Unique name identifier for the agent.",
        min_length=1,
    )
    system_prompt: str = Field(
        default="You are a helpful AI assistant.",
        description="System prompt defining the agent's role and behavior.",
    )
    llm_client: LLMClient = Field(
        ...,
        description="LLM client for generating responses.",
    )
    memory: BaseMemory = Field(
        ...,
        description="Memory instance for storing conversation history.",
    )
    tool_registry: ToolRegistry = Field(
        default_factory=get_default_tool_registry,
        description="Registry for accessing available tools.",
    )
    tools: List[Union[str, Tool]] = Field(
        default_factory=list,
        description="Initial list of tools (function names or Tool instances).",
    )
    max_context_length: Optional[int] = Field(
        default=10,
        ge=1,
        description="Maximum number of messages to include in context.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate agent name.

        Args:
            v: Agent name.

        Returns:
            Validated name.

        Raises:
            ValueError: If name is empty.
        """
        if not v.strip():
            raise ValueError("Agent name cannot be empty or whitespace")
        return v.strip()

    @field_validator("llm_client")
    @classmethod
    def validate_llm_client(cls, v: Any) -> LLMClient:
        """Validate LLM client.

        Args:
            v: LLM client instance.

        Returns:
            Validated LLM client.

        Raises:
            ValueError: If not a valid LLMClient instance.
        """
        if not isinstance(v, LLMClient):
            raise ValueError(
                f"llm_client must be an instance of LLMClient, got {type(v)}"
            )
        return v

    @field_validator("memory")
    @classmethod
    def validate_memory(cls, v: Any) -> BaseMemory:
        """Validate memory instance.

        Args:
            v: Memory instance.

        Returns:
            Validated memory instance.

        Raises:
            ValueError: If not a valid BaseMemory instance.
        """
        if not isinstance(v, BaseMemory):
            raise ValueError(
                f"memory must be an instance of BaseMemory, got {type(v)}"
            )
        return v


class BaseAgent(ABC):
    """Abstract base class for all agents.

    This class defines the interface and common functionality for agents.
    Agents are responsible for processing messages, generating responses,
    managing memory, and utilizing tools.

    Attributes:
        config: Configuration object for the agent.
        _tool_registry: Internal reference to tool registry.
        _tools: List of tool names available to this agent.
    """

    def __init__(self, config: AgentConfig) -> None:
        """Initialize the agent with configuration.

        Args:
            config: Agent configuration.

        Raises:
            ValidationError: If configuration is invalid.
        """
        if not isinstance(config, AgentConfig):
            raise ValidationError(
                f"config must be an instance of AgentConfig, got {type(config)}"
            )

        self.config = config
        self._tool_registry = config.tool_registry
        self._tools: List[str] = []

        # Initialize tools from config
        for tool_ref in config.tools:
            if isinstance(tool_ref, str):
                # Tool name reference
                if not self._tool_registry.has_tool(tool_ref):
                    raise ValidationError(
                        f"Tool '{tool_ref}' not found in registry"
                    )
                self._tools.append(tool_ref)
            elif isinstance(tool_ref, Tool):
                # Tool instance
                self._tool_registry.register_tool(tool_ref)
                self._tools.append(tool_ref.name)
            else:
                raise ValidationError(
                    f"Tool must be string or Tool instance, got {type(tool_ref)}"
                )

    @property
    def name(self) -> str:
        """Get agent name.

        Returns:
            Agent name.
        """
        return self.config.name

    @property
    def system_prompt(self) -> str:
        """Get system prompt.

        Returns:
            System prompt.
        """
        return self.config.system_prompt

    @property
    def llm_client(self) -> LLMClient:
        """Get LLM client.

        Returns:
            LLM client instance.
        """
        return self.config.llm_client

    @property
    def memory(self) -> BaseMemory:
        """Get memory instance.

        Returns:
            Memory instance.
        """
        return self.config.memory

    async def respond(self, messages: List[Message]) -> Message:
        """Generate a response to a list of messages.

        This is a lower-level method that directly processes message lists.
        It's useful for scenarios where you have pre-formatted message sequences.

        Args:
            messages: List of Message objects representing the conversation.

        Returns:
            Message object containing the agent's response.

        Raises:
            LLMError: If there's an error generating the response.
            AgentException: For other agent-related errors.
        """
        try:
            # Process messages (add system prompt, format for LLM)
            processed_messages = await self._process_messages(messages)

            # Generate completion (handles tool calls if needed)
            response_data = await self._create_chat_completion(
                processed_messages
            )

            # Extract the response content
            response_content = self._extract_response_content(response_data)

            # Create response message
            response_message = Message(
                role="assistant",
                content=response_content,
                agent_name=self.name,
                metadata={
                    "response_data": response_data,
                    "tools_used": response_data.get("tools_used", []),
                },
            )

            return response_message

        except LLMError:
            raise
        except Exception as e:
            raise AgentException(f"Failed to generate response: {e}")

    async def generate_response(
        self,
        input_text: str,
        context: Optional[List[Message]] = None,
    ) -> Message:
        """Generate a response to input text with context.

        This is the main high-level method for generating responses.
        It handles memory interaction, context processing, and response generation.

        Args:
            input_text: Input text from user or other agent.
            context: Optional additional context messages.
                If None, uses recent messages from memory.

        Returns:
            Message object containing the agent's response.

        Raises:
            LLMError: If there's an error generating the response.
            AgentException: For other agent-related errors.
        """
        try:
            # Get recent messages from memory
            recent_messages = self.memory.get_messages(
                limit=self.config.max_context_length
            )

            # Combine context if provided
            all_messages = recent_messages.copy()
            if context:
                all_messages.extend(context)

            # Create user message
            user_message = Message(
                role="user",
                content=input_text,
                agent_name="user",  # Default agent name for user input
            )

            # Add to message list for processing
            messages_to_process = all_messages + [user_message]

            # Generate response
            response = await self.respond(messages_to_process)

            # Store both user message and response in memory
            self.memory.add_message(user_message)
            self.memory.add_message(response)

            return response

        except Exception as e:
            raise AgentException(f"Failed to generate response: {e}")

    def add_tool(self, tool: Union[str, Tool, Callable[..., Any]]) -> None:
        """Add a tool to the agent's available tools.

        Args:
            tool: Tool to add. Can be:
                - String: Name of tool in registry
                - Tool instance: Tool object
                - Callable: Function to register as tool

        Raises:
            ToolError: If tool cannot be added.
            ValidationError: If tool is invalid.
        """
        try:
            if isinstance(tool, str):
                # Tool name reference
                if not self._tool_registry.has_tool(tool):
                    raise ToolError(f"Tool '{tool}' not found in registry")
                if tool not in self._tools:
                    self._tools.append(tool)

            elif isinstance(tool, Tool):
                # Tool instance
                self._tool_registry.register_tool(tool)
                if tool.name not in self._tools:
                    self._tools.append(tool.name)

            elif callable(tool):
                # Callable function
                tool_obj = Tool.from_function(tool)
                self._tool_registry.register_tool(tool_obj)
                if tool_obj.name not in self._tools:
                    self._tools.append(tool_obj.name)

            else:
                raise ValidationError(
                    f"Tool must be string, Tool, or callable, got {type(tool)}"
                )

        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Failed to add tool: {e}")

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get descriptions of all available tools.

        Returns:
            List of dictionaries containing tool descriptions.
        """
        available_tools = []
        for tool_name in self._tools:
            try:
                tool = self._tool_registry.get_tool(tool_name)
                tool_description = {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                    "is_async": tool.is_async,
                }
                if tool.returns:
                    tool_description["returns"] = tool.returns
                available_tools.append(tool_description)
            except ToolError:
                # Log warning for tools that are no longer in registry
                logger.warning(
                    f"Tool '{tool_name}' registered to agent '{self.name}' "
                    f"but not found in registry. Skipping."
                )
                continue

        return available_tools

    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool from the agent's available tools.

        Args:
            tool_name: Name of the tool to remove.

        Raises:
            ToolError: If tool is not in agent's tool list.
        """
        if tool_name not in self._tools:
            raise ToolError(
                f"Tool '{tool_name}' is not in agent '{self.name}' tool list"
            )
        self._tools.remove(tool_name)

    def clear_tools(self) -> None:
        """Clear all tools from the agent's available tools."""
        self._tools.clear()

    @abstractmethod
    async def _process_messages(
        self,
        messages: List[Message],
    ) -> List[Dict[str, Any]]:
        """Process messages for LLM consumption.

        This method prepares messages for the LLM API, including:
        - Adding system prompt
        - Converting Message objects to API format
        - Adding tool descriptions if tools are available

        Args:
            messages: List of Message objects.

        Returns:
            List of dictionaries in LLM API format.

        Raises:
            AgentException: If message processing fails.
        """
        pass

    @abstractmethod
    async def _create_chat_completion(
        self,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Create chat completion with tool calling support.

        This method handles the complete tool calling workflow:
        1. Send messages to LLM (with tool descriptions if available)
        2. Check if LLM wants to use a tool
        3. Execute the tool if requested
        4. Send tool result back to LLM for final response

        Args:
            messages: List of message dictionaries in LLM API format.

        Returns:
            Dictionary containing completion response and metadata.

        Raises:
            LLMError: If LLM call fails.
            ToolError: If tool execution fails.
        """
        pass

    def _extract_response_content(self, response_data: Dict[str, Any]) -> str:
        """Extract response content from LLM response data.

        Args:
            response_data: LLM response dictionary.

        Returns:
            Response content as string.

        Raises:
            LLMError: If response format is invalid.
        """
        try:
            choices = response_data.get("choices", [])
            if not choices:
                raise LLMError("No choices in LLM response")

            first_choice = choices[0]
            message = first_choice.get("message", {})

            content = message.get("content")
            if content is None:
                raise LLMError("No content in LLM response message")

            return str(content)

        except Exception as e:
            raise LLMError(f"Failed to extract response content: {e}")

    async def _handle_tool_calls(
        self,
        llm_response: Dict[str, Any],
        current_messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Handle tool calls from LLM response.

        Args:
            llm_response: LLM response dictionary.
            current_messages: Current message history.

        Returns:
            Final response dictionary after handling tool calls.

        Raises:
            ToolError: If tool execution fails.
        """
        choices = llm_response.get("choices", [])
        if not choices:
            return llm_response

        first_choice = choices[0]
        message = first_choice.get("message", {})

        # Check for tool calls in the response
        # Note: In initial version, we use a simple approach where tool calls
        # are indicated by special formatting in the content or metadata
        # For future versions, integrate with OpenAI's official function calling
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return llm_response

        # Initialize tools_used list
        tools_used = []
        tool_results_messages = []

        # Execute each tool call
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args_str = tool_call.get("arguments", "{}")

            # Parse arguments if they're a string
            if isinstance(tool_args_str, str):
                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    raise ToolError(
                        f"Failed to parse tool arguments for '{tool_name}': "
                        f"invalid JSON - {tool_args_str}"
                    )
            else:
                tool_args = tool_args_str

            if not tool_name:
                continue

            try:
                # Get the tool
                tool_obj = self._tool_registry.get_tool(tool_name)

                # Execute the tool
                logger.debug(
                    f"Agent '{self.name}' executing tool '{tool_name}' "
                    f"with args: {tool_args}"
                )
                if tool_obj.is_async:
                    tool_result = await tool_obj.function(**tool_args)
                else:
                    tool_result = tool_obj.function(**tool_args)

                # Record tool usage
                tools_used.append({
                    "name": tool