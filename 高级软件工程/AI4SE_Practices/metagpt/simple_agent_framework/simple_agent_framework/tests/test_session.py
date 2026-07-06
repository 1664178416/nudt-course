```python
"""
Unit tests for the session module of Simple Agent Framework.

This module contains comprehensive tests for:
- Session initialization and configuration
- Multi-agent conversation management
- Message broadcasting and routing
- Session state management
- Session execution (run and run_stream methods)
- Error handling and edge cases
- Custom conclusion checkers

Note: These tests use mocking extensively to isolate session behavior
from external dependencies (agents, memory, etc.).
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch, call

import pytest

from simple_agent_framework.agent import AgentConfig, BaseAgent
from simple_agent_framework.exceptions import SessionError, ValidationError
from simple_agent_framework.memory import BaseMemory, SimpleMemory
from simple_agent_framework.message import Message
from simple_agent_framework.session import Session


# =============================================================================
# Mock Classes for Testing
# =============================================================================


class MockAgent(BaseAgent):
    """Mock agent for testing session interactions."""

    def __init__(
        self,
        name: str = "MockAgent",
        memory: Optional[BaseMemory] = None,
        system_prompt: str = "Mock system prompt",
        generate_response_behavior: str = "normal",
        raise_exception: bool = False,
    ) -> None:
        """Initialize mock agent with proper config structure."""
        # Create mock components
        mock_llm_client = MagicMock()
        mock_memory = memory or SimpleMemory()
        mock_tool_registry = MagicMock()
        
        # Create proper config
        mock_config = AgentConfig(
            name=name,
            system_prompt=system_prompt,
            llm_client=mock_llm_client,
            memory=mock_memory,
            tool_registry=mock_tool_registry,
            tools=[],
            max_context_length=10
        )
        
        # Initialize parent class
        super().__init__(mock_config)
        
        # Override config to use our mock (since AgentConfig is immutable)
        self._config = mock_config
        
        # Track calls
        self.generate_response_calls = []
        self.respond_calls = []
        self.add_message_to_memory_calls = []
        
        # Behavior control
        self.generate_response_behavior = generate_response_behavior
        self.raise_exception = raise_exception
        
        # Tool-related attributes
        self._tool_registry = mock_tool_registry

    @property
    def name(self) -> str:
        """Get agent name from config."""
        return self.config.name

    @property
    def memory(self) -> BaseMemory:
        """Get agent memory from config."""
        return self.config.memory

    @property
    def system_prompt(self) -> str:
        """Get system prompt from config."""
        return self.config.system_prompt

    async def generate_response(
        self,
        input_text: str,
        context: Optional[List[Message]] = None,
    ) -> Message:
        """Mock generate_response with configurable behavior."""
        self.generate_response_calls.append((input_text, context))
        
        if self.raise_exception:
            raise SessionError("Mock agent exception")
        
        # Create response based on behavior
        if self.generate_response_behavior == "normal":
            content = f"Mock response from {self.name} to: {input_text[:50]}..."
        elif self.generate_response_behavior == "conclusion":
            content = f"Final response from {self.name}. Goodbye."
        elif self.generate_response_behavior == "empty":
            content = ""
        else:
            content = f"Response from {self.name}"
        
        response = Message(
            role="assistant",
            content=content,
            agent_name=self.name,
            metadata={
                "turn": len(self.generate_response_calls),
                "mock_response": True,
                "conversation_complete": self.generate_response_behavior == "conclusion",
            },
        )
        
        # Simulate adding to memory (optional, can be mocked)
        if hasattr(self.memory, 'add_message'):
            self.memory.add_message(response)
            self.add_message_to_memory_calls.append(response)
        
        return response

    async def respond(self, messages: List[Message]) -> Message:
        """Mock respond method."""
        self.respond_calls.append(messages)
        last_content = messages[-1].content if messages else "No input"
        return await self.generate_response(last_content, messages)

    # Override abstract methods with mock implementations
    async def _process_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Mock _process_messages."""
        return [{"role": "user", "content": "mock"}]

    async def _create_chat_completion(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Mock _create_chat_completion."""
        return {"choices": [{"message": {"content": "mock"}}]}


class MockMemory(BaseMemory):
    """Mock memory for testing session memory interactions."""

    def __init__(self, max_messages: int = 100, raise_exception: bool = False) -> None:
        """Initialize mock memory with configurable behavior."""
        super().__init__()
        self.messages: List[Message] = []
        self.add_message_calls = []
        self.get_messages_calls = []
        self.clear_calls = []
        self.raise_exception = raise_exception
        self.max_messages = max_messages

    def add_message(self, message: Message) -> None:
        """Mock add_message that records calls."""
        if self.raise_exception:
            raise SessionError("Mock memory exception")
        self.add_message_calls.append(message)
        self.messages.append(message)
        
        # Simulate max_messages limit
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """Mock get_messages that records calls."""
        if self.raise_exception:
            raise SessionError("Mock memory exception")
        self.get_messages_calls.append(limit)
        if limit is None:
            return self.messages.copy()
        return self.messages[-limit:] if limit <= len(self.messages) else self.messages.copy()

    def clear(self) -> None:
        """Mock clear that records calls."""
        if self.raise_exception:
            raise SessionError("Mock memory exception")
        self.clear_calls.append(())
        self.messages.clear()


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_memory() -> MockMemory:
    """Create a mock memory for testing."""
    return MockMemory()


@pytest.fixture
def mock_agent_1() -> MockAgent:
    """Create first mock agent for testing."""
    return MockAgent(name="Agent1")


@pytest.fixture
def mock_agent_2() -> MockAgent:
    """Create second mock agent for testing."""
    return MockAgent(name="Agent2")


@pytest.fixture
def mock_agent_3() -> MockAgent:
    """Create third mock agent for testing."""
    return MockAgent(name="Agent3")


@pytest.fixture
def mock_agents(
    mock_agent_1: MockAgent,
    mock_agent_2: MockAgent,
    mock_agent_3: MockAgent,
) -> List[MockAgent]:
    """Create a list of mock agents for testing."""
    return [mock_agent_1, mock_agent_2, mock_agent_3]


@pytest.fixture
def session_with_agents(
    mock_agents: List[MockAgent],
    mock_memory: MockMemory,
) -> Session:
    """Create a session with mock agents and memory."""
    return Session(agents=mock_agents, shared_memory=mock_memory)


@pytest.fixture
def empty_session() -> Session:
    """Create an empty session for testing."""
    return Session()


@pytest.fixture
def session_with_faulty_memory(
    mock_agents: List[MockAgent],
) -> Session:
    """Create a session with memory that raises exceptions."""
    return Session(agents=mock_agents, shared_memory=MockMemory(raise_exception=True))


@pytest.fixture
def session_with_faulty_agent(
    mock_memory: MockMemory,
) -> Session:
    """Create a session with an agent that raises exceptions."""
    faulty_agent = MockAgent(name="FaultyAgent", raise_exception=True)
    return Session(agents=[faulty_agent], shared_memory=mock_memory)


# =============================================================================
# Test Session Initialization
# =============================================================================


class TestSessionInitialization:
    """Test cases for session initialization and configuration."""

    def test_session_creation_default(self) -> None:
        """Test session creation with default parameters."""
        session = Session()
        
        assert session.agents == []
        assert isinstance(session.shared_memory, SimpleMemory)
        assert session.shared_memory.max_messages == 1000
        assert session._agent_index == 0
        assert not session._active
        assert session._conclusion_checker is None

    def test_session_creation_with_agents(
        self,
        mock_agents: List[MockAgent],
        mock_memory: MockMemory,
    ) -> None:
        """Test session creation with custom agents and memory."""
        session = Session(agents=mock_agents, shared_memory=mock_memory)
        
        assert session.agents == mock_agents
        assert session.shared_memory == mock_memory
        assert session._agent_index == 0
        assert len(session) == 3

    def test_session_creation_with_conclusion_checker(self) -> None:
        """Test session creation with custom conclusion checker."""
        def custom_checker(response: Message, session: Session) -> bool:
            return True
        
        session = Session(conclusion_checker=custom_checker)
        
        assert session._conclusion_checker is custom_checker

    def test_session_creation_empty_agent_list(self) -> None:
        """Test session creation with empty agent list."""
        session = Session(agents=[])
        
        assert session.agents == []
        assert len(session) == 0

    def test_session_creation_invalid_agents_type(self) -> None:
        """Test session creation with invalid agents type."""
        with pytest.raises(ValidationError, match="agents must be a list"):
            Session(agents="not a list")  # type: ignore

    def test_session_creation_invalid_agent_type(self) -> None:
        """Test session creation with invalid agent type in list."""
        with pytest.raises(ValidationError, match="must be an instance of BaseAgent"):
            Session(agents=["not an agent"])  # type: ignore

    def test_session_creation_invalid_memory_type(self) -> None:
        """Test session creation with invalid memory type."""
        with pytest.raises(ValidationError, match="must be an instance of BaseMemory"):
            Session(shared_memory="not a memory")  # type: ignore

    def test_session_creation_invalid_conclusion_checker_type(self) -> None:
        """Test session creation with invalid conclusion checker type."""
        with pytest.raises(ValidationError, match="conclusion_checker must be a callable function"):
            Session(conclusion_checker="not callable")  # type: ignore

    def test_session_repr_string(self, session_with_agents: Session) -> None:
        """Test session string representation."""
        session_str = str(session_with_agents)
        
        assert "Session" in session_str
        assert "Agent1" in session_str
        assert "Agent2" in session_str
        assert "Agent3" in session_str
        assert "active=False" in session_str


# =============================================================================
# Test Agent Management
# =============================================================================


class TestAgentManagement:
    """Test cases for session agent management."""

    def test_add_agent_to_session(
        self,
        empty_session: Session,
        mock_agent_1: MockAgent,
    ) -> None:
        """Test adding an agent to an empty session."""
        empty_session.add_agent(mock_agent_1)
        
        assert len(empty_session) == 1
        assert empty_session.agents[0] == mock_agent_1
        assert empty_session.get_agent_names() == ["Agent1"]

    def test_add_agent_to_existing_session(
        self,
        session_with_agents: Session,
        mock_agent_1: MockAgent,
    ) -> None:
        """Test adding an agent to a session with existing agents."""
        initial_count = len(session_with_agents)
        
        # Create a new agent with a different name
        new_agent = MockAgent(name="NewAgent")
        session_with_agents.add_agent(new_agent)
        
        assert len(session_with_agents) == initial_count + 1
        assert new_agent in session_with_agents.agents
        assert "NewAgent" in session_with_agents.get_agent_names()

    def test_add_agent_with_duplicate_name(
        self,
        session_with_agents: Session,
    ) -> None:
        """Test adding an agent with duplicate name (should warn but allow)."""
        # Create another agent with same name as existing agent
        duplicate_agent = MockAgent(name="Agent1")
        
        # Capture warning
        with patch.object(sys.modules[__name__], 'logger') as mock_logger:
            session_with_agents.add_agent(duplicate_agent)
            
            # Verify warning was logged
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "already exists" in warning_msg
            assert "Agent1" in warning_msg
        
        assert len(session_with_agents) == 4  # Original 3 + duplicate
        assert duplicate_agent in session_with_agents.agents

    def test_add_agent_invalid_type(self, empty_session: Session) -> None:
        """Test adding an invalid agent type."""
        with pytest.raises(ValidationError, match="must be an instance of BaseAgent"):
            empty_session.add_agent("not an agent")  # type: ignore

    def test_add_agent_to_active_session(
        self,
        session_with_agents: Session,
        mock_agent_1: MockAgent,
    ) -> None:
        """Test adding an agent to an active session (should fail)."""
        # Mark session as active
        session_with_agents._active = True
        
        with pytest.raises(SessionError, match="Cannot add agents while session is active"):
            session_with_agents.add_agent(mock_agent_1)

    def test_get_agent_names(self, session_with_agents: Session) -> None:
        """Test getting agent names from session."""
        names = session_with_agents.get_agent_names()
        
        assert names == ["Agent1", "Agent2", "Agent3"]
        assert len(names) == len(session_with_agents)

    def test_session_len(self, session_with_agents: Session) -> None:
        """Test session length property."""
        assert len(session_with_agents) == 3


# =============================================================================
# Test Session State Management
# =============================================================================


class TestSessionStateManagement:
    """Test cases for session state management."""

    def test_session_active_state(self, session_with_agents: Session) -> None:
        """Test session active state management."""
        # Initially not active
        assert not session_with_agents.is_active()
        assert session_with_agents._active is False
        
        # Set to active
        session_with_agents._active = True
        assert session_with_agents.is_active()
        
        # Set back to inactive
        session_with_agents._active = False
        assert not session_with_agents.is_active()

    def test_session_stop_method(self, session_with_agents: Session) -> None:
        """Test session stop method."""
        # Set session as active
        session_with_agents._active = True
        assert session_with_agents.is_active()
        
        # Stop the session
        session_with_agents.stop()
        
        assert not session_with_agents.is_active()
        assert session_with_agents._active is False

    def test_session_stop_when_already_inactive(self, session_with_agents: Session) -> None:
        """Test stopping a session that is already inactive."""
        # Session is initially inactive
        assert not session_with_agents.is_active()
        
        # Stop should not raise an error
        session_with_agents.stop()
        
        # Should still be inactive
        assert not session_with_agents.is_active()


# =============================================================================
# Test Message History Management
# =============================================================================


class TestMessageHistoryManagement:
    """Test cases for session message history management."""

    def test_get_message_history_empty(self, empty_session: Session) -> None:
        """Test getting message history from empty session