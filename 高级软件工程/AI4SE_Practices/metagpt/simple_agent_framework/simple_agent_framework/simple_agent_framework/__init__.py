"""
Simple Agent Framework.

A lightweight, modular framework for building and orchestrating multi-agent systems
with LLM integration, memory management, and tool usage.

Features:
    - 🤖 Modular agent design with base classes for easy customization
    - 🗣️ Session management for multi-agent conversations
    - 🧠 Flexible memory systems (in-memory, with potential for extensions)
    - 🔧 Tool registry for extending agent capabilities
    - ⚡ Async-first architecture for high performance
    - 🔌 LLM client abstraction supporting multiple providers

Core Components:
    - Agent: Base and simple agent implementations
    - Session: Manages multi-agent conversations and turn-taking
    - LLM: Abstract and concrete clients for language model APIs
    - Memory: Storage for conversation history and agent state
    - Tools: Registry and utilities for extending agent capabilities

Example:
    