"""
Helper Governor - 辅助角色治理器

管理辅助角色的生命周期、退出条件和资源使用
"""
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable

from src.utils.logger import get_logger

logger = get_logger()


class ExitConditionType(str, Enum):
    """退出条件类型"""
    MAX_ITERATIONS = "max_iterations"  # 最大迭代次数
    MAX_COST = "max_cost"              # 最大成本
    MAX_DURATION = "max_duration"      # 最大持续时间
    NO_PROGRESS = "no_progress"        # 无进展
    GOAL_ACHIEVED = "goal_achieved"    # 目标达成
    ERROR_THRESHOLD = "error_threshold" # 错误阈值


@dataclass
class HelperExitCondition:
    """辅助角色退出条件"""
    condition_type: ExitConditionType
    threshold: float
    description: str = ""

    # 当前值
    current_value: float = 0.0

    def is_triggered(self) -> bool:
        """是否触发退出条件"""
        return self.current_value >= self.threshold

    def update(self, value: float):
        """更新当前值"""
        self.current_value = value

    def increment(self, delta: float = 1.0):
        """增量更新"""
        self.current_value += delta

    def progress_ratio(self) -> float:
        """进度比例"""
        if self.threshold == 0:
            return 0.0
        return min(1.0, self.current_value / self.threshold)


@dataclass
class HelperRoleState:
    """辅助角色状态"""
    role_name: str
    mission_id: str

    # 生命周期
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    is_active: bool = True

    # 执行统计
    iterations: int = 0
    successful_iterations: int = 0
    failed_iterations: int = 0
    total_cost_usd: float = 0.0

    # 进展跟踪
    last_progress_time: float = field(default_factory=time.time)
    progress_indicator: float = 0.0  # 0.0-1.0

    # 退出条件
    exit_conditions: List[HelperExitCondition] = field(default_factory=list)

    # 退出原因
    exit_reason: Optional[str] = None

    def duration_seconds(self) -> float:
        """持续时间"""
        end = self.end_time or time.time()
        return end - self.start_time

    def time_since_progress(self) -> float:
        """距离上次进展的时间"""
        return time.time() - self.last_progress_time

    def success_rate(self) -> float:
        """成功率"""
        if self.iterations == 0:
            return 0.0
        return self.successful_iterations / self.iterations

    def check_exit_conditions(self) -> Optional[HelperExitCondition]:
        """
        检查退出条件

        Returns:
            触发的退出条件或None
        """
        for condition in self.exit_conditions:
            if condition.is_triggered():
                return condition
        return None


