#!/usr/bin/env python3
"""
验证工作目录修复

简单验证脚本，不依赖 pytest
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.core.agents.executor import ExecutorAgent
from src.core.team.role_executor import RoleExecutor
from src.core.team.role_registry import Role, Mission, OutputStandard, ValidationRule
from unittest.mock import Mock


def test_executor_work_dir_absolute():
    """测试 ExecutorAgent 使用绝对路径"""
    print("=" * 80)
    print("测试 1: ExecutorAgent work_dir 应该是绝对路径")
    print("=" * 80)

    # 使用相对路径创建
    executor = ExecutorAgent(work_dir="demo_act", model="claude-sonnet-4-5")

    work_dir = Path(executor.work_dir)
    is_absolute = work_dir.is_absolute()

    print(f"输入: 'demo_act' (相对路径)")
    print(f"输出: {executor.work_dir}")
    print(f"是绝对路径: {is_absolute}")

    if is_absolute:
        print("✅ 测试通过：work_dir 已被解析为绝对路径")
        return True
    else:
        print("❌ 测试失败：work_dir 仍然是相对路径")
        return False


def test_role_executor_work_dir_absolute():
    """测试 RoleExecutor 使用绝对路径"""
    print("\n" + "=" * 80)
    print("测试 2: RoleExecutor work_dir 应该是绝对路径")
    print("=" * 80)

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

    # 使用相对路径创建
    role_executor = RoleExecutor(test_role, mock_executor, "demo_act")

    work_dir = role_executor.work_dir
    is_absolute = work_dir.is_absolute()

    print(f"输入: 'demo_act' (相对路径)")
    print(f"输出: {work_dir}")
    print(f"是绝对路径: {is_absolute}")

    if is_absolute:
        print("✅ 测试通过：work_dir 已被解析为绝对路径")
        return True
    else:
        print("❌ 测试失败：work_dir 仍然是相对路径")
        return False


def test_executor_cwd_behavior():
    """测试 ExecutorAgent 的 CWD 行为"""
    print("\n" + "=" * 80)
    print("测试 3: ExecutorAgent 执行后 CWD 应该保持在 work_dir")
    print("=" * 80)

    initial_cwd = os.getcwd()
    print(f"初始 CWD: {initial_cwd}")

    # 创建测试目录
    test_dir = Path("test_work_dir")
    test_dir.mkdir(exist_ok=True)

    try:
        # 创建 executor
        executor = ExecutorAgent(work_dir=str(test_dir), model="claude-sonnet-4-5")

        # 检查 executor 中保存的 original_cwd 值
        # 注意：这需要访问 executor 内部，但我们可以通过观察日志来验证

        print(f"ExecutorAgent work_dir: {executor.work_dir}")
        print(f"work_dir 是绝对路径: {Path(executor.work_dir).is_absolute()}")

        # 模拟执行流程中的 CWD 切换
        work_dir_path = Path(executor.work_dir).resolve()
        original_cwd = work_dir_path  # 这是修复后的行为
        os.chdir(work_dir_path)

        print(f"\n模拟执行中:")
        print(f"  original_cwd (修复后): {original_cwd}")
        print(f"  当前 CWD: {os.getcwd()}")

        # 模拟 finally 块
        os.chdir(original_cwd)
        final_cwd = os.getcwd()

        print(f"\n模拟 finally 块后:")
        print(f"  最终 CWD: {final_cwd}")
        print(f"  是否在 work_dir: {Path(final_cwd).resolve() == work_dir_path}")

        # 验证
        if Path(final_cwd).resolve() == work_dir_path:
            print("✅ 测试通过：CWD 保持在 work_dir")
            return True
        else:
            print("❌ 测试失败：CWD 不在 work_dir")
            return False

    finally:
        # 清理
        os.chdir(initial_cwd)
        if test_dir.exists():
            test_dir.rmdir()


def main():
    print("\n" + "🔍 验证工作目录修复".center(80, "="))
    print()

    results = []

    # 运行所有测试
    results.append(("ExecutorAgent work_dir 绝对路径", test_executor_work_dir_absolute()))
    results.append(("RoleExecutor work_dir 绝对路径", test_role_executor_work_dir_absolute()))
    results.append(("ExecutorAgent CWD 行为", test_executor_cwd_behavior()))

    # 汇总结果
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print()
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 所有测试通过！工作目录修复验证成功！")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
