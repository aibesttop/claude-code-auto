"""
Hierarchical Budget Controller - 分层预算控制器

提供4层预算管理：Session → Mission → Role → Action
支持优先级分配、动态调整和降级策略
"""
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger()


class BudgetLevel(str, Enum):
    """预算层级"""
    SESSION = "session"
    MISSION = "mission"
    ROLE = "role"
    ACTION = "action"


@dataclass
class BudgetAllocation:
    """预算分配"""
    level: BudgetLevel
    entity_id: str  # session_id / mission_id / role_name / action_id
    parent_id: Optional[str] = None

    # 预算限制
    total_budget_usd: float = 0.0
    allocated_budget_usd: float = 0.0
    consumed_budget_usd: float = 0.0

    # 优先级 (0-10, 10最高)
    priority: int = 5

    # 时间限制
    start_time: float = field(default_factory=time.time)
    timeout_seconds: Optional[float] = None

    # 状态
    is_active: bool = True
    downgrade_triggered: bool = False

    def remaining_budget(self) -> float:
        """剩余预算"""
        return self.allocated_budget_usd - self.consumed_budget_usd

    def budget_usage_ratio(self) -> float:
        """预算使用率"""
        if self.allocated_budget_usd <= 0:
            return 0.0
        return self.consumed_budget_usd / self.allocated_budget_usd

    def is_timeout(self) -> bool:
        """是否超时"""
        if self.timeout_seconds is None:
            return False
        elapsed = time.time() - self.start_time
        return elapsed > self.timeout_seconds

    def is_budget_exceeded(self) -> bool:
        """是否超预算"""
        return self.consumed_budget_usd > self.allocated_budget_usd


