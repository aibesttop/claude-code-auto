"""
预算管理器单元测试 (Budget Manager Unit Tests)

测试覆盖:
1. 预算初始化
2. 成本估算
3. 预算检查和降级策略
4. 使用记录
5. 报告生成
6. 预算状态监控

运行测试: pytest test_budget_manager.py -v
"""

import pytest
import asyncio
from pathlib import Path
import shutil
from datetime import datetime

from core.budget_manager import (
    BudgetManager,
    BudgetPeriod,
    FallbackStrategy,
    BudgetUsage,
    BudgetLimit
)


@pytest.fixture
def budget_manager():
    """创建测试用的预算管理器"""
    manager = BudgetManager(
        daily_budget=1.0,  # $1 日预算
        enable_auto_fallback=True,
        storage_dir="logs/budget_test"
    )
    yield manager

    # 清理测试数据
    test_dir = Path("logs/budget_test")
    if test_dir.exists():
        shutil.rmtree(test_dir)


@pytest.fixture
def budget_manager_no_fallback():
    """创建禁用降级的预算管理器"""
    manager = BudgetManager(
        daily_budget=1.0,
        enable_auto_fallback=False,
        storage_dir="logs/budget_test_no_fallback"
    )
    yield manager

    # 清理测试数据
    test_dir = Path("logs/budget_test_no_fallback")
    if test_dir.exists():
        shutil.rmtree(test_dir)


class TestBudgetInitialization:
    """测试预算初始化"""

    def test_default_initialization(self):
        """测试默认初始化"""
        manager = BudgetManager()

        assert manager.daily_budget.total == 100.0
        assert manager.weekly_budget.total == 700.0
        assert manager.monthly_budget.total == 3000.0
        assert manager.enable_auto_fallback is True
        assert len(manager.usage_records) == 0

    def test_custom_initialization(self, budget_manager):
        """测试自定义初始化"""
        assert budget_manager.daily_budget.total == 1.0
        assert budget_manager.agent_budget_ratios["executor"] == 0.6
        assert budget_manager.agent_budget_ratios["researcher"] == 0.3

    def test_agent_budget_allocation(self, budget_manager):
        """测试Agent预算分配"""
        total = sum(budget_manager.agent_budget_ratios.values())
        assert abs(total - 1.0) < 0.01  # 总和应接近 100%


