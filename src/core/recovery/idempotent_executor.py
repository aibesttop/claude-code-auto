"""
Idempotent Executor - 幂等执行器

基于执行哈希的幂等性保证，避免重复执行相同操作
"""
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class ExecutionRecord:
    """执行记录"""
    execution_hash: str
    operation_name: str
    input_data: dict
    output_data: Optional[dict] = None

    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_seconds: Optional[float] = None

    status: str = "pending"  # pending, running, completed, failed
    error: Optional[str] = None

    # 元数据
    mission_id: Optional[str] = None
    role_name: Optional[str] = None
    retry_count: int = 0

    def finish(self, status: str, output_data: Optional[dict] = None, error: Optional[str] = None):
        """完成执行"""
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.status = status
        self.output_data = output_data
        self.error = error

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "execution_hash": self.execution_hash,
            "operation_name": self.operation_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "error": self.error,
            "mission_id": self.mission_id,
            "role_name": self.role_name,
            "retry_count": self.retry_count
        }


class IdempotentExecutor:
    """幂等执行器"""

    def __init__(self, storage_dir: Path):
        """
        初始化幂等执行器

        Args:
            storage_dir: 执行记录存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self.execution_cache: Dict[str, ExecutionRecord] = {}

        # 加载已有记录
        self._load_records()

        logger.info(
            f"IdempotentExecutor initialized: {storage_dir}, "
            f"loaded {len(self.execution_cache)} records"
        )

    def _load_records(self):
        """加载已有执行记录"""
        for record_file in self.storage_dir.glob("*.json"):
            try:
                with open(record_file) as f:
                    data = json.load(f)

                record = ExecutionRecord(
                    execution_hash=data["execution_hash"],
                    operation_name=data["operation_name"],
                    input_data=data["input_data"],
                    output_data=data.get("output_data"),
                    start_time=data["start_time"],
                    end_time=data.get("end_time"),
                    duration_seconds=data.get("duration_seconds"),
                    status=data["status"],
                    error=data.get("error"),
                    mission_id=data.get("mission_id"),
                    role_name=data.get("role_name"),
                    retry_count=data.get("retry_count", 0)
                )

                self.execution_cache[record.execution_hash] = record

            except Exception as e:
                logger.warning(f"Failed to load execution record {record_file}: {e}")

    def compute_hash(self, operation_name: str, input_data: dict) -> str:
        """
        计算执行哈希

        Args:
            operation_name: 操作名称
            input_data: 输入数据

        Returns:
            执行哈希 (SHA256)
        """
        # 确保输入数据可序列化且顺序一致
        input_json = json.dumps(
            {
                "operation": operation_name,
                "input": input_data
            },
            sort_keys=True,
            ensure_ascii=False
        )

        hash_value = hashlib.sha256(input_json.encode()).hexdigest()
        return f"exec-{hash_value[:16]}"

    def execute(
        self,
        operation_name: str,
        func: Callable,
        input_data: dict,
        force_rerun: bool = False,
        mission_id: Optional[str] = None,
        role_name: Optional[str] = None,
        **kwargs
    ) -> tuple[bool, Optional[dict]]:
        """
        幂等执行函数

        Args:
            operation_name: 操作名称
            func: 要执行的函数
            input_data: 输入数据
            force_rerun: 强制重新执行
            mission_id: Mission ID
            role_name: 角色名称
            **kwargs: 函数参数

        Returns:
            (success, output_data) tuple
        """
        # 计算执行哈希
        exec_hash = self.compute_hash(operation_name, input_data)

        # 检查是否已执行
        if exec_hash in self.execution_cache and not force_rerun:
            existing_record = self.execution_cache[exec_hash]

            if existing_record.status == "completed":
                logger.info(
                    f"Idempotent execution: {operation_name} already completed, "
                    f"returning cached result (hash={exec_hash[:8]})"
                )
                return True, existing_record.output_data

            elif existing_record.status == "failed":
                logger.warning(
                    f"Idempotent execution: {operation_name} previously failed, "
                    f"retrying (hash={exec_hash[:8]})"
                )
                existing_record.retry_count += 1

        # 创建执行记录
        record = ExecutionRecord(
            execution_hash=exec_hash,
            operation_name=operation_name,
            input_data=input_data,
            mission_id=mission_id,
            role_name=role_name,
            status="running"
        )

        self.execution_cache[exec_hash] = record
        self._save_record(record)

        logger.info(
            f"Starting idempotent execution: {operation_name} (hash={exec_hash[:8]})"
        )

        # 执行函数
        try:
            output_data = func(**kwargs)
            record.finish(status="completed", output_data=output_data)

            logger.info(
                f"Idempotent execution completed: {operation_name}, "
                f"duration={record.duration_seconds:.2f}s"
            )

            self._save_record(record)
            return True, output_data

        except Exception as e:
            error_msg = str(e)
            record.finish(status="failed", error=error_msg)

            logger.error(
                f"Idempotent execution failed: {operation_name}, error={error_msg}"
            )

            self._save_record(record)
            return False, None

    def _save_record(self, record: ExecutionRecord):
        """保存执行记录到文件"""
        record_file = self.storage_dir / f"{record.execution_hash}.json"

        try:
            with open(record_file, 'w') as f:
                json.dump(record.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save execution record: {e}")

    def get_record(self, execution_hash: str) -> Optional[ExecutionRecord]:
        """获取执行记录"""
        return self.execution_cache.get(execution_hash)

    def list_records(
        self,
        operation_name: Optional[str] = None,
        status: Optional[str] = None,
        mission_id: Optional[str] = None
    ) -> list:
        """
        列出执行记录

        Args:
            operation_name: 操作名称过滤
            status: 状态过滤
            mission_id: Mission ID过滤

        Returns:
            执行记录列表
        """
        records = list(self.execution_cache.values())

        # 应用过滤
        if operation_name:
            records = [r for r in records if r.operation_name == operation_name]
        if status:
            records = [r for r in records if r.status == status]
        if mission_id:
            records = [r for r in records if r.mission_id == mission_id]

        return records

    def get_stats(self) -> dict:
        """获取统计信息"""
        records = list(self.execution_cache.values())

        total = len(records)
        completed = sum(1 for r in records if r.status == "completed")
        failed = sum(1 for r in records if r.status == "failed")
        running = sum(1 for r in records if r.status == "running")

        return {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "running": running,
            "success_rate": completed / total if total > 0 else 0.0
        }

    def clear_failed(self):
        """清除失败的执行记录"""
        failed_hashes = [
            h for h, r in self.execution_cache.items()
            if r.status == "failed"
        ]

        for exec_hash in failed_hashes:
            del self.execution_cache[exec_hash]

            # 删除文件
            record_file = self.storage_dir / f"{exec_hash}.json"
            if record_file.exists():
                record_file.unlink()

        logger.info(f"Cleared {len(failed_hashes)} failed execution records")


# 全局单例
_idempotent_executor_instance: Optional[IdempotentExecutor] = None


def get_idempotent_executor(storage_dir: Path = None) -> IdempotentExecutor:
    """
    获取全局幂等执行器实例

    Args:
        storage_dir: 存储目录 (仅在首次调用时使用)

    Returns:
        IdempotentExecutor实例
    """
    global _idempotent_executor_instance

    if _idempotent_executor_instance is None:
        if storage_dir is None:
            # 默认使用项目下的executions目录
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            storage_dir = project_root / "executions"

        _idempotent_executor_instance = IdempotentExecutor(storage_dir)

    return _idempotent_executor_instance
