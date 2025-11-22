"""
Budget Circuit Breaker - 预算断路器

提供熔断保护，防止预算快速耗尽
基于电路断路器模式 (CLOSED → OPEN → HALF_OPEN)
"""
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Callable

from src.utils.logger import get_logger

logger = get_logger()


class CircuitState(str, Enum):
    """断路器状态"""
    CLOSED = "closed"      # 正常状态，允许请求
    OPEN = "open"          # 熔断状态，拒绝请求
    HALF_OPEN = "half_open"  # 半开状态，尝试恢复


@dataclass
class CircuitBreakerConfig:
    """断路器配置"""
    # 失败阈值
    failure_threshold: int = 5  # 连续失败次数
    failure_rate_threshold: float = 0.5  # 失败率阈值 (50%)

    # 时间窗口
    time_window_seconds: float = 60.0  # 统计时间窗口
    open_timeout_seconds: float = 30.0  # OPEN状态持续时间

    # 半开状态测试
    half_open_max_calls: int = 3  # 半开状态允许的测试请求数


@dataclass
class CircuitBreakerStats:
    """断路器统计"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0

    consecutive_failures: int = 0
    last_failure_time: float = 0.0

    state_change_time: float = field(default_factory=time.time)
    half_open_calls: int = 0

    def failure_rate(self) -> float:
        """失败率"""
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls

    def reset_window(self):
        """重置时间窗口"""
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0


class BudgetCircuitBreaker:
    """预算断路器"""

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        """
        初始化断路器

        Args:
            name: 断路器名称
            config: 配置 (可选)
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()

        logger.info(f"BudgetCircuitBreaker initialized: {name}, state={self.state}")

    def call(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> tuple[bool, any]:
        """
        通过断路器调用函数

        Args:
            func: 要调用的函数
            *args, **kwargs: 函数参数

        Returns:
            (success, result) tuple
        """
        # 检查是否允许调用
        if not self._allow_request():
            logger.warning(
                f"Circuit breaker {self.name} is {self.state.value}, "
                f"request rejected"
            )
            return False, None

        # 执行调用
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return True, result

        except Exception as e:
            self._on_failure(e)
            return False, None

    def _allow_request(self) -> bool:
        """是否允许请求"""
        current_time = time.time()

        if self.state == CircuitState.CLOSED:
            # 正常状态，检查时间窗口
            if current_time - self.stats.state_change_time > self.config.time_window_seconds:
                # 时间窗口过期，重置统计
                self.stats.reset_window()
                self.stats.state_change_time = current_time
            return True

        elif self.state == CircuitState.OPEN:
            # 熔断状态，检查是否超过超时时间
            if current_time - self.stats.state_change_time > self.config.open_timeout_seconds:
                # 尝试恢复，进入半开状态
                self._transition_to_half_open()
                return True
            return False

        elif self.state == CircuitState.HALF_OPEN:
            # 半开状态，限制测试请求数
            return self.stats.half_open_calls < self.config.half_open_max_calls

        return False

    def _on_success(self):
        """成功回调"""
        self.stats.total_calls += 1
        self.stats.successful_calls += 1
        self.stats.consecutive_failures = 0

        if self.state == CircuitState.HALF_OPEN:
            self.stats.half_open_calls += 1

            # 半开状态成功，尝试关闭断路器
            if self.stats.half_open_calls >= self.config.half_open_max_calls:
                self._transition_to_closed()

    def _on_failure(self, error: Exception):
        """失败回调"""
        self.stats.total_calls += 1
        self.stats.failed_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.last_failure_time = time.time()

        logger.warning(
            f"Circuit breaker {self.name} recorded failure: {error}, "
            f"consecutive_failures={self.stats.consecutive_failures}"
        )

        if self.state == CircuitState.HALF_OPEN:
            # 半开状态失败，重新打开断路器
            self._transition_to_open()

        elif self.state == CircuitState.CLOSED:
            # 检查是否触发熔断
            should_open = (
                self.stats.consecutive_failures >= self.config.failure_threshold
                or self.stats.failure_rate() >= self.config.failure_rate_threshold
            )

            if should_open:
                self._transition_to_open()

    def _transition_to_open(self):
        """转换到OPEN状态"""
        self.state = CircuitState.OPEN
        self.stats.state_change_time = time.time()

        logger.error(
            f"Circuit breaker {self.name} OPENED: "
            f"consecutive_failures={self.stats.consecutive_failures}, "
            f"failure_rate={self.stats.failure_rate():.1%}"
        )

    def _transition_to_half_open(self):
        """转换到HALF_OPEN状态"""
        self.state = CircuitState.HALF_OPEN
        self.stats.state_change_time = time.time()
        self.stats.half_open_calls = 0

        logger.info(f"Circuit breaker {self.name} transitioned to HALF_OPEN")

    def _transition_to_closed(self):
        """转换到CLOSED状态"""
        self.state = CircuitState.CLOSED
        self.stats.state_change_time = time.time()
        self.stats.reset_window()

        logger.info(f"Circuit breaker {self.name} transitioned to CLOSED (recovered)")

    def force_open(self):
        """强制打开断路器"""
        self._transition_to_open()
        logger.warning(f"Circuit breaker {self.name} force opened")

    def force_close(self):
        """强制关闭断路器"""
        self._transition_to_closed()
        logger.info(f"Circuit breaker {self.name} force closed")

    def reset(self):
        """重置断路器"""
        self.state = CircuitState.CLOSED
        self.stats = CircuitBreakerStats()
        logger.info(f"Circuit breaker {self.name} reset")

    def get_status(self) -> dict:
        """获取断路器状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self.stats.total_calls,
            "successful_calls": self.stats.successful_calls,
            "failed_calls": self.stats.failed_calls,
            "failure_rate": self.stats.failure_rate(),
            "consecutive_failures": self.stats.consecutive_failures,
            "half_open_calls": self.stats.half_open_calls
        }


class BudgetProtectedExecutor:
    """预算保护执行器

    结合预算控制和断路器保护
    """

    def __init__(
        self,
        budget_controller,
        entity_id: str,
        circuit_breaker: Optional[BudgetCircuitBreaker] = None
    ):
        """
        初始化预算保护执行器

        Args:
            budget_controller: HierarchicalBudgetController实例
            entity_id: 实体ID
            circuit_breaker: 断路器 (可选)
        """
        self.budget_controller = budget_controller
        self.entity_id = entity_id
        self.circuit_breaker = circuit_breaker or BudgetCircuitBreaker(
            name=f"cb-{entity_id}"
        )

    def execute_with_budget(
        self,
        func: Callable,
        estimated_cost_usd: float,
        *args,
        **kwargs
    ) -> tuple[bool, any]:
        """
        带预算保护执行函数

        Args:
            func: 要执行的函数
            estimated_cost_usd: 预估成本
            *args, **kwargs: 函数参数

        Returns:
            (success, result) tuple
        """
        # 1. 检查预算是否足够
        budget_status = self.budget_controller.get_budget_status(self.entity_id)
        if budget_status is None:
            logger.error(f"Entity not found: {self.entity_id}")
            return False, None

        if budget_status["remaining"] < estimated_cost_usd:
            logger.warning(
                f"Insufficient budget for {self.entity_id}: "
                f"required=${estimated_cost_usd:.4f}, "
                f"remaining=${budget_status['remaining']:.4f}"
            )
            return False, None

        # 2. 通过断路器执行
        def protected_call():
            # 预先消费预算
            if not self.budget_controller.consume_budget(
                self.entity_id,
                estimated_cost_usd
            ):
                raise RuntimeError("Budget consumption failed")

            # 执行实际函数
            return func(*args, **kwargs)

        success, result = self.circuit_breaker.call(protected_call)

        if not success:
            logger.warning(
                f"Protected execution failed for {self.entity_id}, "
                f"circuit_breaker_state={self.circuit_breaker.state.value}"
            )

        return success, result

    def get_status(self) -> dict:
        """获取执行器状态"""
        budget_status = self.budget_controller.get_budget_status(self.entity_id)
        circuit_status = self.circuit_breaker.get_status()

        return {
            "entity_id": self.entity_id,
            "budget": budget_status,
            "circuit_breaker": circuit_status
        }
