"""
预算管理系统 (Budget Management System)
提供多粒度成本控制、自动降级策略和实时预算监控

核心功能:
1. 多层级预算管理（日预算、迭代预算、Agent预算）
2. 成本预估与预算检查
3. 预算超标时的自动降级策略
4. 实时预算追踪和告警
5. 预算报告生成

作者: Claude + Human
版本: 1.0.0
创建时间: 2025-11-21
"""

from typing import Dict, Optional, Literal, List, Any
from datetime import datetime, date, timedelta
from pathlib import Path
from pydantic import BaseModel, Field
import json
from dataclasses import dataclass, asdict
from enum import Enum

from logger import get_logger

logger = get_logger()


class BudgetPeriod(str, Enum):
    """预算周期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SESSION = "session"


class FallbackStrategy(str, Enum):
    """降级策略"""
    SMALLER_MODEL = "smaller_model"      # 使用更便宜的模型
    CACHE_ONLY = "cache_only"            # 仅使用缓存
    SKIP = "skip"                        # 跳过操作
    BLOCK = "block"                      # 阻止操作


@dataclass
class BudgetLimit:
    """预算限制配置"""
    total: float                          # 总预算（美元）
    warning_threshold: float = 0.8        # 警告阈值（80%）
    critical_threshold: float = 0.95      # 临界阈值（95%）

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BudgetUsage:
    """预算使用记录"""
    period: str                           # 周期标识（如 "2025-11-21"）
    agent_type: str                       # Agent类型
    operation: str                        # 操作类型
    cost_usd: float                       # 成本（美元）
    timestamp: datetime                   # 时间戳
    model: Optional[str] = None           # 使用的模型
    fallback_applied: bool = False        # 是否应用了降级

    def to_dict(self) -> Dict:
        return {
            "period": self.period,
            "agent_type": self.agent_type,
            "operation": self.operation,
            "cost_usd": self.cost_usd,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "fallback_applied": self.fallback_applied
        }


class BudgetCheckResult(BaseModel):
    """预算检查结果"""
    allowed: bool                         # 是否允许执行
    current_usage: float                  # 当前使用量
    budget_limit: float                   # 预算限制
    usage_percentage: float               # 使用百分比
    strategy: FallbackStrategy            # 应用的策略
    recommended_model: Optional[str] = None  # 推荐的模型
    warning_message: Optional[str] = None # 警告消息


class BudgetManager:
    """
    智能预算管理器

    功能:
    - 多粒度预算控制（日/周/月/会话）
    - 按 Agent 类型分配预算
    - 自动降级策略
    - 实时预算监控和告警

    示例:
        >>> manager = BudgetManager(daily_budget=10.0)
        >>> result = await manager.check_budget("executor", "llm_call", estimated_cost=0.05)
        >>> if result.allowed:
        ...     # 执行操作
        ...     manager.record_usage("executor", "llm_call", actual_cost=0.048)
    """

    # 模型定价（每百万tokens，美元）- 与 CostTracker 保持一致
    MODEL_PRICING = {
        "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
        "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
        "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    # 模型降级链（从贵到便宜）
    MODEL_FALLBACK_CHAIN = [
        "claude-3-opus-20240229",
        "claude-3-5-sonnet-20241022",
        "claude-sonnet-4-5",
        "claude-3-haiku-20240307"
    ]

    def __init__(
        self,
        daily_budget: float = 100.0,
        weekly_budget: Optional[float] = None,
        monthly_budget: Optional[float] = None,
        agent_budget_ratios: Optional[Dict[str, float]] = None,
        enable_auto_fallback: bool = True,
        storage_dir: str = "logs/budget"
    ):
        """
        初始化预算管理器

        参数:
            daily_budget: 每日预算（美元）
            weekly_budget: 每周预算（美元，默认为 daily_budget * 7）
            monthly_budget: 每月预算（美元，默认为 daily_budget * 30）
            agent_budget_ratios: Agent预算分配比例
                例: {"planner": 0.1, "executor": 0.6, "researcher": 0.3}
            enable_auto_fallback: 是否启用自动降级
            storage_dir: 预算数据存储目录
        """
        self.daily_budget = BudgetLimit(total=daily_budget)
        self.weekly_budget = BudgetLimit(total=weekly_budget or daily_budget * 7)
        self.monthly_budget = BudgetLimit(total=monthly_budget or daily_budget * 30)

        # Agent预算分配（默认比例）
        self.agent_budget_ratios = agent_budget_ratios or {
            "planner": 0.1,      # 10% - 规划开销小
            "executor": 0.6,     # 60% - 执行主力
            "researcher": 0.3,   # 30% - 研究中等
        }

        self.enable_auto_fallback = enable_auto_fallback

        # 存储目录
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 使用记录（内存中）
        self.usage_records: List[BudgetUsage] = []

        # 加载历史数据
        self._load_usage_history()

        logger.info(f"💰 预算管理器已初始化: 日预算=${daily_budget:.2f}")

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "claude-3-5-sonnet-20241022"
    ) -> float:
        """
        估算 LLM 调用成本

        参数:
            input_tokens: 输入token数
            output_tokens: 输出token数
            model: 模型名称

        返回:
            估算成本（美元）
        """
        pricing = self.MODEL_PRICING.get(model, self.MODEL_PRICING["claude-3-5-sonnet-20241022"])

        cost = (
            (input_tokens / 1_000_000) * pricing["input"] +
            (output_tokens / 1_000_000) * pricing["output"]
        )

        return cost

    def estimate_cost_from_text(
        self,
        input_text: str,
        output_text: str,
        model: str = "claude-3-5-sonnet-20241022"
    ) -> float:
        """
        从文本长度估算成本（粗略估算）

        参数:
            input_text: 输入文本
            output_text: 输出文本
            model: 模型名称

        返回:
            估算成本（美元）
        """
        # 粗略估算：4个字符 ≈ 1个token
        input_tokens = len(input_text) // 4
        output_tokens = len(output_text) // 4

        return self.estimate_cost(input_tokens, output_tokens, model)

    async def check_budget(
        self,
        agent_type: str,
        operation: str,
        estimated_cost: float,
        model: str = "claude-3-5-sonnet-20241022"
    ) -> BudgetCheckResult:
        """
        检查预算并返回执行策略

        参数:
            agent_type: Agent类型（planner/executor/researcher）
            operation: 操作类型（llm_call/web_search等）
            estimated_cost: 估算成本（美元）
            model: 当前使用的模型

        返回:
            BudgetCheckResult: 预算检查结果
        """
        # 获取当前使用量
        daily_usage = self._get_period_usage(BudgetPeriod.DAILY)
        agent_daily_usage = self._get_agent_usage(agent_type, BudgetPeriod.DAILY)

        # 计算 Agent 预算限制
        agent_budget_limit = self.daily_budget.total * self.agent_budget_ratios.get(agent_type, 0.3)

        # 检查总预算
        total_usage_after = daily_usage + estimated_cost
        usage_percentage = (total_usage_after / self.daily_budget.total) * 100

        logger.debug(
            f"预算检查: {agent_type}.{operation} | "
            f"估算成本=${estimated_cost:.4f} | "
            f"当前使用=${daily_usage:.4f}/{self.daily_budget.total:.2f} | "
            f"使用率={usage_percentage:.1f}%"
        )

        # 判断是否超预算
        if total_usage_after > self.daily_budget.total:
            logger.warning(f"⚠️ 日预算超标! 当前=${daily_usage:.4f}, 限制=${self.daily_budget.total:.2f}")
            return self._apply_fallback_strategy(
                agent_type, operation, model, daily_usage, self.daily_budget.total, usage_percentage
            )

        # 检查 Agent 预算
        agent_usage_after = agent_daily_usage + estimated_cost
        if agent_usage_after > agent_budget_limit:
            logger.warning(
                f"⚠️ {agent_type} Agent预算超标! "
                f"当前=${agent_daily_usage:.4f}, 限制=${agent_budget_limit:.2f}"
            )
            return self._apply_fallback_strategy(
                agent_type, operation, model, agent_daily_usage, agent_budget_limit,
                (agent_usage_after / agent_budget_limit) * 100
            )

        # 检查警告阈值
        if usage_percentage >= self.daily_budget.warning_threshold * 100:
            logger.warning(
                f"⚠️ 预算警告: 已使用 {usage_percentage:.1f}% "
                f"(${daily_usage:.4f}/${self.daily_budget.total:.2f})"
            )

            # 如果启用自动降级，提前切换到便宜模型
            if self.enable_auto_fallback and usage_percentage >= self.daily_budget.critical_threshold * 100:
                recommended_model = self._get_cheaper_model(model)
                if recommended_model != model:
                    return BudgetCheckResult(
                        allowed=True,
                        current_usage=daily_usage,
                        budget_limit=self.daily_budget.total,
                        usage_percentage=usage_percentage,
                        strategy=FallbackStrategy.SMALLER_MODEL,
                        recommended_model=recommended_model,
                        warning_message=f"预算紧张，建议使用 {recommended_model}"
                    )

        # 预算充足，允许执行
        return BudgetCheckResult(
            allowed=True,
            current_usage=daily_usage,
            budget_limit=self.daily_budget.total,
            usage_percentage=usage_percentage,
            strategy=FallbackStrategy.SMALLER_MODEL if model != "claude-3-5-sonnet-20241022" else FallbackStrategy.BLOCK,
            recommended_model=model
        )

    def _apply_fallback_strategy(
        self,
        agent_type: str,
        operation: str,
        model: str,
        current_usage: float,
        budget_limit: float,
        usage_percentage: float
    ) -> BudgetCheckResult:
        """应用降级策略"""
        if not self.enable_auto_fallback:
            return BudgetCheckResult(
                allowed=False,
                current_usage=current_usage,
                budget_limit=budget_limit,
                usage_percentage=usage_percentage,
                strategy=FallbackStrategy.BLOCK,
                warning_message="预算超标，操作被阻止"
            )

        # 策略1: 使用缓存（针对 researcher）
        if operation == "web_search" and agent_type == "researcher":
            logger.info("💾 降级策略: 仅使用研究缓存")
            return BudgetCheckResult(
                allowed=True,
                current_usage=current_usage,
                budget_limit=budget_limit,
                usage_percentage=usage_percentage,
                strategy=FallbackStrategy.CACHE_ONLY,
                warning_message="预算超标，仅使用缓存结果"
            )

        # 策略2: 切换到更便宜的模型
        if operation == "llm_call":
            cheaper_model = self._get_cheaper_model(model)
            if cheaper_model != model:
                logger.info(f"💰 降级策略: 切换模型 {model} -> {cheaper_model}")
                return BudgetCheckResult(
                    allowed=True,
                    current_usage=current_usage,
                    budget_limit=budget_limit,
                    usage_percentage=usage_percentage,
                    strategy=FallbackStrategy.SMALLER_MODEL,
                    recommended_model=cheaper_model,
                    warning_message=f"预算超标，自动切换到 {cheaper_model}"
                )

        # 策略3: 阻止操作
        logger.error("🛑 预算耗尽，操作被阻止")
        return BudgetCheckResult(
            allowed=False,
            current_usage=current_usage,
            budget_limit=budget_limit,
            usage_percentage=usage_percentage,
            strategy=FallbackStrategy.BLOCK,
            warning_message="预算耗尽，操作被阻止"
        )

    def _get_cheaper_model(self, current_model: str) -> str:
        """获取更便宜的模型"""
        try:
            current_index = self.MODEL_FALLBACK_CHAIN.index(current_model)
            # 返回下一个更便宜的模型
            if current_index < len(self.MODEL_FALLBACK_CHAIN) - 1:
                return self.MODEL_FALLBACK_CHAIN[current_index + 1]
        except ValueError:
            pass

        # 默认返回最便宜的模型
        return "claude-3-haiku-20240307"

    def record_usage(
        self,
        agent_type: str,
        operation: str,
        actual_cost: float,
        model: Optional[str] = None,
        fallback_applied: bool = False
    ):
        """
        记录实际成本使用

        参数:
            agent_type: Agent类型
            operation: 操作类型
            actual_cost: 实际成本（美元）
            model: 使用的模型
            fallback_applied: 是否应用了降级
        """
        usage = BudgetUsage(
            period=self._get_current_period(BudgetPeriod.DAILY),
            agent_type=agent_type,
            operation=operation,
            cost_usd=actual_cost,
            timestamp=datetime.now(),
            model=model,
            fallback_applied=fallback_applied
        )

        self.usage_records.append(usage)

        # 定期保存到磁盘
        if len(self.usage_records) % 10 == 0:
            self._save_usage_history()

        logger.debug(f"📝 记录使用: {agent_type}.{operation} = ${actual_cost:.4f}")

    def _get_period_usage(self, period: BudgetPeriod) -> float:
        """获取指定周期的总使用量"""
        period_key = self._get_current_period(period)

        total = sum(
            record.cost_usd
            for record in self.usage_records
            if record.period == period_key
        )

        return total

    def _get_agent_usage(self, agent_type: str, period: BudgetPeriod) -> float:
        """获取指定 Agent 在指定周期的使用量"""
        period_key = self._get_current_period(period)

        total = sum(
            record.cost_usd
            for record in self.usage_records
            if record.period == period_key and record.agent_type == agent_type
        )

        return total

    def _get_current_period(self, period: BudgetPeriod) -> str:
        """获取当前周期标识"""
        now = datetime.now()

        if period == BudgetPeriod.DAILY:
            return now.strftime("%Y-%m-%d")
        elif period == BudgetPeriod.WEEKLY:
            # ISO周格式：2025-W47
            return now.strftime("%Y-W%W")
        elif period == BudgetPeriod.MONTHLY:
            return now.strftime("%Y-%m")
        else:
            return "session"

    def generate_report(self, period: BudgetPeriod = BudgetPeriod.DAILY) -> Dict[str, Any]:
        """
        生成预算报告

        参数:
            period: 报告周期

        返回:
            报告字典
        """
        period_key = self._get_current_period(period)
        period_records = [r for r in self.usage_records if r.period == period_key]

        if not period_records:
            return {
                "period": period_key,
                "total_cost": 0.0,
                "budget_limit": self.daily_budget.total,
                "usage_percentage": 0.0,
                "agent_breakdown": {},
                "operation_breakdown": {},
                "fallback_count": 0
            }

        total_cost = sum(r.cost_usd for r in period_records)

        # 按 Agent 统计
        agent_breakdown = {}
        for agent_type in set(r.agent_type for r in period_records):
            agent_cost = sum(r.cost_usd for r in period_records if r.agent_type == agent_type)
            agent_breakdown[agent_type] = {
                "cost": round(agent_cost, 4),
                "percentage": round((agent_cost / total_cost) * 100, 2) if total_cost > 0 else 0,
                "count": len([r for r in period_records if r.agent_type == agent_type])
            }

        # 按操作统计
        operation_breakdown = {}
        for operation in set(r.operation for r in period_records):
            op_cost = sum(r.cost_usd for r in period_records if r.operation == operation)
            operation_breakdown[operation] = {
                "cost": round(op_cost, 4),
                "count": len([r for r in period_records if r.operation == operation])
            }

        # 降级统计
        fallback_count = len([r for r in period_records if r.fallback_applied])

        budget_limit = self.daily_budget.total if period == BudgetPeriod.DAILY else self.weekly_budget.total

        return {
            "period": period_key,
            "total_cost": round(total_cost, 4),
            "budget_limit": budget_limit,
            "usage_percentage": round((total_cost / budget_limit) * 100, 2),
            "remaining_budget": round(budget_limit - total_cost, 4),
            "agent_breakdown": agent_breakdown,
            "operation_breakdown": operation_breakdown,
            "fallback_count": fallback_count,
            "total_operations": len(period_records)
        }

    def print_report(self, period: BudgetPeriod = BudgetPeriod.DAILY):
        """打印预算报告"""
        report = self.generate_report(period)

        print("\n" + "=" * 60)
        print(f"💰 预算报告 - {report['period']}")
        print("=" * 60)
        print(f"总成本: ${report['total_cost']:.4f} / ${report['budget_limit']:.2f}")
        print(f"使用率: {report['usage_percentage']:.2f}%")
        print(f"剩余预算: ${report['remaining_budget']:.4f}")
        print(f"总操作数: {report['total_operations']}")
        print(f"降级次数: {report['fallback_count']}")

        print("\n按 Agent 统计:")
        for agent, stats in report['agent_breakdown'].items():
            print(f"  {agent:12} ${stats['cost']:.4f} ({stats['percentage']:.1f}%) - {stats['count']} 次")

        print("\n按操作统计:")
        for op, stats in report['operation_breakdown'].items():
            print(f"  {op:12} ${stats['cost']:.4f} - {stats['count']} 次")

        print("=" * 60 + "\n")

    def _save_usage_history(self):
        """保存使用历史到磁盘"""
        try:
            today = date.today().strftime("%Y-%m-%d")
            filepath = self.storage_dir / f"budget_usage_{today}.json"

            data = {
                "date": today,
                "records": [record.to_dict() for record in self.usage_records]
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"💾 预算数据已保存到 {filepath}")
        except Exception as e:
            logger.error(f"保存预算数据失败: {e}")

    def _load_usage_history(self):
        """加载今天的使用历史"""
        try:
            today = date.today().strftime("%Y-%m-%d")
            filepath = self.storage_dir / f"budget_usage_{today}.json"

            if not filepath.exists():
                return

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for record_dict in data.get("records", []):
                record = BudgetUsage(
                    period=record_dict["period"],
                    agent_type=record_dict["agent_type"],
                    operation=record_dict["operation"],
                    cost_usd=record_dict["cost_usd"],
                    timestamp=datetime.fromisoformat(record_dict["timestamp"]),
                    model=record_dict.get("model"),
                    fallback_applied=record_dict.get("fallback_applied", False)
                )
                self.usage_records.append(record)

            logger.info(f"📂 已加载 {len(self.usage_records)} 条预算记录")
        except Exception as e:
            logger.warning(f"加载预算历史失败: {e}")

    def reset_daily_budget(self):
        """重置日预算（通常在新的一天开始时调用）"""
        today = self._get_current_period(BudgetPeriod.DAILY)

        # 移除今天之前的记录（保留最近7天）
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.usage_records = [
            r for r in self.usage_records
            if r.period >= cutoff_date
        ]

        logger.info(f"🔄 预算已重置 - {today}")

    def get_budget_status(self) -> Dict[str, Any]:
        """获取当前预算状态（用于监控面板）"""
        daily_usage = self._get_period_usage(BudgetPeriod.DAILY)
        usage_percentage = (daily_usage / self.daily_budget.total) * 100

        # 状态判断
        if usage_percentage >= 100:
            status = "critical"
        elif usage_percentage >= self.daily_budget.critical_threshold * 100:
            status = "warning"
        elif usage_percentage >= self.daily_budget.warning_threshold * 100:
            status = "caution"
        else:
            status = "healthy"

        return {
            "status": status,
            "current_usage": round(daily_usage, 4),
            "budget_limit": self.daily_budget.total,
            "usage_percentage": round(usage_percentage, 2),
            "remaining_budget": round(self.daily_budget.total - daily_usage, 4),
            "agent_usage": {
                agent: round(self._get_agent_usage(agent, BudgetPeriod.DAILY), 4)
                for agent in self.agent_budget_ratios.keys()
            }
        }


# 便捷函数
def create_budget_manager_from_config(config) -> BudgetManager:
    """从配置创建预算管理器"""
    budget_config = getattr(config, 'budget', None)

    if not budget_config:
        # 使用默认配置
        return BudgetManager(daily_budget=10.0)

    return BudgetManager(
        daily_budget=budget_config.daily_budget,
        weekly_budget=getattr(budget_config, 'weekly_budget', None),
        monthly_budget=getattr(budget_config, 'monthly_budget', None),
        agent_budget_ratios=getattr(budget_config, 'agent_ratios', None),
        enable_auto_fallback=getattr(budget_config, 'enable_auto_fallback', True),
        storage_dir=getattr(budget_config, 'storage_dir', 'logs/budget')
    )


if __name__ == "__main__":
    # 测试预算管理器
    import asyncio

    async def test_budget_manager():
        print("🧪 测试预算管理器\n")

        # 创建管理器（日预算 $1）
        manager = BudgetManager(daily_budget=1.0, enable_auto_fallback=True)

        # 测试1: 正常操作
        print("测试1: 正常操作")
        result = await manager.check_budget(
            "executor", "llm_call",
            estimated_cost=0.05,
            model="claude-3-5-sonnet-20241022"
        )
        print(f"  允许: {result.allowed}, 策略: {result.strategy}, 使用率: {result.usage_percentage:.2f}%\n")

        if result.allowed:
            manager.record_usage("executor", "llm_call", 0.048, model="claude-3-5-sonnet-20241022")

        # 测试2: 模拟多次调用
        print("测试2: 模拟多次调用（接近预算限制）")
        for i in range(10):
            result = await manager.check_budget("executor", "llm_call", 0.08)
            if result.allowed:
                manager.record_usage("executor", "llm_call", 0.08,
                                   fallback_applied=(result.strategy == FallbackStrategy.SMALLER_MODEL))
                print(f"  第{i+1}次: 使用率 {result.usage_percentage:.2f}%, 策略: {result.strategy}")

                if result.recommended_model:
                    print(f"    推荐模型: {result.recommended_model}")
            else:
                print(f"  第{i+1}次: 被阻止 - {result.warning_message}")
                break

        # 打印报告
        manager.print_report()

        # 测试预算状态
        status = manager.get_budget_status()
        print(f"预算状态: {status['status']}")
        print(f"剩余预算: ${status['remaining_budget']:.4f}")

    asyncio.run(test_budget_manager())
