"""
Planner Agent
Decomposes goals and manages the high-level plan.
"""
import json
from typing import List, Dict, Optional
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
        self.work_dir = work_dir
        self.goal = goal
        self.plan = Plan()
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.permission_mode = permission_mode
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def get_next_step(self, last_result: str = None) -> Optional[str]:
        """Determines the next sub-task"""
        logger.info("🧠 Planner thinking...")

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
                return None

            next_task = data.get("next_task")
            logger.info(f"👉 Next Task: {next_task}")
            return next_task

        except Exception as e:
            logger.error(f"Planner failed to parse response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return None
