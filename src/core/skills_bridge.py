"""
Skills Bridge - Integrating Superpowers Commands with Agentic Skills

This module creates a bridge between:
1. Superpowers-style commands (user-invoked workflows)
2. Agentic Skills (AI-driven prompt templates with logic flows)

The bridge allows commands to leverage agentic skills' structured reasoning,
while agentic skills can be exposed as invokable commands.
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import yaml
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger()


class CommandType(Enum):
    """Types of commands that can be bridged"""
    # Superpowers-style commands
    COMMIT = "commit"
    REVIEW_PR = "review_pr"
    TEST = "test"
    PLAN = "plan"
    BRAINSTORM = "brainstorm"

    # Agentic skill triggers
    MARKET_RESEARCH = "market_research"
    CODE_ANALYSIS = "code_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    TECHNICAL_WRITING = "technical_writing"


class CommandToSkillMapping:
    """
    Maps Superpowers-style commands to Agentic Skills
    """

    # Mapping of commands to skills with parameter transformation
    MAPPINGS: Dict[CommandType, Dict[str, Any]] = {
        CommandType.COMMIT: {
            "skill": "technical_writer",
            "purpose": "Generate high-quality commit messages",
            "params_transform": {
                "diff_content": "context.changes",
                "branch_name": "context.branch"
            }
        },

        CommandType.REVIEW_PR: {
            "skill": "code_analysis_expert",
            "purpose": "Comprehensive PR review against standards",
            "params_transform": {
                "pr_diff": "context.changes",
                "pr_description": "context.description"
            }
        },

        CommandType.TEST: {
            "skill": "python_expert",
            "purpose": "Generate comprehensive test coverage",
            "params_transform": {
                "target_files": "context.files",
                "existing_tests": "context.tests"
            }
        },

        CommandType.PLAN: {
            "skill": "complex_problem_solver",
            "purpose": "Break down complex tasks into implementation plans",
            "params_transform": {
                "requirement": "context.task",
                "constraints": "context.constraints"
            }
        },

        CommandType.BRAINSTORM: {
            "skill": "creative_innovator",
            "purpose": "Generate diverse creative solutions",
            "params_transform": {
                "problem": "context.challenge",
                "constraints": "context.limitations"
            }
        },

        CommandType.MARKET_RESEARCH: {
            "skill": "market_analyst",
            "purpose": "Conduct market research with proper frameworks",
            "params_transform": {
                "research_question": "context.query",
                "target_market": "context.market"
            }
        },

        CommandType.CODE_ANALYSIS: {
            "skill": "code_analysis_expert",
            "purpose": "Analyze codebase for quality and improvements",
            "params_transform": {
                "target_path": "context.path",
                "analysis_type": "context.type"
            }
        },

        CommandType.ARCHITECTURE_DESIGN: {
            "skill": "system_architect",
            "purpose": "Design system architecture with trade-offs",
            "params_transform": {
                "requirements": "context.requirements",
                "constraints": "context.constraints"
            }
        },

        CommandType.TECHNICAL_WRITING: {
            "skill": "technical_writer",
            "purpose": "Create clear technical documentation",
            "params_transform": {
                "content": "context.material",
                "audience": "context.audience"
            }
        }
    }

    @classmethod
    def get_skill_for_command(cls, command: CommandType) -> Optional[Dict[str, Any]]:
        """Get the agentic skill configuration for a given command"""
        return cls.MAPPINGS.get(command)

    @classmethod
    def transform_params(cls, command: CommandType, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform command context into skill parameters

        Args:
            command: The command type being executed
            context: Raw context from the command execution

        Returns:
            Transformed parameters suitable for the agentic skill
        """
        mapping = cls.get_skill_for_command(command)
        if not mapping:
            return {}

        params = {}
        transform_rules = mapping.get("params_transform", {})

        for skill_param, context_path in transform_rules.items():
            # Navigate through nested context (e.g., "context.changes")
            value = context
            for key in context_path.split("."):
                value = value.get(key, {}) if isinstance(value, dict) else None
                if value is None:
                    break

            if value is not None:
                params[skill_param] = value

        return params


