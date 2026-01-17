"""
Executor Agent (ReAct Engine)
Executes specific sub-tasks using the ReAct pattern.
"""
import json
import re
import os
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path
from datetime import datetime

from src.utils.logger import get_logger
from src.core.tool_registry import registry
from src.core.agents.persona import PersonaEngine
from src.core.agents.sdk_client import run_claude_prompt

logger = get_logger()
FINAL_ANSWER_PATTERN = re.compile(r"(?im)^\s*(?:#+\s*)?Final Answer\s*:?\s*")

REACT_SYSTEM_PROMPT = """
You are a task executor. Use the ReAct format:

Thought: [what you want to do]
Action: [tool name from list below]
Action Input: [JSON input]

Tools:
{tool_descriptions}

CRITICAL: Always use the exact format above. Action Input MUST be valid JSON.

CRITICAL WORKFLOW RULES:
1. If the task requires file outputs (see "Required files" in the task), you MUST call write_file BEFORE Final Answer
2. The Final Answer should only be a brief summary (1-2 sentences), NOT the full content
3. All substantive content MUST be written to files using write_file tool
4. DO NOT skip write_file - providing a Final Answer without saving required files will cause the task to FAIL
5. Each ReAct step should accomplish ONE specific action (research OR write, not both)
6. If the system returns a validation error after completion, it means your output files ON DISK do not meet requirements. DO NOT argue; read the files and fix the gaps.

When done:
Thought: I have completed the task and saved all required files.
Final Answer: [brief summary of what was saved to files]
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
        allowed_tools: Optional[List[str]] = None,
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
        self.allowed_tools = allowed_tools

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
        allowed = set(self.allowed_tools) if self.allowed_tools else None
        if allowed:
            filtered = [s for s in schemas if s["name"] in allowed]
            if filtered:
                schemas = filtered
            else:
                logger.warning("Allowed tools configured but none matched registry; falling back to all tools.")
        desc = []
        for s in schemas:
            desc.append(f"- {s['name']}: {s['description']}")
            input_schema = s.get("input_schema", {})
            if input_schema:
                compact_schema = {
                    "type": "object",
                    "properties": input_schema.get("properties", {})
                }
                required = input_schema.get("required", [])
                if required:
                    compact_schema["required"] = required
                desc.append(f"  Input JSON: {json.dumps(compact_schema, separators=(',', ':'))}")
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

    def _extract_final_answer(self, text: str) -> Optional[str]:
        """Extracts a final answer block, allowing common markdown variants."""
        match = FINAL_ANSWER_PATTERN.search(text)
        if not match:
            return None
        return text[match.end():].strip()

    def _extract_required_files(self, task_description: str) -> List[str]:
        """Extract required file list from the task description."""
        required_files = []
        in_section = False
        for line in task_description.splitlines():
            stripped = line.strip()
            if not in_section:
                if stripped.lower().startswith("required files"):
                    in_section = True
                continue
            if not stripped or stripped.startswith("##"):
                break
            if stripped.startswith("-"):
                filename = stripped.lstrip("-").strip()
                if filename:
                    required_files.append(filename)
        return required_files

    def _is_verification_task(self, task_description: str) -> bool:
        """Best-effort check to avoid blocking verification-only tasks."""
        lowered = task_description.lower()
        keywords = ("verify", "check", "validate", "audit", "review")
        return any(keyword in lowered for keyword in keywords)

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
        required_files = self._extract_required_files(task_description)
        enforce_required_files = bool(required_files) and not self._is_verification_task(task_description)

        # CRITICAL: Change process working directory to match work_dir
        # This ensures all file operations using relative paths are relative to work_dir
        original_cwd = work_dir_path
        os.chdir(work_dir_path)
        logger.info(f"📂 Set CWD to work_dir: {work_dir_path}")

        try:
            tool_desc = self._get_tool_descriptions()

            persona_prompt = self.persona_engine.get_system_prompt()
            base_system_prompt = REACT_SYSTEM_PROMPT.format(tool_descriptions=tool_desc)

            # Add work directory instruction to system prompt
            # IMPORTANT: Use forward slashes for JSON compatibility
            work_dir_str = str(work_dir_path).replace('\\', '/')
            work_dir_instruction = f"\n\n## Working Directory\nAll file operations should use paths relative to: {self.work_dir}\nWhen using write_file or read_file, use RELATIVE paths like 'filename.md' or 'subdir/filename.md'\nDO NOT use absolute paths. Always use forward slashes (/) in paths for JSON compatibility."
            full_system_prompt = f"{base_system_prompt}\n\n{persona_prompt}{work_dir_instruction}"

            history = [
                f"System: {full_system_prompt}",
                f"Task: {task_description}"
            ]

            current_prompt = "\n\n".join(history)
            step = 0
            no_action_count = 0
            max_no_action = 5
            tool_calls = 0

            while step < self.max_steps:
                step += 1
                logger.info(f"🔄 ReAct Step {step}/{self.max_steps}")

                try:
                    response_text, _ = await run_claude_prompt(
                        current_prompt,
                        "./", 
                        # self.work_dir,
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

                # Debug: Log response to help diagnose "No action detected" issue
                logger.info(f"📝 Response length: {len(response_text)} chars")
                if "Action:" in response_text:
                    logger.info("✓ Response contains 'Action:'")
                else:
                    logger.warning("✗ Response MISSING 'Action:' keyword")
                if "Thought:" in response_text:
                    logger.info("✓ Response contains 'Thought:'")
                if "Final Answer:" in response_text:
                    logger.info("✓ Response contains 'Final Answer:'")

                final_answer = self._extract_final_answer(response_text)
                if final_answer is not None:
                    if enforce_required_files:
                        if tool_calls == 0:
                            logger.warning("Final Answer provided but no tools were called.")
                            history.append(response_text.strip())
                            history.append(
                                "System: You must call the appropriate tools before finalizing. "
                                "Use web_search/read_file/write_file as needed."
                            )
                            current_prompt = "\n\n".join(history)
                            no_action_count += 1
                            if no_action_count >= max_no_action:
                                logger.error("Repeated invalid responses without tool use. Aborting.")
                                return (
                                    "Error: Final Answer provided but no tools were called after "
                                    f"{no_action_count} consecutive steps."
                                )
                            continue
                        missing = [
                            filename for filename in required_files
                            if not (work_dir_path / filename).exists()
                        ]
                        if missing:
                            logger.warning(f"Final Answer provided but required files missing: {missing}")
                            history.append(response_text.strip())
                            history.append(
                                "System: Missing required files: "
                                + ", ".join(missing)
                                + ". Use write_file to create them before finalizing."
                            )
                            current_prompt = "\n\n".join(history)
                            no_action_count += 1
                            if no_action_count >= max_no_action:
                                logger.error("Repeated invalid responses without required files. Aborting.")
                                return (
                                    "Error: Final Answer provided but required files missing after "
                                    f"{no_action_count} consecutive steps."
                                )
                            continue
                    logger.info(f"Task Completed: {final_answer}")
                    return final_answer

                action, args = self._parse_action(response_text)

                # Debug: Log parsing results
                logger.info(f"🔍 Parsed: action={action}, args={'None' if args is None else f'<{len(str(args))} chars>'}")
                if action and args is None:
                    logger.warning(f"⚠️ Action '{action}' found but args is None - check JSON format")

                if action and args is not None:
                    no_action_count = 0
                    tool_calls += 1
                    logger.info(f"Calling Tool: {action}")
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
                    no_action_count += 1
                    if action and args is None:
                        logger.warning("Action Input missing or invalid JSON.")
                        history.append(response_text.strip())
                        history.append("System: I saw an Action but the Action Input was missing or invalid JSON. Please restate the tool call using Action and Action Input with valid JSON.")
                        current_prompt = "\n\n".join(history)
                    elif "Thought:" in response_text and not action:
                        history.append(response_text.strip())
                        history.append("System: I did not see a valid 'Action:' and 'Action Input:'. Please format your tool call correctly.")
                        current_prompt = "\n\n".join(history)
                    else:
                        logger.warning("No action detected and no Final Answer.")
                        history.append(response_text.strip())
                        history.append("System: Please continue. If done, say 'Final Answer:'.")
                        current_prompt = "\n\n".join(history)
                    if no_action_count >= max_no_action:
                        logger.error("Repeated invalid responses without Action/Final Answer. Aborting.")
                        return f"Error: No valid Action/Final Answer after {no_action_count} consecutive steps."

            return "Error: Max steps reached without completion."

        finally:
            # Ensure CWD stays at work_dir for validation
            # (original_cwd is set to work_dir_path to keep validation working)
            os.chdir(original_cwd)
            logger.info(f"📂 Ensured CWD at work_dir: {original_cwd}")

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
            # CRITICAL: Use configured logs directory to avoid CWD issues
            from src.config import get_config
            logs_dir = Path(get_config().directories.logs_dir)
            trace_dir = logs_dir / "trace"
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