class HelperGovernor:
    """辅助角色治理器"""

    def __init__(self):
        """初始化治理器"""
        # 活跃的辅助角色
        self.active_helpers: Dict[str, HelperRoleState] = {}

        # 已退出的辅助角色
        self.exited_helpers: List[HelperRoleState] = []

        # 默认退出条件配置
        self.default_exit_conditions = {
            "Debugger": [
                HelperExitCondition(
                    ExitConditionType.MAX_ITERATIONS,
                    threshold=10,
                    description="最多10次调试尝试"
                ),
                HelperExitCondition(
                    ExitConditionType.MAX_COST,
                    threshold=0.5,
                    description="最多花费$0.5"
                ),
                HelperExitCondition(
                    ExitConditionType.NO_PROGRESS,
                    threshold=300,  # 5分钟无进展
                    description="5分钟无进展自动退出"
                )
            ],
            "Reviewer": [
                HelperExitCondition(
                    ExitConditionType.MAX_ITERATIONS,
                    threshold=3,
                    description="最多3轮审查"
                ),
                HelperExitCondition(
                    ExitConditionType.GOAL_ACHIEVED,
                    threshold=1.0,
                    description="审查目标达成"
                )
            ],
            "SecurityExpert": [
                HelperExitCondition(
                    ExitConditionType.MAX_ITERATIONS,
                    threshold=5,
                    description="最多5轮安全扫描"
                ),
                HelperExitCondition(
                    ExitConditionType.MAX_COST,
                    threshold=0.3,
                    description="最多花费$0.3"
                )
            ],
            "PerfAnalyzer": [
                HelperExitCondition(
                    ExitConditionType.MAX_ITERATIONS,
                    threshold=8,
                    description="最多8次性能分析"
                ),
                HelperExitCondition(
                    ExitConditionType.MAX_DURATION,
                    threshold=600,  # 10分钟
                    description="最多运行10分钟"
                )
            ]
        }

        logger.info("HelperGovernor initialized")

    def register_helper(
        self,
        role_name: str,
        mission_id: str,
        custom_exit_conditions: Optional[List[HelperExitCondition]] = None
    ) -> str:
        """
        注册辅助角色

        Args:
            role_name: 角色名称
            mission_id: 任务ID
            custom_exit_conditions: 自定义退出条件 (可选)

        Returns:
            helper_id
        """
        helper_id = f"{role_name}::{mission_id}"

        # 获取退出条件
        if custom_exit_conditions:
            exit_conditions = custom_exit_conditions
        else:
            # 使用默认条件 (深拷贝)
            exit_conditions = []
            if role_name in self.default_exit_conditions:
                for cond in self.default_exit_conditions[role_name]:
                    exit_conditions.append(
                        HelperExitCondition(
                            condition_type=cond.condition_type,
                            threshold=cond.threshold,
                            description=cond.description
                        )
                    )

        state = HelperRoleState(
            role_name=role_name,
            mission_id=mission_id,
            exit_conditions=exit_conditions
        )

        self.active_helpers[helper_id] = state

        logger.info(
            f"Registered helper: {helper_id}, "
            f"exit_conditions={len(exit_conditions)}"
        )

        return helper_id

    def record_iteration(
        self,
        helper_id: str,
        success: bool,
        cost_usd: float = 0.0,
        progress_delta: float = 0.0
    ):
        """
        记录迭代

        Args:
            helper_id: Helper ID
            success: 是否成功
            cost_usd: 成本
            progress_delta: 进展增量
        """
        if helper_id not in self.active_helpers:
            logger.warning(f"Helper not found: {helper_id}")
            return

        state = self.active_helpers[helper_id]

        # 更新统计
        state.iterations += 1
        if success:
            state.successful_iterations += 1
        else:
            state.failed_iterations += 1

        state.total_cost_usd += cost_usd

        # 更新进展
        if progress_delta > 0:
            state.progress_indicator = min(1.0, state.progress_indicator + progress_delta)
            state.last_progress_time = time.time()

        # 更新退出条件
        for condition in state.exit_conditions:
            if condition.condition_type == ExitConditionType.MAX_ITERATIONS:
                condition.update(state.iterations)
            elif condition.condition_type == ExitConditionType.MAX_COST:
                condition.update(state.total_cost_usd)
            elif condition.condition_type == ExitConditionType.MAX_DURATION:
                condition.update(state.duration_seconds())
            elif condition.condition_type == ExitConditionType.NO_PROGRESS:
                condition.update(state.time_since_progress())
            elif condition.condition_type == ExitConditionType.GOAL_ACHIEVED:
                condition.update(state.progress_indicator)
            elif condition.condition_type == ExitConditionType.ERROR_THRESHOLD:
                error_rate = 1.0 - state.success_rate()
                condition.update(error_rate)

        logger.debug(
            f"Recorded iteration for {helper_id}: "
            f"iteration={state.iterations}, success={success}, "
            f"cost=${cost_usd:.4f}, progress={state.progress_indicator:.1%}"
        )

    def should_exit(self, helper_id: str) -> tuple[bool, Optional[str]]:
        """
        检查是否应该退出

        Args:
            helper_id: Helper ID

        Returns:
            (should_exit, reason) tuple
        """
        if helper_id not in self.active_helpers:
            return False, None

        state = self.active_helpers[helper_id]

        # 检查退出条件
        triggered_condition = state.check_exit_conditions()
        if triggered_condition:
            reason = (
                f"{triggered_condition.condition_type.value}: "
                f"{triggered_condition.description} "
                f"(current={triggered_condition.current_value:.1f}, "
                f"threshold={triggered_condition.threshold:.1f})"
            )
            return True, reason

        return False, None

    def exit_helper(
        self,
        helper_id: str,
        reason: Optional[str] = None
    ):
        """
        退出辅助角色

        Args:
            helper_id: Helper ID
            reason: 退出原因
        """
        if helper_id not in self.active_helpers:
            logger.warning(f"Helper not found: {helper_id}")
            return

        state = self.active_helpers.pop(helper_id)
        state.is_active = False
        state.end_time = time.time()
        state.exit_reason = reason or "Manual exit"

        self.exited_helpers.append(state)

        logger.info(
            f"Exited helper: {helper_id}, reason={state.exit_reason}, "
            f"iterations={state.iterations}, duration={state.duration_seconds():.1f}s, "
            f"cost=${state.total_cost_usd:.4f}"
        )

    def get_helper_status(self, helper_id: str) -> Optional[Dict]:
        """
        获取辅助角色状态

        Args:
            helper_id: Helper ID

        Returns:
            状态字典或None
        """
        if helper_id not in self.active_helpers:
            return None

        state = self.active_helpers[helper_id]

        # 检查是否应该退出
        should_exit, exit_reason = self.should_exit(helper_id)

        return {
            "helper_id": helper_id,
            "role_name": state.role_name,
            "mission_id": state.mission_id,
            "is_active": state.is_active,
            "iterations": state.iterations,
            "successful_iterations": state.successful_iterations,
            "failed_iterations": state.failed_iterations,
            "success_rate": state.success_rate(),
            "total_cost_usd": state.total_cost_usd,
            "duration_seconds": state.duration_seconds(),
            "progress_indicator": state.progress_indicator,
            "time_since_progress": state.time_since_progress(),
            "should_exit": should_exit,
            "exit_reason": exit_reason,
            "exit_conditions": [
                {
                    "type": cond.condition_type.value,
                    "threshold": cond.threshold,
                    "current": cond.current_value,
                    "progress": cond.progress_ratio(),
                    "triggered": cond.is_triggered()
                }
                for cond in state.exit_conditions
            ]
        }

    def list_active_helpers(self) -> List[str]:
        """列出活跃的辅助角色"""
        return list(self.active_helpers.keys())

    def get_summary(self) -> Dict:
        """获取治理摘要"""
        total_active = len(self.active_helpers)
        total_exited = len(self.exited_helpers)

        # 统计退出原因
        exit_reasons = {}
        for state in self.exited_helpers:
            if state.exit_reason:
                exit_reasons[state.exit_reason] = \
                    exit_reasons.get(state.exit_reason, 0) + 1

        return {
            "active_helpers": total_active,
            "exited_helpers": total_exited,
            "total_helpers": total_active + total_exited,
            "exit_reasons": exit_reasons
        }


# 全局单例
_helper_governor_instance: Optional[HelperGovernor] = None


def get_helper_governor() -> HelperGovernor:
    """获取全局辅助角色治理器实例"""
    global _helper_governor_instance
    if _helper_governor_instance is None:
        _helper_governor_instance = HelperGovernor()
    return _helper_governor_instance
