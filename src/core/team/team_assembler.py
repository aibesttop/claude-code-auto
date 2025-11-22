"""
Team Assembler

Analyzes initial_prompt and goal to determine which roles are needed.
"""

from typing import List, Dict, Any
from src.core.team.role_registry import RoleRegistry, Role
from src.core.team.dependency_resolver import (
    DependencyResolver,
    CircularDependencyError,
    MissingRoleError
)
from src.core.agents.sdk_client import run_claude_prompt
from src.utils.json_utils import extract_json
import logging

logger = logging.getLogger(__name__)


class TeamAssembler:
    """
    Assembles a team of roles based on initial_prompt and goal.
    
    Uses LLM to analyze the task and determine which roles are needed.
    """
    
    def __init__(self, role_registry: RoleRegistry):
        """
        Initialize the team assembler.
        
        Args:
            role_registry: Registry of available roles
        """
        self.registry = role_registry
    
    async def assemble_team(
        self,
        initial_prompt: str,
        goal: str,
        missions: List[Any] = None,  # Added missions parameter
        work_dir: str = ".",
        model: str = None,
        timeout: int = 60,
        permission_mode: str = "bypassPermissions"
    ) -> List[Role]:
        """
        Analyze initial_prompt and goal to determine which roles are needed.
        
        Args:
            initial_prompt: User's initial prompt describing the workflow
            goal: Overall goal to achieve
            work_dir: Working directory
            model: Claude model to use
            timeout: Timeout in seconds
            permission_mode: Permission mode for SDK
            
        Returns:
            List of Role objects in execution order
        """
        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(initial_prompt, goal, missions)
        
        # Call LLM to analyze
        logger.info("Analyzing initial_prompt to determine required roles...")
        
        try:
            response, _ = await run_claude_prompt(
                analysis_prompt,
                work_dir,
                model=model,
                timeout=timeout,
                permission_mode=permission_mode
            )
        except Exception as e:
            logger.error(f"Failed to call LLM for team assembly: {e}")
            return []
        
        # Parse response
        data = extract_json(response)
        if not data:
            logger.error("Failed to parse team assembly response")
            logger.debug(f"LLM response: {response[:500]}")
            return []
        
        role_names = data.get('roles', [])
        reasoning = data.get('reasoning', '')
        
        logger.info(f"Team assembled: {role_names}")
        logger.info(f"Reasoning: {reasoning}")
        
        # Load roles
        team = []
        for name in role_names:
            role = self.registry.get_role(name)
            if role:
                team.append(role)
            else:
                logger.warning(f"Role not found: {name}")

        if not team:
            logger.error("No valid roles loaded")
            return []

        # Sort roles by dependencies using topological sort
        logger.info("🔧 Resolving role dependencies...")
        resolver = DependencyResolver()

        try:
            # Validate dependencies first
            validation = resolver.validate_dependencies(team)
            if not validation.valid:
                logger.error(f"❌ Dependency validation failed: {validation.error}")
                return []

            if validation.warnings:
                for warning in validation.warnings:
                    logger.warning(f"⚠️ {warning}")

            # Perform topological sort
            sorted_team = resolver.topological_sort(team)
            sorted_names = [r.name for r in sorted_team]

            # Log execution plan
            logger.info(f"✅ Dependency resolution complete")
            logger.info(f"📋 Original LLM order: {role_names}")
            logger.info(f"📋 Dependency-sorted order: {sorted_names}")

            # Warn if LLM order differs from dependency order
            if role_names != sorted_names:
                logger.warning(
                    f"⚠️ LLM-suggested order differs from dependency requirements. "
                    f"Using dependency-correct order: {sorted_names}"
                )

            # Log detailed execution plan
            plan = resolver.format_execution_plan(sorted_team)
            logger.info(f"\n{plan}")

            return sorted_team

        except CircularDependencyError as e:
            logger.error(f"❌ Circular dependency detected: {e}")
            logger.error("Cannot proceed with team execution. Please fix role dependencies.")
            return []

        except MissingRoleError as e:
            logger.error(f"❌ Missing role dependency: {e}")
            logger.error("Cannot proceed with team execution. Please ensure all dependencies exist.")
            return []

        except Exception as e:
            logger.error(f"❌ Unexpected error during dependency resolution: {e}")
            return []
    
    def _build_analysis_prompt(self, initial_prompt: str, goal: str, missions: List[Any] = None) -> str:
        """
        Build the prompt for LLM to analyze required roles.
        
        Args:
            initial_prompt: User's initial prompt
            goal: Overall goal
            missions: List of decomposed missions (optional)
            
        Returns:
            Formatted prompt string
        """
        available_roles = self._format_available_roles()
        
        missions_text = ""
        if missions:
            missions_text = "\n## Decomposed Missions\n"
            for i, m in enumerate(missions, 1):
                # Handle both SubMission objects and dicts
                m_goal = m.goal if hasattr(m, 'goal') else m.get('goal', 'Unknown')
                m_type = m.type if hasattr(m, 'type') else m.get('type', 'general')
                missions_text += f"{i}. [{m_type}] {m_goal}\n"
        
        return f"""
Analyze the following task and determine which roles are needed to complete it.

## Initial Prompt
{initial_prompt}

## Goal
{goal}
{missions_text}
## Available Roles
{available_roles}

## Instructions
1. Identify which roles are needed for this task
2. Consider dependencies between roles (e.g., Architect must come before AI-Native-Writer)
3. Order roles by execution sequence (linear, not parallel)
4. Output ONLY a JSON object with this structure:

{{
    "roles": ["Role-Name-1", "Role-Name-2", "Role-Name-3"],
    "reasoning": "Brief explanation of why these roles and this order"
}}

CRITICAL: Output ONLY the JSON object. No explanatory text before or after.
"""
    
    def _format_available_roles(self) -> str:
        """
        Format available roles for the prompt.
        
        Returns:
            Formatted string of available roles
        """
        if not self.registry.roles:
            return "No roles available."
        
        lines = []
        for name, role in self.registry.roles.items():
            lines.append(f"- **{name}**: {role.description}")
            if role.dependencies:
                lines.append(f"  Dependencies: {', '.join(role.dependencies)}")
        return "\n".join(lines)

    async def assign_roles(
        self,
        missions: List[Any],
        work_dir: str = ".",
        model: str = None,
        timeout: int = 60,
        permission_mode: str = "bypassPermissions"
    ) -> Dict[str, str]:
        """
        Assign the most suitable role to each mission.
        
        Args:
            missions: List of SubMission objects
            work_dir: Working directory
            model: Model to use
            
        Returns:
            Dictionary mapping mission_id to role_name
        """
        available_roles = self._format_available_roles()
        
        missions_text = ""
        for m in missions:
            # Handle both SubMission objects and dicts
            m_id = m.id if hasattr(m, 'id') else m.get('id', 'unknown')
            m_goal = m.goal if hasattr(m, 'goal') else m.get('goal', 'Unknown')
            m_type = m.type if hasattr(m, 'type') else m.get('type', 'general')
            missions_text += f"- ID: {m_id} | Type: {m_type} | Goal: {m_goal}\n"
            
        prompt = f"""
Assign the best available role to each of the following missions.

## Missions
{missions_text}

## Available Roles
{available_roles}

## Instructions
1. For each mission, select the ONE most appropriate role.
2. Consider the mission type and goal.
3. Output ONLY a JSON object mapping mission IDs to Role Names.

Example Output:
{{
    "mission_1": "Market-Researcher",
    "mission_2": "AI-Native-Writer"
}}
"""
        logger.info("🤖 Assigning roles to missions...")
        
        try:
            response, _ = await run_claude_prompt(
                prompt,
                work_dir,
                model=model,
                timeout=timeout,
                permission_mode=permission_mode
            )
            
            data = extract_json(response)
            if not data:
                logger.error("Failed to parse role assignment response")
                return {}
                
            # Validate roles exist
            validated_assignment = {}
            for m_id, role_name in data.items():
                if self.registry.get_role(role_name):
                    validated_assignment[m_id] = role_name
                else:
                    logger.warning(f"Assigned role '{{role_name}}' not found. Using default.")
                    validated_assignment[m_id] = "Market-Researcher" # Fallback
            
            logger.info(f"✅ Role assignments: {{validated_assignment}}")
            return validated_assignment
            
        except Exception as e:
            logger.error(f"Failed to assign roles: {{e}}")
            return {}
