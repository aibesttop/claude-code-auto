"""
Planner Agent
Decomposes goals and manages the high-level plan.
"""
import json
from typing import List, Dict, Optional
from pydantic import BaseModel
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock
from logger import get_logger

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
    status: str = "pending" # pending, in_progress, done

class Plan(BaseModel):
    tasks: List[Task] = []

class PlannerAgent:
    def __init__(self, work_dir: str, goal: str):
        self.work_dir = work_dir
        self.goal = goal
        self.plan = Plan()
        
    async def get_next_step(self, last_result: str = None) -> Optional[str]:
        """Determines the next sub-task"""
        logger.info("🧠 Planner thinking...")
        
        options = ClaudeCodeOptions(
            permission_mode="bypassPermissions",
            cwd=self.work_dir
        )
        
        # Construct prompt
        plan_state = json.dumps([t.model_dump() for t in self.plan.tasks], indent=2)
        try:
            prompt = PLANNER_SYSTEM_PROMPT.format(
                goal=self.goal,
                plan_state=plan_state
            )
        except KeyError as e:
            logger.error(f"❌ Failed to format planner prompt: {e}")
            logger.error("Check for single braces '{' in PLANNER_SYSTEM_PROMPT that should be double braces '{{'")
            # Fallback or re-raise
            raise e
        
        if last_result:
            prompt += f"\n\nLast Executor Result: {last_result}"
            
        async with ClaudeSDKClient(options) as client:
            await client.query(prompt)
            
            response_text = ""
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
                            
            # Parse JSON response
            try:
                # Extract JSON from markdown if needed
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0]
                else:
                    json_str = response_text
                    
                data = json.loads(json_str)
                
                # Update internal plan
                self.plan.tasks = [Task(**t) for t in data.get("plan", [])]
                
                if data.get("is_complete"):
                    logger.info("🎉 Planner: All tasks completed!")
                    return None
                    
                next_task = data.get("next_task")
                logger.info(f"👉 Next Task: {next_task}")
                return next_task
                
            except Exception as e:
                logger.error(f"❌ Planner failed to parse response: {e}")
                logger.debug(f"Raw response: {response_text}")
                return None