class TestCostEstimation:
    """测试成本估算"""

    def test_estimate_cost_sonnet(self, budget_manager):
        """测试 Sonnet 模型成本估算"""
        # 估算 100K input, 50K output tokens
        cost = budget_manager.estimate_cost(
            input_tokens=100_000,
            output_tokens=50_000,
            model="claude-3-5-sonnet-20241022"
        )

        # 100K * $3/M + 50K * $15/M = $0.30 + $0.75 = $1.05
        expected = (100_000 / 1_000_000) * 3.0 + (50_000 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.01

    def test_estimate_cost_haiku(self, budget_manager):
        """测试 Haiku 模型成本估算"""
        cost = budget_manager.estimate_cost(
            input_tokens=100_000,
            output_tokens=50_000,
            model="claude-3-haiku-20240307"
        )

        # 100K * $0.25/M + 50K * $1.25/M = $0.025 + $0.0625 = $0.0875
        expected = (100_000 / 1_000_000) * 0.25 + (50_000 / 1_000_000) * 1.25
        assert abs(cost - expected) < 0.01

    def test_estimate_cost_from_text(self, budget_manager):
        """测试从文本估算成本"""
        input_text = "a" * 400  # ~100 tokens
        output_text = "b" * 200  # ~50 tokens

        cost = budget_manager.estimate_cost_from_text(
            input_text, output_text, model="claude-3-5-sonnet-20241022"
        )

        # 应该是一个很小的成本
        assert cost > 0
        assert cost < 0.01


class TestBudgetCheck:
    """测试预算检查"""

    @pytest.mark.asyncio
    async def test_budget_check_allowed(self, budget_manager):
        """测试预算充足时的检查"""
        result = await budget_manager.check_budget(
            agent_type="executor",
            operation="llm_call",
            estimated_cost=0.05,  # 5% of budget
            model="claude-3-5-sonnet-20241022"
        )

        assert result.allowed is True
        assert result.current_usage == 0.0
        assert result.budget_limit == 1.0
        assert result.usage_percentage == 5.0

    @pytest.mark.asyncio
    async def test_budget_check_exceeded(self, budget_manager):
        """测试预算超标时的检查"""
        # 先用掉大部分预算
        budget_manager.record_usage("executor", "llm_call", 0.95)

        result = await budget_manager.check_budget(
            agent_type="executor",
            operation="llm_call",
            estimated_cost=0.10,  # 会超标
            model="claude-3-5-sonnet-20241022"
        )

        assert result.allowed is True  # 启用了降级，应该允许
        assert result.strategy in [FallbackStrategy.SMALLER_MODEL, FallbackStrategy.CACHE_ONLY]

    @pytest.mark.asyncio
    async def test_budget_check_blocked_no_fallback(self, budget_manager_no_fallback):
        """测试禁用降级时预算超标"""
        # 用完预算
        budget_manager_no_fallback.record_usage("executor", "llm_call", 1.0)

        result = await budget_manager_no_fallback.check_budget(
            agent_type="executor",
            operation="llm_call",
            estimated_cost=0.10,
            model="claude-3-5-sonnet-20241022"
        )

        assert result.allowed is False
        assert result.strategy == FallbackStrategy.BLOCK

    @pytest.mark.asyncio
    async def test_agent_budget_exceeded(self, budget_manager):
        """测试单个Agent预算超标"""
        # Executor 分配 60% = $0.60
        # 用掉 $0.65
        budget_manager.record_usage("executor", "llm_call", 0.65)

        result = await budget_manager.check_budget(
            agent_type="executor",
            operation="llm_call",
            estimated_cost=0.05,
            model="claude-3-5-sonnet-20241022"
        )

        # 应该触发降级
        assert result.strategy != FallbackStrategy.BLOCK or result.allowed is True


class TestFallbackStrategies:
    """测试降级策略"""

    @pytest.mark.asyncio
    async def test_smaller_model_fallback(self, budget_manager):
        """测试切换到更便宜的模型"""
        # 接近预算限制
        budget_manager.record_usage("executor", "llm_call", 0.96)

        result = await budget_manager.check_budget(
            agent_type="executor",
            operation="llm_call",
            estimated_cost=0.05,
            model="claude-3-5-sonnet-20241022"
        )

        # 应该推荐更便宜的模型
        if result.recommended_model:
            assert result.recommended_model == "claude-3-haiku-20240307"

    @pytest.mark.asyncio
    async def test_cache_only_fallback(self, budget_manager):
        """测试仅使用缓存策略"""
        # 用完预算
        budget_manager.record_usage("researcher", "web_search", 1.0)

        result = await budget_manager.check_budget(
            agent_type="researcher",
            operation="web_search",
            estimated_cost=0.05,
            model="claude-3-5-sonnet-20241022"
        )

        # 研究应该降级到仅使用缓存
        assert result.strategy in [FallbackStrategy.CACHE_ONLY, FallbackStrategy.SMALLER_MODEL]

    def test_get_cheaper_model(self, budget_manager):
        """测试获取更便宜的模型"""
        cheaper = budget_manager._get_cheaper_model("claude-3-opus-20240229")
        assert cheaper == "claude-3-5-sonnet-20241022"

        cheaper = budget_manager._get_cheaper_model("claude-3-5-sonnet-20241022")
        assert cheaper == "claude-3-haiku-20240307"

        # 已经是最便宜的
        cheaper = budget_manager._get_cheaper_model("claude-3-haiku-20240307")
        assert cheaper == "claude-3-haiku-20240307"


class TestUsageRecording:
    """测试使用记录"""

    def test_record_usage(self, budget_manager):
        """测试记录使用"""
        budget_manager.record_usage(
            agent_type="executor",
            operation="llm_call",
            actual_cost=0.05,
            model="claude-3-5-sonnet-20241022",
            fallback_applied=False
        )

        assert len(budget_manager.usage_records) == 1
        record = budget_manager.usage_records[0]
        assert record.agent_type == "executor"
        assert record.operation == "llm_call"
        assert record.cost_usd == 0.05
        assert record.fallback_applied is False

    def test_record_usage_with_fallback(self, budget_manager):
        """测试记录降级使用"""
        budget_manager.record_usage(
            agent_type="executor",
            operation="llm_call",
            actual_cost=0.01,
            model="claude-3-haiku-20240307",
            fallback_applied=True
        )

        record = budget_manager.usage_records[0]
        assert record.fallback_applied is True
        assert record.model == "claude-3-haiku-20240307"

    def test_multiple_usage_records(self, budget_manager):
        """测试多条使用记录"""
        for i in range(5):
            budget_manager.record_usage("executor", "llm_call", 0.1)

        assert len(budget_manager.usage_records) == 5
        total_cost = budget_manager._get_period_usage(BudgetPeriod.DAILY)
        assert abs(total_cost - 0.5) < 0.01


class TestReporting:
    """测试报告生成"""

    def test_generate_report_empty(self, budget_manager):
        """测试空报告"""
        report = budget_manager.generate_report()

        assert report["total_cost"] == 0.0
        assert report["budget_limit"] == 1.0
        assert report["usage_percentage"] == 0.0
        assert report["fallback_count"] == 0

    def test_generate_report_with_data(self, budget_manager):
        """测试包含数据的报告"""
        # 添加一些使用记录
        budget_manager.record_usage("executor", "llm_call", 0.20)
        budget_manager.record_usage("executor", "llm_call", 0.15)
        budget_manager.record_usage("researcher", "web_search", 0.10)
        budget_manager.record_usage("planner", "llm_call", 0.05, fallback_applied=True)

        report = budget_manager.generate_report()

        assert report["total_cost"] == 0.50
        assert report["budget_limit"] == 1.0
        assert report["usage_percentage"] == 50.0
        assert report["remaining_budget"] == 0.50
        assert report["total_operations"] == 4
        assert report["fallback_count"] == 1

        # 检查 Agent 分解
        assert "executor" in report["agent_breakdown"]
        assert report["agent_breakdown"]["executor"]["cost"] == 0.35
        assert report["agent_breakdown"]["executor"]["count"] == 2

    def test_agent_usage_calculation(self, budget_manager):
        """测试Agent使用量计算"""
        budget_manager.record_usage("executor", "llm_call", 0.30)
        budget_manager.record_usage("researcher", "web_search", 0.20)

        executor_usage = budget_manager._get_agent_usage("executor", BudgetPeriod.DAILY)
        researcher_usage = budget_manager._get_agent_usage("researcher", BudgetPeriod.DAILY)

        assert executor_usage == 0.30
        assert researcher_usage == 0.20


class TestBudgetStatus:
    """测试预算状态"""

    def test_get_budget_status_healthy(self, budget_manager):
        """测试健康状态"""
        budget_manager.record_usage("executor", "llm_call", 0.30)

        status = budget_manager.get_budget_status()

        assert status["status"] == "healthy"
        assert status["current_usage"] == 0.30
        assert status["budget_limit"] == 1.0
        assert status["usage_percentage"] == 30.0
        assert status["remaining_budget"] == 0.70

    def test_get_budget_status_warning(self, budget_manager):
        """测试警告状态"""
        budget_manager.record_usage("executor", "llm_call", 0.85)  # 85%

        status = budget_manager.get_budget_status()

        assert status["status"] == "caution"
        assert status["usage_percentage"] == 85.0

    def test_get_budget_status_critical(self, budget_manager):
        """测试临界状态"""
        budget_manager.record_usage("executor", "llm_call", 0.96)  # 96%

        status = budget_manager.get_budget_status()

        assert status["status"] == "warning"
        assert status["usage_percentage"] == 96.0

    def test_get_budget_status_exceeded(self, budget_manager):
        """测试超标状态"""
        budget_manager.record_usage("executor", "llm_call", 1.05)  # 105%

        status = budget_manager.get_budget_status()

        assert status["status"] == "critical"
        assert status["usage_percentage"] > 100.0


class TestPersistence:
    """测试持久化"""

    def test_save_usage_history(self, budget_manager):
        """测试保存使用历史"""
        budget_manager.record_usage("executor", "llm_call", 0.50)

        # 触发保存（每10条记录）
        for i in range(9):
            budget_manager.record_usage("executor", "llm_call", 0.01)

        # 检查文件是否存在
        today = datetime.now().strftime("%Y-%m-%d")
        filepath = Path("logs/budget_test") / f"budget_usage_{today}.json"
        assert filepath.exists()

    def test_load_usage_history(self):
        """测试加载使用历史"""
        # 创建管理器并记录一些数据
        manager1 = BudgetManager(
            daily_budget=1.0,
            storage_dir="logs/budget_test_load"
        )
        manager1.record_usage("executor", "llm_call", 0.30)

        # 触发保存
        for i in range(9):
            manager1.record_usage("executor", "llm_call", 0.01)

        # 创建新管理器，应该加载历史数据
        manager2 = BudgetManager(
            daily_budget=1.0,
            storage_dir="logs/budget_test_load"
        )

        assert len(manager2.usage_records) == 10

        # 清理
        test_dir = Path("logs/budget_test_load")
        if test_dir.exists():
            shutil.rmtree(test_dir)


class TestEdgeCases:
    """测试边界情况"""

    @pytest.mark.asyncio
    async def test_zero_estimated_cost(self, budget_manager):
        """测试零成本估算"""
        result = await budget_manager.check_budget(
            agent_type="executor",
            operation="llm_call",
            estimated_cost=0.0,
            model="claude-3-5-sonnet-20241022"
        )

        assert result.allowed is True

    @pytest.mark.asyncio
    async def test_very_large_estimated_cost(self, budget_manager):
        """测试超大成本估算"""
        result = await budget_manager.check_budget(
            agent_type="executor",
            operation="llm_call",
            estimated_cost=100.0,  # 远超预算
            model="claude-3-5-sonnet-20241022"
        )

        # 应该触发降级或阻止
        assert result.strategy != FallbackStrategy.BLOCK or not result.allowed

    def test_unknown_agent_type(self, budget_manager):
        """测试未知Agent类型"""
        # 应该使用默认比例
        budget_manager.record_usage("unknown_agent", "llm_call", 0.10)

        usage = budget_manager._get_agent_usage("unknown_agent", BudgetPeriod.DAILY)
        assert usage == 0.10


def test_budget_manager_integration():
    """集成测试：模拟完整工作流"""
    manager = BudgetManager(daily_budget=1.0)

    # 模拟多次操作
    async def run_workflow():
        for i in range(10):
            result = await manager.check_budget(
                "executor", "llm_call", 0.08, "claude-3-5-sonnet-20241022"
            )

            if result.allowed:
                actual_cost = 0.08 if not result.recommended_model else 0.02
                manager.record_usage(
                    "executor", "llm_call", actual_cost,
                    model=result.recommended_model or "claude-3-5-sonnet-20241022",
                    fallback_applied=(result.recommended_model is not None)
                )

    asyncio.run(run_workflow())

    # 检查报告
    report = manager.generate_report()
    assert report["total_cost"] > 0
    assert report["total_operations"] == 10

    # 清理
    test_dir = Path("logs/budget")
    if test_dir.exists():
        shutil.rmtree(test_dir)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
