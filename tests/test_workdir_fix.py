#!/usr/bin/env python3
"""
测试工作目录修复

验证 ExecutorAgent 和 RoleExecutor 的 CWD 管理是否正确。
"""

import os
import asyncio
import pytest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.core.agents.executor import ExecutorAgent
from src.core.team.role_executor import RoleExecutor
from src.core.team.role_registry import Role, Mission, OutputStandard, ValidationRule


@pytest.mark.asyncio
async def test_executor_keeps_cwd_at_workdir(tmp_path):
    """
    测试 ExecutorAgent 在执行后保持 CWD 在 work_dir
    """
    # 记录初始 CWD
    initial_cwd = os.getcwd()

    # 创建临时工作目录
    work_dir = tmp_path / "test_work"
    work_dir.mkdir()

    # 创建 ExecutorAgent
    executor = ExecutorAgent(
        work_dir=str(work_dir),
        model="claude-sonnet-4-5",
        max_steps=2
    )

    # Mock run_claude_prompt 返回 Final Answer
    with patch('src.core.agents.executor.run_claude_prompt') as mock_prompt:
        mock_prompt.return_value = ("Final Answer: Test completed", {})

        # 执行任务
        result = await executor.execute_task("Test task")

    # 验证结果
    assert "Test completed" in result

    # 关键检查：CWD 应该在 work_dir，而不是 initial_cwd
    current_cwd = os.getcwd()
    assert Path(current_cwd).resolve() == work_dir.resolve(), \
        f"CWD should be at work_dir {work_dir}, but is at {current_cwd}"

    # 恢复 CWD（清理）
    os.chdir(initial_cwd)


@pytest.mark.asyncio
async def test_role_executor_validation_with_correct_cwd(tmp_path):
    """
    测试 RoleExecutor 验证时能找到文件（因为 CWD 在 work_dir）
    """
    initial_cwd = os.getcwd()

    # 创建测试 role
    test_role = Role(
        name="Test-Role",
        description="Test role",
        category="test",
        mission=Mission(
            goal="Test goal",
            success_criteria=["Create file"],
            max_iterations=2
        ),
        output_standard=OutputStandard(
            required_files=["output.md"],
            validation_rules=[
                ValidationRule(
                    type="file_exists",
                    file="output.md"
                )
            ]
        ),
        recommended_persona="default",
        tools=["write_file"],
        dependencies=[]
    )

    # 创建临时工作目录
    work_dir = tmp_path / "test_work"
    work_dir.mkdir()

    # 创建 mock executor
    mock_executor = Mock()
    mock_executor.execute_task = AsyncMock(return_value="Task completed")
    mock_executor.persona_engine = Mock()
    mock_executor.persona_engine.switch_persona = Mock()
    mock_executor.export_react_trace = Mock(return_value="trace.md")

    # 创建 RoleExecutor
    role_executor = RoleExecutor(test_role, mock_executor, str(work_dir))

    # 验证 work_dir 是绝对路径
    assert role_executor.work_dir.is_absolute(), \
        f"work_dir should be absolute, got: {role_executor.work_dir}"

    # 创建输出文件
    output_file = work_dir / "output.md"
    output_file.write_text("Test content")

    # Mock executor.execute_task，并确保 CWD 在 work_dir
    async def mock_execute_task(task):
        # Simulate what real executor does: keep CWD at work_dir
        os.chdir(work_dir)
        return "Task completed"

    mock_executor.execute_task = AsyncMock(side_effect=mock_execute_task)

    # 执行
    result = await role_executor.execute()

    # 验证
    assert result['success'] is True, f"Execution should succeed, got: {result}"
    assert result['validation_result']['passed'] is True, \
        f"Validation should pass, errors: {result['validation_result']['errors']}"

    # 清理
    os.chdir(initial_cwd)


@pytest.mark.asyncio
async def test_workdir_absolute_path_resolution(tmp_path):
    """
    测试 work_dir 总是被解析为绝对路径
    """
    initial_cwd = os.getcwd()

    # 测试相对路径
    relative_path = "demo_act"

    # 创建 ExecutorAgent with relative path
    executor = ExecutorAgent(
        work_dir=relative_path,
        model="claude-sonnet-4-5"
    )

    # 验证 work_dir 被解析为绝对路径
    assert Path(executor.work_dir).is_absolute(), \
        f"work_dir should be absolute, got: {executor.work_dir}"

    # 清理
    os.chdir(initial_cwd)


def test_role_executor_workdir_absolute():
    """
    测试 RoleExecutor 的 work_dir 总是绝对路径
    """
    from pathlib import Path

    # 创建 mock role
    test_role = Role(
        name="Test",
        description="Test",
        category="test",
        mission=Mission(goal="Test", success_criteria=[], max_iterations=1),
        output_standard=OutputStandard(required_files=[], validation_rules=[]),
        recommended_persona="default",
        tools=[],
        dependencies=[]
    )

    # 创建 mock executor
    mock_executor = Mock()
    mock_executor.persona_engine = Mock()
    mock_executor.persona_engine.switch_persona = Mock()

    # 测试相对路径
    role_executor = RoleExecutor(test_role, mock_executor, "demo_act")

    # 验证 work_dir 是绝对路径
    assert role_executor.work_dir.is_absolute(), \
        f"RoleExecutor work_dir should be absolute, got: {role_executor.work_dir}"

    # 测试绝对路径
    abs_path = Path("/tmp/test").resolve()
    role_executor2 = RoleExecutor(test_role, mock_executor, str(abs_path))

    assert role_executor2.work_dir.is_absolute()
    assert role_executor2.work_dir == abs_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
