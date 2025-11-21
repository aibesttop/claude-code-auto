"""
Researcher Agent: wraps web search + summarization.
"""
from typing import Optional
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock
from logger import get_logger
from core.tools.search_tools import web_search

logger = get_logger()

RESEARCH_SYSTEM_PROMPT = """
You are a Researcher Agent.
You use web_search tool results to produce concise, cited summaries.
Given a query, call web_search, then synthesize key findings with sources.
If web_search fails, explain the failure.
"""

class ResearcherAgent:
    def __init__(self, work_dir: str, provider: str = "tavily", enabled: bool = True):
        self.work_dir = work_dir
        self.provider = provider
        self.enabled = enabled

    async def research(self, query: str) -> str:
        if not self.enabled:
            return "Research disabled by config."

        logger.info(f"🔎 Researcher query: {query}")
        search_result = web_search(query)

        options = ClaudeCodeOptions(
            permission_mode="bypassPermissions",
            cwd=self.work_dir
        )

        prompt = f"{RESEARCH_SYSTEM_PROMPT}\n\nQuery: {query}\nSearch Result:\n{search_result}"

        async with ClaudeSDKClient(options) as client:
            await client.query(prompt)
            response_text = ""
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            response_text += block.text
        return response_text.strip()
