"""
Terminal Module - 终态模块

提供任务终态管理、部分交付和恢复指南
"""
from .terminal_state_manager import (
    TerminalStateType,
    TerminalState,
    TerminalStateManager,
    get_terminal_state_manager
)
from .recovery_guide_generator import (
    RecoveryGuide,
    RecoveryGuideGenerator,
    get_recovery_guide_generator
)

__all__ = [
    "TerminalStateType",
    "TerminalState",
    "TerminalStateManager",
    "get_terminal_state_manager",
    "RecoveryGuide",
    "RecoveryGuideGenerator",
    "get_recovery_guide_generator"
]
