"""
Structured Tracer - 结构化追踪器

提供trace_id/span_id分层追踪，支持嵌套调用链跟踪
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class TraceContext:
    """追踪上下文"""
    trace_id: str
    session_id: str
    mission_id: Optional[str] = None
    role_name: Optional[str] = None

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "mission_id": self.mission_id,
            "role_name": self.role_name,
            "metadata": self.metadata
        }


@dataclass
class Span:
    """追踪跨度"""
    span_id: str
    trace_id: str
    parent_span_id: Optional[str]

    # 基本信息
    name: str
    operation: str  # session_start, mission_execute, role_execute, action_call

    # 时间信息
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None

    # 状态
    status: str = "running"  # running, success, failed, timeout
    error: Optional[str] = None

    # 附加数据
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)

    # 资源消耗
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0

    def finish(self, status: str = "success", error: Optional[str] = None):
        """完成Span"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status
        if error:
            self.error = error

    def add_log(self, message: str, level: str = "info", **kwargs):
        """添加日志"""
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            **kwargs
        }
        self.logs.append(log_entry)

    def add_tag(self, key: str, value: str):
        """添加标签"""
        self.tags[key] = value

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "operation": self.operation,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "error": self.error,
            "tags": self.tags,
            "logs": self.logs,
            "cost_usd": self.cost_usd,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens
        }


