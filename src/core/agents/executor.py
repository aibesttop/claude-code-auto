"""
Executor Agent (ReAct Engine)
Executes specific sub-tasks using the ReAct pattern.
"""
import json
import re
import os
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime

from src.utils.logger import get_logger
from src.core.tool_registry import registry
from src.core.agents.persona import PersonaEngine
from src.core.agents.sdk_client import run_claude_prompt

logger = get_logger()

REACT_SYSTEM_PROMPT = """
You are an autonomous Executor Agent.
Your goal is to complete the assigned sub-task using the available tools.

## Tools Available:
{tool_descriptions}

## Format:
To solve the task, you must use the following format:

Thought: [Your reasoning about what to do next]
Action: [The name of the tool to use]
Action Input: [The JSON arguments for the tool]

... (Wait for Observation) ...

Observation: [The result of the tool execution]

... (Repeat Thought/Action/Observation as needed) ...

When you have completed the task, use the format:
Thought: I have completed the task.
Final Answer: [Your summary of what was done]

## Constraints:
1. You must use the tools to verify your work.
2. "Action Input" must be valid JSON.
3. Do not make up tools.
"""


class ExecutorAgent:
    def __init__(
        self,
        work_dir: str,
        persona_config: dict = None,
        *,
        model: Optional[str] = None,
        timeout_seconds: int = 300,
        permission_mode: str = "bypassPermissions",
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.work_dir = work_dir

        # ReAct loop configuration
        # Increased from 10 to 30 for complex tasks (市场调研等需要更多步骤)
        self.max_steps = 30

        self.persona_engine = PersonaEngine(persona_config=persona_config)
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.permission_mode = permission_mode
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Trace tracking
        self.current_task = None
        self.react_history = []
        
    def set_persona(self, persona_name: str):
        """Sets the persona for the agent"""
        if self.persona_engine.switch_persona(persona_name):
            logger.info(f"🎭 Switched persona to: {persona_name}")
        else:
            logger.warning(f"⚠️ Persona not found: {persona_name}")

    def _get_tool_descriptions(self) -> str:
        schemas = registry.get_all_schemas()
        desc = []
        for s in schemas:
            desc.append(f"- {s['name']}: {s['description']}")
            desc.append(f"  Schema: {json.dumps(s['input_schema'])}")
        return "\n".join(desc)

    def _parse_action(self, text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Parses the Action and Action Input from text"""
        action_match = re.search(r"Action:\s*(.+)", text)
        input_match = re.search(r"Action Input:\s*(.+)", text, re.DOTALL)
        
        if not action_match:
            return None, None
            
        action = action_match.group(1).strip()
        
        # If no input match, check if it's a tool that takes no args or if args are implicit
        # But per ReAct format, Action Input is usually expected.
        if not input_match:
            # Try to find a JSON block anywhere in the text if Action Input pattern fails
            # This handles cases where the model forgets "Action Input:" prefix but provides JSON
            from src.utils.json_utils import extract_json
            args = extract_json(text)
            if args and isinstance(args, dict):
                return action, args
            return action, None
            
        input_str = input_match.group(1).strip()
        
        from src.utils.json_utils import extract_json
        args = extract_json(input_str)
        
        if args is not None:
            return action, args
        else:
            logger.error(f"Failed to parse JSON args: {input_str[:200]}...")
            return action, None

    async def execute_task(self, task_description: str) -> str:
        """Executes a single sub-task"""
        logger.info(f"🤖 Executor started task: {task_description}")

        # Record for trace
        self.current_task = task_description
        self.react_history = []

        # Ensure work directory exists and get absolute path
        work_dir_path = Path(self.work_dir).resolve()
        work_dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Work directory: {work_dir_path}")

        # CRITICAL: Change process working directory to match work_dir
        # This ensures all file operations using relative paths are relative to work_dir
        original_cwd = os.getcwd()
        os.chdir(work_dir_path)
        logger.info(f"📂 Changed CWD from {original_cwd} to {work_dir_path}")

        try:
            tool_desc = self._get_tool_descriptions()

            persona_prompt = self.persona_engine.get_system_prompt()
            base_system_prompt = REACT_SYSTEM_PROMPT.format(tool_descriptions=tool_desc)

            # Add work directory instruction to system prompt
            # IMPORTANT: Use forward slashes for JSON compatibility
            work_dir_str = str(work_dir_path).replace('\\', '/')
            work_dir_instruction = f"\n\n## Working Directory\nAll file operations should use paths relative to: {self.work_dir}\nWhen using write_file or read_file, use RELATIVE paths like 'filename.md' or 'subdir/filename.md'\nDO NOT use absolute paths. Always use forward slashes (/) in paths for JSON compatibility."
            full_system_prompt = f"{persona_prompt}\n\n{base_system_prompt}{work_dir_instruction}"

            history = [
                f"System: {full_system_prompt}",
                f"Task: {task_description}"
            ]

            current_prompt = "\n\n".join(history)
            step = 0

            while step < self.max_steps:
                step += 1
                logger.info(f"🔄 ReAct Step {step}/{self.max_steps}")

                try:
                    response_text, _ = await run_claude_prompt(
                        current_prompt,
                        self.work_dir,
                        model=self.model,
                        permission_mode=self.permission_mode,
                        timeout=self.timeout_seconds,
                        max_retries=self.max_retries,
                        retry_delay=self.retry_delay,
                    )

                    # Record for trace
                    self.react_history.append(response_text)

                except Exception as exc:  # pylint: disable=broad-except
                    logger.error(f"Executor Claude query failed: {exc}")
                    return f"Error: {exc}"

                logger.debug(f"Claude Response:\n{response_text}")

                if "Final Answer:" in response_text:
                    final_answer = response_text.split("Final Answer:")[1].strip()
                    logger.info(f"Task Completed: {final_answer}")
                    return final_answer

                action, args = self._parse_action(response_text)

                if action and args is not None:
                    logger.info(f"🛠️ Calling Tool: {action}")
                    result = None
                    try:
                        result = registry.execute(action, args)
                        observation = f"\nObservation: {result}\n"
                    except Exception as e:  # pylint: disable=broad-except
                        observation = f"\nObservation: Error executing tool: {str(e)}\n"

                    logger.debug(f"Tool Result: {result}")

                    history.append(response_text.strip())
                    history.append(observation.strip())
                    current_prompt = "\n\n".join(history)

                else:
                    if "Thought:" in response_text and not action:
                        history.append(response_text.strip())
                        history.append("System: I did not see a valid 'Action:' and 'Action Input:'. Please format your tool call correctly.")
                        current_prompt = "\n\n".join(history)
                    else:
                        logger.warning("⚠️ No action detected and no Final Answer.")
                        history.append(response_text.strip())
                        history.append("System: Please continue. If done, say 'Final Answer:'.")
                        current_prompt = "\n\n".join(history)

            return "Error: Max steps reached without completion."

        finally:
            # Restore original working directory
            os.chdir(original_cwd)
            logger.info(f"📂 Restored CWD to {original_cwd}")

    def export_react_trace(
        self,
        session_id: str,
        role_name: str = "Executor",
        step: int = 1
    ) -> Optional[str]:
        """
        Export ReAct execution history to markdown trace file.
        
        Args:
            session_id: Current session ID
            role_name: Name of the role
            step: Step number
            
        Returns:
            Path to trace file or None
        """
        try:
            trace_dir = Path("logs/trace")
            trace_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{session_id}_{role_name}_executor_step{step}.md"
            trace_path = trace_dir / filename
            
            content = [
                f"# {role_name} - Executor Step {step} Trace",
                "",
                f"**Timestamp**: {datetime.now().isoformat()}",
                f"**Session**: {session_id}",
                "",
                "---",
                "",
                "## Task",
                f"```",
                str(self.current_task) if self.current_task else "N/A",
                "```",
                "",
                "## ReAct History",
                ""
            ]
            
            if self.react_history:
                for i, entry in enumerate(self.react_history, 1):
                    content.append(f"### Step {i}")
                    content.append("```")
                    content.append(str(entry)[:500] if len(str(entry)) > 500 else str(entry))
                    if len(str(entry)) > 500:
                        content.append("...")
                    content.append("```")
                    content.append("")
            else:
                content.append("No execution history recorded.")
                content.append("")
            
            trace_path.write_text("\n".join(content), encoding='utf-8')
            logger.info(f"📝 Executor trace exported: {trace_path}")
            return str(trace_path)
            
        except Exception as e:
            logger.error(f"Failed to export executor trace: {e}")
            return None
