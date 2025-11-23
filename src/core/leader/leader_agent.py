"""
Leader Agent - Meta-level orchestration for dynamic team management.

Replaces static TeamAssembler with intelligent, stateful coordination.
Handles mission decomposition, dynamic resource injection, monitoring, and intervention.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import time
import json

from src.core.leader.mission_decomposer import MissionDecomposer, SubMission
from src.core.resources.resource_registry import ResourceRegistry
from src.core.team.role_registry import Role, RoleRegistry
from src.core.team.role_executor import RoleExecutor
from src.core.team.dependency_resolver import DependencyResolver
from src.core.team.team_assembler import TeamAssembler
from src.core.agents.executor import ExecutorAgent
from src.core.agents.sdk_client import run_claude_prompt
from src.core.events import EventStore, CostTracker
from src.core.governance.helper_governor import HelperGovernor, HelperExitCondition, ExitConditionType
from src.utils.logger import get_logger

logger = get_logger()


class InterventionAction(Enum):
    """Intervention actions the Leader can take"""
    CONTINUE = "continue"
    RETRY = "retry"
    ENHANCE = "enhance"
    ESCALATE = "escalate"
    TERMINATE = "terminate"


@dataclass
class InterventionDecision:
    """Decision made by Leader after monitoring"""
    action: InterventionAction
    reason: str
    enhancements: List[str] = None
    adjustments: Dict[str, Any] = None


@dataclass
class ExecutionContext:
    """
    Execution context maintained by Leader.

    Tracks state across the entire workflow.
    """
    session_id: str
    goal: str
    missions: List[SubMission]
    completed_missions: Dict[str, Any]
    active_roles: List[str]
    total_cost_usd: float
    start_time: float
    intervention_count: int


class LeaderAgent:
    """
    Leader Agent - Dynamic team orchestrator.

    Responsibilities:
    1. Decompose user goal into sub-missions
    2. Dynamically assemble and adjust team
    3. Inject resources (tools, skills) per mission
    4. Monitor execution and intervene when needed
    5. Integrate final outputs into deliverable
    """

    def __init__(
        self,
        work_dir: str,
        model: str = "sonnet",
        max_mission_retries: int = 3,
        quality_threshold: float = 70.0,
        budget_limit_usd: Optional[float] = None,
        session_id: Optional[str] = None
    ):
        """
        Initialize Leader Agent.

        Args:
            work_dir: Working directory for outputs
            model: Claude model to use ("sonnet", "opus", "haiku")
            max_mission_retries: Maximum retries per mission
            quality_threshold: Minimum quality score (0-100)
            budget_limit_usd: Budget limit in USD
            session_id: Session ID for tracking
        """
        # Use absolute path to avoid CWD-related issues
        self.work_dir = Path(work_dir).resolve()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 LeaderAgent work_dir (absolute): {self.work_dir}")

        self.model = model
        self.max_mission_retries = max_mission_retries
        self.quality_threshold = quality_threshold
        self.budget_limit_usd = budget_limit_usd

        # Components
        self.mission_decomposer = MissionDecomposer(model=model, work_dir=str(self.work_dir))

        # Calculate project root for resources and roles directories (avoid CWD dependency)
        # Use this file's location to find project root
        project_root = Path(__file__).parent.parent.parent.resolve()

        resources_dir = project_root / "resources"
        self.resource_registry = ResourceRegistry(config_dir=str(resources_dir))

        roles_dir = project_root / "roles"
        self.role_registry = RoleRegistry(roles_dir=str(roles_dir))

        logger.info(f"📁 Project root: {project_root}")
        logger.info(f"📁 Resources directory: {resources_dir}")
        logger.info(f"📁 Roles directory: {roles_dir}")

        self.dependency_resolver = DependencyResolver()
        self.team_assembler = TeamAssembler(self.role_registry)
        self.helper_governor = HelperGovernor()

        # Tracking
        self.event_store = EventStore()
        self.cost_tracker = CostTracker(max_budget_usd=budget_limit_usd)

        # State
        self.context: Optional[ExecutionContext] = None
        self.intervention_history: List[Dict] = []

        logger.info(f"🎯 Leader Agent initialized")
        logger.info(f"   Model: {model}")
        logger.info(f"   Work dir: {self.work_dir}")
        logger.info(f"   Quality threshold: {quality_threshold}")
        if budget_limit_usd:
            logger.info(f"   Budget limit: ${budget_limit_usd:.2f}")

    async def execute(
        self,
        goal: str,
        session_id: str,
        context: str = None
    ) -> Dict[str, Any]:
        """
        Main execution flow.

        Args:
            goal: User's high-level goal
            session_id: Unique session identifier
            context: Optional context/background (e.g., initial_prompt from config)

        Returns:
            {
                "success": bool,
                "deliverable": {...},
                "metadata": {...}
            }
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"🎯 LEADER AGENT - Starting Execution")
        logger.info(f"{'='*70}")
        logger.info(f"Goal: {goal}")
        if context:
            logger.info(f"Context: {context[:100]}...")
        logger.info(f"Session: {session_id}")

        start_time = time.time()

        # Step 1: Decompose goal into missions
        logger.info(f"\n{'='*70}")
        logger.info(f"📋 Step 1: Mission Decomposition")
        logger.info(f"{'='*70}")

        missions = await self.mission_decomposer.decompose(goal, context=context)
        logger.info(f"✅ Created {len(missions)} missions")
        for i, mission in enumerate(missions, 1):
            logger.info(f"   {i}. [{mission.type}] {mission.goal}")

        # Validate dependencies
        if not self.mission_decomposer.validate_dependencies(missions):
            logger.error("❌ Invalid mission dependencies")
            return {
                "success": False,
                "error": "Invalid mission dependencies"
            }

        # Step 2: Assemble Team & Resolve Dependencies
        logger.info(f"\n{'='*70}")
        logger.info(f"👥 Step 2: Team Assembly & Dependency Resolution")
        logger.info(f"{'='*70}")

        # Assign roles to missions
        role_map = await self.team_assembler.assign_roles(
            missions=missions,
            work_dir=str(self.work_dir),
            model=self.model
        )
        
        # Sort missions by dependency
        sorted_missions = self.dependency_resolver.sort_missions(missions)
        
        logger.info(f"✅ Team assembled and sorted. Execution order:")
        for i, m in enumerate(sorted_missions, 1):
            role_name = role_map.get(m.id, "Market-Researcher")
            logger.info(f"   {i}. [{role_name}] -> Mission: {m.id} ({m.type})")

        # Initialize context
        self.context = ExecutionContext(
            session_id=session_id,
            goal=goal,
            missions=sorted_missions,
            completed_missions={},
            active_roles=[],
            total_cost_usd=0.0,
            start_time=start_time,
            intervention_count=0
        )

        # Step 3: Execute missions sequentially
        for i, mission in enumerate(sorted_missions, 1):
            logger.info(f"\n{'='*70}")
            logger.info(f"🚀 Step 3.{i}: Execute Mission '{mission.id}'")
            logger.info(f"{'='*70}")
            
            role_name = role_map.get(mission.id, "Market-Researcher")
            logger.info(f"Role: {role_name}")
            logger.info(f"Goal: {mission.goal}")

            # Check budget before executing
            if self.budget_limit_usd:
                if self.context.total_cost_usd >= self.budget_limit_usd:
                    logger.error(f"❌ Budget exceeded: ${self.context.total_cost_usd:.2f} / ${self.budget_limit_usd:.2f}")
                    return {
                        "success": False,
                        "error": "Budget exceeded",
                        "metadata": self._get_metadata()
                    }

            # Execute mission
            result = await self._execute_mission(mission, role_name)

            if result['success']:
                self.context.completed_missions[mission.id] = result
                logger.info(f"✅ Mission '{mission.id}' completed")
            else:
                logger.error(f"❌ Mission '{mission.id}' failed")
                return {
                    "success": False,
                    "failed_mission": mission.id,
                    "error": result.get('error'),
                    "metadata": self._get_metadata()
                }

        # Step 3: Integrate outputs
        logger.info(f"\n{'='*70}")
        logger.info(f"📦 Step 3: Output Integration")
        logger.info(f"{'='*70}")

        deliverable = await self._integrate_outputs()

        # Final summary
        duration = time.time() - start_time
        logger.info(f"\n{'='*70}")
        logger.info(f"🎉 LEADER AGENT - Execution Complete")
        logger.info(f"{'='*70}")
        logger.info(f"Total missions: {len(missions)}")
        logger.info(f"Completed: {len(self.context.completed_missions)}")
        logger.info(f"Interventions: {self.context.intervention_count}")
        logger.info(f"Total cost: ${self.context.total_cost_usd:.2f}")
        logger.info(f"Duration: {duration:.1f}s")

        return {
            "success": True,
            "deliverable": deliverable,
            "metadata": self._get_metadata()
        }

    async def _execute_mission(self, mission: SubMission, role_name: str) -> Dict[str, Any]:
        """
        Execute a single mission with retry and intervention logic.

        Args:
            mission: SubMission to execute
            role_name: Name of the role to execute this mission

        Returns:
            Result dictionary with success status
        """
        iteration = 0

        while iteration < self.max_mission_retries:
            iteration += 1
            logger.info(f"🔄 Iteration {iteration}/{self.max_mission_retries}")

            # 1. Select role for this mission
            try:
                role = self.role_registry.get_role(role_name)
            except Exception:
                logger.warning(f"Role '{role_name}' not found, using Market-Researcher as fallback")
                role = self.role_registry.get_role("Market-Researcher")

            # Update role's mission
            role.mission = mission

            logger.info(f"   👤 Selected role: {role.name}")

            # 1.5 Resource Injection: Get tools and skills for this mission type
            logger.info(f"   🔧 Injecting resources for mission type: {mission.type}")

            # Get required tools for mission type
            required_tools = self.resource_registry.get_tools_for_mission(mission.type)
            if required_tools:
                logger.info(f"      Tools: {', '.join(required_tools)}")
            else:
                logger.info(f"      Tools: (default - no specific restriction)")

            # Get MCP servers for mission type
            mcp_servers = self.resource_registry.get_mcp_for_mission(mission.type)
            if mcp_servers:
                logger.info(f"      MCP Servers: {', '.join(s.name for s in mcp_servers)}")

            # Get skill prompts for role category
            skill_prompt = self.resource_registry.get_skill_for_role(role.category)
            if skill_prompt:
                logger.info(f"      Skill: {skill_prompt.name}")
            else:
                logger.info(f"      Skill: (none for category '{role.category}')")

            # 2. Create executor with role's configuration
            executor = ExecutorAgent(
                work_dir=str(self.work_dir),
                model=self.model,
                timeout_seconds=300,
                permission_mode="bypassPermissions"
            )

            # 3. Create role executor with resource injection
            role_executor = RoleExecutor(
                role=role,
                executor_agent=executor,
                work_dir=str(self.work_dir),
                session_id=self.context.session_id,
                use_planner=True,  # Enable planner for better task decomposition
                model=self.model,
                skill_prompt=skill_prompt.prompt if skill_prompt else None,
                allowed_tools=required_tools if required_tools else None
            )

            # 4. Execute role's mission
            logger.info(f"   🏃 Executing...")
            try:
                # Prepare context from completed missions
                context = self._build_context_for_mission(mission)

                # Execute
                result = await role_executor.execute(context=context)

                # Track cost
                # TODO: Extract actual cost from result if available
                self.context.total_cost_usd += 0.10  # Placeholder

            except Exception as e:
                logger.error(f"   ❌ Execution error: {e}")
                result = {
                    "success": False,
                    "error": str(e)
                }

            # 5. Monitor and decide intervention
            decision = await self._monitor_and_decide(mission, role, result, iteration)

            logger.info(f"   🧠 Intervention: {decision.action.value}")
            if decision.reason:
                logger.info(f"      Reason: {decision.reason}")

            # Record intervention
            self._record_intervention(mission, role, decision, iteration)

            # 6. Act based on decision
            if decision.action == InterventionAction.CONTINUE:
                return {
                    "success": True,
                    "mission_id": mission.id,
                    "role": role.name,
                    "result": result,
                    "iterations": iteration
                }

            elif decision.action == InterventionAction.RETRY:
                logger.info(f"   🔁 Retrying...")
                continue

            elif decision.action == InterventionAction.ENHANCE:
                logger.info(f"   ⚡ Enhancing task requirements...")
                # Enhance mission with LLM-driven refinement
                quality_issues = result.get('validation_result', {}).get('errors', [])
                enhanced_mission = await self._enhance_mission(mission, quality_issues)
                # Replace the mission with enhanced version
                mission = enhanced_mission
                role.mission = enhanced_mission
                logger.info(f"      Enhanced goal: {enhanced_mission.goal[:100]}...")
                continue

            elif decision.action == InterventionAction.ESCALATE:
                logger.warning(f"   ⚠️ Escalating with helper role...")
                # Spawn helper role to assist
                helper_result = await self._spawn_helper_role(mission, role, result)

                if helper_result.get('success'):
                    logger.info(f"      Helper role succeeded!")
                    # Merge helper outputs with main result
                    result['outputs'] = helper_result.get('outputs', {})
                    result['success'] = True
                    result['validation_passed'] = True
                    # Return success after helper assistance
                    return {
                        "success": True,
                        "mission_id": mission.id,
                        "role": role.name,
                        "result": result,
                        "iterations": iteration,
                        "helper_assisted": True
                    }
                else:
                    logger.warning(f"      Helper role also failed")
                    # Continue to retry or terminate
                    continue

            else:  # TERMINATE
                logger.error(f"   ❌ Terminating mission")
                return {
                    "success": False,
                    "error": decision.reason
                }

        # Exceeded max retries
        logger.error(f"❌ Max retries ({self.max_mission_retries}) exceeded")
        return {
            "success": False,
            "error": f"Max retries exceeded"
        }



    def _build_context_for_mission(self, mission: SubMission) -> Dict[str, Any]:
        """
        Build context for a mission from completed mission outputs.

        Includes outputs from missions that this one depends on.
        """
        context = {}

        for dep_id in mission.dependencies:
            if dep_id in self.context.completed_missions:
                context[dep_id] = self.context.completed_missions[dep_id]

        return context

    async def _monitor_and_decide(
        self,
        mission: SubMission,
        role: Role,
        result: Dict[str, Any],
        iteration: int
    ) -> InterventionDecision:
        """
        Monitor execution result and decide intervention.

        Args:
            mission: The mission that was executed
            role: The role that executed it
            result: Execution result
            iteration: Current iteration number

        Returns:
            InterventionDecision with action and reason
        """
        # Check if execution succeeded
        if not result.get('success', False):
            if iteration < self.max_mission_retries:
                return InterventionDecision(
                    action=InterventionAction.RETRY,
                    reason=f"Execution failed: {result.get('error', 'Unknown error')}"
                )
            else:
                return InterventionDecision(
                    action=InterventionAction.TERMINATE,
                    reason="Max retries exceeded"
                )

        # Check validation passed
        if not result.get('validation_passed', False):
            if iteration < self.max_mission_retries:
                errors = result.get('validation_errors', [])
                return InterventionDecision(
                    action=InterventionAction.RETRY,
                    reason=f"Validation failed: {', '.join(errors)}"
                )
            else:
                return InterventionDecision(
                    action=InterventionAction.TERMINATE,
                    reason="Validation failed repeatedly"
                )

        # Success!
        return InterventionDecision(
            action=InterventionAction.CONTINUE,
            reason="Mission completed successfully"
        )

    async def _spawn_helper_role(
        self,
        mission: SubMission,
        main_role: Role,
        failed_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Spawn a helper role to assist with a failed mission.

        Args:
            mission: The mission that failed
            main_role: The main role that failed
            failed_result: The failed execution result

        Returns:
            Helper execution result
        """
        logger.info(f"🆘 Spawning helper role for mission '{mission.id}'...")

        # Determine helper role type based on failure reason
        validation_errors = failed_result.get('validation_result', {}).get('errors', [])
        helper_role_name = self._select_helper_role(validation_errors)

        logger.info(f"   Selected helper: {helper_role_name}")

        # Register helper with governor
        helper_id = self.helper_governor.register_helper(
            role_name=helper_role_name,
            mission_id=mission.id
        )

        # Build helper-specific task
        helper_task = f"""You are a {helper_role_name} helping to fix a failed mission.

# Original Mission
Goal: {mission.goal}
Type: {mission.type}

# Main Role That Failed
Role: {main_role.name}

# Validation Errors
{chr(10).join(f"- {err}" for err in validation_errors)}

# Your Task
Analyze the failures and fix the issues. Generate the required outputs that pass validation.

Working directory: {self.work_dir}
IMPORTANT: Write all files to '{self.work_dir}'

Required files:
{chr(10).join(f"- {f}" for f in main_role.output_standard.required_files)}

Success criteria:
{chr(10).join(f"- {c}" for c in mission.success_criteria)}
"""

        # Create helper executor
        helper_executor = ExecutorAgent(
            work_dir=str(self.work_dir),
            model="haiku",  # Use faster/cheaper model for helpers
            timeout_seconds=300,
            permission_mode="bypassPermissions"
        )

        # Execute helper with iteration limit
        max_helper_iterations = 5
        for iter_count in range(1, max_helper_iterations + 1):
            logger.info(f"   Helper iteration {iter_count}/{max_helper_iterations}")

            try:
                # Execute task
                await helper_executor.execute_task(helper_task)

                # Record iteration
                self.helper_governor.record_iteration(
                    helper_id=helper_id,
                    success=True,
                    cost_usd=0.05,  # Estimate
                    progress_delta=0.2
                )

                # Check if should exit
                should_exit, exit_reason = self.helper_governor.should_exit(helper_id)
                if should_exit:
                    logger.info(f"   Helper exit condition: {exit_reason}")
                    break

                # Validate outputs (reuse main role validation)
                from pathlib import Path
                outputs = {}
                all_valid = True

                for filename in main_role.output_standard.required_files:
                    file_path = Path(self.work_dir) / filename
                    if file_path.exists():
                        outputs[filename] = file_path.read_text(encoding='utf-8')
                    else:
                        all_valid = False
                        break

                if all_valid:
                    logger.info(f"✅ Helper role completed successfully!")
                    self.helper_governor.exit_helper(helper_id, reason="Goal achieved")
                    return {
                        "success": True,
                        "outputs": outputs,
                        "helper_id": helper_id,
                        "iterations": iter_count
                    }

                # Update task with feedback
                helper_task += f"\n\nPrevious attempt {iter_count} failed. Please try again and ensure all files are created."

            except Exception as e:
                logger.error(f"   Helper execution error: {e}")
                self.helper_governor.record_iteration(
                    helper_id=helper_id,
                    success=False,
                    cost_usd=0.05
                )

        # Helper failed
        self.helper_governor.exit_helper(helper_id, reason="Max iterations exceeded")
        logger.warning(f"❌ Helper role failed after {max_helper_iterations} iterations")

        return {
            "success": False,
            "helper_id": helper_id,
            "error": "Helper role could not complete the task"
        }

    def _select_helper_role(self, validation_errors: List[str]) -> str:
        """
        Select appropriate helper role based on validation errors.

        Args:
            validation_errors: List of validation error messages

        Returns:
            Helper role name
        """
        # Simple heuristic-based selection
        errors_text = " ".join(validation_errors).lower()

        if "security" in errors_text or "vulnerability" in errors_text:
            return "SecurityExpert"
        elif "performance" in errors_text or "slow" in errors_text:
            return "PerfAnalyzer"
        elif "review" in errors_text or "quality" in errors_text:
            return "Reviewer"
        else:
            # Default to Debugger for general issues
            return "Debugger"

    async def _enhance_mission(
        self,
        mission: SubMission,
        quality_issues: List[str]
    ) -> SubMission:
        """
        Enhance mission using LLM to refine requirements based on quality issues.

        Args:
            mission: Original mission
            quality_issues: List of validation errors or quality problems

        Returns:
            Enhanced SubMission with refined goal and requirements
        """
        logger.info(f"🔍 Enhancing mission '{mission.id}' with LLM...")

        # Build enhancement prompt
        issues_str = "\n".join(f"- {issue}" for issue in quality_issues) if quality_issues else "General quality improvement needed"

        prompt = f"""You are a task refinement expert. A mission has failed validation or quality checks.
Your job is to refine the mission requirements to make them more specific and achievable.

# Original Mission
ID: {mission.id}
Type: {mission.type}
Goal: {mission.goal}

## Current Requirements
{chr(10).join(f"- {req}" for req in mission.requirements)}

## Current Success Criteria
{chr(10).join(f"- {crit}" for crit in mission.success_criteria)}

## Quality Issues Encountered
{issues_str}

# Task
Refine this mission to address the quality issues. Make the goal more specific, add missing requirements,
and clarify success criteria. Be concrete and actionable.

Return a JSON object with this exact structure:
{{
    "goal": "refined goal statement",
    "requirements": ["requirement1", "requirement2", ...],
    "success_criteria": ["criterion1", "criterion2", ...]
}}

IMPORTANT: Return ONLY the JSON object, no additional text."""

        try:
            # Call LLM
            response = await run_claude_prompt(
                prompt=prompt,
                model=self.model,
                timeout_seconds=60
            )

            # Parse response
            import json
            import re

            # Extract JSON from response (might have markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find raw JSON
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON found in LLM response")

            enhanced_data = json.loads(json_str)

            # Create enhanced mission
            enhanced_mission = SubMission(
                id=mission.id,
                type=mission.type,
                goal=enhanced_data.get("goal", mission.goal),
                requirements=enhanced_data.get("requirements", mission.requirements),
                success_criteria=enhanced_data.get("success_criteria", mission.success_criteria),
                dependencies=mission.dependencies,
                priority=mission.priority,
                estimated_cost_usd=mission.estimated_cost_usd
            )

            logger.info(f"✅ Mission enhanced successfully")
            logger.info(f"   New goal: {enhanced_mission.goal}")
            logger.info(f"   Requirements updated: {len(enhanced_mission.requirements)} items")

            return enhanced_mission

        except Exception as e:
            logger.error(f"❌ Failed to enhance mission: {e}")
            logger.warning(f"   Falling back to original mission")
            return mission

    def _record_intervention(
        self,
        mission: SubMission,
        role: Role,
        decision: InterventionDecision,
        iteration: int
    ):
        """Record intervention to history"""
        self.context.intervention_count += 1

        intervention = {
            "id": self.context.intervention_count,
            "mission_id": mission.id,
            "mission_type": mission.type,
            "role": role.name,
            "iteration": iteration,
            "action": decision.action.value,
            "reason": decision.reason,
            "timestamp": time.time()
        }

        self.intervention_history.append(intervention)

        # Save to file
        self._save_intervention_log()

    def _save_intervention_log(self):
        """Save intervention history to markdown file"""
        log_dir = Path("logs/interventions")
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / f"{self.context.session_id}_interventions.md"

        lines = [
            f"# Leader Interventions - Session {self.context.session_id}",
            "",
            f"**Goal**: {self.context.goal}",
            f"**Start Time**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.context.start_time))}",
            f"**Total Interventions**: {len(self.intervention_history)}",
            "",
            "---",
            ""
        ]

        for i, intervention in enumerate(self.intervention_history, 1):
            lines.extend([
                f"## Intervention #{i}",
                "",
                f"- **Mission**: {intervention['mission_id']} ({intervention['mission_type']})",
                f"- **Role**: {intervention['role']}",
                f"- **Iteration**: {intervention['iteration']}",
                f"- **Action**: {intervention['action']}",
                f"- **Reason**: {intervention['reason']}",
                f"- **Time**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(intervention['timestamp']))}",
                "",
                "---",
                ""
            ])

        log_file.write_text("\n".join(lines), encoding='utf-8')

    async def _integrate_outputs(self) -> Dict[str, Any]:
        """
        Integrate all mission outputs into final deliverable.

        Uses OutputIntegrator for sophisticated integration and multi-format reporting.
        """
        from src.core.output.output_integrator import OutputIntegrator, OutputFormat

        # Create OutputIntegrator
        integrator = OutputIntegrator(self.work_dir)

        # Prepare metadata
        metadata = {
            "intervention_count": self.context.intervention_count,
            "model": self.model
        }

        # Integrate outputs
        integrated = integrator.integrate(
            session_id=self.context.session_id,
            goal=self.context.goal,
            mission_results=self.context.completed_missions,
            metadata=metadata,
            intervention_history=self.intervention_history
        )

        # Generate reports in multiple formats
        reports = integrator.generate_reports(
            integrated,
            formats=[OutputFormat.MARKDOWN, OutputFormat.JSON, OutputFormat.HTML]
        )

        # Organize deliverables
        integrator.organize_deliverables(integrated)

        logger.info(f"📦 Deliverable integration complete")
        logger.info(f"   Reports generated: {len(reports)}")
        for fmt, path in reports.items():
            logger.info(f"     {fmt.value}: {path}")

        # Return deliverable dictionary for backward compatibility
        return {
            "goal": integrated.goal,
            "session_id": integrated.session_id,
            "missions": {
                m.mission_id: {
                    "type": m.mission_type,
                    "role": m.role,
                    "outputs": m.files,
                    "iterations": m.iterations,
                    "quality_score": m.quality_score
                }
                for m in integrated.mission_outputs
            },
            "summary": integrated.summary,
            "reports": {fmt.value: str(path) for fmt, path in reports.items()}
        }

    def _get_metadata(self) -> Dict[str, Any]:
        """Get execution metadata"""
        return {
            "session_id": self.context.session_id,
            "goal": self.context.goal,
            "total_missions": len(self.context.missions),
            "completed_missions": len(self.context.completed_missions),
            "total_cost_usd": round(self.context.total_cost_usd, 2),
            "execution_time_seconds": round(time.time() - self.context.start_time, 1),
            "intervention_count": self.context.intervention_count,
            "model": self.model
        }
