"""
Role Executor

Executes a single role's mission with validation loop.
"""

from typing import Dict, Any
from pathlib import Path
from src.core.team.role_registry import Role, ValidationRule
from src.core.agents.executor import ExecutorAgent
import logging
import re

logger = logging.getLogger(__name__)


class RoleExecutor:
    """
    Executes a single role's mission.
    
    Runs a small loop until mission is completed and validated.
    Integrates with existing ExecutorAgent and PersonaEngine.
    """
    
    def __init__(
        self,
        role: Role,
        executor_agent: ExecutorAgent,
        work_dir: str
    ):
        """
        Initialize the role executor.
        
        Args:
            role: Role definition
            executor_agent: Existing ExecutorAgent instance
            work_dir: Working directory
        """
        self.role = role
        self.executor = executor_agent
        self.work_dir = Path(work_dir)
        
        # Switch to recommended Persona
        if self.role.recommended_persona:
            self.executor.persona_engine.switch_persona(
                self.role.recommended_persona,
                reason=f"role_requirement: {self.role.name}"
            )
            logger.info(f"Switched Persona to: {self.role.recommended_persona}")
    
    async def execute(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute role's mission.
        
        Args:
            context: Outputs from previous roles
        
        Returns:
            {
                "success": bool,
                "outputs": Dict[str, str],  # filename -> content
                "iterations": int,
                "validation_result": Dict
            }
        """
        mission = self.role.mission
        max_iterations = mission.max_iterations
        
        logger.info(f"🎭 {self.role.name} starting mission: {mission.goal}")
        
        # Build initial task
        task = self._build_task(mission, context)
        
        # Mission loop
        iteration = 0
        validation = {"passed": False, "errors": []}
        
        while iteration < max_iterations:
            iteration += 1
            logger.info(f"  Iteration {iteration}/{max_iterations}")
            
            # Execute task using existing Executor
            try:
                result = await self.executor.execute_task(task)
            except Exception as e:
                logger.error(f"Executor failed: {e}")
                task = f"Previous attempt failed with error: {e}\n\nPlease try again and fix the issue.\n\n{task}"
                continue
            
            # Validate outputs
            validation = self._validate_outputs()
            
            if validation['passed']:
                logger.info(f"✅ {self.role.name} mission completed!")
                return {
                    "success": True,
                    "outputs": self._collect_outputs(),
                    "iterations": iteration,
                    "validation_result": validation
                }
            else:
                logger.warning(f"⚠️ Validation failed: {validation['errors']}")
                # Build retry task with specific errors to fix
                task = self._build_retry_task(validation['errors'])
        
        # Max iterations reached
        logger.error(f"❌ {self.role.name} failed to complete mission in {max_iterations} iterations")
        return {
            "success": False,
            "outputs": self._collect_outputs(),
            "iterations": iteration,
            "validation_result": validation
        }
    
    def _build_task(self, mission, context: Dict) -> str:
        """Build task description for Executor"""
        context_str = self._format_context(context) if context else "No previous context."
        criteria_str = "\n".join(f"- {c}" for c in mission.success_criteria)
        required_files_str = "\n".join(f"- {f}" for f in self.role.output_standard.required_files)
        
        template_info = ""
        if self.role.output_standard.template:
            template_info = f"\n\nYou MUST follow the standard defined in: {self.role.output_standard.template}"
        
        return f"""
# Mission: {mission.goal}

## Success Criteria
{criteria_str}

## Context from Previous Roles
{context_str}

## Output Standard{template_info}

Required files:
{required_files_str}

## Instructions
1. Complete all success criteria
2. Generate all required files
3. Ensure outputs meet validation rules
4. Use the tools available to you
"""
    
    def _build_retry_task(self, errors: list) -> str:
        """Build retry task with specific errors to fix"""
        errors_str = "\n".join(f"- {error}" for error in errors)
        return f"""
# Mission: Fix Validation Errors

## Issues to Fix
{errors_str}

## Instructions
Fix the above issues and ensure all validation rules pass.
Do NOT regenerate everything, just fix the specific issues.
"""
    
    def _validate_outputs(self) -> Dict[str, Any]:
        """Validate outputs against validation rules"""
        errors = []
        
        for rule in self.role.output_standard.validation_rules:
            rule_type = rule.type
            
            if rule_type == "file_exists":
                file_path = self.work_dir / rule.file
                if not file_path.exists():
                    errors.append(f"Missing required file: {rule.file}")
            
            elif rule_type == "all_files_exist":
                for file in rule.files:
                    file_path = self.work_dir / file
                    if not file_path.exists():
                        errors.append(f"Missing required file: {file}")
            
            elif rule_type == "content_check":
                file_path = self.work_dir / rule.file
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    for required in rule.must_contain:
                        # Normalize whitespace for more flexible matching
                        # Convert multiple spaces/tabs to single space pattern
                        pattern = re.escape(required)
                        # Replace escaped spaces with flexible whitespace pattern
                        pattern = pattern.replace(r'\ ', r'\s+')
                        
                        # Search with case-sensitive matching
                        if not re.search(pattern, content):
                            errors.append(f"{rule.file} missing section: {required}")
                            logger.debug(f"Failed to find '{required}' in {rule.file}")
                            logger.debug(f"Pattern used: {pattern}")
                            logger.debug(f"File content preview: {content[:500]}")
                else:
                    errors.append(f"Cannot check content, file missing: {rule.file}")
            
            elif rule_type == "no_placeholders":
                for file in rule.files:
                    file_path = self.work_dir / file
                    if file_path.exists():
                        content = file_path.read_text(encoding='utf-8')
                        for pattern in rule.forbidden_patterns:
                            if re.search(pattern, content):
                                errors.append(f"{file} contains placeholder: {pattern}")
            
            elif rule_type == "min_length":
                file_path = self.work_dir / rule.file
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    if len(content) < rule.min_chars:
                        errors.append(f"{rule.file} too short: {len(content)} < {rule.min_chars} chars")
        
        return {
            "passed": len(errors) == 0,
            "errors": errors
        }
    
    def _collect_outputs(self) -> Dict[str, str]:
        """Collect all generated outputs"""
        outputs = {}
        for file in self.role.output_standard.required_files:
            file_path = self.work_dir / file
            if file_path.exists():
                outputs[file] = file_path.read_text(encoding='utf-8')
        return outputs
    
    def _format_context(self, context: Dict) -> str:
        """
        Format context from previous roles with full content preservation.

        Strategy:
        - For short content (<500 chars): include full text
        - For long content: save to trace file + provide intelligent summary
        """
        lines = []

        for role_name, role_result in context.items():
            lines.append(f"### {role_name} Outputs")

            if 'outputs' in role_result:
                for file, content in role_result['outputs'].items():
                    if len(content) <= 500:
                        # Short content: include fully
                        lines.append(f"**{file}** (full content):")
                        lines.append(f"```")
                        lines.append(content)
                        lines.append(f"```")
                    else:
                        # Long content: save to trace + intelligent summary
                        trace_file = self._save_context_to_trace(role_name, file, content)

                        # Intelligent summary: first 300 chars + last 100 chars
                        summary_start = content[:300]
                        summary_end = content[-100:]

                        lines.append(f"**{file}** ({len(content)} chars):")
                        lines.append(f"```")
                        lines.append(summary_start)
                        lines.append(f"... [content truncated, see full version below] ...")
                        lines.append(summary_end)
                        lines.append(f"```")
                        lines.append(f"📄 Full content saved to: `{trace_file}`")

                    lines.append("")  # Blank line between files

            # Include iteration info
            if 'iterations' in role_result:
                lines.append(f"*Completed in {role_result['iterations']} iterations*")
                lines.append("")

        if not lines:
            return "No previous context available."

        return "\n".join(lines)

    def _save_context_to_trace(self, role_name: str, filename: str, content: str) -> str:
        """
        Save full context content to trace file for reference.

        Args:
            role_name: Name of the role that generated this content
            filename: Original filename
            content: Full content to save

        Returns:
            Path to the saved trace file
        """
        try:
            from pathlib import Path
            trace_dir = Path("logs/trace")
            trace_dir.mkdir(parents=True, exist_ok=True)

            # Sanitize filename for filesystem
            safe_filename = filename.replace("/", "_").replace("\\", "_")
            trace_filename = f"context_{role_name}_{safe_filename}"
            trace_path = trace_dir / trace_filename

            trace_path.write_text(content, encoding='utf-8')
            return str(trace_path)

        except Exception as e:
            logger.error(f"Failed to save context to trace: {e}")
            return "trace_save_failed"
