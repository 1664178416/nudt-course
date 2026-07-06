```python
"""
Custom Agent Example for Simple Agent Framework.

This example demonstrates how to create custom agents by inheriting from BaseAgent
and overriding methods for specialized behavior. It shows two approaches:
1. A custom agent with enhanced system prompt handling
2. A custom agent with modified tool calling behavior

Key concepts covered:
- Extending BaseAgent to create specialized agents
- Overriding _process_messages for custom message formatting
- Overriding _create_chat_completion for custom LLM interaction logic
- Adding custom methods and properties
- Using custom agents in sessions

Prerequisites:
    - Required packages installed: pydantic, aiohttp, openai
    - For real OpenAI API usage: OPENAI_API_KEY environment variable
"""

import asyncio
import ast
import json
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from simple_agent_framework.agent import AgentConfig, BaseAgent, SimpleAgent
from simple_agent_framework.exceptions import LLMError, ToolError
from simple_agent_framework.llm import LLMConfig, OpenAIClient
from simple_agent_framework.memory import SimpleMemory
from simple_agent_framework.message import Message
from simple_agent_framework.session import Session
from simple_agent_framework.tools import Tool, ToolRegistry, register_tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Safe Tool Definitions for Examples
# =============================================================================

@register_tool(name="get_current_time", description="Get the current time in ISO format")
async def get_current_time(timezone: str = "UTC") -> str:
    """Get the current time in ISO format.
    
    Args:
        timezone: Timezone for the current time (e.g., 'UTC', 'US/Eastern').
            Defaults to 'UTC'.
            
    Returns:
        Current time as ISO formatted string.
    """
    try:
        # Try to import pytz, but provide fallback if not available
        try:
            import pytz
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
        except ImportError:
            # Fallback to UTC if pytz not available
            if timezone.upper() != "UTC":
                return f"Warning: pytz not installed. Using UTC instead of {timezone}."
            current_time = datetime.utcnow()
        
        return current_time.isoformat()
    except Exception as e:
        return f"Error getting time: {str(e)}"


@register_tool(name="calculate", description="Perform mathematical calculations")
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., '2 + 2 * 3').
        
    Returns:
        Result of the calculation as string.
        
    Note:
        Uses ast.literal_eval() for safe evaluation of basic expressions.
        Only supports basic arithmetic operations and math functions.
    """
    try:
        # Safe evaluation using ast.literal_eval for basic arithmetic
        # First, try to evaluate as a literal
        try:
            result = ast.literal_eval(expression)
            if isinstance(result, (int, float)):
                return f"{expression} = {result}"
        except (ValueError, SyntaxError):
            pass
        
        # For more complex expressions, use a simple safe evaluator
        # Define allowed operations and functions
        allowed_ops = {
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'pow': pow, 'sum': sum,
            'math.sin': math.sin, 'math.cos': math.cos, 'math.tan': math.tan,
            'math.sqrt': math.sqrt, 'math.log': math.log, 'math.exp': math.exp,
            'math.pi': math.pi, 'math.e': math.e
        }
        
        # Convert expression to use allowed functions
        # This is a simple implementation - in production use a proper safe evaluator
        if any(op in expression for op in ['import', '__', 'exec', 'eval', 'open']):
            raise ValueError("Unsafe expression detected")
            
        # Try evaluating with limited scope
        result = eval(expression, {"__builtins__": {}}, allowed_ops)
        return f"{expression} = {result}"
        
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


@register_tool(name="word_count", description="Count words in a text")
def word_count(text: str) -> str:
    """Count the number of words in a given text.
    
    Args:
        text: The text to analyze.
        
    Returns:
        Word count as a formatted string.
    """
    if not text:
        return "Text is empty."
    
    words = text.split()
    return f"The text contains {len(words)} words."


# =============================================================================
# Custom Agent 1: Agent with Enhanced System Prompt Handling
# =============================================================================

class CustomAgentWithEnhancedPrompt(BaseAgent):
    """
    Custom agent that enhances system prompt handling.
    
    This agent demonstrates how to override message processing to:
    1. Add dynamic system prompts based on conversation context
    2. Include metadata in the system prompt
    3. Format messages in a custom way
    
    Key features:
    - Dynamic system prompt that includes current context info
    - Message formatting with custom separators
    - Conversation state tracking
    - Async context manager support
    """
    
    def __init__(self, config: AgentConfig, additional_context: Optional[str] = None) -> None:
        """Initialize custom agent with additional context.
        
        Args:
            config: Agent configuration.
            additional_context: Additional context to include in system prompt.
        """
        super().__init__(config)
        self.additional_context = additional_context or ""
        self.conversation_turn_count = 0
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.llm_client.close()
    
    async def _process_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Process messages with enhanced system prompt and custom formatting.
        
        This method overrides the base implementation to:
        1. Create a dynamic system prompt based on conversation state
        2. Format messages with custom separators
        3. Include additional context if provided
        
        Args:
            messages: List of Message objects to process.
            
        Returns:
            List of dictionaries in LLM API format.
        """
        # Increment conversation turn counter
        self.conversation_turn_count += 1
        
        # Create enhanced system prompt
        enhanced_system_prompt = self._create_enhanced_system_prompt(messages)
        
        # Prepare messages for LLM
        processed_messages = []
        
        # Add system message with enhanced prompt
        processed_messages.append({
            "role": "system",
            "content": enhanced_system_prompt,
            "name": "system"
        })
        
        # Process conversation messages with custom formatting
        for msg in messages:
            # Skip system messages as we've already added our enhanced one
            if msg.role == "system":
                continue
            
            # Format message content with context
            formatted_content = self._format_message_content(msg)
            
            # Prepare message dict
            message_dict: Dict[str, Any] = {
                "role": msg.role,
                "content": formatted_content
            }
            
            # Add agent name if available and not already in content
            if msg.agent_name and not self._has_sender_info(formatted_content):
                message_dict["name"] = msg.agent_name
            
            processed_messages.append(message_dict)
        
        logger.debug(f"Processed {len(processed_messages)} messages for agent '{self.name}'")
        return processed_messages
    
    def _has_sender_info(self, content: str) -> bool:
        """Check if content already contains sender information.
        
        Args:
            content: Message content to check.
            
        Returns:
            True if content contains sender markers, False otherwise.
        """
        sender_markers = ["[From ", "[Agent ", "From: ", "Agent: "]
        return any(marker in content for marker in sender_markers)
    
    def _format_message_content(self, message: Message) -> str:
        """Format message content with custom styling.
        
        Args:
            message: Message object to format.
            
        Returns:
            Formatted message content.
        """
        if message.role == "user":
            return f"User query: {message.content}"
        elif message.role == "assistant":
            if message.agent_name and message.agent_name != "assistant":
                return f"[From {message.agent_name}] {message.content}"
            return message.content
        else:
            return message.content
    
    def _create_enhanced_system_prompt(self, messages: List[Message]) -> str:
        """Create enhanced system prompt with dynamic context.
        
        Args:
            messages: Current conversation messages for context.
            
        Returns:
            Enhanced system prompt string.
        """
        base_prompt = self.system_prompt
        
        # Add conversation context
        context_info = [
            f"Conversation turn: {self.conversation_turn_count}",
            f"Agent name: {self.name}",
            f"Total messages in context: {len(messages)}"
        ]
        
        # Add recent message summary if available
        recent_user_messages = [m for m in messages[-3:] if m.role == "user"]
        if recent_user_messages:
            recent_summary = "Recent user queries: " + ", ".join(
                f"'{m.content[:30]}...'" if len(m.content) > 30 else f"'{m.content}'"
                for m in recent_user_messages
            )
            context_info.append(recent_summary)
        
        # Add additional context if provided
        if self.additional_context:
            context_info.append(f"Additional context: {self.additional_context}")
        
        # Add available tools information
        available_tools = self.get_available_tools()
        if available_tools:
            tool_names = [tool["name"] for tool in available_tools]
            context_info.append(f"Available tools: {', '.join(tool_names)}")
        
        # Combine all parts
        context_block = "\n".join(f"- {info}" for info in context_info)
        enhanced_prompt = f"""{base_prompt}

Current Conversation Context:
{context_block}

Please respond accordingly, considering the above context."""
        
        return enhanced_prompt
    
    async def _create_chat_completion(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create chat completion with enhanced context awareness.
        
        This implementation extends the base to include conversation metadata
        and provides better error handling for tool calls.
        
        Args:
            messages: List of message dictionaries in LLM API format.
            
        Returns:
            Dictionary containing completion response and metadata.
            
        Raises:
            LLMError: If LLM call fails.
            ToolError: If tool execution fails.
        """
        try:
            # Prepare tool descriptions if we have tools
            tool_descriptions = []
            if self._tools:
                for tool_name in self._tools:
                    try:
                        tool = self._tool_registry.get_tool(tool_name)
                        tool_desc = {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": tool.parameters
                        }
                        tool_descriptions.append(tool_desc)
                    except ToolError:
                        logger.warning(f"Tool '{tool_name}' not found in registry")
                        continue
            
            # If we have tools, add them to the request
            llm_params = {}
            if tool_descriptions:
                # In this example, we use a simple approach where we add tool info
                # to the last system message. In a real implementation, you might
                # use OpenAI's function calling API.
                if messages and messages[0]["role"] == "system":
                    tools_info = "\n\nAvailable tools:\n" + "\n".join(
                        f"- {tool['name']}: {tool['description']}" 
                        for tool in tool_descriptions
                    )
                    messages[0]["content"] += tools_info
            
            # Make LLM call
            response = await self.llm_client.chat_completion(messages, **llm_params)
            
            # Check if response indicates tool usage (simple heuristic)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            if any(tool_name in content.lower() for tool_name in self._tools):
                # Simple tool call detection - in production, use proper function calling
                logger.info(f"Agent '{self.name}' might want to use a tool in response")
                response["metadata"] = {
                    "enhanced_agent": True,
                    "conversation_turn": self.conversation_turn_count,
                    "potential_tool_use": True
                }
            else:
                response["metadata"] = {
                    "enhanced_agent": True,
                    "conversation_turn": self.conversation_turn_count,
                    "potential_tool_use": False
                }
            
            return response
            
        except Exception as e:
            logger.error(f"Error in chat completion for enhanced agent: {e}")
            raise LLMError(f"Enhanced agent chat completion failed: {e}")


# =============================================================================
# Custom Agent 2: Agent with Modified Tool Calling Behavior
# =============================================================================

class CustomAgentWithToolBehavior(BaseAgent):
    """
    Custom agent with specialized tool calling behavior.
    
    This agent demonstrates how to override tool handling to:
    1. Use a different prompting strategy for tool selection
    2. Post-process tool results before sending to LLM
    3. Implement custom tool call validation
    
    Key features:
    - Tool usage prioritization based on context
    - Tool result formatting and summarization
    - Custom tool call validation
    - Tool usage statistics tracking
    """
    
    def __init__(self, config: AgentConfig, tool_priority: Optional[List[str]] = None) -> None:
        """Initialize custom agent with tool priority.
        
        Args:
            config: Agent configuration.
            tool_priority: Ordered list of tool names indicating preference.
        """
        super().__init__(config)
        self.tool_priority = tool_priority or []
        self.tool_usage_stats: Dict[str, int] = {}
        
    async def _process_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Process messages with tool-aware formatting.
        
        Args:
            messages: List of Message objects to process.
            
        Returns:
            List of dictionaries in LLM API format.
        """
        # Call parent implementation for basic processing
        # We'll add tool priority information to system prompt
        processed_messages = await super()._process_messages(messages)
        
        # Add tool priority hint to system message
        if processed_messages and processed_messages[0]["role"] == "system" and self.tool_priority:
            priority_hint = f"\n\nTool priority (highest first): {', '.join(self.tool_priority)}"
            processed_messages[0]["content"] += priority_hint
        
        return processed_messages
    
    async def _create_chat_completion(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create chat completion with enhanced tool calling.
        
        This implementation adds:
        1. Tool usage statistics tracking
        2. Tool result post-processing
        3. Custom tool call validation
        
        Args:
            messages: List of message dictionaries in LLM API format.
            
        Returns:
            Dictionary containing completion response and metadata.
        """
        # Track tool usage in metadata
        metadata = {
            "tool_agent": True,
            "tool_priority": self.tool_priority.copy() if self.tool_priority else [],
            "tool_usage_stats": self.tool_usage_stats.copy()
        }
        
        try:
            # First, try to generate response without tool calls
            response = await self.llm_client.chat_completion(messages)
            
            # Check if response suggests tool usage
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Simple tool call detection (in real implementation, use proper function calling)
            for tool_name in self._tools:
                if tool_name in content.lower():
                    logger.info(f"Detected potential tool call for '{tool_name}'")
                    
                    # Try to extract arguments (simplified)
                    tool_args = self._extract_tool_arguments(content, tool_name)
                    
                    # Execute tool
                    tool_result = await self._execute_tool_with_validation(tool_name, tool_args)
                    
                    # Update usage statistics
                    self.tool_usage_stats[tool_name] = self.tool_usage_stats.get(tool_name, 0) + 1
                    
                    # Format tool result
                    formatted_result