"""
Terminal State Manager - 终态管理器

管理任务的终态类型、部分交付和状态持久化
"""
import json
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger()


class TerminalStateType(str, Enum):
    """终态类型"""
    SUCCESS = "success"                      # 完全成功
    PARTIAL_SUCCESS = "partial_success"      # 部分成功
    FAILED = "failed"                        # 失败
    TIMEOUT = "timeout"                      # 超时
    BUDGET_EXCEEDED = "budget_exceeded"      # 预算超支
    BLOCKED = "blocked"                      # 阻塞
    CANCELLED = "cancelled"                  # 取消


@dataclass
class TerminalState:
    """任务终态"""
    mission_id: str
    state_type: TerminalStateType

    # 完成情况
    completion_ratio: float  # 0.0-1.0
    completed_steps: List[str] = field(default_factory=list)
    pending_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)

    # 部分交付
    partial_outputs: List[str] = field(default_factory=list)
    deliverables: Dict[str, Any] = field(default_factory=dict)

    # 终止原因
    termination_reason: str = ""
    error_details: Optional[str] = None

    # 资源消耗
    total_cost_usd: float = 0.0
    duration_seconds: float = 0.0

    # 时间戳
    created_at: float = field(default_factory=time.time)

    # 恢复建议
    recovery_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "mission_id": self.mission_id,
            "state_type": self.state_type.value,
            "completion_ratio": self.completion_ratio,
            "completed_steps": self.completed_steps,
            "pending_steps": self.pending_steps,
            "failed_steps": self.failed_steps,
            "partial_outputs": self.partial_outputs,
            "deliverables": self.deliverables,
            "termination_reason": self.termination_reason,
            "error_details": self.error_details,
            "total_cost_usd": self.total_cost_usd,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at,
            "iso_time": datetime.fromtimestamp(self.created_at).isoformat(),
            "recovery_suggestions": self.recovery_suggestions
        }


