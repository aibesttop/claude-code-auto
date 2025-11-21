"""
Researcher Agent: wraps web search + summarization.
增强版：支持缓存、多轮研究、质量评估
"""
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import hashlib
import json

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

DEEP_RESEARCH_PROMPT = """
You are a Deep Research Analyst.
You've completed {round} rounds of research on the topic.

Previous findings:
{previous_findings}

Current search results:
{current_results}

Task: Synthesize ALL findings (previous + current) into a comprehensive summary.
- Identify patterns and connections
- Highlight new insights from this round
- Cite all sources
- Rate the quality of information (1-10)
"""


class ResearchCache:
    """研究结果缓存"""

    def __init__(self, ttl_minutes: int = 60):
        self.cache: Dict[str, Dict] = {}
        self.ttl = timedelta(minutes=ttl_minutes)

    def _get_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.lower().encode()).hexdigest()

    def get(self, query: str) -> Optional[str]:
        """获取缓存结果"""
        key = self._get_key(query)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["timestamp"] < self.ttl:
                logger.info(f"📦 Research cache HIT for: {query[:50]}...")
                return entry["result"]
            else:
                # 过期，删除
                del self.cache[key]
        return None

    def set(self, query: str, result: str):
        """设置缓存"""
        key = self._get_key(query)
        self.cache[key] = {
            "query": query,
            "result": result,
            "timestamp": datetime.now()
        }

    def clear_expired(self):
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry["timestamp"] >= self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        return {
            "total_entries": len(self.cache),
            "oldest_entry": min(
                (e["timestamp"].isoformat() for e in self.cache.values()),
                default=None
            )
        }


class ResearcherAgent:
    def __init__(
        self,
        work_dir: str,
        provider: str = "tavily",
        enabled: bool = True,
        enable_cache: bool = True,
        cache_ttl_minutes: int = 60,
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

        # 缓存
        self.enable_cache = enable_cache
        self.cache = ResearchCache(ttl_minutes=cache_ttl_minutes) if enable_cache else None

        # 统计
        self.stats = {
            "total_queries": 0,
            "cache_hits": 0,
            "deep_research_count": 0
        }

    async def research(self, query: str, use_cache: bool = True) -> str:
        """基础研究（单轮）"""
        if not self.enabled:
            return "Research disabled by config."

        self.stats["total_queries"] += 1

        # 检查缓存
        if use_cache and self.enable_cache:
            cached_result = self.cache.get(query)
            if cached_result:
                self.stats["cache_hits"] += 1
                return cached_result

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
            result = response_text.strip()

            # 存入缓存
            if use_cache and self.enable_cache:
                self.cache.set(query, result)

            return result
        except Exception as exc:  # pylint: disable=broad-except
            logger.error(f"Researcher failed to summarize search results: {exc}")
            return f"Research error: {exc}"

    async def deep_research(self, query: str, max_rounds: int = 3) -> Dict:
        """
        多轮深度研究
        Returns: {
            "query": str,
            "rounds": int,
            "findings": List[str],
            "final_summary": str,
            "quality_score": float
        }
        """
        if not self.enabled:
            return {"error": "Research disabled by config."}

        logger.info(f"🔬 Deep research started: {query} (max {max_rounds} rounds)")
        self.stats["deep_research_count"] += 1

        findings = []
        previous_summary = ""

        for round_num in range(1, max_rounds + 1):
            logger.info(f"🔄 Research round {round_num}/{max_rounds}")

            # 执行搜索
            search_result = web_search(query)

            # 构建提示
            if round_num == 1:
                prompt = f"{RESEARCH_SYSTEM_PROMPT}\n\nQuery: {query}\nSearch Result:\n{search_result}"
            else:
                prompt = DEEP_RESEARCH_PROMPT.format(
                    round=round_num,
                    previous_findings=previous_summary,
                    current_results=search_result
                )

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
                current_finding = response_text.strip()
                findings.append(current_finding)
                previous_summary = current_finding

            except Exception as exc:
                logger.error(f"Round {round_num} failed: {exc}")
                findings.append(f"Round {round_num} error: {exc}")
                break

        # 评估质量
        quality_score = self._evaluate_quality(findings[-1] if findings else "")

        result = {
            "query": query,
            "rounds": len(findings),
            "findings": findings,
            "final_summary": findings[-1] if findings else "No findings",
            "quality_score": quality_score
        }

        logger.info(f"✅ Deep research completed: {len(findings)} rounds, quality={quality_score:.1f}/10")
        return result

    def _evaluate_quality(self, summary: str) -> float:
        """
        评估研究质量（简单启发式）
        基于：长度、引用数量、结构化程度
        """
        if not summary:
            return 0.0

        score = 5.0  # 基础分

        # 长度评分（100-1000字最佳）
        length = len(summary)
        if 100 <= length <= 1000:
            score += 2.0
        elif length > 1000:
            score += 1.0

        # 引用评分（检测URL或引用标记）
        citation_markers = summary.count("http") + summary.count("[") + summary.count("Source:")
        score += min(citation_markers * 0.5, 2.0)

        # 结构化评分（检测段落和列表）
        structure_markers = summary.count("\n\n") + summary.count("-") + summary.count("•")
        score += min(structure_markers * 0.2, 1.0)

        return min(score, 10.0)

    def get_stats(self) -> Dict:
        """获取研究统计"""
        stats = self.stats.copy()
        if self.enable_cache and self.cache:
            stats["cache"] = self.cache.get_stats()
            if self.stats["total_queries"] > 0:
                stats["cache_hit_rate"] = self.stats["cache_hits"] / self.stats["total_queries"]
        return stats
