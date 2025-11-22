"""
Backoff Strategy - 退避策略

提供指数退避和线性退避策略，用于失败重试控制
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger()


class BackoffStrategy(ABC):
    """退避策略基类"""

    @abstractmethod
    def get_wait_time(self, attempt: int) -> float:
        """
        获取等待时间

        Args:
            attempt: 尝试次数 (从1开始)

        Returns:
            等待时间 (秒)
        """
        pass

    @abstractmethod
    def should_retry(self, attempt: int) -> bool:
        """
        是否应该重试

        Args:
            attempt: 尝试次数

        Returns:
            True if should retry
        """
        pass


@dataclass
class ExponentialBackoff(BackoffStrategy):
    """指数退避策略"""

    base_delay: float = 1.0     # 基础延迟 (秒)
    max_delay: float = 60.0     # 最大延迟 (秒)
    multiplier: float = 2.0     # 倍数
    max_attempts: int = 5       # 最大尝试次数

    def get_wait_time(self, attempt: int) -> float:
        """
        计算指数退避等待时间

        公式: min(base_delay * multiplier^(attempt-1), max_delay)

        Args:
            attempt: 尝试次数 (从1开始)

        Returns:
            等待时间 (秒)
        """
        if attempt <= 0:
            return 0.0

        wait_time = self.base_delay * (self.multiplier ** (attempt - 1))
        wait_time = min(wait_time, self.max_delay)

        logger.debug(
            f"Exponential backoff: attempt={attempt}, wait_time={wait_time:.1f}s"
        )

        return wait_time

    def should_retry(self, attempt: int) -> bool:
        """
        检查是否应该重试

        Args:
            attempt: 尝试次数

        Returns:
            True if should retry
        """
        return attempt < self.max_attempts


@dataclass
class LinearBackoff(BackoffStrategy):
    """线性退避策略"""

    base_delay: float = 2.0     # 基础延迟 (秒)
    increment: float = 2.0      # 增量 (秒)
    max_delay: float = 30.0     # 最大延迟 (秒)
    max_attempts: int = 5       # 最大尝试次数

    def get_wait_time(self, attempt: int) -> float:
        """
        计算线性退避等待时间

        公式: min(base_delay + increment * (attempt-1), max_delay)

        Args:
            attempt: 尝试次数 (从1开始)

        Returns:
            等待时间 (秒)
        """
        if attempt <= 0:
            return 0.0

        wait_time = self.base_delay + self.increment * (attempt - 1)
        wait_time = min(wait_time, self.max_delay)

        logger.debug(
            f"Linear backoff: attempt={attempt}, wait_time={wait_time:.1f}s"
        )

        return wait_time

    def should_retry(self, attempt: int) -> bool:
        """
        检查是否应该重试

        Args:
            attempt: 尝试次数

        Returns:
            True if should retry
        """
        return attempt < self.max_attempts


class RetryExecutor:
    """带退避策略的重试执行器"""

    def __init__(self, backoff_strategy: Optional[BackoffStrategy] = None):
        """
        初始化重试执行器

        Args:
            backoff_strategy: 退避策略 (默认使用指数退避)
        """
        self.backoff_strategy = backoff_strategy or ExponentialBackoff()
        logger.info(
            f"RetryExecutor initialized with {type(self.backoff_strategy).__name__}"
        )

    def execute_with_retry(
        self,
        func,
        *args,
        on_retry=None,
        on_failure=None,
        **kwargs
    ):
        """
        带重试执行函数

        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
            on_retry: 重试回调函数 (可选)
            on_failure: 失败回调函数 (可选)

        Returns:
            函数执行结果

        Raises:
            最后一次尝试的异常
        """
        attempt = 0
        last_exception = None

        while True:
            attempt += 1

            try:
                logger.info(f"Executing attempt {attempt}")
                result = func(*args, **kwargs)

                if attempt > 1:
                    logger.info(f"Succeeded on attempt {attempt}")

                return result

            except Exception as e:
                last_exception = e

                logger.warning(
                    f"Attempt {attempt} failed: {str(e)}"
                )

                # 检查是否应该重试
                if not self.backoff_strategy.should_retry(attempt):
                    logger.error(
                        f"Max attempts reached ({attempt}), giving up"
                    )

                    if on_failure:
                        on_failure(attempt, e)

                    raise last_exception

                # 计算等待时间
                wait_time = self.backoff_strategy.get_wait_time(attempt)

                logger.info(
                    f"Retrying in {wait_time:.1f}s (attempt {attempt + 1})"
                )

                # 调用重试回调
                if on_retry:
                    on_retry(attempt, wait_time, e)

                # 等待
                if wait_time > 0:
                    time.sleep(wait_time)

    async def execute_with_retry_async(
        self,
        func,
        *args,
        on_retry=None,
        on_failure=None,
        **kwargs
    ):
        """
        带重试执行异步函数

        Args:
            func: 要执行的异步函数
            *args, **kwargs: 函数参数
            on_retry: 重试回调函数 (可选)
            on_failure: 失败回调函数 (可选)

        Returns:
            函数执行结果

        Raises:
            最后一次尝试的异常
        """
        import asyncio

        attempt = 0
        last_exception = None

        while True:
            attempt += 1

            try:
                logger.info(f"Executing async attempt {attempt}")
                result = await func(*args, **kwargs)

                if attempt > 1:
                    logger.info(f"Succeeded on attempt {attempt}")

                return result

            except Exception as e:
                last_exception = e

                logger.warning(
                    f"Async attempt {attempt} failed: {str(e)}"
                )

                # 检查是否应该重试
                if not self.backoff_strategy.should_retry(attempt):
                    logger.error(
                        f"Max attempts reached ({attempt}), giving up"
                    )

                    if on_failure:
                        on_failure(attempt, e)

                    raise last_exception

                # 计算等待时间
                wait_time = self.backoff_strategy.get_wait_time(attempt)

                logger.info(
                    f"Retrying in {wait_time:.1f}s (attempt {attempt + 1})"
                )

                # 调用重试回调
                if on_retry:
                    on_retry(attempt, wait_time, e)

                # 异步等待
                if wait_time > 0:
                    await asyncio.sleep(wait_time)


def create_exponential_backoff(
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0,
    max_attempts: int = 5
) -> ExponentialBackoff:
    """
    创建指数退避策略

    Args:
        base_delay: 基础延迟 (秒)
        max_delay: 最大延迟 (秒)
        multiplier: 倍数
        max_attempts: 最大尝试次数

    Returns:
        ExponentialBackoff实例
    """
    return ExponentialBackoff(
        base_delay=base_delay,
        max_delay=max_delay,
        multiplier=multiplier,
        max_attempts=max_attempts
    )


def create_linear_backoff(
    base_delay: float = 2.0,
    increment: float = 2.0,
    max_delay: float = 30.0,
    max_attempts: int = 5
) -> LinearBackoff:
    """
    创建线性退避策略

    Args:
        base_delay: 基础延迟 (秒)
        increment: 增量 (秒)
        max_delay: 最大延迟 (秒)
        max_attempts: 最大尝试次数

    Returns:
        LinearBackoff实例
    """
    return LinearBackoff(
        base_delay=base_delay,
        increment=increment,
        max_delay=max_delay,
        max_attempts=max_attempts
    )
