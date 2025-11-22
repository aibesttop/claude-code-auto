"""
Resources Module - Centralized resource management.

Manages MCP servers, skill prompts, and tool mappings for dynamic injection.
"""

from src.core.resources.resource_registry import ResourceRegistry, MCPServerConfig, SkillPrompt

__all__ = [
    'ResourceRegistry',
    'MCPServerConfig',
    'SkillPrompt',
]
