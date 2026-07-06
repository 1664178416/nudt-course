## examples/with_tools.py
```python
"""
Tools Example for Simple Agent Framework.

This example demonstrates how to use tools with agents in the framework.
It covers:
1. Defining tools using decorators and explicit registration
2. Creating agents with access to specific tools
3. Demonstrating tool usage in conversations
4. Showing both simple and complex tool interactions

Prerequisites:
    - Required packages installed: pydantic, aiohttp, openai
    - For real OpenAI API usage: OPENAI_API_KEY environment variable

Note: This example uses a mock LLM client to avoid actual API calls.
Set use_real_api=False to test without API key.
"""

import asyncio
import ast
import json
import os
import sys
import math
import random
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

# Framework core classes
from simple_agent_framework.agent import AgentConfig, SimpleAgent
from simple_agent_framework.llm import LLMClient, LLMConfig, OpenAIClient
from simple_agent_framework.memory import SimpleMemory
from simple_agent_framework.message import Message
from simple_agent_framework.session import Session
from simple_agent_framework.tools import Tool, ToolRegistry, register_tool

# Configure logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global tool registry for the example
example_tool_registry = ToolRegistry()


# =============================================================================
# Tool Definitions
# =============================================================================

@register_tool(name="get_current_time", description="Get the current date and time")
async def get_current_time(timezone_str: Optional[str] = "UTC") -> str:
    """Get the current date and time.
    
    Args:
        timezone_str: Optional timezone string (e.g., 'UTC', 'US/Eastern').
            Defaults to 'UTC'.
    
    Returns:
        Current date and time as a formatted string.
    """
    try:
        # Try to use pytz if available, otherwise use UTC fallback
        try:
            import pytz
            tz_obj = pytz.timezone(timezone_str)
            current_time = datetime.now(tz_obj)
            timezone_display = timezone_str
        except ImportError:
            # Fallback if pytz is not installed
            if timezone_str and timezone_str.upper() != "UTC":
                timezone_display = "UTC (pytz not installed)"
            else:
                timezone_display = "UTC"
            current_time = datetime.utcnow()
        
        return f"Current time in {timezone_display}: {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return f"Error getting time: {str(e)}"


@register_tool(name="calculate", description="Perform basic mathematical calculations")
def calculate(expression: str) -> str:
    """Safely evaluate a basic mathematical expression.
    
    Args:
        expression: A string containing a basic math expression (e.g., "(2 + 3) * 4").
    
    Returns:
        The result as a string, or an error message.
    
    Note:
        Only supports numbers, parentheses, and operators: +, -, *, /, //, %, **.
        Uses ast.literal_eval after validation for safety.
    """
    # Remove whitespace
    expr = expression.strip()
    
    if not expr:
        return "Error: Empty expression"
    
    # Validate characters for safety (basic arithmetic only)
    allowed_chars = set("0123456789+-*/(). //%** ")
    if not all(c in allowed_chars for c in expr):
        return "Error: Expression contains disallowed characters. Only basic arithmetic is allowed."
    
    # Check for potentially unsafe patterns
    unsafe_patterns = ['__', 'import', 'eval', 'exec', 'open', 'compile']
    if any(pattern in expr.lower() for pattern in unsafe_patterns):
        return "Error: Potentially unsafe expression detected."
    
    try:
        # Parse expression into AST
        tree = ast.parse(expr, mode='eval')
        
        # Define allowed AST nodes for basic arithmetic
        allowed_nodes = {
            ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
            ast.USub, ast.UAdd  # Unary operators
        }
        
        # Validate all nodes in the AST
        for node in ast.walk(tree):
            node_type = type(node)
            if node_type not in allowed_nodes:
                return f"Error: Expression contains unsupported operation: {node_type.__name__}"
        
        # Create a safe evaluation environment
        safe_globals = {
            '__builtins__': {},
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'sum': sum, 'pow': pow, 'math': math
        }
        
        # Evaluate safely
        result = eval(compile(tree, '<string>', 'eval'), safe_globals, {})
        
        # Format result nicely
        if isinstance(result, (int, float)):
            return f"Calculation: {expression} = {result}"
        else:
            return f"Result: {result}"
            
    except SyntaxError as e:
        return f"Error: Invalid expression syntax - {e}"
    except ZeroDivisionError:
        return "Error: Division by zero"
    except (ValueError, TypeError, NameError) as e:
        return f"Error calculating '{expression}': {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


@register_tool(name="word_counter", description="Count words, characters, and sentences in text")
def word_counter(text: str) -> Dict[str, Any]:
    """Count words, characters, and sentences in text.
    
    Args:
        text: Text to analyze.
    
    Returns:
        Dictionary with word count, character count, and sentence count.
    """
    if not text or not text.strip():
        return {
            "word_count": 0,
            "character_count": 0,
            "sentence_count": 0,
            "average_word_length": 0.0,
            "message": "Text is empty."
        }
    
    # Clean the text
    cleaned_text = text.strip()
    
    # Word count
    words = cleaned_text.split()
    word_count = len(words)
    
    # Character count (excluding leading/trailing whitespace)
    character_count = len(cleaned_text)
    
    # Sentence count (simple heuristic)
    sentence_endings = ['.', '!', '?', '。', '！', '？']
    sentence_count = 0
    in_sentence = False
    
    for char in cleaned_text:
        if char.isalnum() or char in ',;:"\'':
            in_sentence = True
        elif char in sentence_endings and in_sentence:
            sentence_count += 1
            in_sentence = False
    
    # Count last sentence if not terminated by punctuation
    if in_sentence:
        sentence_count += 1
    
    # Average word length
    avg_word_len = round(character_count / word_count, 2) if word_count > 0 else 0.0
    
    return {
        "word_count": word_count,
        "character_count": character_count,
        "sentence_count": sentence_count,
        "average_word_length": avg_word_len,
        "message": f"Text analysis complete: {word_count} words, {character_count} characters, {sentence_count} sentences."
    }


# Explicit tool registration example (not using decorator)
def fetch_weather(city: str, country: Optional[str] = None) -> str:
    """Fetch weather information for a city.
    
    Args:
        city: Name of the city.
        country: Optional country name for more specific results.
    
    Returns:
        Weather information string.
    
    Note:
        This is a mock implementation. In a real application,
        this would call a weather API.
    """
    # Mock weather database
    cities_weather = {
        "new york": {"temp": 22, "condition": "Sunny", "humidity": 65, "wind_speed": "15 km/h"},
        "london": {"temp": 15, "condition": "Cloudy", "humidity": 80, "wind_speed": "10 km/h"},
        "tokyo": {"temp": 25, "condition": "Clear", "humidity": 70, "wind_speed": "12 km/h"},
        "sydney": {"temp": 28, "condition": "Partly Cloudy", "humidity": 60, "wind_speed": "18 km/h"},
        "paris": {"temp": 20, "condition": "Light Rain", "humidity": 75, "wind_speed": "8 km/h"},
        "beijing": {"temp": 18, "condition": "Smoggy", "humidity": 70, "wind_speed": "5 km/h"},
        "mumbai": {"temp": 30, "condition": "Humid", "humidity": 85, "wind_speed": "7 km/h"},
    }
    
    city_lower = city.lower().strip()
    location = f"{city.title()}, {country}" if country else city.title()
    
    if city_lower in cities_weather:
        weather = cities_weather[city_lower]
        return (f"Weather in {location}:\n"
                f"  Temperature: {weather['temp']}°C\n"
                f"  Condition: {weather['condition']}\n"
                f"  Humidity: {weather['humidity']}%\n"
                f"  Wind Speed: {weather['wind_speed']}")
    else:
        available_cities = ", ".join(sorted(c.title() for c in cities_weather.keys()))
        return (f"Weather data not available for {location}.\n"
                f"Available cities: {available_cities}")


# Register the weather tool explicitly using Tool.from_function
weather_tool = Tool.from_function(
    func=fetch_weather,
    name="fetch_weather",
    description="Get current weather information for a city",
    parameters={
        "city": {
            "type": "str",
            "description": "Name of the city (e.g., 'New York', 'Tokyo')",
            "required": True
        },
        "country": {
            "type": "str", 
            "description": "Country name (optional, e.g., 'USA', 'Japan')",
            "required": False,
            "default": None
        }
    },
    returns="Formatted weather report as string"
)

example_tool_registry.register_tool(weather_tool)


# Complex tool example with multiple operations
class DataProcessor:
    """Example class that provides data processing tools."""
    
    @staticmethod
    @register_tool(name="filter_data", description="Filter a list of items based on criteria")
    def filter_items(
        items: List[Any],
        criteria: str,
        case_sensitive: bool = False
    ) -> List[Any]:
        """Filter a list of items containing the criteria string.
        
        Args:
            items: List of items (strings or convertible to string).
            criteria: String to search for in items.
            case_sensitive: Whether the search is case sensitive.
        
        Returns:
            Filtered list of items containing the criteria.
        """
        if not items:
            return []
        
        if not isinstance(items, list):
            return [f"Error: Expected list, got {type(items).__name__}"]
        
        if not criteria or not isinstance(criteria, str):
            return [f"Error: Invalid criteria '{criteria}'"]
        
        search_criteria = criteria if case_sensitive else criteria.lower()
        filtered = []
        
        for item in items:
            try:
                item_str = str(item)
                if not case_sensitive:
                    item_str = item_str.lower()
                
                if search_criteria in item_str:
                    filtered.append(item)
            except Exception:
                # Skip items that cannot be converted to string
                continue
        
        return filtered
    
    @staticmethod
    @register_tool(name="sort_data", description="Sort a list of items")
    def sort_items(
        items: List[Any],
        reverse: bool = False,
        key: Optional[str] = None
    ) -> List[Any]:
        """Sort a list of items.
        
        Args:
            items: List of items to sort.
            reverse: Sort in descending order if True.
            key: Optional attribute name to sort by (for objects).
        
        Returns:
            Sorted list of items.
        """
        if not items:
            return []
        
        if not isinstance(items, list):
            return [f"Error: Expected list, got {type(items).__name__}"]
        
        try:
            if key:
                # Sort by object attribute
                return sorted(items, 
                            key=lambda x: getattr(x, key, str(x)), 
                            reverse=reverse)
            else:
                # Try natural sort, fallback to string sort
                try:
                    return sorted(items, reverse=reverse)
                except TypeError:
                    return sorted(items, key=str, reverse=reverse)
        except Exception as e:
            return [f"Error sorting items: {str(e)}"]


# =============================================================================
# Mock LLM Client for Demonstration
# =============================================================================

class MockToolAwareLLMClient(LLMClient):
    """Mock LLM client that simulates tool-aware responses.
    
    This client demonstrates how an LLM might respond with tool calls
    when it recognizes certain patterns in the input.
    """
    
    def __init__(self, config: LLMConfig) -> None:
        """Initialize mock client with configuration."""
        super().__init__(config)
        self.call_count = 0
    
    async def chat_completion(self, messages: List[Message], **kwargs: Any) -> Dict[str, Any]:
        """Simulate an LLM response, sometimes suggesting tool use based on input.
        
        Args:
            messages: List of Message objects.
            **kwargs: Additional parameters (ignored in mock).
            
        Returns:
            Mock completion response.
        """
        self.call_count += 1
        
        # Extract the last user message content
        last_user_content = ""
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_content = msg.content
                break
        
        # Simple heuristic to decide response based on query
        query_lower = last_user_content.lower()
        
        # Check for tool-related queries
        tool_suggestion = None
        response_text = ""
        
        # Time-related queries
        if any(time_word in query_lower for time_word in ['time', 'current time', 'what time', 'clock', 'date']):
            response_text = ("I can check the current time for you. "
                           "I'll use the 'get_current_time' tool to get the current date and time.")
            tool_suggestion = "get_current_time"
        
        # Math-related queries
        elif any(math_word in query_lower for math_word in ['calculate', 'math', 'compute', 'what is', 'times', 'plus', 'minus', 'divide', 'multiply']):
            # Try to extract a mathematical expression
            import re
            math_pattern = r'\b\d+[\s\d\+\-\*\/\(\)\.\%\^]+\d+\b'
            matches = re.findall(math_pattern, last_user_content)
            
            if matches:
                expression = matches[0]
                response_text = (f"I can calculate '{expression}' for you. "
                               f"I'll use the 'calculate' tool to compute the result.")
                tool_suggestion = "calculate"
            else:
                response_text = ("I can help with mathematical calculations. "
                               "Please provide a mathematical expression like '2 + 2 * 3' and I'll calculate it for you using the 'calculate' tool.")
        
        # Weather-related queries
