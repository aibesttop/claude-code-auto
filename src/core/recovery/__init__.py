"""
Recovery Module - 恢复机制模块

提供幂等执行、检查点管理和故障恢复功能
"""
from .idempotent_executor import (
    ExecutionRecord,
    IdempotentExecutor,
    get_idempotent_executor
)
from .checkpoint_manager import (
    Checkpoint,
    CheckpointManager,
    get_checkpoint_manager
)

__all__ = [
    "ExecutionRecord",
    "IdempotentExecutor",
    "get_idempotent_executor",
    "Checkpoint",
    "CheckpointManager",
    "get_checkpoint_manager"
]