class SkillPromptBuilder:
    """
    Builds enhanced prompts by combining command intent with agentic skill structure
    """

    def __init__(self, skills_config_path: str = "resources/skill_prompts.yaml"):
        self.skills_config_path = Path(skills_config_path)
        self.skills = self._load_skills()

    def _load_skills(self) -> Dict[str, Any]:
        """Load agentic skills configuration"""
        if not self.skills_config_path.exists():
            logger.warning(f"Skills config not found: {self.skills_config_path}")
            return {}

        with open(self.skills_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        return config.get('skills', {})

    def build_prompt(
        self,
        command: CommandType,
        context: Dict[str, Any],
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Build an enhanced prompt combining command and agentic skill

        Args:
            command: The command being executed
            context: Execution context
            custom_instructions: Any additional user instructions

        Returns:
            Enhanced prompt string
        """
        # Get mapping
        mapping = CommandToSkillMapping.get_skill_for_command(command)
        if not mapping:
            return self._fallback_prompt(context)

        # Get skill configuration
        skill_name = mapping.get("skill")
        skill_config = self.skills.get(skill_name, {})

        # Build prompt
        prompt_parts = [
            f"# Role: {skill_config.get('role', 'AI Assistant')}",
            f"\n# Purpose: {mapping.get('purpose', 'Execute task')}",
            f"\n# Task Context:",
            f"{self._format_context(context)}",
            f"\n# Approach (from {skill_name} skill):",
            f"\n{skill_config.get('logic_flow', 'Proceed with task')}",
        ]

        # Add constraints
        if 'constraints' in skill_config:
            prompt_parts.append(
                f"\n# Constraints:\n" +
                "\n".join(f"- {c}" for c in skill_config['constraints'])
            )

        # Add reflection questions
        if 'reflection' in skill_config:
            prompt_parts.append(
                f"\n# Self-Reflection:\n" +
                "\n".join(f"- {r}" for r in skill_config['reflection'])
            )

        # Add custom instructions
        if custom_instructions:
            prompt_parts.append(f"\n# Additional Instructions:\n{custom_instructions}")

        return "\n".join(prompt_parts)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context into readable string"""
        lines = []
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"  - {key}: {value}")
            elif isinstance(value, list):
                lines.append(f"  - {key}: [{', '.join(str(v) for v in value[:3])}...]")
            elif isinstance(value, dict):
                lines.append(f"  - {key}: <complex object>")
        return "\n".join(lines) if lines else "  (no context provided)"

    def _fallback_prompt(self, context: Dict[str, Any]) -> str:
        """Fallback prompt when no skill mapping exists"""
        return f"""# Task Execution

Execute the following task to the best of your ability.

## Context:
{self._format_context(context)}

## Instructions:
1. Analyze the request carefully
2. Execute with appropriate tools
3. Provide clear output
"""


class AgenticCommandRegistry:
    """
    Registry that exposes agentic skills as invokable commands
    """

    def __init__(self):
        self.bridge = CommandToSkillMapping()
        self.prompt_builder = SkillPromptBuilder()
        self._registered_commands: Dict[str, CommandType] = {}

    def register_command(self, name: str, command_type: CommandType):
        """Register a new command"""
        self._registered_commands[name] = command_type
        logger.info(f"Registered command: {name} -> {command_type.value}")

    def execute_command(
        self,
        command_name: str,
        context: Dict[str, Any],
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Execute a command using its associated agentic skill

        Args:
            command_name: Name of the command to execute
            context: Execution context
            custom_instructions: Additional instructions

        Returns:
            Enhanced prompt for execution
        """
        if command_name not in self._registered_commands:
            logger.warning(f"Unknown command: {command_name}")
            return self.prompt_builder._fallback_prompt(context)

        command_type = self._registered_commands[command_name]
        return self.prompt_builder.build_prompt(command_type, context, custom_instructions)

    def list_commands(self) -> List[Dict[str, str]]:
        """List all registered commands"""
        return [
            {
                "name": name,
                "type": cmd_type.value,
                "skill": self.bridge.get_skill_for_command(cmd_type).get("skill", "unknown"),
                "purpose": self.bridge.get_skill_for_command(cmd_type).get("purpose", "")
            }
            for name, cmd_type in self._registered_commands.items()
        ]


# Global registry instance
agentic_command_registry = AgenticCommandRegistry()

# Register default commands
_default_commands = {
    "/commit": CommandType.COMMIT,
    "/review": CommandType.REVIEW_PR,
    "/test": CommandType.TEST,
    "/plan": CommandType.PLAN,
    "/brainstorm": CommandType.BRAINSTORM,
    "/market-research": CommandType.MARKET_RESEARCH,
    "/analyze": CommandType.CODE_ANALYSIS,
    "/architecture": CommandType.ARCHITECTURE_DESIGN,
    "/docs": CommandType.TECHNICAL_WRITING,
}

for cmd_name, cmd_type in _default_commands.items():
    agentic_command_registry.register_command(cmd_name, cmd_type)


def get_agentic_prompt(command_name: str, context: Dict[str, Any]) -> str:
    """
    Convenience function to get agentic-enhanced prompt for a command

    Args:
        command_name: The command to execute (e.g., "/commit", "/plan")
        context: Execution context

    Returns:
        Enhanced prompt combining command with agentic skill
    """
    return agentic_command_registry.execute_command(command_name, context)


if __name__ == "__main__":
    # Example usage
    print("=== Agentic Command Registry ===")
    for cmd in agentic_command_registry.list_commands():
        print(f"{cmd['name']}: {cmd['purpose']}")
        print(f"  → Skill: {cmd['skill']}\n")

    # Example: Get prompt for /commit command
    print("\n=== Example: /commit Prompt ===")
    commit_prompt = get_agentic_prompt("/commit", {
        "context": {
            "changes": "Added new feature for user authentication",
            "branch": "feature/auth"
        }
    })
    print(commit_prompt[:500] + "...")
