"""
Checkpoint Manager - 检查点管理器

提供任务执行的检查点保存和恢复功能
"""
import json
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class Checkpoint:
    """执行检查点"""
    checkpoint_id: str
    mission_id: str
    role_name: Optional[str] = None

    # 检查点时间
    created_at: float = field(default_factory=time.time)

    # 执行状态
    completed_steps: List[str] = field(default_factory=list)
    current_step: Optional[str] = None
    remaining_steps: List[str] = field(default_factory=list)

    # 状态数据
    state_data: Dict[str, Any] = field(default_factory=dict)

    # 输出累积
    accumulated_outputs: List[str] = field(default_factory=list)

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "checkpoint_id": self.checkpoint_id,
            "mission_id": self.mission_id,
            "role_name": self.role_name,
            "created_at": self.created_at,
            "iso_time": datetime.fromtimestamp(self.created_at).isoformat(),
            "completed_steps": self.completed_steps,
            "current_step": self.current_step,
            "remaining_steps": self.remaining_steps,
            "state_data": self.state_data,
            "accumulated_outputs": self.accumulated_outputs,
            "metadata": self.metadata
        }


class CheckpointManager:
    """检查点管理器"""

    def __init__(self, checkpoint_dir: Path):
        """
        初始化检查点管理器

        Args:
            checkpoint_dir: 检查点存储目录
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # 当前活跃检查点
        self.active_checkpoints: Dict[str, Checkpoint] = {}

        logger.info(f"CheckpointManager initialized: {checkpoint_dir}")

    def create_checkpoint(
        self,
        mission_id: str,
        role_name: Optional[str] = None,
        completed_steps: List[str] = None,
        current_step: Optional[str] = None,
        remaining_steps: List[str] = None,
        state_data: Dict[str, Any] = None,
        accumulated_outputs: List[str] = None,
        **metadata
    ) -> Checkpoint:
        """
        创建检查点

        Args:
            mission_id: Mission ID
            role_name: 角色名称
            completed_steps: 已完成步骤
            current_step: 当前步骤
            remaining_steps: 剩余步骤
            state_data: 状态数据
            accumulated_outputs: 累积输出
            **metadata: 元数据

        Returns:
            Checkpoint实例
        """
        checkpoint_id = f"ckpt-{mission_id}-{int(time.time())}"

        checkpoint = Checkpoint(
            checkpoint_id=checkpoint_id,
            mission_id=mission_id,
            role_name=role_name,
            completed_steps=completed_steps or [],
            current_step=current_step,
            remaining_steps=remaining_steps or [],
            state_data=state_data or {},
            accumulated_outputs=accumulated_outputs or [],
            metadata=metadata
        )

        # 保存到内存和磁盘
        self.active_checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint(checkpoint)

        logger.info(
            f"Created checkpoint: {checkpoint_id}, "
            f"mission={mission_id}, role={role_name}, "
            f"completed_steps={len(checkpoint.completed_steps)}"
        )

        return checkpoint

    def update_checkpoint(
        self,
        checkpoint_id: str,
        completed_steps: Optional[List[str]] = None,
        current_step: Optional[str] = None,
        remaining_steps: Optional[List[str]] = None,
        state_data: Optional[Dict[str, Any]] = None,
        accumulated_outputs: Optional[List[str]] = None
    ) -> bool:
        """
        更新检查点

        Args:
            checkpoint_id: 检查点ID
            completed_steps: 已完成步骤 (可选)
            current_step: 当前步骤 (可选)
            remaining_steps: 剩余步骤 (可选)
            state_data: 状态数据 (可选)
            accumulated_outputs: 累积输出 (可选)

        Returns:
            True if update successful
        """
        if checkpoint_id not in self.active_checkpoints:
            logger.warning(f"Checkpoint not found: {checkpoint_id}")
            return False

        checkpoint = self.active_checkpoints[checkpoint_id]

        # 更新字段
        if completed_steps is not None:
            checkpoint.completed_steps = completed_steps
        if current_step is not None:
            checkpoint.current_step = current_step
        if remaining_steps is not None:
            checkpoint.remaining_steps = remaining_steps
        if state_data is not None:
            checkpoint.state_data.update(state_data)
        if accumulated_outputs is not None:
            checkpoint.accumulated_outputs = accumulated_outputs

        # 保存到磁盘
        self._save_checkpoint(checkpoint)

        logger.debug(f"Updated checkpoint: {checkpoint_id}")
        return True

    def add_completed_step(
        self,
        checkpoint_id: str,
        step_name: str,
        step_output: Optional[str] = None
    ) -> bool:
        """
        添加已完成步骤

        Args:
            checkpoint_id: 检查点ID
            step_name: 步骤名称
            step_output: 步骤输出 (可选)

        Returns:
            True if successful
        """
        if checkpoint_id not in self.active_checkpoints:
            return False

        checkpoint = self.active_checkpoints[checkpoint_id]

        # 添加到已完成步骤
        if step_name not in checkpoint.completed_steps:
            checkpoint.completed_steps.append(step_name)

        # 从剩余步骤中移除
        if step_name in checkpoint.remaining_steps:
            checkpoint.remaining_steps.remove(step_name)

        # 添加输出
        if step_output:
            checkpoint.accumulated_outputs.append(step_output)

        self._save_checkpoint(checkpoint)

        logger.debug(
            f"Added completed step to checkpoint {checkpoint_id}: {step_name}"
        )
        return True

    def load_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """
        加载检查点

        Args:
            checkpoint_id: 检查点ID

        Returns:
            Checkpoint实例或None
        """
        # 先查内存
        if checkpoint_id in self.active_checkpoints:
            return self.active_checkpoints[checkpoint_id]

        # 查磁盘
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        if not checkpoint_file.exists():
            logger.warning(f"Checkpoint file not found: {checkpoint_id}")
            return None

        try:
            with open(checkpoint_file) as f:
                data = json.load(f)

            checkpoint = Checkpoint(
                checkpoint_id=data["checkpoint_id"],
                mission_id=data["mission_id"],
                role_name=data.get("role_name"),
                created_at=data["created_at"],
                completed_steps=data.get("completed_steps", []),
                current_step=data.get("current_step"),
                remaining_steps=data.get("remaining_steps", []),
                state_data=data.get("state_data", {}),
                accumulated_outputs=data.get("accumulated_outputs", []),
                metadata=data.get("metadata", {})
            )

            self.active_checkpoints[checkpoint_id] = checkpoint

            logger.info(f"Loaded checkpoint: {checkpoint_id}")
            return checkpoint

        except Exception as e:
            logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            return None

    def _save_checkpoint(self, checkpoint: Checkpoint):
        """保存检查点到文件"""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint.checkpoint_id}.json"

        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def resume_from_checkpoint(
        self,
        checkpoint_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        从检查点恢复

        Args:
            checkpoint_id: 检查点ID

        Returns:
            恢复上下文字典或None
        """
        checkpoint = self.load_checkpoint(checkpoint_id)
        if checkpoint is None:
            return None

        logger.info(
            f"Resuming from checkpoint: {checkpoint_id}, "
            f"completed_steps={len(checkpoint.completed_steps)}, "
            f"remaining_steps={len(checkpoint.remaining_steps)}"
        )

        # 构建恢复上下文
        resume_context = {
            "checkpoint_id": checkpoint.checkpoint_id,
            "mission_id": checkpoint.mission_id,
            "role_name": checkpoint.role_name,
            "completed_steps": checkpoint.completed_steps,
            "current_step": checkpoint.current_step,
            "remaining_steps": checkpoint.remaining_steps,
            "state_data": checkpoint.state_data,
            "accumulated_outputs": checkpoint.accumulated_outputs,
            "metadata": checkpoint.metadata
        }

        return resume_context

    def list_checkpoints(
        self,
        mission_id: Optional[str] = None,
        role_name: Optional[str] = None
    ) -> List[Checkpoint]:
        """
        列出检查点

        Args:
            mission_id: Mission ID过滤
            role_name: 角色名称过滤

        Returns:
            检查点列表
        """
        checkpoints = []

        # 扫描检查点文件
        for checkpoint_file in self.checkpoint_dir.glob("ckpt-*.json"):
            try:
                with open(checkpoint_file) as f:
                    data = json.load(f)

                # 应用过滤
                if mission_id and data.get("mission_id") != mission_id:
                    continue
                if role_name and data.get("role_name") != role_name:
                    continue

                checkpoint = Checkpoint(
                    checkpoint_id=data["checkpoint_id"],
                    mission_id=data["mission_id"],
                    role_name=data.get("role_name"),
                    created_at=data["created_at"],
                    completed_steps=data.get("completed_steps", []),
                    current_step=data.get("current_step"),
                    remaining_steps=data.get("remaining_steps", []),
                    state_data=data.get("state_data", {}),
                    accumulated_outputs=data.get("accumulated_outputs", []),
                    metadata=data.get("metadata", {})
                )

                checkpoints.append(checkpoint)

            except Exception as e:
                logger.warning(f"Failed to load checkpoint file {checkpoint_file}: {e}")

        # 按创建时间排序
        checkpoints.sort(key=lambda c: c.created_at, reverse=True)

        logger.info(f"Found {len(checkpoints)} checkpoints")
        return checkpoints

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        删除检查点

        Args:
            checkpoint_id: 检查点ID

        Returns:
            True if deletion successful
        """
        # 从内存移除
        if checkpoint_id in self.active_checkpoints:
            del self.active_checkpoints[checkpoint_id]

        # 删除文件
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_id}.json"
        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                logger.info(f"Deleted checkpoint: {checkpoint_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete checkpoint file: {e}")
                return False

        return False

    def get_latest_checkpoint(self, mission_id: str) -> Optional[Checkpoint]:
        """
        获取任务的最新检查点

        Args:
            mission_id: Mission ID

        Returns:
            最新的Checkpoint或None
        """
        checkpoints = self.list_checkpoints(mission_id=mission_id)
        if not checkpoints:
            return None

        # 已按创建时间降序排序
        return checkpoints[0]


# 全局单例
_checkpoint_manager_instance: Optional[CheckpointManager] = None


def get_checkpoint_manager(checkpoint_dir: Path = None) -> CheckpointManager:
    """
    获取全局检查点管理器实例

    Args:
        checkpoint_dir: 检查点目录 (仅在首次调用时使用)

    Returns:
        CheckpointManager实例
    """
    global _checkpoint_manager_instance

    if _checkpoint_manager_instance is None:
        if checkpoint_dir is None:
            # 默认使用项目下的checkpoints目录
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            checkpoint_dir = project_root / "checkpoints"

        _checkpoint_manager_instance = CheckpointManager(checkpoint_dir)

    return _checkpoint_manager_instance
