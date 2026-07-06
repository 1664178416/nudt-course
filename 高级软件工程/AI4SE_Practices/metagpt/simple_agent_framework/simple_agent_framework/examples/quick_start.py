"""
Quick start example for Simple Agent Framework.

This example demonstrates the most basic usage of the framework:
1. Creating an LLM client
2. Creating an agent with memory
3. Running a simple conversation with the agent
4. Creating a session with multiple agents for more complex interactions

Prerequisites:
    - OpenAI API key set as environment variable OPENAI_API_KEY
    - Required packages installed: pydantic, aiohttp, openai

Note: This example uses a mock LLM client for demonstration purposes
to avoid actual API calls. Set use_mock=True to test without API key.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from simple_agent_framework.agent import AgentConfig, SimpleAgent
from simple_agent_framework.llm import LLMClient, LLMConfig, OpenAIClient
from simple_agent_framework.memory import SimpleMemory
from simple_agent_framework.message import Message
from simple_agent_framework.session import Session


class MockLLMClient(LLMClient):
    """Mock LLM client for demonstration without actual API calls.
    
    This client inherits from LLMClient to ensure interface compatibility.
    """
    
    def __init__(self, config: LLMConfig) -> None:
        """Initialize mock client with configuration."""
        super().__init__(config)
    
    async def chat_completion(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> Dict[str, Any]:
        """Return a mock completion response."""
        # Extract content from the last message for context
        last_message_content = ""
        if messages:
            last_message = messages[-1]
            last_message_content = last_message.content[:100]  # Use last message, truncated
        
        # Generate mock response based on input
        if last_message_content:
            response_text = f"Mock response to: {last_message_content}..."
        else:
            response_text = "Hello! I'm a mock AI assistant. How can I help you?"
        
        return {
            "id": "mock-chat-completion-123",
            "object": "chat.completion",
            "created": int(datetime.now().timestamp()),
            "model": self.config.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
        }
    
    async def chat_completion_stream(
        self,
        messages: List[Message],
        **kwargs: Any
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Mock streaming completion."""
        response_text = "Mock streaming response"
        for i, char in enumerate(response_text):
            yield {
                "id": "mock-chat-completion-stream-123",
                "object": "chat.completion.chunk",
                "created": int(datetime.now().timestamp()),
                "model": self.config.model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": char},
                    "finish_reason": None if i < len(response_text) - 1 else "stop"
                }]
            }
            await asyncio.sleep(0.01)  # Simulate streaming delay
    
    async def close(self) -> None:
        """Close mock client."""
        pass


async def single_agent_example(use_mock: bool = True) -> None:
    """
    Example with a single agent having a conversation.
    
    Args:
        use_mock: Whether to use mock LLM client for demonstration.
    """
    print("=" * 60)
    print("SINGLE AGENT EXAMPLE")
    print("=" * 60)
    
    try:
        # 1. Create LLM client configuration
        llm_config = LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY", "mock-key") if not use_mock else "mock-key",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500
        )
        
        # 2. Create LLM client
        if use_mock:
            llm_client = MockLLMClient(llm_config)
        else:
            llm_client = OpenAIClient(config=llm_config)
        
        # 3. Create memory for the agent
        memory = SimpleMemory(max_messages=50)
        
        # 4. Create agent configuration
        agent_config = AgentConfig(
            name="Assistant",
            system_prompt="You are a helpful AI assistant. Be concise and friendly.",
            llm_client=llm_client,
            memory=memory,
            tools=[],  # Empty list, no tools for this example
            max_context_length=10
        )
        
        # 5. Create the agent
        agent = SimpleAgent(agent_config)
        
        print(f"Created agent: {agent.name}")
        print(f"System prompt: {agent.system_prompt[:50]}...")
        print("-" * 40)
        
        # 6. Have a conversation with the agent
        conversation_topics = [
            "Hello! Can you introduce yourself?",
            "What's the weather like today?",
            "Can you help me write a simple Python function?",
            "Thank you for your help!"
        ]
        
        for topic in conversation_topics:
            print(f"You: {topic}")
            
            # Generate response
            response = await agent.generate_response(topic)
            
            print(f"{agent.name}: {response.content}")
            print("-" * 40)
        
        # 7. Show conversation history
        print("\nConversation History:")
        history = memory.get_messages(limit=10)
        for i, msg in enumerate(history[-6:], 1):  # Show last 6 messages
            role_display = "USER" if msg.role == "user" else "ASSISTANT"
            print(f"{i}. [{role_display}] {msg.agent_name}: {msg.content[:60]}...")
        
        # 8. Clean up
        await llm_client.close()
            
    except Exception as e:
        print(f"Error in single agent example: {e}")
        raise


