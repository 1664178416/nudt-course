"""
Tools module for the Simple Agent Framework.

This module provides the ToolRegistry for managing tool functions that agents can use.
Tools are callable functions that extend agent capabilities (e.g., web search, calculations).
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TypeVar,
    Union,
    get_type_hints,
)

from pydantic import BaseModel, ConfigDict, Field

from simple_agent_framework.exceptions import ToolError, ValidationError

# Type variable for tool functions
T = TypeVar("T")


class Tool(BaseModel):
    """Represents a tool function with metadata for agent usage.

    Attributes:
        name: Unique name of the tool.
        function: The actual callable function.
        description: Human-readable description of what the tool does.
        parameters: Schema describing the tool's parameters.
        returns: Description of what the tool returns.
        is_async: Whether the function is async (coroutine).
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    name: str = Field(
        ...,
        description="Unique name of the tool.",
        min_length=1,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
    )
    function: Callable[..., Any] = Field(
        ...,
        description="The actual callable function.",
    )
    description: str = Field(
        ...,
        description="Human-readable description of what the tool does.",
        min_length=1,
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Schema describing the tool's parameters.",
    )
    returns: str = Field(
        default="",
        description="Description of what the tool returns.",
    )
    is_async: bool = Field(
        default=False,
        description="Whether the function is async (coroutine).",
    )

    @classmethod
    def from_function(
        cls,
        func: Callable[..., Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        returns: Optional[str] = None,
    ) -> Tool:
        """Create a Tool instance from a function.

        Args:
            func: The callable function to wrap as a tool.
            name: Tool name. If None, uses function name.
            description: Tool description. If None, uses function docstring.
            parameters: Parameter schema. If None, auto-extracted from signature.
            returns: Return description. If None, extracted from docstring.

        Returns:
            Tool instance.

        Raises:
            ToolError: If function inspection fails.
        """
        try:
            # Determine tool name
            tool_name = name or func.__name__
            if not tool_name:
                raise ToolError("Tool must have a name")

            # Get description from docstring if not provided
            tool_description = description or ""
            if not tool_description and func.__doc__:
                # Use the first non-empty line of the docstring as summary
                doc_lines = [
                    line.strip() 
                    for line in func.__doc__.split("\n") 
                    if line.strip()
                ]
                if doc_lines:
                    tool_description = doc_lines[0]

            # Auto-extract parameters if not provided
            tool_parameters = parameters or {}
            if not tool_parameters:
                tool_parameters = cls._extract_parameters(func)

            # Auto-extract return description if not provided
            tool_returns = returns or ""
            if not tool_returns and func.__doc__:
                tool_returns = cls._extract_return_description(func)

            # Check if function is async
            is_async_func = inspect.iscoroutinefunction(func)

            return cls(
                name=tool_name,
                function=func,
                description=tool_description,
                parameters=tool_parameters,
                returns=tool_returns,
                is_async=is_async_func,
            )

        except Exception as e:
            raise ToolError(f"Failed to create tool from function: {e}")

    @staticmethod
    def _extract_parameters(func: Callable[..., Any]) -> Dict[str, Any]:
        """Extract parameter information from function signature.

        Args:
            func: Function to inspect.

        Returns:
            Dictionary mapping parameter names to their schema.

        Note:
            This is a basic extraction that handles simple docstring patterns.
            For robust parameter description parsing across different docstring
            styles (Google, Numpy, Sphinx), consider integrating a library like
            `docstring_parser` in the future.
        """
        try:
            signature = inspect.signature(func)
            type_hints = get_type_hints(func)

            parameters: Dict[str, Any] = {}
            for param_name, param in signature.parameters.items():
                # Skip 'self' parameter for methods
                if param_name == "self":
                    continue

                # Get type name
                type_name = "Any"
                if param_name in type_hints:
                    type_obj = type_hints[param_name]
                    if hasattr(type_obj, "__name__"):
                        type_name = type_obj.__name__
                    elif hasattr(type_obj, "__origin__"):
                        # Handle generic types like List[str]
                        origin_name = type_obj.__origin__.__name__
                        args = getattr(type_obj, "__args__", [])
                        if args:
                            type_name = f"{origin_name}[{', '.join(arg.__name__ for arg in args if hasattr(arg, '__name__'))}]"
                        else:
                            type_name = origin_name

                param_info: Dict[str, Any] = {
                    "type": type_name,
                    "required": param.default == inspect.Parameter.empty,
                }

                # Add default value if available
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default

                # Add description if available in docstring
                # Simple extraction: look for param_name in docstring
                if func.__doc__:
                    for line in func.__doc__.split("\n"):
                        if f"{param_name}:" in line.lower():
                            parts = line.split(":", 1)
                            if len(parts) > 1:
                                param_info["description"] = parts[1].strip()
                            break

                parameters[param_name] = param_info

            return parameters

        except Exception as e:
            raise ToolError(f"Failed to extract parameters from function: {e}")

    @staticmethod
    def _extract_return_description(func: Callable[..., Any]) -> str:
        """Extract return description from function docstring.
        
        Args:
            func: Function to extract return description from.
            
        Returns:
            Return description string, empty if not found.
        """
        if not func.__doc__:
            return ""
            
        docstring = func.__doc__
        doc_lower = docstring.lower()
        
        # Common patterns for return sections in docstrings
        return_markers = [
            ':returns:',    # Sphinx style
            'returns:',     # Common style
            'return:',      # Sometimes singular
            ':return:',     # Sphinx singular
        ]
        
        # Find the earliest occurrence of any return marker
        earliest_pos = None
        found_marker = None
        
        for marker in return_markers:
            marker_pos = doc_lower.find(marker)
            if marker_pos != -1:
                if earliest_pos is None or marker_pos < earliest_pos:
                    earliest_pos = marker_pos
                    found_marker = marker
        
        if earliest_pos is None or found_marker is None:
            return ""
        
        # Extract text after the marker
        after_marker = docstring[earliest_pos + len(found_marker):]
        
        # Collect lines until we hit an empty line or another section
        return_lines = []
        for line in after_marker.split('\n'):
            stripped = line.strip()
            
            # Empty line might indicate end of section
            if not stripped:
                if return_lines:  # We've already collected some return description
                    break
                else:
                    continue  # Skip leading empty lines
            
            # Check if this is the start of another section
            # (common patterns: line ending with colon, or starting with common markers)
            if (stripped.endswith(':') or 
                any(stripped.lower().startswith(marker) for marker in ['args:', 'arguments:', 'parameters:', 'raises:', 'examples:'])):
                break
            
            return_lines.append(stripped)
        
        # Join with spaces for a clean description
        return ' '.join(return_lines) if return_lines else ""


class BaseToolRegistry(ABC):
    """Abstract base class for tool registries.

    Tool registries manage the registration and retrieval of tools
    that agents can use to extend their capabilities.
    """

    @abstractmethod
    def register_tool(
        self,
        tool: Union[Callable[..., Any], Tool],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Register a tool in the registry.

        Args:
            tool: Either a Tool instance or a callable function.
            name: Tool name (only used if tool is a callable).
            description: Tool description (only used if tool is a callable).

        Raises:
            ToolError: If registration fails.
        """
        pass

    @abstractmethod
    def get_tool(self, name: str) -> Tool:
        """Get a tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            Tool instance.

        Raises:
            ToolError: If tool is not found.
        """
        pass

    @abstractmethod
    def get_tools_descriptions(self) -> List[Dict[str, Any]]:
        """Get descriptions of all registered tools.

        Returns:
            List of dictionaries containing tool descriptions.
        """
        pass

    @abstractmethod
    def list_tools(self) -> List[str]:
        """List names of all registered tools.

        Returns:
            List of tool names.
        """
        pass

    @abstractmethod
    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Tool name to check.

        Returns:
            True if tool is registered, False otherwise.
        """
        pass

    @abstractmethod
    def unregister_tool(self, name: str) -> None:
        """Unregister a tool from the registry.

        Args:
            name: Name of the tool to unregister.

        Raises:
            ToolError: If tool is not found.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all tools from the registry."""
        pass


class ToolRegistry(BaseToolRegistry):
    """Concrete implementation of a tool registry.

    This registry stores tools in memory and provides methods for
    registration, retrieval, and management.
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Tool] = {}

    def register_tool(
        self,
        tool: Union[Callable[..., Any], Tool],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        """Register a tool in the registry.

        Args:
            tool: Either a Tool instance or a callable function.
            name: Tool name (only used if tool is a callable).
            description: Tool description (only used if tool is a callable).

        Raises:
            ToolError: If tool with the same name is already registered.
            ValidationError: If tool is invalid.
        """
        try:
            # Convert function to Tool if needed
            if callable(tool) and not isinstance(tool, Tool):
                tool_obj = Tool.from_function(
                    func=tool,
                    name=name,
                    description=description,
                )
            elif isinstance(tool, Tool):
                tool_obj = tool
            else:
                raise ToolError(
                    f"tool must be a callable or Tool instance, got {type(tool)}"
                )

            # Check if tool already exists
            if tool_obj.name in self._tools:
                raise ToolError(f"Tool '{tool_obj.name}' is already registered")

            # Register the tool
            self._tools[tool_obj.name] = tool_obj

        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Failed to register tool: {e}")

    def get_tool(self, name: str) -> Tool:
        """Get a tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            Tool instance.

        Raises:
            ToolError: If tool is not found.
        """
        if name not in self._tools:
            raise ToolError(f"Tool '{name}' is not registered")

        return self._tools[name]

    def get_tools_descriptions(self) -> List[Dict[str, Any]]:
        """Get descriptions of all registered tools.

        Returns:
            List of dictionaries containing tool descriptions.
        """
        descriptions: List[Dict[str, Any]] = []

        for tool_name, tool in self._tools.items():
            description: Dict[str, Any] = {
                "name": tool_name,
                "description": tool.description,
                "parameters": tool.parameters,
                "is_async": tool.is_async,
            }

            if tool.returns:
                description["returns"] = tool.returns

            descriptions.append(description)

        return descriptions

    def list_tools(self) -> List[str]:
        """List names of all registered tools.

        Returns:
            List of tool names in alphabetical order.
        """
        return sorted(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Tool name to check.

        Returns:
            True if tool is registered, False otherwise.
        """
        return name in self._tools

    def unregister_tool(self, name: str) -> None:
        """Unregister a tool from the registry.

        Args:
            name: Name of the tool to unregister.

        Raises:
            ToolError: If tool is not found.
        """
        if name not in self._tools:
            raise ToolError(f"Tool '{name}' is not registered")

        del self._tools[name]

    def clear(self) -> None:
        """Clear all tools from the registry."""
        self._tools.clear()

    def __len__(self) -> int:
        """Get the number of registered tools.

        Returns:
            Number of registered tools.
        """
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Tool name to check.

        Returns:
            True if tool is registered, False otherwise.
        """
        return name in self._tools

    def __str__(self) -> str:
        """Get string representation of the registry.

        Returns:
            String representation.
        """
        return f"ToolRegistry(tools={len(self._tools)})"


# Global default tool registry (singleton pattern)
_default_registry: ToolRegistry = ToolRegistry()


def get_default_tool_registry() -> ToolRegistry:
    """Get the global default tool registry.

    Returns:
        Global ToolRegistry instance (singleton).
    """
    return _default_registry


def register_tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Callable[[T], T]:
    """Decorator factory for registering tools in the default registry.

    Args:
        name: Tool name. If None, uses function name.
        description: Tool description. If None, uses function docstring.

    Returns:
        Decorator function that registers the decorated function as a tool.

    Example:
        @register_tool(name="search", description="Search the web")
        async def search_web(query: str) -> str:
            '''Search the web for information.
            
            Args:
                query: Search query string
                
            Returns:
                Search results as string
            '''
            # ... implementation ...
    """

    def decorator(func: T) -> T:
        """Inner decorator that registers the function."""
        registry = get_default_tool_registry()
        registry.register_tool(func, name=name, description=description)
        return func

    return decorator
