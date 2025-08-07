"""Dynamic tool discovery and registry system."""

import os
import importlib
import importlib.util
import inspect
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Union, Set
from collections import defaultdict


from gnosis_ahp.tools.base import BaseTool, FunctionTool, tool

class ToolError(Exception):
    pass

class ValidationError(Exception):
    pass


logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for discovering and managing tools."""
    
    RESERVED_NAMES = {
        "auth", "openapi", "schema", "session", "human_home", 
        "robots.txt", "health", "static", "docs", "redoc"
    }
    RESERVED_PATTERN = re.compile(r"^(auth|openapi|schema|session|docs|redoc|health)(\/.*)?$")

    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, Set[str]] = defaultdict(set)
        
    def is_reserved(self, name: str) -> bool:
        """Check if a tool name conflicts with a reserved path."""
        return name in self.RESERVED_NAMES or self.RESERVED_PATTERN.match(name) is not None

    def register(self, tool_obj: Union[BaseTool, Callable, type], category: Optional[str] = None, override: bool = False) -> None:
        """Register a tool in the registry."""
        if callable(tool_obj) and not isinstance(tool_obj, BaseTool):
            tool_instance = FunctionTool(tool_obj) if not (inspect.isclass(tool_obj) and issubclass(tool_obj, BaseTool)) else tool_obj()
        else:
            tool_instance = tool_obj

        if not isinstance(tool_instance, BaseTool):
            raise ToolError(f"Invalid tool type: {type(tool_instance)}")
        
        if self.is_reserved(tool_instance.name):
            raise ToolError(f"Tool name '{tool_instance.name}' is reserved.")

        if tool_instance.name in self.tools and not override:
            raise ToolError(f"Tool '{tool_instance.name}' already registered.")
        
        try:
            schema = tool_instance.get_schema()
            if not schema.get("name") or not schema.get("description"):
                raise ValidationError("Tool must have name and description.")
        except Exception as e:
            raise ToolError(f"Invalid tool schema: {e}")
        
        self.tools[tool_instance.name] = {
            "instance": tool_instance,
            "schema": schema,
            "category": category or "general"
        }
        
        if category:
            self.categories[category].add(tool_instance.name)
        
        logger.info(f"Registered tool: {tool_instance.name} (category: {category or 'general'})")
    
    def discover_tools(self, path: Union[str, Path], strict: bool = False) -> List[Dict[str, Any]]:
        """Discover tools from a file or directory. By default, it will log errors and skip invalid tools."""
        ahp_env = os.getenv("AHP_ENVIRONMENT", "local")
        logger.info(f"Tool discovery running in '{ahp_env}' mode (strict={strict}).")

        path = Path(path)
        discovered_schemas = []
        
        files_to_scan = [path] if path.is_file() else path.glob("**/*.py")

        for py_file in files_to_scan:
            if py_file.name in ("__init__.py", "base.py", "tool_registry.py") or py_file.name.startswith("test_"):
                continue

            if ahp_env == "cloud" and py_file.name == "docker_api.py":
                logger.info("Skipping docker_api.py in cloud environment.")
                continue
                
            logger.info(f"Scanning for tools in: {py_file.name}")
            try:
                tools_to_reg = self._extract_tools_from_file(py_file)
                for t in tools_to_reg:
                    try:
                        file_category = py_file.stem
                        self.register(t, category=file_category)
                        discovered_schemas.append(t.get_schema())
                    except ToolError as e:
                        logger.warning(f"Skipping invalid tool '{getattr(t, 'name', 'unknown')}' in {py_file}: {e}")
            except (ToolError, SyntaxError, IndentationError) as e:
                if strict:
                    raise
                logger.error(f"Could not load tools from {py_file}: {e}", exc_info=True)
        
        logger.info(f"Discovered and registered {len(discovered_schemas)} tools from {path}")
        return discovered_schemas
    
    def _extract_tools_from_file(self, file_path: Path) -> List[BaseTool]:
        """Extract tool instances from a Python file."""
        tools = []
        module_name = f"gnosis_ahp.tools.{file_path.stem}"
        
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, BaseTool):
                    tools.append(obj)
        except Exception as e:
            # This will catch SyntaxError and other import-time problems.
            raise ToolError(f"Failed to import or inspect module {module_name} from {file_path}: {e}")
        
        return tools

    def get_tool(self, name: str) -> BaseTool:
        """Get a tool instance by name."""
        if name not in self.tools:
            raise ToolError(f"Tool '{name}' not found")
        return self.tools[name]["instance"]

    def get_schemas(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get schemas for tools."""
        if category:
            tool_names = self.categories.get(category, set())
            return [self.tools[name]["schema"] for name in tool_names if name in self.tools]
        return [data["schema"] for data in self.tools.values()]

_global_registry = ToolRegistry()

def get_global_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return _global_registry
