"""
Professional Web Search Tool for Agentic Workflows
Optimized for Market Research and Competitive Intelligence
"""
import os
import json
from typing import Optional, Literal
from src.core.tool_registry import tool

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

@tool
def web_search(
    query: str,
    search_depth: Literal["basic", "advanced"] = "advanced",
    max_results: int = 5,
    days: Optional[int] = 365
) -> str:
    """
    Advanced web search tool for real-time information retrieval.

    Args:
        query: The specific search query.
        search_depth: 'basic' for quick facts, 'advanced' for in-depth analysis (recommended for research).
        max_results: Number of results to return (1-10).
        days: Limit results to the last N days (useful for current trends).

    Returns:
        A structured Markdown string containing search results and source links.
    """
    if not TavilyClient:
        return "Error: tavily-python not installed. Please run 'pip install tavily-python'."

    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set. Please set it to use web search."

    try:
        client = TavilyClient(api_key=api_key)

        # 调用 Tavily API
        # search_depth="advanced" 会消耗 2 个 credit，但对市场研究至关重要
        response = client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            days=days,
            include_answer=True,
            include_raw_content=False  # 设置为 True 如果需要全文解析，但要注意 Token 消耗
        )

        output = []

        # 1. 提取 Tavily 生成的 AI 总结
        if response.get("answer"):
            output.append(f"### Direct Answer Summary\n{response['answer']}\n")

        # 2. 格式化搜索结果
        output.append("### Detailed Sources")
        results = response.get("results", [])

        if not results:
            return f"No significant results found for query: '{query}'"

        for i, result in enumerate(results, 1):
            title = result.get('title', 'No Title')
            url = result.get('url', '#')
            # 增加内容长度到 800 字符左右，保证市场研究有足够素材
            content = result.get('content', '')

            source_block = (
                f"#### Source {i}: {title}\n"
                f"- **URL:** {url}\n"
                f"- **Content Snippet:** {content}\n"
            )
            output.append(source_block)

        return "\n".join(output)

    except Exception as e:
        # 增加错误上下文
        return f"Search Failed for '{query}': {str(e)}"
