"""
Context Module - 上下文管理

提供版本化上下文快照的创建、验证和管理功能
"""
from .versioned_context import (
    ContextSnapshot,
    VersionedContextManager,
    get_context_manager
)

__all__ = [
    "ContextSnapshot",
    "VersionedContextManager",
    "get_context_manager"
]
