"""
Superpowers Adapter - Integrates Superpowers Commands with Agentic Skills

This module provides practical integration between:
- Superpowers-style /commands (user-invoked)
- Agentic Skills (prompt templates with logic flows)

Usage:
    from src.core.superpowers_adapter import execute_with_skill, list_available_commands

    # Execute a command with agentic skill enhancement
    result = execute_with_skill("/commit", {
        "changes": "Added user authentication",
        "branch": "feature/auth"
    })

    # List all available commands
    commands = list_available_commands()
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

from src.utils.logger import get_logger

logger = get_logger()


class CommandCategory(Enum):
    """Categories of commands"""
    CODE = "code"
    PLANNING = "planning"
    RESEARCH = "research"
    AUTOMATION = "automation"


class SuperpowersAdapter:
    """
    Adapter that bridges Superpowers commands with Agentic Skills
    """

    def __init__(
        self,
        config_path: str = "resources/superpowers_integration.yaml",
        skills_path: str = "resources/skill_prompts.yaml"
    ):
        self.config_path = Path(config_path)
        self.skills_path = Path(skills_path)
        self.config = self._load_config()
        self.skills = self._load_skills()
        self._build_command_index()

    def _load_config(self) -> Dict[str, Any]:
        """Load integration configuration"""
        if not self.config_path.exists():
            logger.warning(f"Integration config not found: {self.config_path}")
            return self._default_config()

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_skills(self) -> Dict[str, Any]:
        """Load agentic skills configuration"""
        if not self.skills_path.exists():
            logger.warning(f"Skills config not found: {self.skills_path}")
            return {}

        with open(self.skills_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config.get('skills', {})

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration if file not found"""
        return {
            "integration": {"enabled": True, "version": "1.0"},
            "commands": {},
            "skill_enhancement": {
                "include_sections": ["role", "logic_flow", "constraints"],
                "combination_strategy": "merge",
                "priority": "skill_over_command"
            },
            "output": {
                "show_skill_info": True,
                "format": "markdown"
            },
            "fallback": {
                "on_unknown_command": "execute_without_skill",
                "fallback_skill": "complex_problem_solver"
            }
        }

    def _build_command_index(self):
        """Build index mapping command names to their configurations"""
        self.command_index: Dict[str, Dict[str, Any]] = {}

        commands_config = self.config.get('commands', {})
        for cmd_name, cmd_config in commands_config.items():
            self.command_index[cmd_name] = {
                "skill_name": cmd_config.get("skill"),
                "purpose": cmd_config.get("purpose", ""),
                "auto_apply": cmd_config.get("auto_apply", True),
                "enhancement": cmd_config.get("skill_enhancement", {}),
                "output_format": cmd_config.get("output_format")
            }

    def execute_with_skill(
        self,
        command: str,
        context: Dict[str, Any],
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a command enhanced with agentic skill

        Args:
            command: Command name (e.g., "/commit", "/plan")
            context: Execution context
            custom_instructions: Additional user instructions

        Returns:
            Result containing:
            - enhanced_prompt: The prompt to use
            - skill_used: Which agentic skill was applied
            - metadata: Additional execution metadata
        """
        # Normalize command name
        command = command if command.startswith("/") else f"/{command}"

        # Check if integration is enabled
        if not self.config.get('integration', {}).get('enabled', False):
            return self._execute_without_skill(command, context)

        # Get command configuration
        cmd_config = self.command_index.get(command)
        if not cmd_config:
            return self._handle_unknown_command(command, context)

        # Get skill configuration
        skill_name = cmd_config["skill_name"]
        skill_config = self.skills.get(skill_name, {})

        if not skill_config:
            logger.warning(f"Skill not found: {skill_name}")
            return self._handle_missing_skill(command, context, skill_name)

        # Build enhanced prompt
        enhanced_prompt = self._build_enhanced_prompt(
            command,
            context,
            cmd_config,
            skill_config,
            custom_instructions
        )

        return {
            "enhanced_prompt": enhanced_prompt,
            "skill_used": skill_name,
            "skill_role": skill_config.get("role"),
            "command": command,
            "purpose": cmd_config["purpose"],
            "success": True,
            "metadata": {
                "integration_version": self.config.get('integration', {}).get('version'),
                "enhancement_applied": True
            }
        }

    def _build_enhanced_prompt(
        self,
        command: str,
        context: Dict[str, Any],
        cmd_config: Dict[str, Any],
        skill_config: Dict[str, Any],
        custom_instructions: Optional[str]
    ) -> str:
        """Build the enhanced prompt combining command and skill"""

        # Get enhancement settings
        enhancement_config = cmd_config.get("skill_enhancement", {})
        include_sections = self.config.get('skill_enhancement', {}).get(
            'include_sections',
            ['role', 'logic_flow', 'constraints']
        )

        # Build prompt sections
        prompt_parts = []

        # 1. Header with command info
        prompt_parts.append(f"# Command: {command}")
        prompt_parts.append(f"# Purpose: {cmd_config['purpose']}\n")

        # 2. Role (if included)
        if 'role' in include_sections and 'role' in skill_config:
            prompt_parts.append(f"## Role")
            prompt_parts.append(skill_config['role'])
            prompt_parts.append("")

        # 3. Task Context
        prompt_parts.append("## Task Context")
        prompt_parts.append(self._format_context(context))
        prompt_parts.append("")

        # 4. Logic Flow (if included)
        if 'logic_flow' in include_sections and 'logic_flow' in skill_config:
            prompt_parts.append("## Approach")
            prompt_parts.append(skill_config['logic_flow'])
            prompt_parts.append("")

        # 5. Constraints (if included)
        if 'constraints' in include_sections and 'constraints' in skill_config:
            prompt_parts.append("## Constraints")
            for constraint in skill_config['constraints']:
                prompt_parts.append(f"- {constraint}")
            prompt_parts.append("")

        # 6. Tool Preferences (if available)
        if 'tool_preference' in skill_config:
            prompt_parts.append("## Available Tools")
            tools = skill_config['tool_preference']
            if isinstance(tools, dict):
                for category, tool_list in tools.items():
                    prompt_parts.append(f"- {category}: {', '.join(tool_list)}")
            prompt_parts.append("")

        # 7. Reflection Questions (if included)
        if 'reflection' in include_sections and 'reflection' in skill_config:
            prompt_parts.append("## Self-Reflection Questions")
            for question in skill_config['reflection']:
                prompt_parts.append(f"- {question}")
            prompt_parts.append("")

        # 8. Custom Instructions (if provided)
        if custom_instructions:
            prompt_parts.append("## Additional Instructions")
            prompt_parts.append(custom_instructions)
            prompt_parts.append("")

        # 9. Output Format (if specified)
        output_format = cmd_config.get('output_format')
        if output_format:
            prompt_parts.append(f"## Output Format")
            prompt_parts.append(f"Please provide output in: {output_format} format")
            prompt_parts.append("")

        return "\n".join(prompt_parts)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context into readable string"""
        lines = []

        for key, value in context.items():
            if isinstance(value, str):
                lines.append(f"- **{key}**: {value}")
            elif isinstance(value, (int, float, bool)):
                lines.append(f"- **{key}**: {value}")
            elif isinstance(value, list):
                items = [str(v) for v in value[:5]]  # Limit to 5 items
                if len(value) > 5:
                    items.append(f"... and {len(value) - 5} more")
                lines.append(f"- **{key}**: {', '.join(items)}")
            elif isinstance(value, dict):
                lines.append(f"- **{key}**: <complex object with {len(value)} keys>")
            else:
                lines.append(f"- **{key}**: {type(value).__name__}")

        return "\n".join(lines) if lines else "- (no context provided)"

    def _execute_without_skill(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute command without agentic skill enhancement"""
        return {
            "enhanced_prompt": f"Execute command: {command}\n\nContext: {self._format_context(context)}",
            "skill_used": None,
            "command": command,
            "success": True,
            "metadata": {"enhancement_applied": False}
        }

    def _handle_unknown_command(self, command: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown command based on fallback configuration"""
        fallback = self.config.get('fallback', {})
        strategy = fallback.get('on_unknown_command', 'execute_without_skill')

        logger.warning(f"Unknown command: {command}, using fallback: {strategy}")

        if strategy == 'error':
            return {
                "error": f"Unknown command: {command}",
                "success": False,
                "available_commands": list(self.command_index.keys())
            }
        elif strategy == 'ask_user':
            return {
                "prompt": f"Command '{command}' not recognized. Available commands: {', '.join(self.command_index.keys())}",
                "success": False,
                "requires_user_input": True
            }
        else:  # execute_without_skill
            return self._execute_without_skill(command, context)

    def _handle_missing_skill(
        self,
        command: str,
        context: Dict[str, Any],
        skill_name: str
    ) -> Dict[str, Any]:
        """Handle missing agentic skill"""
        fallback = self.config.get('fallback', {})
        strategy = fallback.get('on_missing_skill', 'warn_and_continue')

        logger.warning(f"Skill not found: {skill_name}, fallback: {strategy}")

        if strategy == 'error':
            return {
                "error": f"Required skill not found: {skill_name}",
                "success": False
            }
        else:  # warn_and_continue
            return self._execute_without_skill(command, context)

    def list_available_commands(
        self,
        category: Optional[CommandCategory] = None
    ) -> List[Dict[str, str]]:
        """
        List all available commands

        Args:
            category: Optional category filter

        Returns:
            List of command information
        """
        commands = []

        for cmd_name, cmd_config in self.command_index.items():
            cmd_info = {
                "name": cmd_name,
                "purpose": cmd_config["purpose"],
                "skill": cmd_config["skill_name"],
                "auto_apply": cmd_config["auto_apply"]
            }

            # Add category based on command name
            if any(x in cmd_name for x in ['/commit', '/review', '/test', '/analyze']):
                cmd_info["category"] = CommandCategory.CODE.value
            elif any(x in cmd_name for x in ['/plan', '/brainstorm', '/architecture']):
                cmd_info["category"] = CommandCategory.PLANNING.value
            elif any(x in cmd_name for x in ['/market-research', '/docs', '/research']):
                cmd_info["category"] = CommandCategory.RESEARCH.value
            elif any(x in cmd_name for x in ['/scrape', '/automate']):
                cmd_info["category"] = CommandCategory.AUTOMATION.value
            else:
                cmd_info["category"] = "general"

            # Filter by category if specified
            if category is None or cmd_info["category"] == category.value:
                commands.append(cmd_info)

        return sorted(commands, key=lambda x: x["name"])

    def get_command_example(self, command: str) -> Optional[Dict[str, Any]]:
        """Get example usage for a command"""
        examples = self.config.get('examples', {})
        return examples.get(command)


# Global adapter instance
_adapter = None

def get_adapter() -> SuperpowersAdapter:
    """Get or create global adapter instance"""
    global _adapter
    if _adapter is None:
        _adapter = SuperpowersAdapter()
    return _adapter


def execute_with_skill(
    command: str,
    context: Dict[str, Any],
    custom_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to execute command with agentic skill

    Args:
        command: Command name (e.g., "/commit", "/plan")
        context: Execution context
        custom_instructions: Additional instructions

    Returns:
        Execution result with enhanced prompt

    Example:
        result = execute_with_skill("/commit", {
            "changes": "Added OAuth2 authentication",
            "branch": "feature/oauth2"
        })
        print(result["enhanced_prompt"])
    """
    adapter = get_adapter()
    return adapter.execute_with_skill(command, context, custom_instructions)


def list_available_commands(
    category: Optional[CommandCategory] = None
) -> List[Dict[str, str]]:
    """
    List all available commands

    Args:
        category: Optional category filter

    Returns:
        List of command information
    """
    adapter = get_adapter()
    return adapter.list_available_commands(category)


if __name__ == "__main__":
    # Example usage
    print("=" * 60)
    print("Superpowers Adapter - Available Commands")
    print("=" * 60)

    for category in CommandCategory:
        print(f"\n## {category.value.upper()} Commands")
        commands = list_available_commands(category)
        for cmd in commands:
            print(f"  {cmd['name']}: {cmd['purpose']}")
            print(f"    → Skill: {cmd['skill']}")
            print(f"    → Auto-apply: {cmd['auto_apply']}")

    # Example: Get enhanced prompt for /commit
    print("\n" + "=" * 60)
    print("Example: Enhanced Prompt for /commit")
    print("=" * 60)

    result = execute_with_skill("/commit", {
        "changes": "Implemented user authentication with OAuth2",
        "branch": "feature/oauth2",
        "files": ["src/auth/oauth.py", "src/auth/handlers.py"]
    })

    print(result["enhanced_prompt"])
