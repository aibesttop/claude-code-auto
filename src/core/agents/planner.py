"""
Planner Agent
Decomposes goals and manages the high-level plan.
"""
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel

from src.utils.logger import get_logger
from src.core.agents.sdk_client import run_claude_prompt

logger = get_logger()

PLANNER_SYSTEM_PROMPT = """You are a Planner. Break this goal into sub-tasks:

Goal: {goal}

Current Plan:
{plan_state}

Rules:
- Create 3-7 atomic sub-tasks if plan is empty
- Update status: done/pending
- Output next task for executor
- Output ONLY JSON

{{
    "plan": [{{"id": 1, "task": "...", "status": "pending"}}],
    "next_task": "...",
    "is_complete": false
}}
"""


class Task(BaseModel):
    id: int
    task: str
    status: str = "pending"  # pending, in_progress, done


class Plan(BaseModel):
    tasks: List[Task] = []


class PlannerAgent:
    def __init__(
        self,
        work_dir: str,
        goal: str,
        *,
        model: Optional[str] = None,
        timeout_seconds: int = 300,
        permission_mode: str = "bypassPermissions",
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        # Use absolute path to avoid CWD-related issues
        self.work_dir = str(Path(work_dir).resolve())
        logger.info(f"📁 PlannerAgent work_dir (absolute): {self.work_dir}")
        self.goal = goal
        self.plan = Plan()
        self.model = model
        self.base_timeout_seconds = timeout_seconds
        self.permission_mode = permission_mode
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Trace tracking
        self.last_result = None
        self.last_response = None
        self.next_task = None
        self.confidence = "N/A"
        self.call_count = 0  # Track number of calls for dynamic timeout

    def _calculate_dynamic_timeout(self) -> int:
        """
        Calculate dynamic timeout based on call context.

        Strategy:
        - First call (plan creation): 2x base timeout (most complex)
        - Subsequent calls: base timeout (simpler updates)
        - Large plan state (>10 tasks): +50% timeout
        """
        timeout = self.base_timeout_seconds

        # First call needs more time (creating plan from scratch)
        if self.call_count == 0:
            timeout = self.base_timeout_seconds * 2
            logger.info(f"🕐 First Planner call - using extended timeout: {timeout}s")

        # Large plans need more time
        plan_size = len(self.plan.tasks)
        if plan_size > 10:
            timeout = int(timeout * 1.5)
            logger.info(f"🕐 Large plan ({plan_size} tasks) - using extended timeout: {timeout}s")

        return max(timeout, 120)  # Minimum 2 minutes

    async def get_next_step(self, last_result: str = None) -> Optional[str]:
        """Determines the next sub-task"""
        logger.info("🧠 Planner thinking...")

        # Increment call counter
        self.call_count += 1

        # Calculate dynamic timeout
        dynamic_timeout = self._calculate_dynamic_timeout()

        # Store for trace export
        self.last_result = last_result

        plan_state = json.dumps([t.model_dump() for t in self.plan.tasks], indent=2)
        try:
            prompt = PLANNER_SYSTEM_PROMPT.format(
                goal=self.goal,
                plan_state=plan_state
            )
        except KeyError as e:
            logger.error(f"Failed to format planner prompt: {e}")
            logger.error("Check for single braces '{' in PLANNER_SYSTEM_PROMPT that should be double braces '{{'")
            raise e

        if last_result:
            prompt += f"\n\nLast Executor Result: {last_result}"

        try:
            response_text, _ = await run_claude_prompt(
                prompt,
                self.work_dir,
                model=self.model,
                permission_mode=self.permission_mode,
                timeout=dynamic_timeout,  # Use dynamic timeout
                max_retries=self.max_retries,
                retry_delay=self.retry_delay,
            )

            # Store response for trace
            self.last_response = response_text

        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f"Planner query failed: {exc}")

            # Degradation strategy: If planning fails, return direct task
            if self.call_count == 1 and len(self.plan.tasks) == 0:
                # First call failed - return the goal itself as the only task
                logger.warning("⚠️ Planner first call failed, using direct execution mode")
                logger.info(f"📋 Direct task: {self.goal}")

                # Create a simple single-task plan
                self.plan.tasks = [
                    Task(id=1, task=self.goal, status="pending")
                ]

                # Return the goal as the next task
                return self.goal

            # Subsequent calls - mark all pending as done and finish
            if len(self.plan.tasks) > 0:
                logger.warning("⚠️ Planner update failed, marking remaining tasks as done")
                return None

            # Complete failure
            return None

        try:
            from src.utils.json_utils import extract_json
            data = extract_json(response_text)

            if not data or not isinstance(data, dict):
                logger.error(f"Planner failed to find valid JSON in response: {response_text[:200]}...")
                return None

            self.plan.tasks = [Task(**t) for t in data.get("plan", [])]

            if data.get("is_complete"):
                logger.info("🎉 Planner: All tasks completed!")
                self.next_task = None
                return None

            next_task = data.get("next_task")
            self.next_task = next_task
            logger.info(f"👉 Next Task: {next_task}")
            return next_task

        except Exception as e:
            logger.error(f"Planner failed to parse response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return None

    def export_plan_to_markdown(
        self,
        session_id: str,
        role_name: str = "Planner",
        step: int = 1
    ) -> Optional[str]:
        """
        Export current plan state to markdown trace file.

        Args:
            session_id: Current session ID
            role_name: Name of the role (default: "Planner")
            step: Step number in the workflow

        Returns:
            Path to the created trace file, or None if failed
        """
        try:
            # Ensure trace directory exists
            trace_dir = Path("logs/trace")
            trace_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            filename = f"{session_id}_{role_name}_step{step}.md"
            trace_path = trace_dir / filename

            # Build markdown content
            content_lines = [
                f"# {role_name} - Step {step} Planning Trace",
                "",
                f"**Timestamp**: {datetime.now().isoformat()}",
                f"**Session ID**: {session_id}",
                "",
                "---",
                "",
                "## Goal",
                f"{self.goal}",
                ""
            ]

            # Previous context
            if self.last_result:
                content_lines.extend([
                    "## Previous Execution Result",
                    "```",
                    self.last_result[:500] if len(self.last_result) > 500 else self.last_result,
                    "..." if len(self.last_result) > 500 else "",
                    "```",
                    ""
                ])

            # Current plan
            if self.plan.tasks:
                content_lines.extend([
                    "## Current Plan",
                    ""
                ])
                for task in self.plan.tasks:
                    status_icon = "✅" if task.status == "done" else ("🔄" if task.status == "in_progress" else "⏳")
                    content_lines.append(f"{status_icon} **Task {task.id}**: {task.task} ({task.status})")
                content_lines.append("")

            # Next task
            if self.next_task:
                content_lines.extend([
                    "## Next Task Decision",
                    f"```",
                    self.next_task,
                    "```",
                    ""
                ])

            # LLM Response (truncated)
            if self.last_response:
                content_lines.extend([
                    "## LLM Response",
                    "```json",
                    self.last_response[:800] if len(self.last_response) > 800 else self.last_response,
                    "..." if len(self.last_response) > 800 else "",
                    "```",
                    ""
                ])

            # Confidence/Metadata
            content_lines.extend([
                "## Metadata",
                f"- Model: {self.model or 'default'}",
                f"- Total Tasks: {len(self.plan.tasks)}",
                f"- Completed: {len([t for t in self.plan.tasks if t.status == 'done'])}",
                f"- Pending: {len([t for t in self.plan.tasks if t.status == 'pending'])}",
                ""
            ])

            # Write to file
            trace_path.write_text("\n".join(content_lines), encoding='utf-8')

            logger.info(f"📝 Plan trace exported: {trace_path}")
            return str(trace_path)

        except Exception as e:
            logger.error(f"Failed to export plan trace: {e}")
            return None
