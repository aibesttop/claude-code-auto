"""
Executor Agent (ReAct Engine)
Executes specific sub-tasks using the ReAct pattern.
"""
import json
import re
from typing import List, Dict, Any, Tuple
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage
from logger import get_logger
from core.tool_registry import registry
from core.agents.persona import PersonaEngine

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
    def __init__(self, work_dir: str, persona_config: dict = None):
        self.work_dir = work_dir
        self.max_steps = 10
        self.persona_engine = PersonaEngine(persona_config=persona_config)
        
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

    def _parse_action(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """Parses the Action and Action Input from text"""
        action_match = re.search(r"Action:\s*(.+)", text)
        input_match = re.search(r"Action Input:\s*(.+)", text, re.DOTALL)
        
        if not action_match or not input_match:
            return None, None
            
        action = action_match.group(1).strip()
        input_str = input_match.group(1).strip()
        
        # Cleanup JSON string if it has markdown code blocks
        if input_str.startswith("```json"):
            input_str = input_str[7:]
        if input_str.startswith("```"):
            input_str = input_str[3:]
        if input_str.endswith("```"):
            input_str = input_str[:-3]
            
        try:
            args = json.loads(input_str)
            return action, args
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON args: {input_str}")
            return action, None

    async def execute_task(self, task_description: str) -> str:
        """Executes a single sub-task"""
        logger.info(f"🤖 Executor started task: {task_description}")
        
        options = ClaudeCodeOptions(
            permission_mode="bypassPermissions",
            cwd=self.work_dir
        )
        
        tool_desc = self._get_tool_descriptions()
        
        # Combine Persona Prompt + ReAct Prompt
        persona_prompt = self.persona_engine.get_system_prompt()
        base_system_prompt = REACT_SYSTEM_PROMPT.format(tool_descriptions=tool_desc)
        full_system_prompt = f"{persona_prompt}\n\n{base_system_prompt}"
        
        # Initial prompt (kept as running history to avoid context loss)
        history = [
            f"System: {full_system_prompt}",
            f"Task: {task_description}"
        ]
        
        current_prompt = "\n\n".join(history)
        
        async with ClaudeSDKClient(options) as client:
            step = 0
            while step < self.max_steps:
                step += 1
                logger.info(f"🔄 ReAct Step {step}/{self.max_steps}")
                
                # Query Claude
                await client.query(current_prompt)
                
                response_text = ""
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_text += block.text
                    elif isinstance(message, ResultMessage):
                        break
                
                logger.debug(f"Claude Response:\n{response_text}")
                
                # Check for Final Answer
                if "Final Answer:" in response_text:
                    final_answer = response_text.split("Final Answer:")[1].strip()
                    logger.info(f"✅ Task Completed: {final_answer}")
                    return final_answer
                
                # Parse Action
                action, args = self._parse_action(response_text)
                
                if action and args is not None:
                    # Execute Tool
                    logger.info(f"🛠️ Calling Tool: {action}")
                    try:
                        result = registry.execute(action, args)
                        observation = f"\nObservation: {result}\n"
                    except Exception as e:
                        observation = f"\nObservation: Error executing tool: {str(e)}\n"
                        
                    logger.debug(f"Tool Result: {result}")
                    
                    # Append to history for next turn to preserve ReAct trace
                    history.append(response_text.strip())
                    history.append(observation.strip())
                    current_prompt = "\n\n".join(history)
                    
                else:
                    # No action found, maybe just thinking or asking for clarification?
                    # Or malformed output.
                    if "Thought:" in response_text and not action:
                        # It might be thinking without acting yet, or failed to format.
                        # We'll prompt it to continue or fix format.
                        history.append(response_text.strip())
                        history.append("System: I did not see a valid 'Action:' and 'Action Input:'. Please format your tool call correctly.")
                        current_prompt = "\n\n".join(history)
                    else:
                        # Assume it's done or stuck
                        logger.warning("⚠️ No action detected and no Final Answer.")
                        history.append(response_text.strip())
                        history.append("System: Please continue. If done, say 'Final Answer:'.")
                        current_prompt = "\n\n".join(history)

            return "Error: Max steps reached without completion."
