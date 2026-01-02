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

PLANNER_SYSTEM_PROMPT = """
You are the Planner Agent.
Your job is to break down a high-level goal into a sequence of atomic sub-tasks.

Current Goal: {goal}

Current Plan State:
{plan_state}

Instructions:
1. Analyze the goal and the current state.
2. If the plan is empty, create a list of sub-tasks.
3. If the plan exists, mark completed tasks and determine the next task.
4. Output the NEXT sub-task to be executed by the Executor.
5. If all tasks are done, output "ALL DONE".

CRITICAL: Your response MUST be ONLY a valid JSON object. Do NOT include any explanatory text before or after the JSON.
Do NOT write "Here is the plan:" or "Looking at..." or any other text. Output ONLY the JSON object.

Format your response as a JSON object:
{{
    "plan": [
        {{"id": 1, "task": "...", "status": "done/pending"}}
    ],
    "next_task": "The specific instruction for the Executor",
    "is_complete": boolean
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
<<<<<<< HEAD
        # 
        self.work_dir = Path(work_dir).resolve()
        logger.info(f"📁 PlannerAgent work_dir (absolute): {self.work_dir}")
=======
        # Use absolute path to avoid CWD-related issues
        self.work_dir = str(Path(work_dir).resolve())
        logger.info(f"📁 PlannerAgent work_dir (absolute): {self.work_dir}")

>>>>>>> e5caba88dacdd6a00e56e8bd8f33a68f1908aac5
        self.goal = goal
        self.plan = Plan()
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.permission_mode = permission_mode
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Trace tracking
        self.last_result = None
        self.last_response = None
        self.next_task = None
        self.confidence = "N/A"

    async def get_next_step(self, last_result: str = None) -> Optional[str]:
        """Determines the next sub-task"""
        logger.info("🧠 Planner thinking...")

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
                timeout=self.timeout_seconds,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay,
            )

            # Store response for trace
            self.last_response = response_text

        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f"Planner query failed: {exc}")
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