class TerminalStateManager:
    """终态管理器"""

    def __init__(self, storage_dir: Path):
        """
        初始化终态管理器

        Args:
            storage_dir: 终态存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 活跃任务终态
        self.active_states: Dict[str, TerminalState] = {}

        logger.info(f"TerminalStateManager initialized: {storage_dir}")

    def create_terminal_state(
        self,
        mission_id: str,
        state_type: TerminalStateType,
        completion_ratio: float,
        completed_steps: List[str],
        pending_steps: List[str],
        failed_steps: List[str],
        partial_outputs: List[str],
        deliverables: Dict[str, Any],
        termination_reason: str,
        error_details: Optional[str] = None,
        total_cost_usd: float = 0.0,
        duration_seconds: float = 0.0
    ) -> TerminalState:
        """
        创建终态

        Args:
            mission_id: 任务ID
            state_type: 终态类型
            completion_ratio: 完成度
            completed_steps: 已完成步骤
            pending_steps: 待完成步骤
            failed_steps: 失败步骤
            partial_outputs: 部分输出
            deliverables: 交付物
            termination_reason: 终止原因
            error_details: 错误详情
            total_cost_usd: 总成本
            duration_seconds: 持续时间

        Returns:
            TerminalState实例
        """
        terminal_state = TerminalState(
            mission_id=mission_id,
            state_type=state_type,
            completion_ratio=completion_ratio,
            completed_steps=completed_steps,
            pending_steps=pending_steps,
            failed_steps=failed_steps,
            partial_outputs=partial_outputs,
            deliverables=deliverables,
            termination_reason=termination_reason,
            error_details=error_details,
            total_cost_usd=total_cost_usd,
            duration_seconds=duration_seconds
        )

        # 生成恢复建议
        terminal_state.recovery_suggestions = self._generate_recovery_suggestions(
            terminal_state
        )

        # 保存
        self.active_states[mission_id] = terminal_state
        self._save_terminal_state(terminal_state)

        logger.info(
            f"Created terminal state for {mission_id}: "
            f"type={state_type.value}, completion={completion_ratio:.1%}, "
            f"cost=${total_cost_usd:.4f}"
        )

        return terminal_state

    def _generate_recovery_suggestions(
        self,
        terminal_state: TerminalState
    ) -> List[str]:
        """
        生成恢复建议

        Args:
            terminal_state: 终态

        Returns:
            恢复建议列表
        """
        suggestions = []

        if terminal_state.state_type == TerminalStateType.PARTIAL_SUCCESS:
            suggestions.append(
                f"任务部分完成 ({terminal_state.completion_ratio:.1%})，"
                f"可从检查点恢复继续执行剩余步骤"
            )

            if terminal_state.pending_steps:
                suggestions.append(
                    f"待完成步骤: {', '.join(terminal_state.pending_steps[:3])}"
                    + ("..." if len(terminal_state.pending_steps) > 3 else "")
                )

            if terminal_state.partial_outputs:
                suggestions.append(
                    f"已产出 {len(terminal_state.partial_outputs)} 个部分结果，"
                    f"可基于这些结果继续"
                )

        elif terminal_state.state_type == TerminalStateType.TIMEOUT:
            suggestions.append("任务超时，建议增加时间限制或简化任务范围")
            suggestions.append("检查是否存在性能瓶颈或死循环")

        elif terminal_state.state_type == TerminalStateType.BUDGET_EXCEEDED:
            suggestions.append("预算超支，建议增加预算或优化资源使用")
            suggestions.append(
                f"当前成本: ${terminal_state.total_cost_usd:.4f}，"
                f"可考虑使用更便宜的模型或减少调用次数"
            )

        elif terminal_state.state_type == TerminalStateType.BLOCKED:
            suggestions.append("任务被阻塞，检查依赖关系是否满足")

            if terminal_state.failed_steps:
                suggestions.append(
                    f"失败步骤: {', '.join(terminal_state.failed_steps[:3])}"
                )

        elif terminal_state.state_type == TerminalStateType.FAILED:
            suggestions.append("任务失败，检查错误日志并修复问题后重试")

            if terminal_state.error_details:
                suggestions.append(f"错误信息: {terminal_state.error_details[:100]}")

        # 通用建议
        if terminal_state.completion_ratio > 0.5:
            suggestions.append(
                "已完成超过50%，建议从检查点恢复而非重新开始"
            )

        return suggestions

    def _save_terminal_state(self, terminal_state: TerminalState):
        """保存终态到文件"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{terminal_state.mission_id}_{timestamp}.json"
        filepath = self.storage_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(terminal_state.to_dict(), f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved terminal state to {filepath}")

        except Exception as e:
            logger.error(f"Failed to save terminal state: {e}")

    def load_terminal_state(self, mission_id: str) -> Optional[TerminalState]:
        """
        加载最新的终态

        Args:
            mission_id: 任务ID

        Returns:
            TerminalState实例或None
        """
        # 先查内存
        if mission_id in self.active_states:
            return self.active_states[mission_id]

        # 查文件
        pattern = f"{mission_id}_*.json"
        files = sorted(self.storage_dir.glob(pattern), reverse=True)

        if not files:
            logger.warning(f"No terminal state found for {mission_id}")
            return None

        try:
            with open(files[0]) as f:
                data = json.load(f)

            terminal_state = TerminalState(
                mission_id=data["mission_id"],
                state_type=TerminalStateType(data["state_type"]),
                completion_ratio=data["completion_ratio"],
                completed_steps=data.get("completed_steps", []),
                pending_steps=data.get("pending_steps", []),
                failed_steps=data.get("failed_steps", []),
                partial_outputs=data.get("partial_outputs", []),
                deliverables=data.get("deliverables", {}),
                termination_reason=data.get("termination_reason", ""),
                error_details=data.get("error_details"),
                total_cost_usd=data.get("total_cost_usd", 0.0),
                duration_seconds=data.get("duration_seconds", 0.0),
                created_at=data["created_at"],
                recovery_suggestions=data.get("recovery_suggestions", [])
            )

            self.active_states[mission_id] = terminal_state

            logger.info(f"Loaded terminal state for {mission_id}")
            return terminal_state

        except Exception as e:
            logger.error(f"Failed to load terminal state: {e}")
            return None

    def get_partial_deliverables(
        self,
        mission_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取部分交付物

        Args:
            mission_id: 任务ID

        Returns:
            交付物字典或None
        """
        terminal_state = self.load_terminal_state(mission_id)
        if terminal_state is None:
            return None

        return {
            "mission_id": mission_id,
            "state_type": terminal_state.state_type.value,
            "completion_ratio": terminal_state.completion_ratio,
            "deliverables": terminal_state.deliverables,
            "partial_outputs": terminal_state.partial_outputs,
            "recovery_suggestions": terminal_state.recovery_suggestions
        }

    def list_terminal_states(
        self,
        state_type: Optional[TerminalStateType] = None
    ) -> List[TerminalState]:
        """
        列出所有终态

        Args:
            state_type: 终态类型过滤 (可选)

        Returns:
            终态列表
        """
        terminal_states = []

        for filepath in self.storage_dir.glob("*.json"):
            try:
                with open(filepath) as f:
                    data = json.load(f)

                # 应用过滤
                if state_type and data["state_type"] != state_type.value:
                    continue

                terminal_state = TerminalState(
                    mission_id=data["mission_id"],
                    state_type=TerminalStateType(data["state_type"]),
                    completion_ratio=data["completion_ratio"],
                    completed_steps=data.get("completed_steps", []),
                    pending_steps=data.get("pending_steps", []),
                    failed_steps=data.get("failed_steps", []),
                    partial_outputs=data.get("partial_outputs", []),
                    deliverables=data.get("deliverables", {}),
                    termination_reason=data.get("termination_reason", ""),
                    error_details=data.get("error_details"),
                    total_cost_usd=data.get("total_cost_usd", 0.0),
                    duration_seconds=data.get("duration_seconds", 0.0),
                    created_at=data["created_at"],
                    recovery_suggestions=data.get("recovery_suggestions", [])
                )

                terminal_states.append(terminal_state)

            except Exception as e:
                logger.warning(f"Failed to load terminal state from {filepath}: {e}")

        # 按创建时间排序
        terminal_states.sort(key=lambda s: s.created_at, reverse=True)

        logger.info(f"Found {len(terminal_states)} terminal states")
        return terminal_states

    def get_statistics(self) -> Dict:
        """获取终态统计"""
        terminal_states = self.list_terminal_states()

        total = len(terminal_states)
        if total == 0:
            return {
                "total": 0,
                "by_type": {},
                "avg_completion_ratio": 0.0,
                "total_cost_usd": 0.0
            }

        # 按类型统计
        by_type = {}
        for state in terminal_states:
            by_type[state.state_type.value] = \
                by_type.get(state.state_type.value, 0) + 1

        # 平均完成度
        avg_completion = sum(s.completion_ratio for s in terminal_states) / total

        # 总成本
        total_cost = sum(s.total_cost_usd for s in terminal_states)

        return {
            "total": total,
            "by_type": by_type,
            "avg_completion_ratio": avg_completion,
            "total_cost_usd": total_cost
        }


# 全局单例
_terminal_state_manager_instance: Optional[TerminalStateManager] = None


def get_terminal_state_manager(
    storage_dir: Path = None
) -> TerminalStateManager:
    """
    获取全局终态管理器实例

    Args:
        storage_dir: 存储目录 (仅在首次调用时使用)

    Returns:
        TerminalStateManager实例
    """
    global _terminal_state_manager_instance

    if _terminal_state_manager_instance is None:
        if storage_dir is None:
            # 默认使用项目下的terminal_states目录
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            storage_dir = project_root / "terminal_states"

        _terminal_state_manager_instance = TerminalStateManager(storage_dir)

    return _terminal_state_manager_instance
