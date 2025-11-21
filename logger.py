"""
统一日志系统
提供结构化日志、文件轮转、多格式输出等功能
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime
import json


class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # 添加额外字段
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'iteration'):
            log_data['iteration'] = record.iteration

        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


class DetailedFormatter(logging.Formatter):
    """详细格式化器"""

    def __init__(self):
        fmt = (
            '%(asctime)s | %(levelname)-8s | '
            '[%(name)s:%(funcName)s:%(lineno)d] | '
            '%(message)s'
        )
        super().__init__(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S')

    def format(self, record: logging.LogRecord) -> str:
        # 添加会话和迭代信息
        original_msg = record.msg
        extra_info = []

        if hasattr(record, 'session_id') and record.session_id:
            extra_info.append(f"Session:{record.session_id[:8]}")
        if hasattr(record, 'iteration') and record.iteration:
            extra_info.append(f"Iter:{record.iteration}")

        if extra_info:
            record.msg = f"[{' | '.join(extra_info)}] {original_msg}"

        result = super().format(record)
        record.msg = original_msg  # 恢复原始消息
        return result


class SimpleFormatter(logging.Formatter):
    """简单格式化器"""

    def __init__(self):
        fmt = '%(asctime)s - %(levelname)s - %(message)s'
        super().__init__(fmt=fmt, datefmt='%H:%M:%S')


class WorkflowLogger:
    """工作流日志管理器"""

    def __init__(
        self,
        name: str = "workflow",
        log_dir: str = "logs",
        level: str = "INFO",
        format_type: str = "detailed",
        console_output: bool = True,
        file_output: bool = True,
        max_file_size_mb: int = 10,
        backup_count: int = 5
    ):
        self.name = name
        self.log_dir = Path(log_dir)
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        self.logger.handlers.clear()  # 清除现有处理器
        self.logger.propagate = False  # 不传播到父logger

        # 选择格式化器
        if format_type == "json":
            formatter = JsonFormatter()
        elif format_type == "simple":
            formatter = SimpleFormatter()
        else:  # detailed
            formatter = DetailedFormatter()

        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 文件处理器
        if file_output:
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # 主日志文件
            log_file = self.log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # 错误日志文件（只记录 ERROR 和 CRITICAL）
            error_log_file = self.log_dir / f"{name}_error.log"
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            self.logger.addHandler(error_handler)

    def get_logger(self) -> logging.Logger:
        """获取 logger 实例"""
        return self.logger

    def debug(self, msg: str, **kwargs):
        """记录 DEBUG 级别日志"""
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs):
        """记录 INFO 级别日志"""
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs):
        """记录 WARNING 级别日志"""
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg: str, **kwargs):
        """记录 ERROR 级别日志"""
        self.logger.error(msg, extra=kwargs)

    def critical(self, msg: str, **kwargs):
        """记录 CRITICAL 级别日志"""
        self.logger.critical(msg, extra=kwargs)

    def exception(self, msg: str, **kwargs):
        """记录异常日志（包含堆栈跟踪）"""
        self.logger.exception(msg, extra=kwargs)

    def log_iteration_start(self, iteration: int, session_id: str):
        """记录迭代开始"""
        self.info(
            f"开始第 {iteration} 轮迭代",
            session_id=session_id,
            iteration=iteration
        )

    def log_iteration_end(
        self,
        iteration: int,
        session_id: str,
        success: bool,
        duration: float
    ):
        """记录迭代结束"""
        status = "成功" if success else "失败"
        self.info(
            f"第 {iteration} 轮迭代{status}，耗时 {duration:.2f}秒",
            session_id=session_id,
            iteration=iteration
        )

    def log_decision(
        self,
        iteration: int,
        session_id: str,
        decision: dict
    ):
        """记录 AI 决策"""
        completed = decision.get('completed', False)
        confidence = decision.get('confidence', 'N/A')
        self.info(
            f"AI 决策: completed={completed}, confidence={confidence}",
            session_id=session_id,
            iteration=iteration
        )

    def log_error_with_retry(
        self,
        iteration: int,
        session_id: str,
        error: Exception,
        retry_count: int,
        max_retries: int
    ):
        """记录错误和重试信息"""
        self.warning(
            f"迭代失败 ({type(error).__name__}: {error})，"
            f"重试 {retry_count}/{max_retries}",
            session_id=session_id,
            iteration=iteration
        )


# 全局日志实例
_logger: Optional[WorkflowLogger] = None


def setup_logger(
    name: str = "workflow",
    log_dir: str = "logs",
    level: str = "INFO",
    format_type: str = "detailed",
    console_output: bool = True,
    file_output: bool = True,
    max_file_size_mb: int = 10,
    backup_count: int = 5
) -> WorkflowLogger:
    """设置全局日志器"""
    global _logger
    _logger = WorkflowLogger(
        name=name,
        log_dir=log_dir,
        level=level,
        format_type=format_type,
        console_output=console_output,
        file_output=file_output,
        max_file_size_mb=max_file_size_mb,
        backup_count=backup_count
    )
    return _logger


def get_logger() -> WorkflowLogger:
    """获取全局日志器"""
    if _logger is None:
        return setup_logger()
    return _logger


if __name__ == "__main__":
    # 测试日志系统
    logger = setup_logger(
        level="DEBUG",
        format_type="detailed"
    )

    logger.info("这是一条普通信息")
    logger.debug("这是调试信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")

    # 测试带会话和迭代信息的日志
    logger.log_iteration_start(1, "session-123")
    logger.log_decision(
        1,
        "session-123",
        {"completed": False, "confidence": 0.9}
    )
    logger.log_iteration_end(1, "session-123", True, 5.5)

    # 测试异常日志
    try:
        raise ValueError("测试异常")
    except Exception as e:
        logger.exception("捕获到异常")

    print("\n✅ 日志系统测试完成！请查看 logs/ 目录")
