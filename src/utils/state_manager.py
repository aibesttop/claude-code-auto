"""
状态持久化管理模块
负责保存和恢复工作流执行状态，支持断点续传
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import json
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    INITIALIZED = "initialized"      # 已初始化
    RUNNING = "running"              # 运行中
    PAUSED = "paused"                # 已暂停
    COMPLETED = "completed"          # 已完成
    FAILED = "failed"                # 失败
    TIMEOUT = "timeout"              # 超时
    EMERGENCY_STOP = "emergency_stop"  # 紧急停止


@dataclass
class IterationRecord:
    """单次迭代记录"""
    iteration: int
    timestamp: str
    decision: Dict[str, Any]
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "IterationRecord":
        return cls(**data)


@dataclass
class ExecutionState:
    """工作流执行状态"""
    # 基本信息
    session_id: str
    goal: str
    work_dir: str

    # 执行状态
    status: WorkflowStatus
    current_iteration: int
    max_iterations: int

    # 时间信息
    start_time: str
    last_update: str
    total_duration_seconds: float = 0.0

    # 历史记录
    history: List[IterationRecord] = field(default_factory=list)

    # Persona切换历史
    persona_history: List[Dict[str, Any]] = field(default_factory=list)
    current_persona: str = "default"

    # 错误信息
    error_count: int = 0
    last_error: Optional[str] = None

    # 统计信息
    successful_iterations: int = 0
    failed_iterations: int = 0

    def add_iteration(
        self,
        decision: Dict[str, Any],
        duration: float,
        success: bool = True,
        error: Optional[str] = None
    ):
        """添加迭代记录"""
        record = IterationRecord(
            iteration=self.current_iteration,
            timestamp=datetime.now().isoformat(),
            decision=decision,
            duration_seconds=duration,
            success=success,
            error_message=error
        )

        self.history.append(record)
        self.last_update = datetime.now().isoformat()

        if success:
            self.successful_iterations += 1
        else:
            self.failed_iterations += 1
            self.error_count += 1
            self.last_error = error

    def add_persona_switch(
        self,
        from_persona: str,
        to_persona: str,
        reason: Optional[str] = None
    ):
        """添加Persona切换记录"""
        switch_record = {
            "timestamp": datetime.now().isoformat(),
            "iteration": self.current_iteration,
            "from_persona": from_persona,
            "to_persona": to_persona,
            "reason": reason
        }
        self.persona_history.append(switch_record)
        self.current_persona = to_persona
        self.last_update = datetime.now().isoformat()

    def update_duration(self):
        """更新总执行时长"""
        start = datetime.fromisoformat(self.start_time)
        now = datetime.now()
        self.total_duration_seconds = (now - start).total_seconds()

    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.max_iterations == 0:
            return 0.0
        return (self.current_iteration / self.max_iterations) * 100

    def get_average_iteration_time(self) -> float:
        """获取平均迭代时间（秒）"""
        if not self.history:
            return 0.0
        total_time = sum(record.duration_seconds for record in self.history)
        return total_time / len(self.history)

    def get_success_rate(self) -> float:
        """获取成功率"""
        total = self.successful_iterations + self.failed_iterations
        if total == 0:
            return 0.0
        return (self.successful_iterations / total) * 100

    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        # 转换 WorkflowStatus 枚举为字符串
        data['status'] = self.status.value
        return data

    def save(self, file_path: Path):
        """保存状态到文件"""
        self.update_duration()

        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, file_path: Path) -> Optional["ExecutionState"]:
        """从文件加载状态"""
        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 转换 history
            if 'history' in data:
                data['history'] = [
                    IterationRecord.from_dict(record)
                    for record in data['history']
                ]

            # 转换 status
            if 'status' in data:
                data['status'] = WorkflowStatus(data['status'])

            return cls(**data)
        except Exception as e:
            raise RuntimeError(f"加载状态文件失败: {e}")

    @classmethod
    def create_new(
        cls,
        session_id: str,
        goal: str,
        work_dir: str,
        max_iterations: int
    ) -> "ExecutionState":
        """创建新的执行状态"""
        now = datetime.now().isoformat()
        return cls(
            session_id=session_id,
            goal=goal,
            work_dir=work_dir,
            status=WorkflowStatus.INITIALIZED,
            current_iteration=0,
            max_iterations=max_iterations,
            start_time=now,
            last_update=now,
            history=[],
            error_count=0,
            successful_iterations=0,
            failed_iterations=0
        )

    def print_summary(self):
        """打印状态摘要"""
        print("\n" + "=" * 60)
        print("工作流执行状态摘要")
        print("=" * 60)
        print(f"会话ID: {self.session_id}")
        print(f"目标: {self.goal}")
        print(f"状态: {self.status.value}")
        print(f"进度: {self.current_iteration}/{self.max_iterations} "
              f"({self.get_progress_percentage():.1f}%)")
        print(f"成功率: {self.get_success_rate():.1f}%")
        print(f"总时长: {self.total_duration_seconds:.1f}秒")
        if self.history:
            print(f"平均迭代时间: {self.get_average_iteration_time():.1f}秒")
        print(f"成功次数: {self.successful_iterations}")
        print(f"失败次数: {self.failed_iterations}")
        if self.last_error:
            print(f"最后错误: {self.last_error}")
        print("=" * 60 + "\n")


class StateManager:
    """状态管理器"""

    def __init__(self, state_file_path: Path):
        self.state_file_path = state_file_path
        self._state: Optional[ExecutionState] = None

    def load_or_create(
        self,
        session_id: str,
        goal: str,
        work_dir: str,
        max_iterations: int,
        force_new: bool = False
    ) -> ExecutionState:
        """加载现有状态或创建新状态"""
        if force_new:
            self._state = ExecutionState.create_new(
                session_id=session_id,
                goal=goal,
                work_dir=work_dir,
                max_iterations=max_iterations
            )
            return self._state

        # 尝试加载现有状态
        self._state = ExecutionState.load(self.state_file_path)

        if self._state is None:
            # 不存在则创建新状态
            self._state = ExecutionState.create_new(
                session_id=session_id,
                goal=goal,
                work_dir=work_dir,
                max_iterations=max_iterations
            )
        else:
            # 验证加载的状态
            if self._state.goal != goal:
                print(f"⚠️  警告: 目标已变化 '{self._state.goal}' -> '{goal}'")

        return self._state

    def get_state(self) -> ExecutionState:
        """获取当前状态"""
        if self._state is None:
            raise RuntimeError("状态未初始化，请先调用 load_or_create()")
        return self._state

    def save(self):
        """保存当前状态"""
        if self._state is None:
            raise RuntimeError("没有可保存的状态")
        self._state.save(self.state_file_path)

    def update_and_save(self, **kwargs):
        """更新状态并保存"""
        state = self.get_state()
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        self.save()

    def backup_state(self, backup_suffix: str = ".backup"):
        """备份状态文件"""
        if self.state_file_path.exists():
            backup_path = self.state_file_path.with_suffix(
                self.state_file_path.suffix + backup_suffix
            )
            import shutil
            shutil.copy2(self.state_file_path, backup_path)
            return backup_path
        return None


if __name__ == "__main__":
    # 测试状态管理器
    from pathlib import Path

    state_file = Path("test_state.json")

    # 创建状态管理器
    manager = StateManager(state_file)

    # 创建新状态
    state = manager.load_or_create(
        session_id="test-session-123",
        goal="测试目标",
        work_dir="test_dir",
        max_iterations=10
    )

    # 添加迭代记录
    state.current_iteration = 1
    state.status = WorkflowStatus.RUNNING
    state.add_iteration(
        decision={"completed": False, "next_prompt": "继续测试"},
        duration=5.5,
        success=True
    )

    # 保存
    manager.save()

    # 打印摘要
    state.print_summary()

    # 重新加载
    manager2 = StateManager(state_file)
    state2 = manager2.load_or_create(
        session_id="test-session-123",
        goal="测试目标",
        work_dir="test_dir",
        max_iterations=10
    )

    print("✅ 状态持久化测试通过！")
    state2.print_summary()

    # 清理测试文件
    state_file.unlink()
