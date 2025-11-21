"""
Lightweight helper around claude_code_sdk for one-shot prompts with retries.

We intentionally use the simple query() API (non-streaming) to avoid control
protocol initialization timeouts seen with ClaudeSDKClient. Each call spins up
its own CLI process, collects the assistant text, and returns it.
"""
import asyncio
from typing import Optional, Tuple

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    query as claude_query,
)

from logger import get_logger

logger = get_logger()


async def run_claude_prompt(
    prompt: str,
    work_dir: str,
    *,
    model: Optional[str] = None,
    permission_mode: str = "bypassPermissions",
    timeout: int = 300,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> Tuple[str, Optional[ResultMessage]]:
    """
    Send a single prompt to Claude Code CLI with retries and timeout.

    Returns:
        tuple: (assistant_text, ResultMessage or None)
    Raises:
        RuntimeError after exhausting retries
    """
    last_error: Optional[str] = None

    for attempt in range(1, max_retries + 1):
        try:
            options = ClaudeCodeOptions(
                permission_mode=permission_mode,
                cwd=work_dir,
                model=model,
            )

            response_text = ""
            result_message: Optional[ResultMessage] = None

            async def prompt_stream():
                yield {
                    "type": "user",
                    "message": {"role": "user", "content": prompt},
                    "parent_tool_use_id": None,
                    "session_id": "default",
                }

            async def _collect():
                nonlocal response_text, result_message
                async for message in claude_query(prompt=prompt_stream(), options=options):
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_text += block.text
                    elif isinstance(message, ResultMessage):
                        result_message = message

            await asyncio.wait_for(_collect(), timeout=timeout)
            return response_text.strip(), result_message

        except asyncio.TimeoutError:
            last_error = f"Timeout after {timeout}s"
            logger.error(
                f"Claude query timeout (attempt {attempt}/{max_retries}): {last_error}"
            )
        except Exception as exc:  # pylint: disable=broad-except
            last_error = str(exc)
            logger.error(
                f"Claude query failed (attempt {attempt}/{max_retries}): {exc}"
            )

        if attempt < max_retries:
            await asyncio.sleep(retry_delay)

    raise RuntimeError(last_error or "Unknown Claude SDK error")