class HierarchicalBudgetController:
    """分层预算控制器"""

    def __init__(self, session_budget_usd: float = 10.0):
        """
        初始化分层预算控制器

        Args:
            session_budget_usd: Session级总预算 (USD)
        """
        self.allocations: Dict[str, BudgetAllocation] = {}

        # 创建Session级预算
        self.session_id = f"session-{int(time.time())}"
        self.allocations[self.session_id] = BudgetAllocation(
            level=BudgetLevel.SESSION,
            entity_id=self.session_id,
            total_budget_usd=session_budget_usd,
            allocated_budget_usd=session_budget_usd,
            priority=10
        )

        # 降级阈值配置
        self.downgrade_thresholds = {
            "critical": 0.95,  # 95%触发紧急降级
            "warning": 0.80,   # 80%触发预警降级
            "normal": 0.60     # 60%开始监控
        }

        logger.info(
            f"HierarchicalBudgetController initialized: "
            f"session={self.session_id}, budget=${session_budget_usd}"
        )

    def allocate_mission_budget(
        self,
        mission_id: str,
        budget_usd: float,
        priority: int = 5,
        timeout_seconds: Optional[float] = None
    ) -> BudgetAllocation:
        """
        为Mission分配预算

        Args:
            mission_id: Mission ID
            budget_usd: 分配预算 (USD)
            priority: 优先级 (0-10)
            timeout_seconds: 超时时间 (秒)

        Returns:
            BudgetAllocation实例
        """
        session_alloc = self.allocations[self.session_id]

        # 检查Session预算是否足够
        if session_alloc.remaining_budget() < budget_usd:
            logger.warning(
                f"Insufficient session budget for {mission_id}: "
                f"requested ${budget_usd}, available ${session_alloc.remaining_budget():.2f}"
            )
            # 降级：分配剩余预算
            budget_usd = session_alloc.remaining_budget()

        mission_alloc = BudgetAllocation(
            level=BudgetLevel.MISSION,
            entity_id=mission_id,
            parent_id=self.session_id,
            total_budget_usd=budget_usd,
            allocated_budget_usd=budget_usd,
            priority=priority,
            timeout_seconds=timeout_seconds
        )

        self.allocations[mission_id] = mission_alloc

        # 从Session预算中扣除
        session_alloc.consumed_budget_usd += budget_usd

        logger.info(
            f"Allocated mission budget: {mission_id}, "
            f"budget=${budget_usd:.4f}, priority={priority}"
        )

        return mission_alloc

    def allocate_role_budget(
        self,
        mission_id: str,
        role_name: str,
        budget_usd: float,
        priority: int = 5
    ) -> Optional[BudgetAllocation]:
        """
        为Role分配预算

        Args:
            mission_id: Mission ID
            role_name: 角色名称
            budget_usd: 分配预算 (USD)
            priority: 优先级

        Returns:
            BudgetAllocation实例或None
        """
        if mission_id not in self.allocations:
            logger.error(f"Mission not found: {mission_id}")
            return None

        mission_alloc = self.allocations[mission_id]
        role_id = f"{mission_id}::{role_name}"

        # 检查Mission预算是否足够
        if mission_alloc.remaining_budget() < budget_usd:
            logger.warning(
                f"Insufficient mission budget for {role_id}: "
                f"requested ${budget_usd}, available ${mission_alloc.remaining_budget():.2f}"
            )
            # 降级：分配剩余预算
            budget_usd = mission_alloc.remaining_budget()

        role_alloc = BudgetAllocation(
            level=BudgetLevel.ROLE,
            entity_id=role_id,
            parent_id=mission_id,
            total_budget_usd=budget_usd,
            allocated_budget_usd=budget_usd,
            priority=priority
        )

        self.allocations[role_id] = role_alloc

        # 从Mission预算中扣除
        mission_alloc.consumed_budget_usd += budget_usd

        logger.info(
            f"Allocated role budget: {role_id}, "
            f"budget=${budget_usd:.4f}, priority={priority}"
        )

        return role_alloc

    def allocate_action_budget(
        self,
        role_id: str,
        action_name: str,
        budget_usd: float
    ) -> Optional[BudgetAllocation]:
        """
        为Action分配预算

        Args:
            role_id: Role ID (format: mission_id::role_name)
            action_name: 动作名称
            budget_usd: 分配预算 (USD)

        Returns:
            BudgetAllocation实例或None
        """
        if role_id not in self.allocations:
            logger.error(f"Role not found: {role_id}")
            return None

        role_alloc = self.allocations[role_id]
        action_id = f"{role_id}::{action_name}"

        # 检查Role预算是否足够
        if role_alloc.remaining_budget() < budget_usd:
            logger.warning(
                f"Insufficient role budget for {action_id}: "
                f"requested ${budget_usd}, available ${role_alloc.remaining_budget():.2f}"
            )
            # 降级：分配剩余预算
            budget_usd = role_alloc.remaining_budget()

        action_alloc = BudgetAllocation(
            level=BudgetLevel.ACTION,
            entity_id=action_id,
            parent_id=role_id,
            total_budget_usd=budget_usd,
            allocated_budget_usd=budget_usd,
            priority=role_alloc.priority  # 继承Role优先级
        )

        self.allocations[action_id] = action_alloc

        # 从Role预算中扣除
        role_alloc.consumed_budget_usd += budget_usd

        logger.debug(
            f"Allocated action budget: {action_id}, budget=${budget_usd:.4f}"
        )

        return action_alloc

    def consume_budget(self, entity_id: str, cost_usd: float) -> bool:
        """
        消费预算

        Args:
            entity_id: 实体ID (可以是任何层级)
            cost_usd: 消费金额 (USD)

        Returns:
            True if consumption successful
        """
        if entity_id not in self.allocations:
            logger.error(f"Entity not found: {entity_id}")
            return False

        alloc = self.allocations[entity_id]

        # 检查预算是否足够
        if alloc.remaining_budget() < cost_usd:
            logger.warning(
                f"Budget exceeded for {entity_id}: "
                f"cost=${cost_usd:.4f}, remaining=${alloc.remaining_budget():.4f}"
            )
            # 触发降级
            self._trigger_downgrade(entity_id)
            return False

        # 消费预算
        alloc.consumed_budget_usd += cost_usd

        # 检查是否需要降级
        usage_ratio = alloc.budget_usage_ratio()
        if usage_ratio >= self.downgrade_thresholds["critical"]:
            self._trigger_downgrade(entity_id, level="critical")
        elif usage_ratio >= self.downgrade_thresholds["warning"]:
            self._trigger_downgrade(entity_id, level="warning")

        logger.debug(
            f"Consumed budget: {entity_id}, cost=${cost_usd:.4f}, "
            f"remaining=${alloc.remaining_budget():.4f}, "
            f"usage={usage_ratio:.1%}"
        )

        return True

    def _trigger_downgrade(self, entity_id: str, level: str = "critical"):
        """
        触发降级策略

        Args:
            entity_id: 实体ID
            level: 降级级别 (warning / critical)
        """
        alloc = self.allocations[entity_id]

        if alloc.downgrade_triggered:
            return  # 已触发过降级

        alloc.downgrade_triggered = True

        logger.warning(
            f"Budget downgrade triggered for {entity_id}: "
            f"level={level}, usage={alloc.budget_usage_ratio():.1%}"
        )

        # 降级策略
        if level == "critical":
            # 紧急降级：停止分配新预算
            alloc.is_active = False
            logger.warning(f"Entity {entity_id} deactivated due to budget exhaustion")
        elif level == "warning":
            # 预警降级：降低优先级，减少预算分配
            alloc.priority = max(0, alloc.priority - 2)
            logger.info(f"Entity {entity_id} priority lowered to {alloc.priority}")

    def get_budget_status(self, entity_id: str) -> Optional[Dict]:
        """
        获取预算状态

        Args:
            entity_id: 实体ID

        Returns:
            预算状态字典或None
        """
        if entity_id not in self.allocations:
            return None

        alloc = self.allocations[entity_id]

        return {
            "entity_id": entity_id,
            "level": alloc.level.value,
            "allocated": alloc.allocated_budget_usd,
            "consumed": alloc.consumed_budget_usd,
            "remaining": alloc.remaining_budget(),
            "usage_ratio": alloc.budget_usage_ratio(),
            "priority": alloc.priority,
            "is_active": alloc.is_active,
            "is_timeout": alloc.is_timeout(),
            "downgrade_triggered": alloc.downgrade_triggered
        }

    def get_session_summary(self) -> Dict:
        """
        获取Session级别预算汇总

        Returns:
            预算汇总字典
        """
        session_alloc = self.allocations[self.session_id]

        # 统计各层级分配
        mission_count = sum(
            1 for a in self.allocations.values()
            if a.level == BudgetLevel.MISSION
        )
        role_count = sum(
            1 for a in self.allocations.values()
            if a.level == BudgetLevel.ROLE
        )
        action_count = sum(
            1 for a in self.allocations.values()
            if a.level == BudgetLevel.ACTION
        )

        return {
            "session_id": self.session_id,
            "total_budget": session_alloc.total_budget_usd,
            "consumed": session_alloc.consumed_budget_usd,
            "remaining": session_alloc.remaining_budget(),
            "usage_ratio": session_alloc.budget_usage_ratio(),
            "mission_count": mission_count,
            "role_count": role_count,
            "action_count": action_count,
            "allocations_total": len(self.allocations)
        }

    def reallocate_by_priority(self, available_budget: float) -> List[str]:
        """
        根据优先级重新分配预算

        用于预算不足时的动态调整

        Args:
            available_budget: 可用预算

        Returns:
            受影响的entity_id列表
        """
        # 获取所有活跃的Mission级分配，按优先级排序
        missions = [
            (entity_id, alloc)
            for entity_id, alloc in self.allocations.items()
            if alloc.level == BudgetLevel.MISSION and alloc.is_active
        ]
        missions.sort(key=lambda x: x[1].priority, reverse=True)

        reallocated = []
        remaining = available_budget

        for entity_id, alloc in missions:
            if remaining <= 0:
                # 预算耗尽，停用低优先级任务
                alloc.is_active = False
                reallocated.append(entity_id)
                logger.warning(
                    f"Mission {entity_id} deactivated due to budget reallocation"
                )
            else:
                # 按优先级分配
                min_budget = alloc.total_budget_usd * 0.3  # 至少30%
                allocated = min(remaining, alloc.total_budget_usd)
                allocated = max(allocated, min_budget)

                alloc.allocated_budget_usd = allocated
                remaining -= allocated
                reallocated.append(entity_id)

        logger.info(
            f"Budget reallocation completed: {len(reallocated)} missions affected"
        )

        return reallocated


# 全局单例
_budget_controller_instance: Optional[HierarchicalBudgetController] = None


def get_budget_controller(
    session_budget_usd: float = None
) -> HierarchicalBudgetController:
    """
    获取全局预算控制器实例

    Args:
        session_budget_usd: Session预算 (仅在首次调用时使用)

    Returns:
        HierarchicalBudgetController实例
    """
    global _budget_controller_instance

    if _budget_controller_instance is None:
        if session_budget_usd is None:
            session_budget_usd = 10.0  # 默认$10

        _budget_controller_instance = HierarchicalBudgetController(
            session_budget_usd=session_budget_usd
        )

    return _budget_controller_instance
