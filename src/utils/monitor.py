"""
Performance Monitoring

Tracks execution times and provides performance statistics
for measuring optimization impact.
"""
import time
from functools import wraps
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceStats:
    """Statistics for a monitored operation."""
    name: str
    count: int = 0
    total_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    durations: List[float] = field(default_factory=list)

    @property
    def avg_time(self) -> float:
        """Average execution time."""
        return self.total_time / self.count if self.count > 0 else 0.0

    @property
    def p50(self) -> float:
        """Median execution time."""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        mid = len(sorted_durations) // 2
        return sorted_durations[mid]

    @property
    def p95(self) -> float:
        """95th percentile execution time."""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        idx = int(len(sorted_durations) * 0.95)
        return sorted_durations[min(idx, len(sorted_durations) - 1)]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "count": self.count,
            "total_time": round(self.total_time, 3),
            "avg_time": round(self.avg_time, 3),
            "min_time": round(self.min_time, 3),
            "max_time": round(self.max_time, 3),
            "p50": round(self.p50, 3),
            "p95": round(self.p95, 3)
        }


class PerformanceMonitor:
    """
    Performance monitoring for critical code paths.

    Usage:
        monitor = PerformanceMonitor()

        @monitor.measure("tool_execution")
        def execute_tool(name, args):
            ...

        stats = monitor.get_stats("tool_execution")
        print(f"Avg time: {stats.avg_time:.3f}s")
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize monitor.

        Args:
            max_history: Maximum number of duration samples to keep per metric
        """
        self.metrics: Dict[str, PerformanceStats] = {}
        self.max_history = max_history

    def measure(self, name: str) -> Callable:
        """
        Decorator to measure function execution time.

        Args:
            name: Metric name for tracking

        Example:
            @monitor.measure("validation")
            def validate_file(path):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.perf_counter() - start
                    self._record(name, duration)

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.perf_counter() - start
                    self._record(name, duration)

            # Return appropriate wrapper based on function type
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def _record(self, name: str, duration: float):
        """Record a timing measurement."""
        if name not in self.metrics:
            self.metrics[name] = PerformanceStats(name=name)

        stats = self.metrics[name]
        stats.count += 1
        stats.total_time += duration
        stats.min_time = min(stats.min_time, duration)
        stats.max_time = max(stats.max_time, duration)

        # Keep limited history for percentile calculations
        if len(stats.durations) >= self.max_history:
            # Remove oldest 10% when full
            stats.durations = stats.durations[self.max_history // 10:]

        stats.durations.append(duration)

    def get_stats(self, name: str) -> Optional[PerformanceStats]:
        """
        Get statistics for a metric.

        Args:
            name: Metric name

        Returns:
            PerformanceStats or None if metric doesn't exist
        """
        return self.metrics.get(name)

    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """Get all tracked metrics."""
        return self.metrics.copy()

    def print_summary(self):
        """Print performance summary to logger."""
        if not self.metrics:
            logger.info("No performance metrics recorded")
            return

        logger.info("\n" + "=" * 80)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 80)

        for name, stats in sorted(self.metrics.items()):
            logger.info(f"\n{name}:")
            logger.info(f"  Count:     {stats.count}")
            logger.info(f"  Total:     {stats.total_time:.3f}s")
            logger.info(f"  Average:   {stats.avg_time:.3f}s")
            logger.info(f"  Min:       {stats.min_time:.3f}s")
            logger.info(f"  Max:       {stats.max_time:.3f}s")
            logger.info(f"  P50:       {stats.p50:.3f}s")
            logger.info(f"  P95:       {stats.p95:.3f}s")

        logger.info("=" * 80 + "\n")

    def export_json(self) -> dict:
        """Export all metrics as JSON-serializable dict."""
        return {
            name: stats.to_dict()
            for name, stats in self.metrics.items()
        }

    def reset(self):
        """Clear all metrics."""
        self.metrics.clear()
        logger.info("Performance metrics reset")


# Global monitor instance (singleton pattern)
_global_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def measure(name: str) -> Callable:
    """
    Convenience function for global monitor.

    Example:
        from src.utils.monitor import measure

        @measure("file_validation")
        def validate_file(path):
            ...
    """
    return get_monitor().measure(name)


def print_performance_summary():
    """Print global performance summary."""
    get_monitor().print_summary()


def reset_performance_metrics():
    """Reset global performance metrics."""
    get_monitor().reset()


# Example usage
if __name__ == "__main__":
    import asyncio

    monitor = PerformanceMonitor()

    @monitor.measure("sync_operation")
    def slow_function():
        time.sleep(0.1)
        return "done"

    @monitor.measure("async_operation")
    async def async_slow_function():
        await asyncio.sleep(0.05)
        return "done"

    # Test sync
    for _ in range(5):
        slow_function()

    # Test async
    async def test_async():
        for _ in range(5):
            await async_slow_function()

    asyncio.run(test_async())

    # Print stats
    monitor.print_summary()
