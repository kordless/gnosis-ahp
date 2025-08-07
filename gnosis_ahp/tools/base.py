"""Base tool interface for gnosis-agent tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, get_type_hints, AsyncGenerator
from dataclasses import dataclass
import inspect
import json


@dataclass
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseTool(ABC):
    """Abstract base class for tools."""
    
    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        """Initialize the tool.
        
        Args:
            name: Tool name (defaults to class name)
            description: Tool description (defaults to docstring)
        """
        self.name = name or self.__class__.__name__
        self.description = description or (self.__doc__ or "").strip()
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments.
        
        Args:
            **kwargs: Tool-specific arguments. Can also contain context like 'session'.
            
        Returns:
            ToolResult with execution outcome
        """
        pass

    async def execute_streaming(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the tool and stream back results.
        
        Yields:
            Dicts representing chunks of the result. The last chunk should have type='final'.
        """
        # Default implementation for non-streaming tools
        result = await self.execute(**kwargs)
        yield {
            "type": "final",
            "data": result.data,
            "error": result.error,
            "success": result.success
        }
    
    @abstractmethod
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's schema for LLM consumption.
        
        Returns:
            Dictionary with tool schema including parameters
        """
        pass
    
    def validate_arguments(self, **kwargs) -> Dict[str, Any]:
        """Validate and normalize arguments.
        
        Args:
            **kwargs: Arguments to validate
            
        Returns:
            Validated arguments
            
        Raises:
            ValidationError: If arguments are invalid
        """
        # Default implementation - subclasses can override
        return kwargs


class FunctionTool(BaseTool):
    """Wrapper to convert a regular function into a tool."""
    
    def __init__(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None, cost: int = 0, session_required: bool = False):
        """Initialize a function-based tool.        
        Args:
            func: The function to wrap
            name: Tool name (defaults to function name)
            description: Tool description (defaults to function docstring)
            cost: Cost in satoshis to execute the tool
            session_required: Whether the tool requires a session to operate.
        """
        self.func = func
        self.is_async = inspect.iscoroutinefunction(func)
        self.is_async_generator = inspect.isasyncgenfunction(func)
        self.cost = cost
        self.session_required = session_required
        
        # Extract name and description
        tool_name = name or func.__name__
        tool_desc = description or (func.__doc__ or "").strip().split('\n')[0]
        
        super().__init__(name=tool_name, description=tool_desc)
        
        # Set the name attribute on the instance
        self.name = tool_name
        
        # Extract type hints for schema generation
        self.type_hints = get_type_hints(func)
        self.signature = inspect.signature(func)

    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the wrapped function."""
        try:
            # Separate tool arguments from context
            tool_args = {k: v for k, v in kwargs.items() if k in self.signature.parameters}
            
            # Validate and convert arguments
            validated_args = self.validate_arguments(**tool_args)
            
            # Execute function
            if self.is_async:
                result = await self.func(**validated_args)
            else:
                result = self.func(**validated_args)
            
            return ToolResult(success=True, data=result)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def execute_streaming(self, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute the wrapped function and stream results."""
        try:
            # Separate tool arguments from context
            tool_args = {k: v for k, v in kwargs.items() if k in self.signature.parameters}
            validated_args = self.validate_arguments(**tool_args)

            if self.is_async_generator:
                # Stream from async generator
                async for chunk in self.func(**validated_args):
                    yield {"type": "chunk", "data": chunk}
                yield {"type": "final", "data": None} # Signal end of stream
            else:
                # Execute regular function and yield a single final result
                result = await self.execute(**kwargs)
                yield {
                    "type": "final",
                    "data": result.data,
                    "error": result.error,
                    "success": result.success
                }
        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def get_schema(self) -> Dict[str, Any]:
        """Generate schema from function signature."""
        properties = {}
        required = []
        
        for param_name, param in self.signature.parameters.items():
            if param_name in ['self', 'session']: # Hide session from the public schema
                continue
                
            # Get type information
            param_type = self.type_hints.get(param_name, Any)
            type_name = self._python_type_to_json_type(param_type)
            
            # Build property schema
            prop_schema = {"type": type_name}
            
            # Add description from docstring if available
            if self.func.__doc__:
                # Simple extraction - could be improved with docstring parsing
                prop_schema["description"] = f"Parameter {param_name}"
            
            properties[param_name] = prop_schema
            
            # Check if required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        
        schema = {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            },
            "x-ahp-session-required": self.session_required
        }
        return schema
    
    def _python_type_to_json_type(self, python_type: Any) -> str:
        """Convert Python type to JSON schema type."""
        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
            type(None): "null"
        }
        
        # Handle Optional types
        origin = getattr(python_type, '__origin__', None)
        if origin is not None:
            if origin is list:
                return "array"
            elif origin is dict:
                return "object"
        
        return type_mapping.get(python_type, "string")
    
    def validate_arguments(self, **kwargs) -> Dict[str, Any]:
        """Validate and convert arguments based on type hints."""
        validated = {}
        
        for param_name, param_value in kwargs.items():
            if param_name in self.type_hints:
                expected_type = self.type_hints[param_name]
                
                # Convert string to expected type if needed
                if isinstance(param_value, str) and expected_type != str:
                    try:
                        if expected_type == int:
                            param_value = int(param_value)
                        elif expected_type == float:
                            param_value = float(param_value)
                        elif expected_type == bool:
                            param_value = param_value.lower() in ('true', '1', 'yes')
                    except ValueError:
                        pass  # Keep original value if conversion fails
                
                validated[param_name] = param_value
            else:
                # No type hint, keep as is
                validated[param_name] = param_value
        
        return validated


class DualUseTool(FunctionTool):
    """A tool that can be used both as a tool and called directly."""
    
    def __call__(self, *args, **kwargs):
        """Allow direct calling of the tool."""
        # For direct calls, we bypass the ToolResult wrapper
        if self.is_async:
            # Return the coroutine for async functions
            return self.func(*args, **kwargs)
        else:
            # Call synchronously
            return self.func(*args, **kwargs)


def tool(name: Optional[str] = None, description: Optional[str] = None, cost: int = 0, session_required: bool = False):
    """Decorator to convert a function into a tool.
    
    Args:
        name: Optional tool name
        description: Optional tool description
        cost: Cost in satoshis to execute the tool
        session_required: Whether the tool requires a session to operate.
        
    Example:
        @tool(description="Add two numbers", cost=10)
        def add(a: int, b: int) -> int:
            return a + b
            
        # Can be used as a tool:
        result = await add.execute(a=1, b=2)  # Returns ToolResult
        
        # Or called directly:
        result = add(1, 2)  # Returns 3
    """
    def decorator(func: Callable) -> DualUseTool:
        return DualUseTool(func, name=name, description=description, cost=cost, session_required=session_required)
    
    return decorator

