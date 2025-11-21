"""
Core Tool Registry System
Implements a lightweight MCP-like protocol for defining and executing tools.
"""
import inspect
import json
import functools
from typing import Callable, Dict, Any, List, Optional, get_type_hints
from pydantic import BaseModel, create_model
from logger import get_logger

logger = get_logger()

class Tool:
    """Represents a callable tool with schema"""
    def __init__(self, func: Callable, name: str = None, description: str = None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or "No description provided."
        self.schema = self._generate_schema()

    def _generate_schema(self) -> Dict[str, Any]:
        """Generates JSON schema from type hints"""
        type_hints = get_type_hints(self.func)
        params = {}
        required = []
        
        sig = inspect.signature(self.func)
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
                
            param_type = type_hints.get(param_name, str)
            # Map Python types to JSON types (simplified)
            type_map = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object"
            }
            json_type = type_map.get(param_type, "string")
            
            params[param_name] = {
                "type": json_type,
                "description": f"Parameter {param_name}" # Could parse docstring for better desc
            }
            
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": params,
                "required": required
            }
        }

    def execute(self, **kwargs) -> Any:
        """Executes the tool"""
        try:
            logger.info(f"🔧 Executing tool: {self.name} with args: {kwargs}")
            return self.func(**kwargs)
        except Exception as e:
            logger.error(f"❌ Tool execution failed: {e}")
            raise

class ToolRegistry:
    """Registry for managing tools"""
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool instance"""
        if tool.name in self._tools:
            logger.warning(f"⚠️ Overwriting existing tool: {tool.name}")
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def register_function(self, func: Callable):
        """Decorator to register a function as a tool"""
        tool = Tool(func)
        self.register(tool)
        return func

    def get_tool(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools"""
        return [tool.schema for tool in self._tools.values()]

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return tool.execute(**arguments)

# Global registry instance
registry = ToolRegistry()

def tool(func):
    """Decorator for defining tools"""
    registry.register_function(func)
    return func
