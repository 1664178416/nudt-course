```python
"""
Unit tests for the agent module of Simple Agent Framework.

This module contains comprehensive tests for:
- BaseAgent and SimpleAgent initialization
- Response generation methods
- Tool management functionality
- Memory interaction
- Error handling and edge cases

Note: These tests use mocking extensively to isolate agent behavior
from external dependencies (LLM, memory, tools).
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from simple_agent_framework.agent import AgentConfig, BaseAgent, SimpleAgent
from simple_agent_framework.exceptions import (
    AgentException,
    LLMError,
    ToolError,
    ValidationError,
)
from simple_agent_framework.llm import LLMClient, LLMConfig
from simple_agent_framework.memory import BaseMemory, SimpleMemory
from simple_agent_framework.message import Message
from simple_agent_framework.tools import Tool, ToolRegistry

# =============================================================================
# Test Fixtures and Mock Objects
# =============================================================================


class MockLLMClient(LLMClient):
    """Mock LLM client for testing agent interactions."""

    def __init__(self, config: LLMConfig) -> None:
        super().__init__(config)
        self.chat_completion_calls = []
        self.chat_completion_responses = []
        self.stream_responses = []
        self.close_called = False

    async def chat_completion(
        self, messages: List[Message], **kwargs: Any
    ) -> Dict[str, Any]:
        """Mock chat completion that records calls and returns configured responses."""
        self.chat_completion_calls.append((messages, kwargs))
        if self.chat_completion_responses:
            return self.chat_completion_responses.pop(0)
        return {
            "id": "test-chat-completion-123",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": self.config.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Mock response from LLM",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }

    async def chat_completion_stream(
        self, messages: List[Message], **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Mock streaming chat completion."""
        # Record the call
        self.chat_completion_calls.append((messages, kwargs))
        # Yield pre-configured chunks
        for chunk in self.stream_responses:
            yield chunk
            await asyncio.sleep(0.001)

    async def close(self) -> None:
        """Mark close as called."""
        self.close_called = True


class MockMemory(BaseMemory):
    """Mock memory for testing agent memory interactions."""

    def __init__(self) -> None:
        super().__init__()
        self.messages: List[Message] = []
        self.add_message_calls = []
        self.get_messages_calls = []
        self.clear_calls = 0

    def add_message(self, message: Message) -> None:
        """Add message and record the call."""
        self.add_message_calls.append(message)
        self.messages.append(message)

    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Get messages and record the call."""
        self.get_messages_calls.append(limit)
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:] if limit <= len(self.messages) else self.messages.copy()

    def clear(self) -> None:
        """Clear memory and record the call."""
        self.clear_calls += 1
        self.messages.clear()


class MockToolRegistry(ToolRegistry):
    """Mock tool registry for testing tool interactions."""

    def __init__(self) -> None:
        super().__init__()
        self._tools: Dict[str, Tool] = {}
        self.register_tool_calls = []
        self.get_tool_calls = []
        self.get_tools_descriptions_calls = []
        self.list_tools_calls = []
        self.has_tool_calls = []
        self.unregister_tool_calls = []
        self.clear_calls = []

    def register_tool(
        self,
        tool: Any,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Register tool and record the call."""
        self.register_tool_calls.append((tool, name, description))
        if isinstance(tool, Tool):
            self._tools[tool.name] = tool
        elif callable(tool):
            # Simulate Tool.from_function behavior for a mock
            tool_name = name or tool.__name__
            mock_tool = Tool(
                name=tool_name,
                function=tool,
                description=description or f"Mock tool {tool_name}",
                parameters={},
                returns="",
                is_async=asyncio.iscoroutinefunction(tool),
            )
            self._tools[tool_name] = mock_tool
        else:
            # Handle other cases if needed, or raise like the real registry might
            pass

    def get_tool(self, name: str) -> Tool:
        """Get tool and record the call."""
        self.get_tool_calls.append(name)
        if name not in self._tools:
            raise ToolError(f"Tool '{name}' not found")
        return self._tools[name]

    def get_tools_descriptions(self) -> List[Dict[str, Any]]:
        """Get tool descriptions and record the call."""
        self.get_tools_descriptions_calls.append(())
        return [
            {
                "name": name,
                "description": tool.description,
                "parameters": tool.parameters,
                "is_async": tool.is_async,
            }
            for name, tool in self._tools.items()
        ]

    def list_tools(self) -> List[str]:
        """List tools and record the call."""
        self.list_tools_calls.append(())
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if tool exists and record the call."""
        self.has_tool_calls.append(name)
        return name in self._tools

    def unregister_tool(self, name: str) -> None:
        """Unregister tool and record the call."""
        self.unregister_tool_calls.append(name)
        if name in self._tools:
            del self._tools[name]

    def clear(self) -> None:
        """Clear registry and record the call."""
        self.clear_calls.append(())
        self._tools.clear()


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing abstract methods."""
    
    def __init__(self, config: AgentConfig) -> None:
        super().__init__(config)
        self.processed_messages_history = []
        self.chat_completion_history = []
    
    async def _process_messages(
        self,
        messages: List[Message],
    ) -> List[Dict[str, Any]]:
        """Concrete implementation for testing."""
        self.processed_messages_history.append(messages)
        
        # Simple processing: convert messages to dict format
        processed = []
        for msg in messages:
            msg_dict = {
                "role": msg.role,
                "content": msg.content,
            }
            if msg.agent_name:
                msg_dict["name"] = msg.agent_name
            processed.append(msg_dict)
        
        return processed
    
    async def _create_chat_completion(
        self,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Concrete implementation for testing."""
        self.chat_completion_history.append(messages)
        
        # Use the LLM client to generate response
        # Convert dict messages back to Message objects for the mock LLM
        message_objects = [
            Message(
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                agent_name=msg.get("name"),
            )
            for msg in messages
        ]
        
        return await self.llm_client.chat_completion(message_objects)


@pytest.fixture
def mock_llm_config() -> LLMConfig:
    """Create a mock LLM configuration for testing."""
    return LLMConfig(
        api_key="test-api-key",
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=500,
    )


@pytest.fixture
def mock_llm_client(mock_llm_config: LLMConfig) -> MockLLMClient:
    """Create a mock LLM client for testing."""
    return MockLLMClient(mock_llm_config)


@pytest.fixture
def mock_memory() -> MockMemory:
    """Create a mock memory for testing."""
    return MockMemory()


@pytest.fixture
def mock_tool_registry() -> MockToolRegistry:
    """Create a mock tool registry for testing."""
    return MockToolRegistry()


@pytest.fixture
def mock_tool() -> Tool:
    """Create a mock tool for testing."""
    return Tool(
        name="mock_tool",
        function=lambda x: x,
        description="A mock tool for testing",
        parameters={"x": {"type": "Any", "required": True}},
        returns="The input value",
        is_async=False,
    )


@pytest.fixture
def valid_agent_config(
    mock_llm_client: MockLLMClient,
    mock_memory: MockMemory,
    mock_tool_registry: MockToolRegistry,
) -> AgentConfig:
    """Create a valid agent configuration for testing."""
    return AgentConfig(
        name="TestAgent",
        system_prompt="You are a test agent. Be helpful.",
        llm_client=mock_llm_client,
        memory=mock_memory,
        tool_registry=mock_tool_registry,
        tools=[],
        max_context_length=10,
    )


@pytest.fixture
def simple_agent(valid_agent_config: AgentConfig) -> SimpleAgent:
    """Create a SimpleAgent instance for testing."""
    return SimpleAgent(valid_agent_config)


@pytest.fixture
def concrete_test_agent(valid_agent_config: AgentConfig) -> ConcreteTestAgent:
    """Create a ConcreteTestAgent instance for testing."""
    return ConcreteTestAgent(valid_agent_config)


# =============================================================================
# Test Agent Initialization
# =============================================================================


class TestAgentInitialization:
    """Test cases for agent initialization and configuration."""

    def test_agent_config_creation(self, valid_agent_config: AgentConfig) -> None:
        """Test that AgentConfig can be created with valid parameters."""
        assert valid_agent_config.name == "TestAgent"
        assert valid_agent_config.system_prompt == "You are a test agent. Be helpful."
        assert isinstance(valid_agent_config.llm_client, LLMClient)
        assert isinstance(valid_agent_config.memory, BaseMemory)
        assert isinstance(valid_agent_config.tool_registry, ToolRegistry)
        assert valid_agent_config.tools == []
        assert valid_agent_config.max_context_length == 10

    def test_agent_config_defaults(self) -> None:
        """Test AgentConfig defaults when not specified."""
        mock_llm_client = MockLLMClient(LLMConfig(api_key="test"))
        mock_memory = SimpleMemory()

        config = AgentConfig(
            name="TestAgent",
            llm_client=mock_llm_client,
            memory=mock_memory,
        )

        assert config.name == "TestAgent"
        assert config.system_prompt == "You are a helpful AI assistant."
        assert config.llm_client == mock_llm_client
        assert config.memory == mock_memory
        assert config.tools == []
        assert config.max_context_length == 10

    def test_agent_config_validation_name(self) -> None:
        """Test AgentConfig name validation."""
        mock_llm_client = MockLLMClient(LLMConfig(api_key="test"))
        mock_memory = SimpleMemory()

        # Empty name should raise ValueError
        with pytest.raises(ValueError, match="Agent name cannot be empty or whitespace"):
            AgentConfig(
                name="",
                llm_client=mock_llm_client,
                memory=mock_memory,
            )

        # Whitespace-only name should raise ValueError
        with pytest.raises(ValueError, match="Agent name cannot be empty or whitespace"):
            AgentConfig(
                name="   ",
                llm_client=mock_llm_client,
                memory=mock_memory,
            )

        # Name with leading/trailing whitespace should be stripped
        config = AgentConfig(
            name="  TestAgent  ",
            llm_client=mock_llm_client,
            memory=mock_memory,
        )
        assert config.name == "TestAgent"

    def test_agent_config_validation_llm_client(self) -> None:
        """Test AgentConfig LLM client validation."""
        mock_memory = SimpleMemory()

        # Invalid LLM client type should raise ValueError
        with pytest.raises(ValueError, match="llm_client must be an instance of LLMClient"):
            AgentConfig(
                name="TestAgent",
                llm_client="not an llm client",  # type: ignore
                memory=mock_memory,
            )

    def test_agent_config_validation_memory(self) -> None:
        """Test AgentConfig memory validation."""
        mock_llm_client = MockLLMClient(LLMConfig(api_key="test"))

        # Invalid memory type should raise ValueError
        with pytest.raises(ValueError, match="memory must be an instance of BaseMemory"):
            AgentConfig(
                name="TestAgent",
                llm_client=mock_llm_client,
                memory="not a memory",  # type: ignore
            )

    def test_base_agent_initialization_valid_config(
        self, valid_agent_config: AgentConfig
    ) -> None:
        """Test BaseAgent initialization with valid configuration."""
        # Use SimpleAgent since BaseAgent is abstract
        agent = SimpleAgent(valid_agent_config)

        assert agent.config == valid_agent_config
        assert agent.name == "TestAgent"
        assert agent.system_prompt == "You are a test agent. Be helpful."
        assert agent.llm_client == valid_agent_config.llm_client
        assert agent.memory == valid_agent_config.memory
        assert agent._tool_registry == valid_agent_config.tool_registry
        assert agent._tools == []

    def test_base_agent_initialization_invalid_config(self) -> None:
        """Test BaseAgent initialization with invalid configuration."""
        # Use SimpleAgent since BaseAgent is abstract
        with pytest.raises(ValidationError, match="config must be an instance of AgentConfig"):
            SimpleAgent("not a config")  # type: ignore

    def test_base_agent_initialization_with_tools(
        self,
        valid_agent_config: AgentConfig,
        mock_tool: Tool,
        mock_tool_registry: MockToolRegistry,
    ) -> None:
        """Test BaseAgent initialization with tools in configuration."""
        # Register mock tool in registry
        mock_tool_registry.register_tool(mock_tool)

        # Create config with tool reference
        config = AgentConfig(
            name="TestAgent",
            system_prompt="You are a test agent.",
            llm_client=valid_agent_config.llm_client,
            memory=valid_agent_config.memory,
            tool_registry=mock_tool_registry,
            tools=[mock_tool.name],  # Add tool by name
        )

        agent = SimpleAgent(config)

        assert mock_tool.name in agent._tools
        assert len(agent._tools) == 1
        # Verify the tool registry was queried
        assert mock_tool.name in mock_tool_registry.has_tool_calls

    def test_base_agent_initialization_with_tool_instance(
        self,
        valid_agent_config: AgentConfig,
        mock_tool: Tool,
        mock_tool_registry: MockToolRegistry,
    ) -> None:
        """Test BaseAgent initialization with Tool instance in configuration."""
        # Create config with Tool instance
        config = AgentConfig(
            name="TestAgent",
            system_prompt="You are a test agent.",
            llm_client=valid_agent_config.llm_client,
            memory=valid_agent_config