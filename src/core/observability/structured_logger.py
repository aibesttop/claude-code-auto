"""
Structured Logger - 结构化日志器

提供JSONL格式的流式日志记录，支持与追踪系统集成
"""
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger()


class StructuredLogger:
    """结构化日志器"""

    def __init__(
        self,
        log_dir: Path,
        session_id: str,
        enable_console: bool = True,
        enable_file: bool = True
    ):
        """
        初始化结构化日志器

        Args:
            log_dir: 日志目录
            session_id: Session ID
            enable_console: 是否输出到控制台
            enable_file: 是否输出到文件
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = session_id
        self.enable_console = enable_console
        self.enable_file = enable_file

        # JSONL日志文件
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{session_id}_{timestamp}.jsonl"

        if self.enable_file:
            # 创建日志文件
            self.log_file.touch()

        logger.info(
            f"StructuredLogger initialized: session={session_id}, "
            f"log_file={self.log_file}"
        )

    def log(
        self,
        level: str,
        message: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        mission_id: Optional[str] = None,
        role_name: Optional[str] = None,
        **extra
    ):
        """
        记录结构化日志

        Args:
            level: 日志级别 (debug, info, warning, error, critical)
            message: 日志消息
            trace_id: Trace ID
            span_id: Span ID
            mission_id: Mission ID
            role_name: 角色名称
            **extra: 额外字段
        """
        log_entry = {
            "timestamp": time.time(),
            "iso_time": datetime.utcnow().isoformat() + "Z",
            "level": level.upper(),
            "message": message,
            "session_id": self.session_id,
            "trace_id": trace_id,
            "span_id": span_id,
            "mission_id": mission_id,
            "role_name": role_name,
            **extra
        }

        # 移除None值
        log_entry = {k: v for k, v in log_entry.items() if v is not None}

        # 输出到文件 (JSONL格式)
        if self.enable_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            except Exception as e:
                logger.error(f"Failed to write structured log: {e}")

        # 输出到控制台 (可选)
        if self.enable_console:
            self._console_log(level, message, log_entry)

    def _console_log(self, level: str, message: str, log_entry: dict):
        """输出到控制台"""
        # 简化的控制台输出
        context_parts = []
        if log_entry.get("trace_id"):
            context_parts.append(f"trace={log_entry['trace_id'][:8]}")
        if log_entry.get("span_id"):
            context_parts.append(f"span={log_entry['span_id'][:8]}")
        if log_entry.get("mission_id"):
            context_parts.append(f"mission={log_entry['mission_id']}")
        if log_entry.get("role_name"):
            context_parts.append(f"role={log_entry['role_name']}")

        context_str = f"[{', '.join(context_parts)}]" if context_parts else ""

        log_line = f"{level.upper()} {context_str} {message}"

        # 使用标准logger输出
        if level == "debug":
            logger.debug(log_line)
        elif level == "info":
            logger.info(log_line)
        elif level == "warning":
            logger.warning(log_line)
        elif level == "error":
            logger.error(log_line)
        elif level == "critical":
            logger.critical(log_line)

    def debug(self, message: str, **kwargs):
        """记录DEBUG日志"""
        self.log("debug", message, **kwargs)

    def info(self, message: str, **kwargs):
        """记录INFO日志"""
        self.log("info", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录WARNING日志"""
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录ERROR日志"""
        self.log("error", message, **kwargs)

    def critical(self, message: str, **kwargs):
        """记录CRITICAL日志"""
        self.log("critical", message, **kwargs)

    def log_span_event(
        self,
        span_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        trace_id: Optional[str] = None,
        **kwargs
    ):
        """
        记录Span事件

        Args:
            span_id: Span ID
            event_type: 事件类型 (span_start, span_end, span_log)
            event_data: 事件数据
            trace_id: Trace ID
            **kwargs: 额外字段
        """
        self.log(
            level="info",
            message=f"Span event: {event_type}",
            trace_id=trace_id,
            span_id=span_id,
            event_type=event_type,
            event_data=event_data,
            **kwargs
        )

    def log_budget_event(
        self,
        entity_id: str,
        event_type: str,
        budget_data: Dict[str, Any],
        **kwargs
    ):
        """
        记录预算事件

        Args:
            entity_id: 实体ID
            event_type: 事件类型 (budget_allocated, budget_consumed, budget_exceeded)
            budget_data: 预算数据
            **kwargs: 额外字段
        """
        self.log(
            level="info",
            message=f"Budget event: {event_type}",
            entity_id=entity_id,
            event_type=event_type,
            budget_data=budget_data,
            **kwargs
        )

    def log_quality_event(
        self,
        mission_id: str,
        event_type: str,
        quality_data: Dict[str, Any],
        **kwargs
    ):
        """
        记录质量评估事件

        Args:
            mission_id: Mission ID
            event_type: 事件类型 (evaluation_start, evaluation_end, dimension_evaluated)
            quality_data: 质量数据
            **kwargs: 额外字段
        """
        self.log(
            level="info",
            message=f"Quality event: {event_type}",
            mission_id=mission_id,
            event_type=event_type,
            quality_data=quality_data,
            **kwargs
        )

    def query_logs(
        self,
        level: Optional[str] = None,
        trace_id: Optional[str] = None,
        mission_id: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        查询日志

        Args:
            level: 日志级别过滤
            trace_id: Trace ID过滤
            mission_id: Mission ID过滤
            limit: 返回数量限制

        Returns:
            日志条目列表
        """
        if not self.log_file.exists():
            return []

        results = []

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if len(results) >= limit:
                        break

                    try:
                        entry = json.loads(line.strip())

                        # 应用过滤
                        if level and entry.get("level") != level.upper():
                            continue
                        if trace_id and entry.get("trace_id") != trace_id:
                            continue
                        if mission_id and entry.get("mission_id") != mission_id:
                            continue

                        results.append(entry)

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Failed to query logs: {e}")

        return results

    def get_log_stats(self) -> Dict[str, Any]:
        """
        获取日志统计

        Returns:
            日志统计字典
        """
        if not self.log_file.exists():
            return {
                "total_logs": 0,
                "file_size_bytes": 0
            }

        stats = {
            "log_file": str(self.log_file),
            "file_size_bytes": self.log_file.stat().st_size,
            "total_logs": 0,
            "by_level": {},
            "unique_traces": set(),
            "unique_missions": set()
        }

        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        stats["total_logs"] += 1

                        # 统计级别
                        level = entry.get("level", "UNKNOWN")
                        stats["by_level"][level] = stats["by_level"].get(level, 0) + 1

                        # 统计trace和mission
                        if entry.get("trace_id"):
                            stats["unique_traces"].add(entry["trace_id"])
                        if entry.get("mission_id"):
                            stats["unique_missions"].add(entry["mission_id"])

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Failed to get log stats: {e}")

        # 转换set为count
        stats["unique_traces"] = len(stats["unique_traces"])
        stats["unique_missions"] = len(stats["unique_missions"])

        return stats


# 全局单例
_structured_logger_instance: Optional[StructuredLogger] = None


def get_structured_logger(
    log_dir: Path = None,
    session_id: str = None
) -> StructuredLogger:
    """
    获取全局结构化日志器实例

    Args:
        log_dir: 日志目录 (仅在首次调用时使用)
        session_id: Session ID (仅在首次调用时使用)

    Returns:
        StructuredLogger实例
    """
    global _structured_logger_instance

    if _structured_logger_instance is None:
        if log_dir is None:
            # 默认使用项目下的logs/structured目录
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            log_dir = project_root / "logs" / "structured"

        if session_id is None:
            session_id = f"session-{int(time.time())}"

        _structured_logger_instance = StructuredLogger(
            log_dir=log_dir,
            session_id=session_id
        )

    return _structured_logger_instance
