"""
Memory module for the Simple Agent Framework.

This module provides base memory interfaces and concrete implementations
for storing and retrieving message histories in agent conversations.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field

from simple_agent_framework.exceptions import MemoryError, ValidationError
from simple_agent_framework.message import Message


class BaseMemory(ABC):
    """
    Abstract base class for memory implementations.

    Memory is responsible for storing and retrieving conversation messages.
    """

    def __init__(self) -> None:
        """Initialize the memory with an empty messages list."""
        self.messages: List[Message] = []

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """
        Add a message to memory.

        Args:
            message: The message to add.

        Raises:
            MemoryError: If there's an error adding the message.
        """
        pass

    @abstractmethod
    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from memory.

        Args:
            limit: Maximum number of messages to return.
                If None, return all messages.

        Returns:
            List of messages.

        Raises:
            MemoryError: If there's an error retrieving messages.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all messages from memory.

        Raises:
            MemoryError: If there's an error clearing messages.
        """
        pass

    def get_recent_messages(self, count: int) -> List[Message]:
        """
        Get the most recent messages.

        Args:
            count: Number of recent messages to return.

        Returns:
            List of recent messages.

        Raises:
            ValidationError: If count is not a positive integer.
        """
        if not isinstance(count, int) or count <= 0:
            raise ValidationError(
                f"count must be a positive integer, got {count}"
            )
        return self.get_messages(limit=count)

    def to_json(self) -> str:
        """
        Serialize memory to JSON.

        Returns:
            JSON string representation of memory.
        """
        messages_data = [msg.to_dict() for msg in self.messages]
        return json.dumps({"messages": messages_data}, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls: Type[BaseMemory], json_str: str) -> BaseMemory:
        """
        Deserialize memory from JSON.

        Args:
            json_str: JSON string representation of memory.

        Returns:
            BaseMemory instance.

        Raises:
            ValidationError: If JSON parsing fails or data is invalid.
        """
        try:
            data = json.loads(json_str)
            memory = cls()
            for msg_data in data.get("messages", []):
                memory.add_message(Message.from_dict(msg_data))
            return memory
        except Exception as e:
            raise ValidationError(f"Failed to create memory from JSON: {e}")


class SimpleMemory(BaseMemory):
    """
    Simple in-memory implementation using a list with size limit.

    This implementation stores messages in a list and removes old messages
    when the maximum capacity is reached.

    Attributes:
        max_messages: Maximum number of messages to store.
    """

    def __init__(self, max_messages: int = 100) -> None:
        """
        Initialize SimpleMemory with a maximum message capacity.

        Args:
            max_messages: Maximum number of messages to store. Defaults to 100.

        Raises:
            ValidationError: If max_messages is not a positive integer.
        """
        super().__init__()

        if not isinstance(max_messages, int) or max_messages <= 0:
            raise ValidationError(
                f"max_messages must be a positive integer, got {max_messages}"
            )

        self.max_messages = max_messages

    def add_message(self, message: Message) -> None:
        """
        Add a message to memory.

        If the number of messages exceeds max_messages, remove the oldest message.

        Args:
            message: The message to add.

        Raises:
            ValidationError: If message is not a Message instance.
            MemoryError: If there's an error adding the message.
        """
        if not isinstance(message, Message):
            raise ValidationError(
                f"message must be a Message instance, got {type(message)}"
            )

        try:
            self.messages.append(message)

            # Remove oldest messages if we exceed the limit
            while len(self.messages) > self.max_messages:
                self.messages.pop(0)
        except Exception as e:
            raise MemoryError(f"Failed to add message to memory: {e}")

    def get_messages(self, limit: Optional[int] = None) -> List[Message]:
        """
        Get messages from memory.

        Args:
            limit: Maximum number of messages to return.
                If None, return all messages.

        Returns:
            List of messages (a copy to prevent external modification).

        Raises:
            ValidationError: If limit is not a positive integer or None.
            MemoryError: If there's an error retrieving messages.
        """
        if limit is not None and (not isinstance(limit, int) or limit <= 0):
            raise ValidationError(
                f"limit must be a positive integer or None, got {limit}"
            )

        try:
            if limit is None:
                return self.messages.copy()

            # Return a new list containing the most recent 'limit' messages
            start_idx = max(0, len(self.messages) - limit)
            return self.messages[start_idx:].copy()
        except Exception as e:
            raise MemoryError(f"Failed to get messages from memory: {e}")

    def clear(self) -> None:
        """
        Clear all messages from memory.

        Raises:
            MemoryError: If there's an error clearing messages.
        """
        try:
            self.messages.clear()
        except Exception as e:
            raise MemoryError(f"Failed to clear memory: {e}")

    def __len__(self) -> int:
        """
        Get the number of messages in memory.

        Returns:
            Number of messages.
        """
        return len(self.messages)

    def __str__(self) -> str:
        """
        Get string representation of memory.

        Returns:
            String representation.
        """
        return f"SimpleMemory(max_messages={self.max_messages}, messages={len(self.messages)})"
