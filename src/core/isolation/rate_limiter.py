"""
Rate Limiter - 速率限制器

基于令牌桶算法的请求速率限制
"""
import time
from dataclasses import dataclass
from typing import Dict, Optional
from collections import deque

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class RateLimitConfig:
    """速率限制配置"""
    max_requests: int  # 最大请求数
    time_window_seconds: float  # 时间窗口 (秒)
    burst_size: int = None  # 突发容量 (默认等于max_requests)

    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = self.max_requests


class RateLimiter:
    """速率限制器 (令牌桶算法)"""

    def __init__(self):
        """初始化速率限制器"""
        # 角色速率限制配置
        self.role_configs: Dict[str, RateLimitConfig] = {}

        # 令牌桶状态: role_name -> (tokens, last_refill_time)
        self.token_buckets: Dict[str, tuple[float, float]] = {}

        # 请求历史: role_name -> deque of timestamps
        self.request_history: Dict[str, deque] = {}

        # 初始化默认配置
        self._initialize_default_configs()

        logger.info("RateLimiter initialized")

    def _initialize_default_configs(self):
        """初始化默认速率限制配置"""

        # Coder: 中等速率 (60 req/min)
        self.role_configs["Coder"] = RateLimitConfig(
            max_requests=60,
            time_window_seconds=60.0,
            burst_size=80
        )

        # Tester: 高速率 (120 req/min, 测试可能频繁)
        self.role_configs["Tester"] = RateLimitConfig(
            max_requests=120,
            time_window_seconds=60.0,
            burst_size=150
        )

        # DocWriter: 低速率 (30 req/min)
        self.role_configs["DocWriter"] = RateLimitConfig(
            max_requests=30,
            time_window_seconds=60.0,
            burst_size=40
        )

        # Reviewer: 中低速率 (40 req/min)
        self.role_configs["Reviewer"] = RateLimitConfig(
            max_requests=40,
            time_window_seconds=60.0,
            burst_size=50
        )

        # Debugger: 中高速率 (80 req/min, 调试可能频繁)
        self.role_configs["Debugger"] = RateLimitConfig(
            max_requests=80,
            time_window_seconds=60.0,
            burst_size=100
        )

        # Architect: 低速率 (20 req/min, 设计工作较慢)
        self.role_configs["Architect"] = RateLimitConfig(
            max_requests=20,
            time_window_seconds=60.0,
            burst_size=30
        )

        # SecurityExpert: 低速率 (25 req/min, 审计较慢)
        self.role_configs["SecurityExpert"] = RateLimitConfig(
            max_requests=25,
            time_window_seconds=60.0,
            burst_size=35
        )

        # PerfAnalyzer: 中等速率 (50 req/min)
        self.role_configs["PerfAnalyzer"] = RateLimitConfig(
            max_requests=50,
            time_window_seconds=60.0,
            burst_size=60
        )

        # Leader: 高速率 (200 req/min, 协调角色需要高吞吐)
        self.role_configs["Leader"] = RateLimitConfig(
            max_requests=200,
            time_window_seconds=60.0,
            burst_size=250
        )

        logger.info(
            f"Initialized default rate limits for {len(self.role_configs)} roles"
        )

    def set_rate_limit(
        self,
        role_name: str,
        config: RateLimitConfig
    ):
        """
        设置角色速率限制

        Args:
            role_name: 角色名称
            config: 速率限制配置
        """
        self.role_configs[role_name] = config

        # 初始化令牌桶
        self.token_buckets[role_name] = (float(config.burst_size), time.time())

        logger.info(
            f"Set rate limit for {role_name}: "
            f"{config.max_requests} req/{config.time_window_seconds}s, "
            f"burst={config.burst_size}"
        )

    def allow_request(
        self,
        role_name: str,
        cost: float = 1.0
    ) -> bool:
        """
        检查是否允许请求 (令牌桶算法)

        Args:
            role_name: 角色名称
            cost: 请求成本 (令牌数)

        Returns:
            True if request allowed
        """
        if role_name not in self.role_configs:
            logger.warning(f"No rate limit config for role: {role_name}, allowing request")
            return True

        config = self.role_configs[role_name]
        current_time = time.time()

        # 获取或初始化令牌桶
        if role_name not in self.token_buckets:
            self.token_buckets[role_name] = (float(config.burst_size), current_time)

        tokens, last_refill = self.token_buckets[role_name]

        # 计算令牌补充
        elapsed = current_time - last_refill
        refill_rate = config.max_requests / config.time_window_seconds
        new_tokens = min(
            config.burst_size,
            tokens + (elapsed * refill_rate)
        )

        # 检查是否有足够令牌
        if new_tokens >= cost:
            # 消费令牌
            self.token_buckets[role_name] = (new_tokens - cost, current_time)

            # 记录请求
            if role_name not in self.request_history:
                self.request_history[role_name] = deque()
            self.request_history[role_name].append(current_time)

            # 清理旧历史 (保留最近1小时)
            cutoff_time = current_time - 3600
            while (self.request_history[role_name] and
                   self.request_history[role_name][0] < cutoff_time):
                self.request_history[role_name].popleft()

            logger.debug(
                f"Request allowed for {role_name}: "
                f"cost={cost}, remaining_tokens={new_tokens - cost:.1f}"
            )
            return True

        else:
            # 令牌不足，拒绝请求
            wait_time = (cost - new_tokens) / refill_rate

            logger.warning(
                f"Rate limit exceeded for {role_name}: "
                f"required={cost}, available={new_tokens:.1f}, "
                f"wait={wait_time:.1f}s"
            )

            # 更新令牌桶 (不消费令牌)
            self.token_buckets[role_name] = (new_tokens, current_time)
            return False

    def get_wait_time(self, role_name: str, cost: float = 1.0) -> float:
        """
        获取需要等待的时间

        Args:
            role_name: 角色名称
            cost: 请求成本

        Returns:
            等待时间 (秒)
        """
        if role_name not in self.role_configs:
            return 0.0

        config = self.role_configs[role_name]
        current_time = time.time()

        if role_name not in self.token_buckets:
            return 0.0

        tokens, last_refill = self.token_buckets[role_name]

        # 计算当前令牌数
        elapsed = current_time - last_refill
        refill_rate = config.max_requests / config.time_window_seconds
        current_tokens = min(
            config.burst_size,
            tokens + (elapsed * refill_rate)
        )

        # 如果令牌足够，无需等待
        if current_tokens >= cost:
            return 0.0

        # 计算需要等待的时间
        needed_tokens = cost - current_tokens
        wait_time = needed_tokens / refill_rate

        return wait_time

    def get_rate_limit_status(self, role_name: str) -> Optional[Dict]:
        """
        获取速率限制状态

        Args:
            role_name: 角色名称

        Returns:
            速率限制状态字典或None
        """
        if role_name not in self.role_configs:
            return None

        config = self.role_configs[role_name]
        current_time = time.time()

        # 获取当前令牌数
        if role_name in self.token_buckets:
            tokens, last_refill = self.token_buckets[role_name]
            elapsed = current_time - last_refill
            refill_rate = config.max_requests / config.time_window_seconds
            current_tokens = min(
                config.burst_size,
                tokens + (elapsed * refill_rate)
            )
        else:
            current_tokens = config.burst_size

        # 获取请求历史统计
        recent_requests = 0
        if role_name in self.request_history:
            cutoff_time = current_time - config.time_window_seconds
            recent_requests = sum(
                1 for t in self.request_history[role_name]
                if t >= cutoff_time
            )

        return {
            "role": role_name,
            "max_requests": config.max_requests,
            "time_window_seconds": config.time_window_seconds,
            "burst_size": config.burst_size,
            "current_tokens": current_tokens,
            "recent_requests": recent_requests,
            "utilization": recent_requests / config.max_requests,
            "is_throttled": current_tokens < 1.0
        }

    def reset_limits(self, role_name: Optional[str] = None):
        """
        重置速率限制

        Args:
            role_name: 角色名称 (None则重置全部)
        """
        if role_name:
            # 重置指定角色
            if role_name in self.role_configs:
                config = self.role_configs[role_name]
                self.token_buckets[role_name] = (float(config.burst_size), time.time())
                if role_name in self.request_history:
                    self.request_history[role_name].clear()
                logger.info(f"Reset rate limit for {role_name}")
        else:
            # 重置全部
            for role_name, config in self.role_configs.items():
                self.token_buckets[role_name] = (float(config.burst_size), time.time())
            self.request_history.clear()
            logger.info("Reset all rate limits")

    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有角色的速率限制状态"""
        return {
            role_name: self.get_rate_limit_status(role_name)
            for role_name in self.role_configs.keys()
        }


# 全局单例
_rate_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取全局速率限制器实例"""
    global _rate_limiter_instance
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    return _rate_limiter_instance
