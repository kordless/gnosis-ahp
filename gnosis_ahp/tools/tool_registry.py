"""Dynamic tool discovery and registry system."""

import os
import importlib
import importlib.util
import inspect
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Set
from collections import defaultdict

from gnosis_ahp.tools.base import BaseTool, FunctionTool, tool
#from gnosis_ahp.utils.errors import ToolError, ValidationError

# Simple error classes to avoid dependency on a full utils package for now
class ToolError(Exception):
    pass

class ValidationError(Exception):
    pass


logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for discovering and managing tools."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, Set[str]] = defaultdict(set)
        self.usage_limits: Dict[str, int] = {}
        self.usage_counts: Dict[str, int] = defaultdict(int)
        
    def register(
        self, 
        tool_obj: Union[BaseTool, Callable, type],
        category: Optional[str] = None,
        usage_limit: Optional[int] = None,
        override: bool = False
    ) -> None:
        """Register a tool in the registry.
        
        Args:
            tool_obj: Tool instance, function, or tool class
            category: Optional category for organization
            usage_limit: Optional usage limit (None = unlimited)
            override: Whether to override existing tool
            
        Raises:
            ToolError: If tool is invalid or already registered
        """
        # Convert functions to FunctionTool
        if callable(tool_obj) and not isinstance(tool_obj, BaseTool):
            if inspect.isclass(tool_obj) and issubclass(tool_obj, BaseTool):
                # It's a tool class, instantiate it
                tool_instance = tool_obj()
            else:
                # It's a regular function, wrap it
                tool_instance = FunctionTool(tool_obj)
        else:
            tool_instance = tool_obj

        if not isinstance(tool_instance, BaseTool):
            raise ToolError(f"Invalid tool type: {type(tool_instance)}")
        
        # Check for duplicates
        if tool_instance.name in self.tools and not override:
            raise ToolError(f"Tool '{tool_instance.name}' already registered")
        
        # Validate the tool
        try:
            schema = tool_instance.get_schema()
            if not schema.get("name") or not schema.get("description"):
                raise ValidationError("Tool must have name and description")
        except Exception as e:
            raise ToolError(f"Invalid tool schema: {str(e)}")
        
        # Register the tool
        self.tools[tool_instance.name] = {
            "instance": tool_instance,
            "schema": schema,
            "category": category or "general",
            "usage_limit": usage_limit
        }
        
        # Add to category
        if category:
            self.categories[category].add(tool_instance.name)
        
        # Set usage limit
        if usage_limit is not None:
            self.usage_limits[tool_instance.name] = usage_limit
        
        logger.info(f"Registered tool: {tool_instance.name} (category: {category or 'general'})")
    
    def discover_tools(
        self, 
        path: Union[str, Path],
        category: Optional[str] = None,
        recursive: bool = True,
        strict: bool = False
    ) -> List[Dict[str, Any]]:
        """Discover tools from a file or directory.
        
        Args:
            path: File or directory path to scan
            category: Category to assign discovered tools
            recursive: Whether to scan directories recursively
            strict: Whether to raise errors on invalid tools
            
        Returns:
            List of discovered tool schemas
        """
        path = Path(path)
        discovered = []
        
        if path.is_file() and path.suffix == '.py':
            # Single file
            tools_to_reg = self._extract_tools_from_file(path, strict)
            for t in tools_to_reg:
                try:
                    self.register(t, category=category)
                    discovered.append(t.get_schema())
                except ToolError as e:
                    if strict:
                        raise
                    logger.warning(f"Skipping invalid tool: {e}")
                    
        elif path.is_dir():
            # Directory
            pattern = "**/*.py" if recursive else "*.py"
            for py_file in path.glob(pattern):
                # Skip registry, base, init, and test files from discovery
                if py_file.name in ("__init__.py", "base.py", "tool_registry.py") or py_file.name.startswith("test_"):
                    continue
                    
                tools_to_reg = self._extract_tools_from_file(py_file, strict)
                for t in tools_to_reg:
                    try:
                        # Use file name as category if none provided
                        file_category = category or py_file.stem
                        self.register(t, category=file_category)
                        discovered.append(t.get_schema())
                    except ToolError as e:
                        if strict:
                            raise
                        logger.warning(f"Skipping invalid tool in {py_file}: {e}")
        
        logger.info(f"Discovered {len(discovered)} tools from {path}")
        return discovered
    
    def _extract_tools_from_file(self, file_path: Path, strict: bool = True) -> List[BaseTool]:
        """Extract tool instances from a Python file."""
        tools = []
        module_name = f"gnosis_ahp.tools.{file_path.stem}"
        
        try:
            module = importlib.import_module(module_name)
            
            # Find tools in module
            for name, obj in inspect.getmembers(module):
                if name.startswith('_'):
                    continue
                
                if isinstance(obj, BaseTool):
                    tools.append(obj)
                elif inspect.isclass(obj) and issubclass(obj, BaseTool) and obj != BaseTool:
                    try:
                        tools.append(obj())
                    except Exception as e:
                        if strict:
                            raise ToolError(f"Could not instantiate {obj}: {e}")
                        logger.warning(f"Could not instantiate tool '{obj.__name__}' from {file_path.name}: {e}")

        except ImportError as e:
            logger.warning(f"Skipping tool file {file_path.name} due to missing dependency: {e}")
            if strict:
                raise ToolError(f"Could not import module {module_name}: {e}")
        except Exception as e:
            if strict:
                raise ToolError(f"Error loading tools from {file_path}: {e}")
            logger.error(f"Error loading module {module_name}: {e}", exc_info=True)
        
        return tools

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool instance by name."""
        if name not in self.tools:
            raise ToolError(f"Tool '{name}' not found")
        
        if name in self.usage_limits and self.usage_counts[name] >= self.usage_limits[name]:
            raise ToolError(f"Tool '{name}' usage limit exceeded")
        
        self.usage_counts[name] += 1
        return self.tools[name]["instance"]

    def get_all_tools(self) -> List[BaseTool]:
        """Get all registered tools."""
        return [tool_data["instance"] for tool_data in self.tools.values()]
    
    def get_schemas(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get schemas for tools."""
        if category:
            tool_names = self.categories.get(category, set())
            return [self.tools[name]["schema"] for name in tool_names if name in self.tools]
        else:
            return [tool_data["schema"] for tool_data in self.tools.values()]

    def list_categories(self) -> List[str]:
        """List all tool categories."""
        return list(self.categories.keys())

# Global registry instance
_global_registry = ToolRegistry()

def get_global_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return _global_registry
