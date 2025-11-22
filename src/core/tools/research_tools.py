"""
Research Tools

Wraps ResearcherAgent as callable tools for role execution.
Provides deep_research and quick_research functions.
"""
import asyncio
from typing import Dict, Optional
from src.core.tool_registry import tool
from src.core.agents.researcher import ResearcherAgent
from src.utils.logger import get_logger

logger = get_logger()

# Global singleton to avoid repeated initialization
_researcher_instance: Optional[ResearcherAgent] = None


def get_researcher() -> ResearcherAgent:
    """
    Get or create the global ResearcherAgent instance.

    Returns:
        ResearcherAgent: Singleton instance
    """
    global _researcher_instance
    if _researcher_instance is None:
        logger.info("Initializing global ResearcherAgent instance")
        _researcher_instance = ResearcherAgent(
            work_dir=".",
            provider="tavily",
            enabled=True,
            enable_cache=True,
            cache_ttl_minutes=60
        )
    return _researcher_instance


@tool
def quick_research(query: str) -> str:
    """
    Execute quick web research on a query (single round with caching).

    Args:
        query: Research query string

    Returns:
        Research summary with citations

    Example:
        result = quick_research("AI agent architectures 2024")
    """
    researcher = get_researcher()

    # Run async method in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(researcher.research(query, use_cache=True))
    return result


@tool
def deep_research(query: str, max_results: int = 3) -> dict:
    """
    Execute deep multi-round research on a query.

    This tool performs iterative research across multiple rounds,
    building a comprehensive understanding of the topic.

    Args:
        query: Research query string
        max_results: Maximum number of research rounds (1-5)

    Returns:
        {
            "query": str,
            "rounds": int,
            "findings": List[str],
            "final_summary": str,
            "quality_score": float,  # 0-10
            "sources": List[dict]
        }

    Example:
        result = deep_research(
            query="AI agent architectures 2024",
            max_results=3
        )
        print(result["final_summary"])
    """
    researcher = get_researcher()

    # Validate max_results
    max_rounds = max(1, min(max_results, 5))

    # Run async method in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(researcher.deep_research(query, max_rounds=max_rounds))

    # Format response for better usability
    return {
        "query": result.get("query", query),
        "rounds": result.get("rounds", max_rounds),
        "findings": result.get("findings", []),
        "final_summary": result.get("final_summary", ""),
        "quality_score": result.get("quality_score", 0.0),
        "sources": result.get("sources", [])
    }


@tool
def get_research_stats() -> dict:
    """
    Get statistics about research tool usage.

    Returns:
        {
            "total_queries": int,
            "cache_hits": int,
            "deep_research_count": int,
            "cache_hit_rate": float
        }

    Example:
        stats = get_research_stats()
        print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
    """
    researcher = get_researcher()
    stats = researcher.stats.copy()

    # Calculate cache hit rate
    if stats["total_queries"] > 0:
        stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_queries"]
    else:
        stats["cache_hit_rate"] = 0.0

    return stats
