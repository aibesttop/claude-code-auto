"""
Role Executor

Executes a single role's mission with validation loop.

Enhanced for Tier-3 with reflection/review loops.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from src.core.team.role_registry import Role, ValidationRule, ReviewConfig
from src.core.agents.executor import ExecutorAgent
from src.core.agents.planner import PlannerAgent
from src.core.agents.sdk_client import run_claude_prompt
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
        permission_mode: str = "bypassPermissions",
        skill_prompt: Optional[str] = None,
        allowed_tools: Optional[List[str]] = None
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
            skill_prompt: Additional skill prompt for role enhancement
            allowed_tools: List of allowed tools (None = all tools allowed)
        """
        self.role = role
        self.executor = executor_agent
        # Use absolute path to avoid CWD-related issues
        self.work_dir = Path(work_dir).resolve()
        self.session_id = session_id or "unknown"
        logger.info(f"📁 RoleExecutor work_dir (absolute): {self.work_dir}")
        self.use_planner = use_planner
        self.skill_prompt = skill_prompt
        self.allowed_tools = allowed_tools

        # Estimate task complexity for adaptive validation
        self.task_complexity = self._estimate_task_complexity(role.mission.goal)
        logger.info(f"Estimated task complexity: {self.task_complexity}")

        # Initialize Planner if requested
        self.planner = None
        if use_planner:
            self.planner = PlannerAgent(
                work_dir=str(self.work_dir),  # Use resolved absolute path
                goal=role.mission.goal,
                model=model,
                timeout_seconds=timeout_seconds,
                permission_mode=permission_mode,
                required_files=self.role.output_standard.required_files,
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

        # Mission loop with infinite loop protection
        iteration = 0
        validation = {"passed": False, "errors": []}
        previous_errors = []  # Track error history to detect loops
        same_error_count = 0  # Count consecutive identical errors
        MAX_SAME_ERROR_RETRIES = 2  # Exit after N identical errors

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

                # Collect outputs
                outputs = self._collect_outputs()

                # Execute reflection loop if configured (Tier-3 feature)
                if self.role.reflection and self.role.reflection.enabled:
                    logger.info("🔍 Executing reflection loop...")
                    reflection_result = await self._execute_reflection_loop(outputs, context)
                    outputs = reflection_result["outputs"]

                    logger.info(
                        f"Reflection completed: {reflection_result['iterations']} iterations, "
                        f"{len(reflection_result['feedback'])} issues addressed"
                    )

                return {
                    "success": True,
                    "outputs": outputs,
                    "iterations": iteration,
                    "validation_result": validation,
                    "validation_passed": validation["passed"],
                    "validation_errors": validation["errors"],
                }
            else:
                logger.warning(f"⚠️ Validation failed: {validation['errors']}")

                # Check for infinite loop: same errors repeating
                current_errors = sorted(validation['errors'])
                if previous_errors and current_errors == previous_errors:
                    same_error_count += 1
                    logger.warning(f"🔁 Same validation errors detected {same_error_count} times in a row")

                    if same_error_count >= MAX_SAME_ERROR_RETRIES:
                        logger.error(
                            f"❌ Breaking infinite loop: Same errors repeated {same_error_count} times. "
                            f"Errors: {current_errors[:3]}... "
                            f"Possible causes: validation logic issue, file path problem, or agent unable to fix."
                        )
                        return {
                            "success": False,
                            "outputs": self._collect_outputs(),
                            "iterations": iteration,
                            "validation_result": validation,
                            "validation_passed": validation["passed"],
                            "validation_errors": validation["errors"],
                            "exit_reason": "infinite_loop_detected"
                        }
                else:
                    # Different errors - reset counter
                    same_error_count = 0

                previous_errors = current_errors

                # Build retry task with specific errors to fix
                task = self._build_retry_task(validation['errors'])

        # Max iterations reached
        logger.error(f"❌ {self.role.name} failed to complete mission in {max_iterations} iterations")
        return {
            "success": False,
            "outputs": self._collect_outputs(),
            "iterations": iteration,
            "validation_result": validation,
            "validation_passed": validation["passed"],
            "validation_errors": validation["errors"],
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

        # Mission loop with planning and infinite loop protection
        iteration = 0
        last_result = context_str
        validation = {"passed": False, "errors": []}
        previous_errors = []  # Track error history to detect loops
        same_error_count = 0  # Count consecutive identical errors
        MAX_SAME_ERROR_RETRIES = 2  # Exit after N identical errors

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"  Planning iteration {iteration}/{max_iterations}")

            # 1. Planning phase - get next sub-task
            try:
                next_task = await self.planner.get_next_step(last_result)
            except Exception as e:
                logger.error(f"Planner failed: {e}")

                # Degradation: If planner fails on first iteration, execute directly
                if iteration == 1:
                    logger.warning("⚠️ Planner failed on first attempt, falling back to direct execution")
                    next_task = self.role.mission.goal
                else:
                    logger.error("❌ Planner failed after initial planning, aborting")
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
                task_prompt = self._build_planner_task(next_task, context_str)
                result = await self.executor.execute_task(task_prompt)
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
                error_str = str(e).lower()

                # Special handling for timeout errors
                if "timeout" in error_str:
                    logger.error(f"⏰ Executor timeout after {self.executor.timeout_seconds}s")

                    # If this is the first execution failure, try to break task into smaller pieces
                    if iteration == 1:
                        logger.warning("⚠️ First execution timed out - task may be too complex")
                        logger.warning("💡 Suggestion: Consider breaking down the mission into smaller sub-missions")

                    # Continue to next iteration (may succeed with partial work)
                    last_result = f"Task: {next_task}\nFailed with timeout: {e}"
                    continue
                else:
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
                    "validation_result": validation,
                    "validation_passed": validation["passed"],
                    "validation_errors": validation["errors"],
                }
            else:
                logger.info(f"⏳ Validation not yet passed: {validation['errors']}")

                # Check for infinite loop: same errors repeating
                current_errors = sorted(validation['errors'])
                if previous_errors and current_errors == previous_errors:
                    same_error_count += 1
                    logger.warning(f"🔁 Same validation errors detected {same_error_count} times in a row")

                    if same_error_count >= MAX_SAME_ERROR_RETRIES:
                        logger.error(
                            f"❌ Breaking infinite loop in planner mode: Same errors repeated {same_error_count} times. "
                            f"Errors: {current_errors[:3]}... "
                        )
                        return {
                            "success": False,
                            "outputs": self._collect_outputs(),
                            "iterations": iteration,
                            "validation_result": validation,
                            "validation_passed": validation["passed"],
                            "validation_errors": validation["errors"],
                            "exit_reason": "infinite_loop_detected"
                        }
                else:
                    # Different errors - reset counter
                    same_error_count = 0

                previous_errors = current_errors

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
                "validation_result": validation,
                "validation_passed": validation["passed"],
                "validation_errors": validation["errors"],
            }

        # Max iterations reached or planner stopped
        logger.error(f"❌ {self.role.name} failed to complete mission in {iteration} iterations")
        return {
            "success": False,
            "outputs": self._collect_outputs(),
            "iterations": iteration,
            "validation_result": validation,
            "validation_passed": validation["passed"],
            "validation_errors": validation["errors"],
        }
    
    def _build_task(self, mission, context: Dict) -> str:
        """Build task description for Executor"""
        context_str = self._format_context(context) if context else "No previous context."
        criteria_str = "\n".join(f"- {c}" for c in mission.success_criteria)
        required_files_str = "\n".join(f"- {f}" for f in self.role.output_standard.required_files)

        template_info = ""
        if self.role.output_standard.template:
            template_info = f"\n\nYou MUST follow the standard defined in: {self.role.output_standard.template}"

        # Add skill prompt if provided (from ResourceRegistry)
        skill_section = ""
        if self.skill_prompt:
            skill_section = f"""
## Role Enhancement
{self.skill_prompt}
"""

        # Add allowed tools information
        tools_section = ""
        if self.allowed_tools:
            tools_list = "\n".join(f"- {tool}" for tool in self.allowed_tools)
            tools_section = f"""
## Available Tools
You should primarily use the following tools for this task:
{tools_list}
"""

        return f"""
# Mission: {mission.goal}
{skill_section}
## Success Criteria
{criteria_str}

## Context from Previous Roles
{context_str}

## Output Standard{template_info}

Working Directory: {self.work_dir}
IMPORTANT: Use RELATIVE paths for all file operations.
- Correct ReAct tool call:
  Action: write_file
  Action Input: {{"path":"market-research.md","content":"..."}}
- Correct ReAct tool call:
  Action: write_file
  Action Input: {{"path":"docs/analysis.md","content":"..."}}
- WRONG: Action Input uses absolute path like "{self.work_dir}/market-research.md"
- WRONG: Action Input uses repo-prefixed path like "demo_act/market-research.md"

The working directory is already set to {self.work_dir}, so just use filenames directly.

Required files (use these exact filenames):
{required_files_str}
{tools_section}
## Instructions
1. Complete all success criteria
2. Generate all required files using RELATIVE paths
3. Ensure outputs meet validation rules
4. Use the appropriate tools for this task type
5. Use the ReAct format (Thought/Action/Action Input) and call tools before Final Answer
"""

    def _build_planner_task(self, next_task: str, context_str: str) -> str:
        """Build a constrained subtask prompt for planner-driven execution."""
        required_files_str = "\n".join(f"- {f}" for f in self.role.output_standard.required_files) or "None."
        template_info = ""
        if self.role.output_standard.template:
            template_info = f"\n\nYou MUST follow the standard defined in: {self.role.output_standard.template}"

        return f"""
# Subtask
{next_task}

## Context from Previous Roles
{context_str}

## Output Standard{template_info}

Working Directory: {self.work_dir}
IMPORTANT: Use RELATIVE paths for all file operations.

Required files (use these exact filenames if this subtask produces deliverables):
{required_files_str}

## Instructions
1. Use tools when needed
2. If you write outputs, use the required filenames exactly
3. Do not invent alternate filenames
4. Use the ReAct format (Thought/Action/Action Input) and call tools before Final Answer
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
IMPORTANT: Use RELATIVE paths only (e.g., "filename.md", not "{self.work_dir}/filename.md").
The working directory is already set to: {self.work_dir}
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
                        # Flexible pattern matching for markdown headers
                        # Handles variations like "## Header", "##Header", "##  Header"

                        # Method 1: Try exact match first (fastest)
                        if required in content:
                            continue  # Found - skip to next requirement

                        # Method 2: Try flexible whitespace pattern
                        # Escape special regex chars but preserve structure
                        pattern = re.escape(required)
                        # Allow flexible whitespace: 0 or more spaces/tabs
                        pattern = pattern.replace(r'\ ', r'\s*')

                        # Search with multiline and case-sensitive matching
                        if re.search(pattern, content, re.MULTILINE):
                            continue  # Found - skip to next requirement

                        # Method 3: Try normalized comparison (remove extra whitespace)
                        normalized_required = ' '.join(required.split())
                        normalized_content = ' '.join(content.split())

                        if normalized_required in normalized_content:
                            logger.warning(f"Found '{required}' in {rule.file} with whitespace normalization")
                            continue

                        # Method 4: Try semantic/synonym matching (multilingual support)
                        # Extract header text without markdown syntax
                        required_text = required.replace('#', '').strip().lower()

                        # Define synonym groups for common headers
                        synonym_groups = {
                            'target users': ['user segments', 'target audience', 'users', '目标用户', '用户画像'],
                            'competitor analysis': ['competitive analysis', 'competition', 'competitors', '竞品分析', '竞争分析'],
                            'market size': ['market analysis', 'market overview', '市场规模', '市场分析'],
                            'user pain points': ['pain points', 'challenges', 'problems', '用户痛点', '痛点分析'],
                            'opportunities': ['market opportunities', 'business opportunities', '市场机会', '商业机会'],
                            'executive summary': ['summary', 'overview', '执行摘要', '概述'],
                        }

                        # Check if any synonym exists in content
                        found_synonym = False
                        if required_text in synonym_groups:
                            for synonym in synonym_groups[required_text]:
                                # Try case-insensitive search with ## prefix (flexible markdown header)
                                patterns_to_try = [
                                    r'#{1,6}\s*' + re.escape(synonym),  # ## Synonym (any level)
                                    re.escape(synonym),  # Just the text anywhere in content
                                ]
                                for syn_pattern in patterns_to_try:
                                    if re.search(syn_pattern, content, re.IGNORECASE | re.MULTILINE):
                                        logger.info(f"✓ Found synonym '{synonym}' for '{required}' in {rule.file}")
                                        found_synonym = True
                                        break
                                if found_synonym:
                                    break

                        if found_synonym:
                            continue  # Found synonym - skip to next requirement

                        # Not found - log detailed error
                        errors.append(f"{rule.file} missing section: {required}")
                        logger.warning(f"❌ Failed to find '{required}' in {rule.file}")
                        logger.debug(f"Tried pattern: {pattern}")
                        logger.debug(f"File content (first 1000 chars):\n{content[:1000]}")
                        logger.debug(f"File content (headers only):")
                        # Extract and log all markdown headers for debugging
                        headers = re.findall(r'^#{1,6}\s+.+$', content, re.MULTILINE)
                        for h in headers[:20]:  # Limit to first 20 headers
                            logger.debug(f"  Found header: {h}")
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
            from src.config import get_config
            logs_dir = Path(get_config().directories.logs_dir)
            trace_dir = logs_dir / "trace"
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

    async def _execute_reflection_loop(
        self,
        outputs: Dict[str, str],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute Tier-3 reflection/review loop (self-correction).

        After initial output, switch to "critic" mode and review the work.
        Iteratively refine until quality is acceptable or max retries reached.

        Args:
            outputs: Initial output files from execution
            context: Additional context

        Returns:
            {
                "refined": bool,
                "outputs": Dict[str, str],
                "iterations": int,
                "feedback": List[str]
            }
        """
        if not self.role.reflection or not self.role.reflection.enabled:
            return {"refined": False, "outputs": outputs, "iterations": 0, "feedback": []}

        reflection_config = self.role.reflection
        max_retries = reflection_config.max_retries

        logger.info(f"🔍 Starting reflection loop for {self.role.name}")
        logger.info(f"   Review aspects: {', '.join(reflection_config.aspects) if reflection_config.aspects else 'general'}")
        logger.info(f"   Max retries: {max_retries}")

        current_outputs = outputs
        feedback_history = []

        for iteration in range(1, max_retries + 1):
            logger.info(f"  Reflection iteration {iteration}/{max_retries}")

            # Compose critic prompt
            critic_prompt = self._build_critic_prompt(current_outputs, feedback_history)

            # Execute critic review
            try:
                review_result, _ = await run_claude_prompt(
                    critic_prompt,
                    str(self.work_dir),
                    model=self.executor.model,
                    permission_mode=self.executor.permission_mode,
                    timeout=120,  # Shorter timeout for reviews
                    max_retries=1
                )

                # Parse review for issues
                issues_found = self._parse_review_for_issues(review_result)

                if not issues_found:
                    logger.info(f"✅ Review passed - no issues found in iteration {iteration}")
                    return {
                        "refined": iteration > 1,
                        "outputs": current_outputs,
                        "iterations": iteration,
                        "feedback": feedback_history
                    }

                logger.info(f"⚠️ Found {len(issues_found)} issues: {[i[:50] for i in issues_found]}")
                feedback_history.extend(issues_found)

                # Refine based on feedback
                refinement_task = self._build_refinement_task(current_outputs, issues_found)
                refined_result = await self.executor.execute_task(refinement_task)

                # Update outputs
                current_outputs = self._collect_outputs()

            except Exception as e:
                logger.error(f"Reflection iteration {iteration} failed: {e}")
                break

        # Max retries reached
        logger.warning(f"⚠️ Reflection loop completed after {max_retries} iterations")
        return {
            "refined": True,
            "outputs": current_outputs,
            "iterations": max_retries,
            "feedback": feedback_history
        }

    def _build_critic_prompt(
        self,
        outputs: Dict[str, str],
        previous_feedback: List[str] = None
    ) -> str:
        """
        Build critic prompt for reflection loop.

        Args:
            outputs: Current output files to review
            previous_feedback: Previous iteration feedback (if any)

        Returns:
            Critic prompt string
        """
        reflection_config = self.role.reflection
        role_name = reflection_config.reviewer_role or "Self-Reviewer"

        # Build output summary
        output_summary = []
        for filename, content in outputs.items():
            preview = content[:500] + "..." if len(content) > 500 else content
            output_summary.append(f"\n## {filename}\n{preview}")

        # Build aspects section
        aspects_section = ""
        if reflection_config.aspects:
            aspects_section = f"\nReview Aspects: {', '.join(reflection_config.aspects)}\n"

        # Build previous feedback section
        feedback_section = ""
        if previous_feedback:
            feedback_section = "\n## Previous Feedback (Already Addressed)\n"
            feedback_section += "\n".join(f"- {fb}" for fb in previous_feedback[-3:])
            feedback_section += "\n"

        # Use custom template if provided
        if reflection_config.critic_prompt_template:
            return reflection_config.critic_prompt_template.format(
                role=role_name,
                aspects=', '.join(reflection_config.aspects),
                outputs='\n'.join(output_summary),
                previous_feedback=feedback_section
            )

        # Default critic prompt
        return f"""Act as a {role_name} and critically review the following output.

# Your Task
Find flaws, issues, or areas for improvement in the provided work.{aspects_section}

# Output Files to Review
{"".join(output_summary)}
{feedback_section}
# Instructions
1. Identify specific issues (be precise and actionable)
2. Prioritize critical issues (security, logic errors, missing requirements)
3. Ignore minor stylistic issues unless they affect clarity
4. Output ONLY a JSON object:
{{
    "issues_found": [
        {{
            "file": "filename.md",
            "issue": "Description of the problem",
            "severity": "critical|major|minor",
            "suggestion": "How to fix it"
        }}
    ]
}}

If NO issues found, return: {{"issues_found": []}}

CRITICAL: Output ONLY the JSON object. No explanatory text."""

    def _parse_review_for_issues(self, review_result: str) -> List[str]:
        """
        Parse review result to extract issues.

        Args:
            review_result: Review output from LLM

        Returns:
            List of issue descriptions
        """
        try:
            import json
            data = json.loads(review_result.strip())
            issues = data.get("issues_found", [])

            if not issues:
                return []

            # Extract issue descriptions
            return [
                f"[{issue.get('severity', 'major').upper()}] {issue.get('file', 'unknown')}: "
                f"{issue.get('issue', 'no description')}"
                for issue in issues
            ]

        except Exception as e:
            logger.warning(f"Failed to parse review JSON: {e}")
            # Fallback: try to extract bullet points
            issues = re.findall(r'[-*]\s*\[(\w+)\]\s*(.+)', review_result)
            return [f"[{severity}] {desc}" for severity, desc in issues] if issues else []

    def _build_refinement_task(
        self,
        outputs: Dict[str, str],
        issues: List[str]
    ) -> str:
        """
        Build refinement task based on review feedback.

        Args:
            outputs: Current outputs
            issues: Issues to fix

        Returns:
            Refinement task string
        """
        issues_text = "\n".join(f"- {issue}" for issue in issues)

        return f"""# Refinement Task

Your previous work has been reviewed and needs refinement. Fix the following issues:

## Issues to Fix
{issues_text}

## Instructions
1. Review the issues listed above
2. Fix each issue in the appropriate file
3. Ensure all fixes maintain quality and coherence
4. Use the write_file tool to save updated files

Files to update: {', '.join(outputs.keys())}

Begin refinement now."""
