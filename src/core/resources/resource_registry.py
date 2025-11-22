"""
Resource Registry - Centralized management of MCP servers, tools, and skills.

Manages all available resources for dynamic injection into roles.
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import yaml

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class MCPServerConfig:
    """MCP Server configuration"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class SkillPrompt:
    """Skill prompt for role enhancement"""
    name: str
    category: str
    prompt: str
    tags: List[str] = field(default_factory=list)


@dataclass
class ToolMapping:
    """Mission type to tool mapping"""
    mission_type: str
    required_tools: List[str] = field(default_factory=list)
    optional_tools: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)


class ResourceRegistry:
    """
    Resource Registry - Centralized resource management.

    Loads and manages:
    - MCP server configurations
    - Skill prompts
    - Tool mappings

    Provides methods to query resources for dynamic injection.
    """

    def __init__(self, config_dir: str = "resources"):
        """
        Initialize resource registry.

        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = Path(config_dir)

        # Resource storage
        self.mcp_servers: Dict[str, MCPServerConfig] = {}
        self.skills: Dict[str, SkillPrompt] = {}
        self.tool_mappings: Dict[str, ToolMapping] = {}

        # Load configurations
        self._load_mcp_servers()
        self._load_skills()
        self._load_tool_mappings()

        logger.info(f"📚 Resource Registry initialized")
        logger.info(f"   MCP Servers: {len(self.mcp_servers)}")
        logger.info(f"   Skills: {len(self.skills)}")
        logger.info(f"   Tool Mappings: {len(self.tool_mappings)}")

    def _load_mcp_servers(self):
        """Load MCP server configurations from YAML"""
        config_file = self.config_dir / "mcp_servers.yaml"

        if not config_file.exists():
            logger.warning(f"MCP config not found: {config_file}")
            self._create_default_mcp_config(config_file)
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            for name, config in data.get('mcp_servers', {}).items():
                self.mcp_servers[name] = MCPServerConfig(
                    name=name,
                    command=config.get('command', ''),
                    args=config.get('args', []),
                    env=config.get('env', {}),
                    capabilities=config.get('capabilities', []),
                    description=config.get('description', '')
                )

            logger.info(f"✅ Loaded {len(self.mcp_servers)} MCP servers")

        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")

    def _load_skills(self):
        """Load skill prompts from YAML"""
        config_file = self.config_dir / "skill_prompts.yaml"

        if not config_file.exists():
            logger.warning(f"Skills config not found: {config_file}")
            self._create_default_skills_config(config_file)
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            for name, config in data.get('skills', {}).items():
                self.skills[name] = SkillPrompt(
                    name=name,
                    category=config.get('category', ''),
                    prompt=config.get('prompt', ''),
                    tags=config.get('tags', [])
                )

            logger.info(f"✅ Loaded {len(self.skills)} skill prompts")

        except Exception as e:
            logger.error(f"Failed to load skills config: {e}")

    def _load_tool_mappings(self):
        """Load tool mappings from YAML"""
        config_file = self.config_dir / "tool_mappings.yaml"

        if not config_file.exists():
            logger.warning(f"Tool mappings not found: {config_file}")
            self._create_default_mappings_config(config_file)
            return

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            for mission_type, config in data.get('mappings', {}).items():
                self.tool_mappings[mission_type] = ToolMapping(
                    mission_type=mission_type,
                    required_tools=config.get('required_tools', []),
                    optional_tools=config.get('optional_tools', []),
                    mcp_servers=config.get('mcp_servers', [])
                )

            logger.info(f"✅ Loaded {len(self.tool_mappings)} tool mappings")

        except Exception as e:
            logger.error(f"Failed to load tool mappings: {e}")

    def _create_default_mcp_config(self, config_file: Path):
        """Create default MCP configuration"""
        config_file.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            "mcp_servers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"],
                    "capabilities": ["read_file", "write_file", "list_directory"],
                    "description": "Local filesystem access"
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Created default MCP config: {config_file}")

    def _create_default_skills_config(self, config_file: Path):
        """Create default skills configuration"""
        config_file.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            "skills": {
                "market_analyst": {
                    "category": "research",
                    "prompt": "You are an expert market analyst with deep experience in competitive intelligence and market sizing.",
                    "tags": ["research", "market_analysis"]
                },
                "python_expert": {
                    "category": "engineering",
                    "prompt": "You are a senior Python developer with expertise in clean architecture and best practices.",
                    "tags": ["engineering", "python"]
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Created default skills config: {config_file}")

    def _create_default_mappings_config(self, config_file: Path):
        """Create default tool mappings configuration"""
        config_file.parent.mkdir(parents=True, exist_ok=True)

        default_config = {
            "mappings": {
                "market_research": {
                    "required_tools": ["web_search", "write_file"],
                    "optional_tools": ["deep_research"],
                    "mcp_servers": ["filesystem"]
                },
                "documentation": {
                    "required_tools": ["write_file", "read_file"],
                    "optional_tools": [],
                    "mcp_servers": ["filesystem"]
                }
            }
        }

        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Created default tool mappings: {config_file}")

    def get_mcp_for_mission(self, mission_type: str) -> List[MCPServerConfig]:
        """
        Get MCP servers required for a mission type.

        Args:
            mission_type: Type of mission

        Returns:
            List of MCP server configurations
        """
        mapping = self.tool_mappings.get(mission_type)
        if not mapping:
            logger.warning(f"No tool mapping for mission type: {mission_type}")
            return []

        servers = []
        for server_name in mapping.mcp_servers:
            if server_name in self.mcp_servers:
                servers.append(self.mcp_servers[server_name])
            else:
                logger.warning(f"MCP server not found: {server_name}")

        return servers

    def get_tools_for_mission(self, mission_type: str) -> List[str]:
        """
        Get tools required for a mission type.

        Args:
            mission_type: Type of mission

        Returns:
            List of tool names
        """
        mapping = self.tool_mappings.get(mission_type)
        if not mapping:
            return []

        return mapping.required_tools + mapping.optional_tools

    def get_skill_for_role(self, role_category: str) -> Optional[SkillPrompt]:
        """
        Get skill prompt for a role category.

        Args:
            role_category: Category of role (research, engineering, etc.)

        Returns:
            SkillPrompt if found, None otherwise
        """
        for skill in self.skills.values():
            if skill.category == role_category:
                return skill

        logger.warning(f"No skill found for category: {role_category}")
        return None

    def get_skill_by_name(self, name: str) -> Optional[SkillPrompt]:
        """Get skill by name"""
        return self.skills.get(name)

    def get_mcp_by_name(self, name: str) -> Optional[MCPServerConfig]:
        """Get MCP server by name"""
        return self.mcp_servers.get(name)

    def list_all_resources(self) -> Dict[str, Any]:
        """List all available resources"""
        return {
            "mcp_servers": list(self.mcp_servers.keys()),
            "skills": list(self.skills.keys()),
            "tool_mappings": list(self.tool_mappings.keys())
        }
