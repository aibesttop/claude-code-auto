"""
Role Executor

Executes a single role's mission with validation loop.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from src.core.team.role_registry import Role, ValidationRule
from src.core.agents.executor import ExecutorAgent
from src.core.agents.planner import PlannerAgent
from src.core.team.quality_validator import SemanticQualityValidator
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
        work_dir: str,
        session_id: Optional[str] = None,
        use_planner: bool = False,
        model: Optional[str] = None,
        timeout_seconds: int = 300,
        permission_mode: str = "bypassPermissions"
    ):
        """
        Initialize the role executor.

        Args:
            role: Role definition
            executor_agent: Existing ExecutorAgent instance
            work_dir: Working directory
            session_id: Session ID for trace logging
            use_planner: Whether to use PlannerAgent for sub-task decomposition
            model: Model to use for planner (if use_planner=True)
            timeout_seconds: Timeout for planner calls
            permission_mode: Permission mode for planner
        """
        self.role = role
        self.executor = executor_agent
        self.work_dir = Path(work_dir)
        self.session_id = session_id or "unknown"
        self.use_planner = use_planner

        # Estimate task complexity for adaptive validation
        self.task_complexity = self._estimate_task_complexity(role.mission.goal)
        logger.info(f"Estimated task complexity: {self.task_complexity}")

        # Initialize Planner if requested
        self.planner = None
        if use_planner:
            self.planner = PlannerAgent(
                work_dir=work_dir,
                goal=role.mission.goal,
                model=model,
                timeout_seconds=timeout_seconds,
                permission_mode=permission_mode
            )
            logger.info(f"Initialized PlannerAgent for role: {self.role.name}")

        # Switch to recommended Persona
        if self.role.recommended_persona:
            self.executor.persona_engine.switch_persona(
                self.role.recommended_persona,
                reason=f"role_requirement: {self.role.name}"
            )
            logger.info(f"Switched Persona to: {self.role.recommended_persona}")
    
    async def execute(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute role's mission (with optional planner integration).

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
        if self.use_planner and self.planner:
            return await self._execute_with_planner(context)
        else:
            return await self._execute_direct(context)

    async def _execute_direct(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute role's mission directly (original behavior).

        Args:
            context: Outputs from previous roles

        Returns:
            Execution result dictionary
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
            validation = await self._validate_outputs()

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

    async def _execute_with_planner(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute role's mission with planning decomposition.

        Args:
            context: Outputs from previous roles

        Returns:
            Execution result dictionary
        """
        mission = self.role.mission
        max_iterations = mission.max_iterations

        logger.info(f"🎭 {self.role.name} starting mission with planner: {mission.goal}")

        # Build context description
        context_str = self._format_context(context) if context else "No previous context."

        # Mission loop with planning
        iteration = 0
        last_result = context_str
        validation = {"passed": False, "errors": []}

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"  Planning iteration {iteration}/{max_iterations}")

            # 1. Planning phase - get next sub-task
            try:
                next_task = await self.planner.get_next_step(last_result)
            except Exception as e:
                logger.error(f"Planner failed: {e}")
                break

            # Export plan trace
            try:
                trace_file = self.planner.export_plan_to_markdown(
                    session_id=self.session_id,
                    role_name=self.role.name,
                    step=iteration
                )
                logger.info(f"📝 Plan trace exported: {trace_file}")
            except Exception as e:
                logger.warning(f"Failed to export plan trace: {e}")

            # Check if planning is complete
            if not next_task:
                logger.info("📋 Planner indicates all tasks complete")
                break

            logger.info(f"📋 Planner next task: {next_task}")

            # 2. Execution phase
            try:
                result = await self.executor.execute_task(next_task)
                last_result = f"Task: {next_task}\nResult: {result}"
                logger.info(f"Execution result: {result[:200]}...")

                # Export executor trace
                try:
                    exec_trace = self.executor.export_react_trace(
                        session_id=self.session_id,
                        role_name=self.role.name,
                        step=iteration
                    )
                    logger.info(f"📝 ReAct trace exported: {exec_trace}")
                except Exception as e:
                    logger.warning(f"Failed to export ReAct trace: {e}")

            except Exception as e:
                logger.error(f"Executor failed: {e}")
                last_result = f"Task: {next_task}\nFailed with error: {e}"
                continue

            # 3. Validation phase
            validation = await self._validate_outputs()

            if validation['passed']:
                logger.info(f"✅ {self.role.name} mission completed with planner!")
                return {
                    "success": True,
                    "outputs": self._collect_outputs(),
                    "iterations": iteration,
                    "validation_result": validation
                }
            else:
                logger.info(f"⏳ Validation not yet passed: {validation['errors']}")
                # Feed validation errors back to planner
                last_result += f"\n\nValidation errors: {validation['errors']}"

        # Check final validation state
        validation = await self._validate_outputs()
        if validation['passed']:
            logger.info(f"✅ {self.role.name} mission completed!")
            return {
                "success": True,
                "outputs": self._collect_outputs(),
                "iterations": iteration,
                "validation_result": validation
            }

        # Max iterations reached or planner stopped
        logger.error(f"❌ {self.role.name} failed to complete mission in {iteration} iterations")
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

