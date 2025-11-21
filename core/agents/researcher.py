"""
Researcher Agent: wraps web search + summarization.
"""
from typing import Optional

from logger import get_logger
from core.tools.search_tools import web_search
from core.agents.sdk_client import run_claude_prompt

logger = get_logger()

RESEARCH_SYSTEM_PROMPT = """
You are a Researcher Agent.
You use web_search tool results to produce concise, cited summaries.
Given a query, call web_search, then synthesize key findings with sources.
If web_search fails, explain the failure.
"""


class ResearcherAgent:
    def __init__(
        self,
        work_dir: str,
        provider: str = "tavily",
        enabled: bool = True,
        *,
        model: Optional[str] = None,
        timeout_seconds: int = 300,
        permission_mode: str = "bypassPermissions",
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.work_dir = work_dir
        self.provider = provider
        self.enabled = enabled
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.permission_mode = permission_mode
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    async def research(self, query: str) -> str:
        if not self.enabled:
            return "Research disabled by config."

        logger.info(f"🔎 Researcher query: {query}")
        search_result = web_search(query)

        prompt = f"{RESEARCH_SYSTEM_PROMPT}\n\nQuery: {query}\nSearch Result:\n{search_result}"

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
            return response_text.strip()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f"Researcher failed to summarize search results: {exc}")
            return f"Research error: {exc}"
