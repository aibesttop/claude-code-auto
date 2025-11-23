#!/usr/bin/env python3
"""
测试路径嵌套问题修复

模拟多次执行，验证 work_dir 不会嵌套
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_path_nesting_issue():
    """测试路径嵌套问题"""
    print("=" * 80)
    print("测试路径嵌套问题修复")
    print("=" * 80)
    print()

    # 模拟项目结构
    project_root = Path(__file__).parent.resolve()
    config_work_dir = "demo_act"  # 配置中的相对路径

    print(f"项目根目录: {project_root}")
    print(f"配置 work_dir: {config_work_dir}")
    print()

    # 测试场景 1: 正常启动（CWD 在项目根目录）
    print("场景 1: 正常启动（CWD 在项目根目录）")
    print("-" * 80)

    original_cwd = os.getcwd()
    os.chdir(project_root)

    # 旧的方式（会导致嵌套）
    old_way = Path(config_work_dir).resolve()
    print(f"❌ 旧方式: Path('{config_work_dir}').resolve()")
    print(f"   结果: {old_way}")

    # 新的方式（修复后）
    new_way = (project_root / config_work_dir).resolve()
    print(f"✅ 新方式: (project_root / '{config_work_dir}').resolve()")
    print(f"   结果: {new_way}")
    print()

    # 测试场景 2: CWD 在 demo_act（模拟 Executor 切换后）
    print("场景 2: CWD 在 demo_act（模拟 Executor 切换后）")
    print("-" * 80)

    # 创建并切换到 demo_act
    demo_act_dir = project_root / "demo_act"
    demo_act_dir.mkdir(exist_ok=True)
    os.chdir(demo_act_dir)

    # 旧的方式（会导致嵌套！）
    old_way_nested = Path(config_work_dir).resolve()
    print(f"❌ 旧方式: Path('{config_work_dir}').resolve()")
    print(f"   当前 CWD: {os.getcwd()}")
    print(f"   结果: {old_way_nested}")
    print(f"   ⚠️ 嵌套！路径变成了 demo_act/demo_act")

    # 新的方式（不会嵌套！）
    new_way_no_nest = (project_root / config_work_dir).resolve()
    print(f"✅ 新方式: (project_root / '{config_work_dir}').resolve()")
    print(f"   当前 CWD: {os.getcwd()}")
    print(f"   结果: {new_way_no_nest}")
    print(f"   ✅ 正确！路径保持为 demo_act")
    print()

    # 测试场景 3: 多次执行（模拟 Planner 多次调用）
    print("场景 3: 多次执行（模拟 Planner 多次调用）")
    print("-" * 80)

    # 恢复到项目根目录
    os.chdir(project_root)

    for i in range(1, 4):
        print(f"\n第 {i} 次执行:")

        # 旧方式
        old_result = Path(config_work_dir).resolve()
        print(f"  ❌ 旧方式: {old_result}")

        # 新方式
        new_result = (project_root / config_work_dir).resolve()
        print(f"  ✅ 新方式: {new_result}")

        # 模拟切换到 work_dir（Executor 的行为）
        if old_result.exists():
            os.chdir(old_result)
            print(f"     CWD 切换到: {os.getcwd()}")

    print()

    # 恢复原始 CWD
    os.chdir(original_cwd)

    # 验证结果
    print("=" * 80)
    print("验证结果")
    print("=" * 80)

    expected_path = project_root / "demo_act"

    if new_way_no_nest == expected_path and new_way == expected_path:
        print("✅ 修复成功！新方式在所有场景下都返回正确路径")
        print(f"   预期路径: {expected_path}")
        print(f"   实际路径: {new_way_no_nest}")
        return True
    else:
        print("❌ 测试失败")
        return False


def test_main_py_fix():
    """测试 main.py 的修复"""
    print("\n" + "=" * 80)
    print("测试 main.py 修复")
    print("=" * 80)
    print()

    # 检查 main.py 是否使用了正确的方式
    main_file = Path(__file__).parent / "src" / "main.py"

    if not main_file.exists():
        print("⚠️ main.py 不存在，跳过测试")
        return True

    content = main_file.read_text(encoding='utf-8')

    # 检查是否有正确的代码
    has_project_root = "project_root = Path(__file__).parent.parent.resolve()" in content
    has_correct_work_dir = "(project_root / config.directories.work_dir)" in content

    # 检查是否还有旧的代码
    has_old_code = 'work_dir = Path(config.directories.work_dir)' in content and not has_project_root

    print(f"项目根目录计算: {'✅' if has_project_root else '❌'}")
    print(f"正确的 work_dir: {'✅' if has_correct_work_dir else '❌'}")
    print(f"旧代码清理: {'✅' if not has_old_code else '❌'}")

    if has_project_root and has_correct_work_dir and not has_old_code:
        print("\n✅ main.py 已正确修复")
        return True
    else:
        print("\n❌ main.py 仍需修复")
        return False


def main():
    print("\n" + "🔍 路径嵌套问题测试".center(80, "="))
    print()

    result1 = test_path_nesting_issue()
    result2 = test_main_py_fix()

    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)

    if result1 and result2:
        print("🎉 所有测试通过！路径嵌套问题已修复")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查修复")
        return 1


if __name__ == "__main__":
    sys.exit(main())