Working Directory: {self.work_dir}
IMPORTANT: You must write all files to the directory '{self.work_dir}'.
Example: write_file("{self.work_dir}/example.md", ...)

Required files:
{required_files_str}

## Instructions
1. Complete all success criteria
2. Generate all required files in '{self.work_dir}'
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
IMPORTANT: Write files to '{self.work_dir}'.
"""
    
    async def _validate_outputs(self) -> Dict[str, Any]:
        """Validate outputs against validation rules (format + optional quality)"""
        errors = []

        # 1. Format validation (original rules)
        format_errors = self._validate_format()
        errors.extend(format_errors)

        # 2. Semantic quality validation (optional, costs tokens)
        if self.role.enable_quality_check:
            quality_errors = await self._validate_quality()
            errors.extend(quality_errors)

        return {
            "passed": len(errors) == 0,
            "errors": errors
        }

    def _validate_format(self) -> List[str]:
        """Validate format rules (file existence, content, length)"""
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

                    # Use adaptive min_chars based on task complexity
                    effective_min_chars = rule.get_effective_min_chars(self.task_complexity)

                    if len(content) < effective_min_chars:
                        complexity_info = f" [complexity: {self.task_complexity}]" if rule.adaptive else ""
                        errors.append(
                            f"{rule.file} too short: {len(content)} < {effective_min_chars} chars{complexity_info}"
                        )

        return errors

    async def _validate_quality(self) -> List[str]:
        """Validate semantic quality using LLM"""
        errors = []

        try:
            validator = SemanticQualityValidator(str(self.work_dir))

            for file in self.role.output_standard.required_files:
                file_path = self.work_dir / file

                if not file_path.exists():
                    continue  # Already caught by format validation

                try:
                    content = file_path.read_text(encoding='utf-8')

                    quality = await validator.score_output(
                        content=content,
                        success_criteria=self.role.mission.success_criteria
                    )

                    logger.info(f"📊 Quality score for {file}: {quality.overall_score}/100")

                    if quality.overall_score < self.role.quality_threshold:
                        error_msg = (
                            f"{file} quality score too low: {quality.overall_score:.1f}/100 "
                            f"(threshold: {self.role.quality_threshold}). "
                        )

                        if quality.issues:
                            error_msg += f"Issues: {', '.join(quality.issues[:3])}"  # Limit to 3 issues

                        if quality.suggestions:
                            error_msg += f" Suggestions: {', '.join(quality.suggestions[:2])}"

                        errors.append(error_msg)

                except Exception as e:
                    logger.error(f"Failed to validate quality for {file}: {e}")
                    errors.append(f"{file} quality validation failed: {str(e)}")

        except Exception as e:
            logger.error(f"Quality validation system error: {e}")
            errors.append(f"Quality validation system error: {str(e)}")

        return errors
    
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

    def _estimate_task_complexity(self, goal: str) -> str:
        """
        Estimate task complexity based on goal description.

        Complexity levels:
        - simple: Quick, basic tasks
        - medium: Standard tasks (default)
        - complex: Comprehensive, detailed tasks
        - expert: Advanced, sophisticated tasks

        Args:
            goal: Task goal description

        Returns:
            Complexity level string
        """
        goal_lower = goal.lower()

        # Method 1: Keyword matching (high priority)
        simple_keywords = ["simple", "quick", "basic", "brief", "short"]
        complex_keywords = ["comprehensive", "detailed", "in-depth", "thorough", "extensive"]
        expert_keywords = ["expert", "advanced", "sophisticated", "cutting-edge", "state-of-the-art"]

        if any(word in goal_lower for word in expert_keywords):
            return "expert"

        if any(word in goal_lower for word in complex_keywords):
            return "complex"

        if any(word in goal_lower for word in simple_keywords):
            return "simple"

        # Method 2: Length-based heuristic
        if len(goal) < 100:
            return "simple"

        if len(goal) > 500:
            return "complex"

        # Method 3: Success criteria count (if available)
        if hasattr(self, 'role') and self.role.mission.success_criteria:
            criteria_count = len(self.role.mission.success_criteria)
            if criteria_count >= 5:
                return "complex"
            elif criteria_count <= 2:
                return "simple"

        # Default
        return "medium"
