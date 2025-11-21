"""
Unified logging with optional structured output and helpers.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional
from datetime import datetime
import json


class JsonFormatter(logging.Formatter):
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
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'iteration'):
            log_data['iteration'] = record.iteration
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data, ensure_ascii=False)


class DetailedFormatter(logging.Formatter):
    def __init__(self):
        fmt = (
            '%(asctime)s | %(levelname)-8s | '
            '[%(name)s:%(funcName)s:%(lineno)d] | '
            '%(message)s'
        )
        super().__init__(fmt=fmt, datefmt='%Y-%m-%d %H:%M:%S')

    def format(self, record: logging.LogRecord) -> str:
        original_msg = record.msg
        extra_info = []
        if hasattr(record, 'session_id') and record.session_id:
            extra_info.append(f"Session:{record.session_id[:8]}")
        if hasattr(record, 'iteration') and record.iteration:
            extra_info.append(f"Iter:{record.iteration}")
        if extra_info:
            record.msg = f"[{' | '.join(extra_info)}] {original_msg}"
        result = super().format(record)
        record.msg = original_msg
        return result


class SimpleFormatter(logging.Formatter):
    def __init__(self):
        fmt = '%(asctime)s - %(levelname)s - %(message)s'
        super().__init__(fmt=fmt, datefmt='%H:%M:%S')


class WorkflowLogger:
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
        self.logger.handlers.clear()
        self.logger.propagate = False

        if format_type == "json":
            formatter = JsonFormatter()
        elif format_type == "simple":
            formatter = SimpleFormatter()
        else:
            formatter = DetailedFormatter()

        if console_output:
            # Configure stdout for UTF-8 encoding to support emojis on Windows
            if hasattr(sys.stdout, 'reconfigure'):
                try:
                    sys.stdout.reconfigure(encoding='utf-8')
                except Exception:
                    pass  # Fallback if reconfigure fails
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        if file_output:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_file = self.log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

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
        return self.logger

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, extra=kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra=kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, extra=kwargs)

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra=kwargs)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, extra=kwargs)

    def exception(self, msg: str, **kwargs):
        self.logger.exception(msg, extra=kwargs)

    def log_iteration_start(self, iteration: int, session_id: str):
        self.info("Iteration start", session_id=session_id, iteration=iteration)

    def log_iteration_end(
        self,
        iteration: int,
        session_id: str,
        success: bool,
        duration: float
    ):
        status = "success" if success else "failure"
        self.info(
            f"Iteration end: {status}, duration={duration:.2f}s",
            session_id=session_id,
            iteration=iteration
        )

    def log_decision(
        self,
        iteration: int,
        session_id: str,
        decision: dict
    ):
        completed = decision.get('completed', False)
        confidence = decision.get('confidence', 'N/A')
        self.info(
            f"Decision: completed={completed}, confidence={confidence}",
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
        self.warning(
            f"Iteration failed ({type(error).__name__}: {error}) retry {retry_count}/{max_retries}",
            session_id=session_id,
            iteration=iteration
        )

    def log_event(self, event: str, data: dict = None, **kwargs):
        payload = data or {}
        self.info(f"EVENT {event} | {payload}", **kwargs)

    def log_cost(self, iteration: int, session_id: str, duration: float, cost: float = None):
        msg = f"Iteration cost: duration={duration:.2f}s"
        if cost is not None:
            msg += f", cost={cost:.4f}"
        self.info(msg, session_id=session_id, iteration=iteration)


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
    if _logger is None:
        return setup_logger()
    return _logger


if __name__ == "__main__":
    logger = setup_logger(level="DEBUG", format_type="detailed")
    logger.info("Logger smoke test")
    logger.log_event("sample", {"hello": "world"})
    logger.log_cost(1, "session-123", 1.23, cost=0.001)
