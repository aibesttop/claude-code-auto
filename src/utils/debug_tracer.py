"""
Debug Tracer - 代码执行路径追踪工具

提供函数级别的执行追踪,用于调试和性能分析。
"""

import functools
import time
import logging
from pathlib import Path
from typing import Callable, Any, Dict, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ExecutionTracer:
    """
    执行路径追踪器

    记录函数调用链、执行时间、参数和返回值
    """

    def __init__(self, output_dir: str = "logs/traces", enabled: bool = True):
        """
        初始化追踪器

        Args:
            output_dir: 追踪日志输出目录
            enabled: 是否启用追踪
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.enabled = enabled
        self.current_session = []
        self.session_start = None
        self.depth = 0  # 调用深度

    def start_session(self, session_name: str):
        """开始一个新的追踪会话"""
        if not self.enabled:
            return

        self.session_start = time.time()
        self.current_session = [{
            "event": "session_start",
            "name": session_name,
            "timestamp": datetime.now().isoformat(),
            "unix_time": self.session_start
        }]
        self.depth = 0

        logger.info(f"🔍 Tracer: Started session '{session_name}'")

    def end_session(self, save: bool = True) -> Optional[str]:
        """结束当前追踪会话并保存"""
        if not self.enabled:
            return None

        duration = time.time() - self.session_start if self.session_start else 0
        self.current_session.append({
            "event": "session_end",
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration
        })

        if save:
            return self._save_session()

        return None

    def log_call(self, func_name: str, args: tuple, kwargs: dict):
        """记录函数调用"""
        if not self.enabled:
            return

        self.current_session.append({
            "event": "call",
            "function": func_name,
            "depth": self.depth,
            "timestamp": datetime.now().isoformat(),
            "args": str(args)[:200],  # 限制长度
            "kwargs": str(kwargs)[:200]
        })

        self.depth += 1

    def log_return(self, func_name: str, result: Any, duration: float):
        """记录函数返回"""
        if not self.enabled:
            return

        self.depth -= 1

        self.current_session.append({
            "event": "return",
            "function": func_name,
            "depth": self.depth,
            "timestamp": datetime.now().isoformat(),
            "duration_ms": round(duration * 1000, 2),
            "result": str(result)[:200]
        })

    def log_exception(self, func_name: str, exception: Exception):
        """记录异常"""
        if not self.enabled:
            return

        self.depth -= 1

        self.current_session.append({
            "event": "exception",
            "function": func_name,
            "depth": self.depth,
            "timestamp": datetime.now().isoformat(),
            "exception": str(exception),
            "type": type(exception).__name__
        })

    def _save_session(self) -> Optional[str]:
        """保存追踪会话到文件"""
        if not self.current_session:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{timestamp}.json"
        filepath = self.output_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)

            logger.info(f"🔍 Tracer: Saved trace to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save trace: {e}")
            return None


# 全局追踪器实例
_global_tracer = ExecutionTracer()


def get_tracer() -> ExecutionTracer:
    """获取全局追踪器实例"""
    return _global_tracer


def trace_function(
    tracer: Optional[ExecutionTracer] = None,
    log_args: bool = True,
    log_result: bool = True,
    log_exceptions: bool = True
):
    """
    函数追踪装饰器

    Usage:
        @trace_function()
        def my_function(arg1, arg2):
            ...

    Args:
        tracer: 追踪器实例 (None = 使用全局实例)
        log_args: 是否记录参数
        log_result: 是否记录返回值
        log_exceptions: 是否记录异常
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            t = tracer or _global_tracer
            if not t.enabled:
                return await func(*args, **kwargs)

            func_name = f"{func.__module__}.{func.__qualname__}"
            start_time = time.time()

            if log_args:
                t.log_call(func_name, args, kwargs)

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if log_result:
                    t.log_return(func_name, result, duration)

                return result

            except Exception as e:
                if log_exceptions:
                    t.log_exception(func_name, e)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            t = tracer or _global_tracer
            if not t.enabled:
                return func(*args, **kwargs)

            func_name = f"{func.__module__}.{func.__qualname__}"
            start_time = time.time()

            if log_args:
                t.log_call(func_name, args, kwargs)

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if log_result:
                    t.log_return(func_name, result, duration)

                return result

            except Exception as e:
                if log_exceptions:
                    t.log_exception(func_name, e)
                raise

        # 根据函数类型返回适当的包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


import asyncio


class CallStackVisualizer:
    """调用栈可视化工具"""

    @staticmethod
    def visualize_trace(trace_file: str) -> str:
        """
        将追踪文件转换为可视化调用栈

        Args:
            trace_file: 追踪JSON文件路径

        Returns:
            可视化字符串
        """
        try:
            with open(trace_file, 'r', encoding='utf-8') as f:
                trace = json.load(f)
        except Exception as e:
            return f"Error loading trace: {e}"

        lines = []
        lines.append("=" * 80)
        lines.append("EXECUTION TRACE VISUALIZATION")
        lines.append("=" * 80)
        lines.append("")

        for event in trace:
            event_type = event.get("event")

            if event_type == "session_start":
                lines.append(f"🚀 Session: {event.get('name')}")
                lines.append(f"   Started: {event.get('timestamp')}")
                lines.append("")

            elif event_type == "call":
                depth = event.get("depth", 0)
                indent = "  " * depth
                func = event.get("function", "unknown").split(".")[-1]
                args = event.get("args", "")[:50]
                lines.append(f"{indent}└─→ {func}({args}...)")

            elif event_type == "return":
                depth = event.get("depth", 0)
                indent = "  " * depth
                func = event.get("function", "unknown").split(".")[-1]
                duration = event.get("duration_ms", 0)
                result = event.get("result", "")[:30]
                lines.append(f"{indent}└─← {func} ({duration}ms) → {result}")

            elif event_type == "exception":
                depth = event.get("depth", 0)
                indent = "  " * depth
                func = event.get("function", "unknown").split(".")[-1]
                exc = event.get("exception", "unknown")
                lines.append(f"{indent}└─✗ {func} → ❌ {exc}")

            elif event_type == "session_end":
                duration = event.get("duration_seconds", 0)
                lines.append("")
                lines.append(f"✅ Completed in {duration:.2f}s")
                lines.append("=" * 80)

        return "\n".join(lines)

    @staticmethod
    def generate_flamegraph(trace_file: str, output_file: str = None):
        """
        生成火焰图数据 (可用于Chrome DevTools)

        Args:
            trace_file: 追踪JSON文件路径
            output_file: 输出文件路径 (可选)
        """
        # 这里可以实现火焰图生成逻辑
        # 由于需要Chrome Trace Event Format, 这里简化处理
        pass


def enable_tracing(enabled: bool = True, output_dir: str = "logs/traces"):
    """
    启用/禁用全局追踪

    Args:
        enabled: 是否启用
        output_dir: 输出目录
    """
    global _global_tracer
    _global_tracer = ExecutionTracer(output_dir=output_dir, enabled=enabled)
    logger.info(f"🔍 Tracing {'enabled' if enabled else 'disabled'}")
