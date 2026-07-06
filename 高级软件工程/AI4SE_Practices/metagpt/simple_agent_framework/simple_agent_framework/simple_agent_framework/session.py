## simple_agent_framework/session.py

```python
"""
Session module for the Simple Agent Framework.

This module provides the Session class for managing multi-agent conversations.
It coordinates multiple agents, handles message routing, and maintains shared
memory for the conversation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple

from simple_agent_framework.agent import BaseAgent
from simple_agent_framework.exceptions import SessionError, ValidationError
from simple_agent_framework.memory import BaseMemory, SimpleMemory
from simple_agent_framework.message import Message


# Configure module logger
logger = logging.getLogger(__name__)


class Session:
    """
    Manages multi-agent conversations and coordinates message passing.

    The Session class orchestrates conversations between multiple agents,
    handling message routing, turn-taking, and maintaining shared conversation
    memory.

    Attributes:
        agents: List of agents participating in the session.
        shared_memory: BaseMemory instance for storing conversation history.
        _agent_index: Current agent index for round-robin selection.
        _active: Whether the session is currently active (running).
        _conclusion_checker: Function to check if conversation has concluded.
    """

    def __init__(
        self,
        agents: Optional[List[BaseAgent]] = None,
        shared_memory: Optional[BaseMemory] = None,
        conclusion_checker: Optional[Callable[[Message, Session], bool]] = None,
    ) -> None:
        """
        Initialize a new session with agents and shared memory.

        Args:
            agents: List of agents participating in the session.
                Defaults to empty list.
            shared_memory: Shared memory for storing conversation history.
                Defaults to SimpleMemory with 1000 message capacity.
            conclusion_checker: Custom function to check if conversation
                has concluded. Should accept (response: Message,
                session: Session) and return bool.

        Raises:
            ValidationError: If agents or shared_memory are invalid types.
            SessionError: If session initialization fails.
        """
        try:
            # Validate and set agents
            if agents is None:
                agents = []
            elif not isinstance(agents, list):
                raise ValidationError(
                    f"agents must be a list, got {type(agents)}"
                )

            # Validate each agent
            for i, agent in enumerate(agents):
                if not isinstance(agent, BaseAgent):
                    raise ValidationError(
                        f"agent at index {i} must be an instance of BaseAgent, "
                        f"got {type(agent)}"
                    )

            self.agents = agents.copy()

            # Validate and set shared memory
            if shared_memory is None:
                shared_memory = SimpleMemory(max_messages=1000)
            elif not isinstance(shared_memory, BaseMemory):
                raise ValidationError(
                    f"shared_memory must be an instance of BaseMemory, "
                    f"got {type(shared_memory)}"
                )

            self.shared_memory = shared_memory

            # Set conclusion checker
            if conclusion_checker and not callable(conclusion_checker):
                raise ValidationError(
                    "conclusion_checker must be a callable function"
                )
            self._conclusion_checker = conclusion_checker

            # Initialize session state
            self._agent_index = 0
            self._active = False

            logger.debug(
                f"Session initialized with {len(self.agents)} agents and "
                f"{shared_memory.__class__.__name__}"
            )

        except ValidationError:
            raise
        except Exception as e:
            raise SessionError(f"Failed to initialize session: {e}")

    async def run(
        self,
        task: str,
        max_turns: int = 10,
    ) -> str:
        """
        Run a multi-agent conversation to complete a task.

        Args:
            task: The task description or initial message to start the conversation.
            max_turns: Maximum number of conversation turns to execute.
                Defaults to 10.

        Returns:
            The final result or summary of the conversation as a string.

        Raises:
            ValidationError: If parameters are invalid.
            SessionError: If session execution fails.

        Examples:
            >>> session = Session(agents=[agent1, agent2])
            >>> result = await session.run("Analyze the market trends")
        """
        # Validate parameters
        if not isinstance(task, str) or not task.strip():
            raise ValidationError(
                f"task must be a non-empty string, got {type(task)}"
            )

        if not isinstance(max_turns, int) or max_turns <= 0:
            raise ValidationError(
                f"max_turns must be a positive integer, got {max_turns}"
            )

        if not self.agents:
            raise SessionError("No agents available in the session")

        try:
            self._active = True

            # Create initial user message
            initial_message = Message(
                role="user",
                content=task,
                agent_name="user",
                metadata={"task": task, "is_initial": True, "turn": 0}
            )

            # Add initial message to shared memory
            self.shared_memory.add_message(initial_message)

            logger.info(
                f"Starting session with task: '{task[:50]}{'...' if len(task) > 50 else ''}' "
                f"and {len(self.agents)} agents"
            )

            # Run conversation loop
            current_turn = 0
            final_response = None

            while current_turn < max_turns and self._active:
                try:
                    # Select next agent
                    current_agent = self._select_next_agent()

                    # Get recent messages from shared memory for context
                    recent_messages = self.shared_memory.get_messages(
                        limit=min(20, max_turns * 2)  # Reasonable context limit
                    )

                    # Prepare input: use the most recent non-system message content
                    input_text = task  # Default to original task
                    for msg in reversed(recent_messages):
                        if msg.role != "system":
                            input_text = msg.content
                            break

                    logger.debug(
                        f"Turn {current_turn + 1}/{max_turns}: "
                        f"Agent '{current_agent.name}' responding to: '{input_text[:100]}{'...' if len(input_text) > 100 else ''}'"
                    )

                    # Generate response from current agent
                    response = await current_agent.generate_response(
                        input_text=input_text,
                        context=recent_messages
                    )

                    # Ensure response has correct metadata
                    response.agent_name = current_agent.name
                    response.metadata = response.metadata or {}
                    response.metadata.update({
                        "turn": current_turn + 1,
                        "speaker": current_agent.name,
                        "is_final": False
                    })

                    # Add response to shared memory
                    self.shared_memory.add_message(response)

                    # Broadcast response to other agents
                    broadcast_responses = await self._broadcast_to_agents(response)

                    # Add broadcast responses to shared memory
                    for broadcast_response in broadcast_responses:
                        self.shared_memory.add_message(broadcast_response)

                    # Check if conversation should conclude
                    should_conclude = False
                    if self._conclusion_checker:
                        try:
                            should_conclude = self._conclusion_checker(response, self)
                        except Exception as e:
                            logger.warning(f"Conclusion checker error: {e}")

                    # Check for explicit conclusion in response metadata
                    if response.metadata.get("conversation_complete", False):
                        should_conclude = True

                    # Store final response for return
                    final_response = response

                    # Increment turn counter
                    current_turn += 1

                    # Check stopping conditions
                    if should_conclude:
                        logger.info(f"Conversation concluded by conclusion checker at turn {current_turn}")
                        break

                    # Small delay to prevent tight loops in async context
                    await asyncio.sleep(0.01)

                except Exception as e:
                    logger.error(f"Error in conversation turn {current_turn + 1}: {e}")
                    # Decide whether to continue or break based on error severity
                    if isinstance(e, (SessionError, ValidationError)):
                        raise
                    # For other errors, log and continue if possible
                    continue

            # Mark final response if exists
            if final_response:
                final_response.metadata["is_final"] = True

            # Extract final result
            if final_response:
                result = final_response.content
                logger.info(f"Session completed after {current_turn} turns")
            else:
                result = "Conversation did not produce a final result."
                logger.warning("Session completed without final response")

            self._active = False
            return result

        except Exception as e:
            self._active = False
            raise SessionError(f"Session execution failed: {e}")

    async def run_stream(
        self,
        task: str,
        max_turns: int = 10,
    ) -> AsyncGenerator[str, None]:
        """
        Run a multi-agent conversation with streaming output.

        Args:
            task: The task description or initial message to start the conversation.
            max_turns: Maximum number of conversation turns to execute.

        Yields:
            Streaming output chunks from the conversation.

        Raises:
            ValidationError: If parameters are invalid.
            SessionError: If session execution fails.
        """
        # Validate parameters (same as run method)
        if not isinstance(task, str) or not task.strip():
            raise ValidationError(
                f"task must be a non-empty string, got {type(task)}"
            )

        if not isinstance(max_turns, int) or max_turns <= 0:
            raise ValidationError(
                f"max_turns must be a positive integer, got {max_turns}"
            )

        if not self.agents:
            raise SessionError("No agents available in the session")

        try:
            self._active = True

            # Create initial user message
            initial_message = Message(
                role="user",
                content=task,
                agent_name="user",
                metadata={"task": task, "is_initial": True, "turn": 0}
            )

            self.shared_memory.add_message(initial_message)
            yield f"Session started with task: {task}\n\n"

            current_turn = 0

            while current_turn < max_turns and self._active:
                current_agent = self._select_next_agent()
                recent_messages = self.shared_memory.get_messages(limit=20)

                # Prepare input
                input_text = task
                for msg in reversed(recent_messages):
                    if msg.role != "system":
                        input_text = msg.content
                        break

                yield f"\n[Turn {current_turn + 1}] {current_agent.name} is responding...\n"

                # Generate response (simplified for streaming - actual implementation
                # would need to integrate with agent's streaming capabilities)
                response = await current_agent.generate_response(
                    input_text=input_text,
                    context=recent_messages
                )

                response.agent_name = current_agent.name
                response.metadata = response.metadata or {}
                response.metadata.update({
                    "turn": current_turn + 1,
                    "speaker": current_agent.name
                })

                self.shared_memory.add_message(response)

                # Yield the response
                yield f"{current_agent.name}: {response.content}\n"

                # Broadcast to other agents
                broadcast_responses = await self._broadcast_to_agents(response)
                for broadcast_response in broadcast_responses:
                    self.shared_memory.add_message(broadcast_response)

                # Check conclusion
                should_conclude = False
                if self._conclusion_checker:
                    try:
                        should_conclude = self._conclusion_checker(response, self)
                    except Exception as e:
                        logger.warning(f"Conclusion checker error: {e}")

                if response.metadata.get("conversation_complete", False):
                    should_conclude = True

                current_turn += 1

                if should_conclude:
                    yield "\nConversation concluded.\n"
                    break

                await asyncio.sleep(0.01)

            self._active = False
            yield f"\nSession completed after {current_turn} turns.\n"

        except Exception as e:
            self._active = False
            raise SessionError(f"Streaming session execution failed: {e}")

    def add_agent(self, agent: BaseAgent) -> None:
        """
        Add an agent to the session.

        Args:
            agent: Agent instance to add.

        Raises:
            ValidationError: If agent is not a BaseAgent instance.
            SessionError: If session is currently active.
        """
        if not isinstance(agent, BaseAgent):
            raise ValidationError(
                f"agent must be an instance of BaseAgent, got {type(agent)}"
            )

        if self._active:
            raise SessionError("Cannot add agents while session is active")

        # Check for duplicate agent names
        existing_names = {a.name for a in self.agents}
        if agent.name in existing_names:
            logger.warning(
                f"Agent with name '{agent.name}' already exists in session. "
                f"Adding anyway (agents should have unique names)."
            )

        self.agents.append(agent)
        logger.debug(f"Added agent '{agent.name}' to session")

    def get_message_history(self) -> List[Message]:
        """
        Get the complete message history from shared memory.

        Returns:
            List of all messages in the conversation.
        """
        return self.shared_memory.get_messages(limit=None)

    def clear_history(self) -> None:
        """
        Clear the conversation history from shared memory.

        Raises:
            SessionError: If session is currently active.
        """
        if self._active:
            raise SessionError("Cannot clear history while session is active")

        self.shared_memory.clear()
        logger.debug("Cleared session message history")

    def _select_next_agent(self) -> BaseAgent:
        """
        Select the next agent to speak using round-robin algorithm.

        Returns:
            The next agent in rotation.

        Raises:
            SessionError: If no agents are available.
        """
        if not self.agents:
            raise SessionError("No agents available for selection")

        # Simple round-robin selection
        agent = self.agents[self._agent_index]
        self._agent_index = (self._agent_index + 1) % len(self.agents)

        return agent

    async def _broadcast_to_agents(self, message: Message) -> List[Message]:
        """
        Broadcast a message to all agents except the sender.

        This method adds the message to each agent's personal memory,
        allowing them to be aware of the conversation context.

        Args:
            message: The message to broadcast.

        Returns:
            List of any automatic responses generated by agents upon receiving
            the broadcast. This allows for reactive/interrupt-style responses.

        Note:
            In the initial implementation, this simply adds the message to
            each agent's memory without generating immediate responses.
            Future versions could implement interrupt mechanisms.
        """
        responses = []
        sender_name = message.agent_name

        for agent in self.agents:
            # Skip the sender
            if agent.name == sender_name:
                continue

            try:
                # Add message to agent's personal memory
                agent.memory.add_message(message)

                # Optional: Generate automatic response based on message
                # This could be implemented for reactive agents
                # For now, we just log the broadcast
                logger.debug(
                    f"Broadcast message from '{sender_name}' to agent '{agent.name}'"
                )

            except Exception as e:
                logger.error(
                    f"Failed to broadcast message to agent '{agent.name}': {e}"
                )

        return responses

    def stop(self) -> None:
        """
        Stop the session gracefully.

        This sets the active flag to False, which will cause the
        conversation loop to exit on the next iteration.
        """
        if self._active:
            logger.info("Stopping session gracefully")
            self._active = False

    def is_active(self) -> bool:
        """
        Check if the session is currently active.

        Returns:
            True if session is active, False otherwise.
        """
        return self._active

    def get_agent_names(self) -> List[str]:
        """
        Get names of all agents in the session.

        Returns:
            List of agent names.
        """
        return [agent.name for agent in self.agents]

    def __len__(self) -> int:
        """
        Get the number of agents in the session.

        Returns:
            Number of agents.
        """
        return len(self.agents)

    def __str__(self) -> str:
        """
        Get string representation of the session.

        Returns:
            String representation.
        """
        agent_names = ", ".join(self.get_agent_names())
        return f"Session(agents=[{agent_names}], active={self._active}, messages={len(self.shared_memory