class StructuredTracer:
    """结构化追踪器"""

    def __init__(self):
        """初始化追踪器"""
        self.active_spans: Dict[str, Span] = {}
        self.completed_spans: List[Span] = []
        self.current_trace: Optional[TraceContext] = None

        # Span栈，用于跟踪嵌套调用
        self.span_stack: List[str] = []

        logger.info("StructuredTracer initialized")

    def start_trace(
        self,
        session_id: str,
        mission_id: Optional[str] = None,
        role_name: Optional[str] = None,
        **metadata
    ) -> TraceContext:
        """
        开始新的追踪

        Args:
            session_id: Session ID
            mission_id: Mission ID (可选)
            role_name: 角色名称 (可选)
            **metadata: 元数据

        Returns:
            TraceContext实例
        """
        trace_id = f"trace-{uuid.uuid4().hex[:16]}"

        self.current_trace = TraceContext(
            trace_id=trace_id,
            session_id=session_id,
            mission_id=mission_id,
            role_name=role_name,
            metadata=metadata
        )

        logger.info(
            f"Started trace: {trace_id}, session={session_id}, "
            f"mission={mission_id}, role={role_name}"
        )

        return self.current_trace

    def start_span(
        self,
        name: str,
        operation: str,
        parent_span_id: Optional[str] = None,
        **tags
    ) -> Span:
        """
        开始新的Span

        Args:
            name: Span名称
            operation: 操作类型
            parent_span_id: 父Span ID (可选，不提供则使用栈顶)
            **tags: 标签

        Returns:
            Span实例
        """
        if self.current_trace is None:
            logger.warning("No active trace, starting default trace")
            self.start_trace(session_id="default")

        span_id = f"span-{uuid.uuid4().hex[:12]}"

        # 确定父Span
        if parent_span_id is None and self.span_stack:
            parent_span_id = self.span_stack[-1]

        span = Span(
            span_id=span_id,
            trace_id=self.current_trace.trace_id,
            parent_span_id=parent_span_id,
            name=name,
            operation=operation,
            tags=tags
        )

        self.active_spans[span_id] = span
        self.span_stack.append(span_id)

        logger.debug(
            f"Started span: {span_id}, name={name}, operation={operation}, "
            f"parent={parent_span_id}"
        )

        return span

    def finish_span(
        self,
        span_id: str,
        status: str = "success",
        error: Optional[str] = None,
        cost_usd: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0
    ):
        """
        完成Span

        Args:
            span_id: Span ID
            status: 状态
            error: 错误信息
            cost_usd: 成本
            input_tokens: 输入token数
            output_tokens: 输出token数
        """
        if span_id not in self.active_spans:
            logger.warning(f"Span not found: {span_id}")
            return

        span = self.active_spans.pop(span_id)
        span.finish(status=status, error=error)
        span.cost_usd = cost_usd
        span.input_tokens = input_tokens
        span.output_tokens = output_tokens

        self.completed_spans.append(span)

        # 从栈中移除
        if span_id in self.span_stack:
            self.span_stack.remove(span_id)

        logger.debug(
            f"Finished span: {span_id}, status={status}, "
            f"duration={span.duration_ms:.2f}ms, cost=${cost_usd:.6f}"
        )

    @contextmanager
    def span(
        self,
        name: str,
        operation: str,
        **tags
    ):
        """
        Span上下文管理器

        用法:
        with tracer.span("operation_name", "action_call") as span:
            # do something
            span.add_log("Processing...")

        Args:
            name: Span名称
            operation: 操作类型
            **tags: 标签
        """
        span = self.start_span(name, operation, **tags)

        try:
            yield span
            self.finish_span(span.span_id, status="success")

        except Exception as e:
            self.finish_span(
                span.span_id,
                status="failed",
                error=str(e)
            )
            raise

    def get_current_span(self) -> Optional[Span]:
        """获取当前活跃Span (栈顶)"""
        if not self.span_stack:
            return None
        span_id = self.span_stack[-1]
        return self.active_spans.get(span_id)

    def get_span(self, span_id: str) -> Optional[Span]:
        """获取指定Span"""
        # 先查活跃Span
        if span_id in self.active_spans:
            return self.active_spans[span_id]

        # 再查已完成Span
        for span in self.completed_spans:
            if span.span_id == span_id:
                return span

        return None

    def get_trace_summary(self) -> Optional[Dict]:
        """
        获取追踪汇总

        Returns:
            追踪汇总字典或None
        """
        if self.current_trace is None:
            return None

        # 统计所有Span
        total_spans = len(self.active_spans) + len(self.completed_spans)
        completed_count = len(self.completed_spans)
        success_count = sum(
            1 for s in self.completed_spans if s.status == "success"
        )
        failed_count = sum(
            1 for s in self.completed_spans if s.status == "failed"
        )

        # 计算总成本和token数
        total_cost = sum(s.cost_usd for s in self.completed_spans)
        total_input_tokens = sum(s.input_tokens for s in self.completed_spans)
        total_output_tokens = sum(s.output_tokens for s in self.completed_spans)

        # 计算总时长
        total_duration = sum(
            s.duration_ms for s in self.completed_spans
            if s.duration_ms is not None
        )

        return {
            "trace_id": self.current_trace.trace_id,
            "session_id": self.current_trace.session_id,
            "mission_id": self.current_trace.mission_id,
            "role_name": self.current_trace.role_name,
            "total_spans": total_spans,
            "completed_spans": completed_count,
            "active_spans": len(self.active_spans),
            "success_count": success_count,
            "failed_count": failed_count,
            "total_cost_usd": total_cost,
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_duration_ms": total_duration
        }

    def get_span_tree(self) -> List[Dict]:
        """
        获取Span树结构 (用于可视化)

        Returns:
            Span树列表
        """
        all_spans = list(self.active_spans.values()) + self.completed_spans

        # 构建树
        span_dict = {s.span_id: s.to_dict() for s in all_spans}

        # 找到根Span (没有父Span的)
        roots = [
            s for s in span_dict.values()
            if s["parent_span_id"] is None
        ]

        def build_tree(span_data: dict) -> dict:
            """递归构建树"""
            children = [
                build_tree(child)
                for child in span_dict.values()
                if child["parent_span_id"] == span_data["span_id"]
            ]
            span_data["children"] = children
            return span_data

        return [build_tree(root) for root in roots]

    def export_spans(self) -> List[Dict]:
        """
        导出所有Span数据

        Returns:
            Span数据列表
        """
        all_spans = list(self.active_spans.values()) + self.completed_spans
        return [s.to_dict() for s in all_spans]

    def clear(self):
        """清空追踪数据"""
        self.active_spans.clear()
        self.completed_spans.clear()
        self.span_stack.clear()
        self.current_trace = None
        logger.info("Tracer cleared")


# 全局单例
_tracer_instance: Optional[StructuredTracer] = None


def get_tracer() -> StructuredTracer:
    """获取全局追踪器实例"""
    global _tracer_instance
    if _tracer_instance is None:
        _tracer_instance = StructuredTracer()
    return _tracer_instance