async def multi_agent_session_example(use_mock: bool = True) -> None:
    """
    Example with multiple agents in a session.
    
    Args:
        use_mock: Whether to use mock LLM client for demonstration.
    """
    print("\n" + "=" * 60)
    print("MULTI-AGENT SESSION EXAMPLE")
    print("=" * 60)
    
    agents = []
    
    try:
        # Define agent configurations with different roles
        agent_definitions = [
            {
                "name": "Analyst",
                "system_prompt": "You are a data analyst. You analyze information and provide insights. Be analytical and precise.",
                "memory_size": 30,
                "context_length": 8
            },
            {
                "name": "Developer",
                "system_prompt": "You are a software developer. You write clean, efficient code and solve technical problems.",
                "memory_size": 30,
                "context_length": 8
            },
            {
                "name": "Manager",
                "system_prompt": "You are a project manager. You coordinate between team members and ensure tasks are completed.",
                "memory_size": 30,
                "context_length": 8
            }
        ]
        
        # Create agents with their own LLM client and memory
        for agent_def in agent_definitions:
            llm_config = LLMConfig(
                api_key=os.getenv("OPENAI_API_KEY", "mock-key") if not use_mock else "mock-key",
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=300
            )
            
            if use_mock:
                llm_client = MockLLMClient(llm_config)
            else:
                llm_client = OpenAIClient(config=llm_config)
            
            agent_config = AgentConfig(
                name=agent_def["name"],
                system_prompt=agent_def["system_prompt"],
                llm_client=llm_client,
                memory=SimpleMemory(max_messages=agent_def["memory_size"]),
                tools=[],  # Empty tools list
                max_context_length=agent_def["context_length"]
            )
            
            agents.append(SimpleAgent(agent_config))
        
        # Create session with the agents
        session = Session(
            agents=agents,
            shared_memory=SimpleMemory(max_messages=100)
        )
        
        print(f"Created session with {len(session)} agents:")
        for agent in session.agents:
            print(f"  - {agent.name}: {agent.system_prompt[:40]}...")
        print("-" * 40)
        
        # Run a collaborative task
        task = ("Plan and design a simple web application for task management. "
                "Include: 1) Feature analysis, 2) Technical architecture, 3) Project timeline")
        
        print(f"Task: {task}")
        print("\nRunning session...")
        print("-" * 40)
        
        result = await session.run(
            task=task,
            max_turns=6  # 2 turns per agent
        )
        
        print("\nFinal Result:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        # Show session statistics
        history = session.get_message_history()
        print(f"\nSession Statistics:")
        print(f"  Total messages: {len(history)}")
        print(f"  Total agents: {len(session)}")
        
        # Count messages by agent
        agent_counts = {}
        for msg in history:
            agent_name = msg.agent_name or "Unknown"
            agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
        
        print("  Messages by sender:")
        for agent_name, count in sorted(agent_counts.items()):
            print(f"    {agent_name}: {count} messages")
        
        # Clean up
        for agent in agents:
            await agent.llm_client.close()
                
    except Exception as e:
        print(f"Error in multi-agent session example: {e}")
        raise


async def custom_conclusion_checker(response: Message, session: Session) -> bool:
    """
    Custom conclusion checker for sessions.
    
    Args:
        response: The latest message in the conversation.
        session: The current session object.
        
    Returns:
        True if conversation should end, False otherwise.
    """
    # Example: End if "goodbye" or similar is in the response
    ending_phrases = ["goodbye", "farewell", "that's all", "conclusion", "summary"]
    
    content_lower = response.content.lower()
    if any(phrase in content_lower for phrase in ending_phrases):
        print(f"  Conclusion checker: Detected ending phrase in '{response.agent_name}'s response")
        return True
    
    # Example: End if we've had 3 messages from each agent
    history = session.get_message_history()
    if len(history) >= len(session.agents) * 3:
        print(f"  Conclusion checker: Reached maximum messages per agent")
        return True
    
    return False


async def session_with_custom_conclusion(use_mock: bool = True) -> None:
    """
    Example session with custom conclusion logic.
    
    Args:
        use_mock: Whether to use mock LLM client for demonstration.
    """
    print("\n" + "=" * 60)
    print("SESSION WITH CUSTOM CONCLUSION CHECKER")
    print("=" * 60)
    
    agents = []
    
    try:
        # Define agents for debate
        debate_definitions = [
            {
                "name": "Debater_A",
                "system_prompt": "You advocate for remote work. Present strong arguments for flexible work arrangements.",
                "memory_size": 20
            },
            {
                "name": "Debater_B",
                "system_prompt": "You advocate for office work. Present strong arguments for in-person collaboration.",
                "memory_size": 20
            }
        ]
        
        # Create debate agents
        for agent_def in debate_definitions:
            llm_config = LLMConfig(
                api_key=os.getenv("OPENAI_API_KEY", "mock-key") if not use_mock else "mock-key",
                model="gpt-3.5-turbo",
                temperature=0.8,
                max_tokens=200
            )
            
            if use_mock:
                llm_client = MockLLMClient(llm_config)
            else:
                llm_client = OpenAIClient(config=llm_config)
            
            agent_config = AgentConfig(
                name=agent_def["name"],
                system_prompt=agent_def["system_prompt"],
                llm_client=llm_client,
                memory=SimpleMemory(max_messages=agent_def["memory_size"]),
                tools=[]  # Empty tools list
            )
            
            agents.append(SimpleAgent(agent_config))
        
        # Create session with custom conclusion checker
        session = Session(
            agents=agents,
            shared_memory=SimpleMemory(max_messages=50),
            conclusion_checker=custom_conclusion_checker
        )
        
        print(f"Created debate session with {len(session)} agents")
        print("Topic: Remote work vs Office work")
        print("-" * 40)
        
        # Run the debate
        result = await session.run(
            task="Debate the merits of remote work versus office work. "
                 "Each agent should present their strongest arguments.",
            max_turns=8  # Will likely end earlier due to conclusion checker
        )
        
        print("\nDebate Result:")
        print("-" * 40)
        print(result)
        
        # Show final message
        history = session.get_message_history()
        if history:
            last_msg = history[-1]
            print(f"\nFinal message by {last_msg.agent_name}:")
            print(f"  {last_msg.content[:100]}...")
        
        # Clean up
        for agent in agents:
            await agent.llm_client.close()
                
    except Exception as e:
        print(f"Error in session with custom conclusion: {e}")
        raise


async def main() -> None:
    """
    Main function to run all examples.
    
    Note: Set use_mock=False to use real OpenAI API (requires OPENAI_API_KEY).
    """
    use_mock = True  # Set to False to use real OpenAI API
    
    # Check for API key if not using mock
    if not use_mock and not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        print("Please set your OpenAI API key or run with use_mock=True.")
        sys.exit(1)
    
    print("Simple Agent Framework - Quick Start Examples")
    print("=" * 60)
    
    try:
        # Run single agent example
        await single_agent_example(use_mock)
        
        # Run multi-agent session example
        await multi_agent_session_example(use_mock)
        
        # Run session with custom conclusion checker
        await session_with_custom_conclusion(use_mock)
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the main async function
    asyncio.run(main())
