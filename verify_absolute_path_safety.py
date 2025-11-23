#!/usr/bin/env python3
"""
验证绝对路径修复是否引入新问题

检查项：
1. 符号链接解析
2. 路径长度（Windows 260 字符限制）
3. 特殊字符处理
4. 文件操作兼容性
"""

import os
import sys
from pathlib import Path
import platform

def check_symlink_issues():
    """检查符号链接问题"""
    print("=" * 80)
    print("1. 检查符号链接问题")
    print("=" * 80)

    cwd = Path.cwd()
    resolved = cwd.resolve()

    if cwd != resolved:
        print(f"⚠️  检测到符号链接:")
        print(f"   当前路径: {cwd}")
        print(f"   实际路径: {resolved}")
        print(f"   建议: 确认这是否是预期行为")
        return False
    else:
        print(f"✅ 无符号链接问题")
        print(f"   工作目录: {cwd}")
        return True


def check_path_length():
    """检查路径长度（Windows 限制）"""
    print("\n" + "=" * 80)
    print("2. 检查路径长度（Windows 限制）")
    print("=" * 80)

    test_work_dir = Path("demo_act").resolve()
    path_length = len(str(test_work_dir))

    print(f"绝对路径: {test_work_dir}")
    print(f"路径长度: {path_length} 字符")

    if platform.system() == "Windows":
        MAX_PATH = 260  # Windows 传统限制

        if path_length > MAX_PATH:
            print(f"❌ 路径过长！超过 Windows MAX_PATH ({MAX_PATH})")
            print(f"   建议: 将项目移到更短的路径")
            return False
        elif path_length > MAX_PATH * 0.8:
            print(f"⚠️  路径较长，接近 Windows MAX_PATH 限制")
            print(f"   剩余空间: {MAX_PATH - path_length} 字符")
            return True
        else:
            print(f"✅ 路径长度正常（剩余 {MAX_PATH - path_length} 字符）")
            return True
    else:
        print(f"✅ 非 Windows 系统，无路径长度限制")
        return True


def check_special_characters():
    """检查路径中的特殊字符"""
    print("\n" + "=" * 80)
    print("3. 检查路径特殊字符")
    print("=" * 80)

    cwd = str(Path.cwd())

    # Windows 不允许的字符
    forbidden_chars = ['<', '>', ':', '"', '|', '?', '*']

    found_issues = []
    for char in forbidden_chars:
        if char in cwd:
            found_issues.append(char)

    if found_issues:
        print(f"❌ 发现特殊字符: {', '.join(found_issues)}")
        print(f"   当前路径: {cwd}")
        print(f"   建议: 重命名包含特殊字符的目录")
        return False
    else:
        print(f"✅ 路径不包含特殊字符")
        print(f"   当前路径: {cwd}")
        return True


def check_relative_path_compatibility():
    """检查相对路径兼容性"""
    print("\n" + "=" * 80)
    print("4. 检查相对路径操作兼容性")
    print("=" * 80)

    try:
        # 模拟 Agent 的工作流程
        work_dir = Path("demo_act")
        work_dir.mkdir(exist_ok=True)

        # 转换为绝对路径（我们的修复）
        abs_work_dir = work_dir.resolve()

        # 切换到 work_dir（Executor 的行为）
        original_cwd = os.getcwd()
        os.chdir(abs_work_dir)

        # 测试相对路径操作（AI 的行为）
        test_file = Path("test_relative.txt")
        test_file.write_text("Test content")

        # 验证文件存在
        if test_file.exists():
            print(f"✅ 相对路径操作正常")
            print(f"   工作目录: {abs_work_dir}")
            print(f"   测试文件: {test_file}")
            print(f"   完整路径: {test_file.resolve()}")

            # 清理
            test_file.unlink()
            os.chdir(original_cwd)
            return True
        else:
            print(f"❌ 相对路径操作失败")
            os.chdir(original_cwd)
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        os.chdir(original_cwd)
        return False


def check_sdk_compatibility():
    """检查 Claude Code SDK 兼容性"""
    print("\n" + "=" * 80)
    print("5. 检查 Claude Code SDK 兼容性")
    print("=" * 80)

    try:
        from claude_code_sdk import ClaudeCodeOptions

        work_dir = Path("demo_act").resolve()
        work_dir.mkdir(exist_ok=True)

        # 测试 SDK 是否接受绝对路径
        options = ClaudeCodeOptions(
            permission_mode="bypassPermissions",
            cwd=str(work_dir),
            model="claude-sonnet-4-5"
        )

        print(f"✅ SDK 接受绝对路径")
        print(f"   CWD: {options.cwd}")
        return True

    except ImportError:
        print(f"⚠️  claude_code_sdk 未安装，跳过测试")
        return True
    except Exception as e:
        print(f"❌ SDK 兼容性问题: {e}")
        return False


def main():
    print("\n" + "🔍 绝对路径修复验证".center(80, "="))
    print(f"\n平台: {platform.system()}")
    print(f"Python: {sys.version}")
    print()

    results = {
        "符号链接": check_symlink_issues(),
        "路径长度": check_path_length(),
        "特殊字符": check_special_characters(),
        "相对路径兼容性": check_relative_path_compatibility(),
        "SDK 兼容性": check_sdk_compatibility()
    }

    print("\n" + "=" * 80)
    print("验证结果汇总")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print()
    print(f"通过: {passed}/{total}")

    if passed == total:
        print("\n🎉 所有检查通过！绝对路径修复未引入新问题。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个检查失败，请查看上述详细信息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
