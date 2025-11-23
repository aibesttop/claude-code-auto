#!/usr/bin/env python3
"""
诊断工作目录配置问题

检查：
1. 配置文件中的 work_dir 设置
2. Team orchestrator 传递给 role executor 的 work_dir
3. Executor 实际切换到的目录
4. 验证器查找文件的目录
"""

import os
import sys
from pathlib import Path
import yaml

def diagnose_workdir_config():
    """诊断工作目录配置"""

    print("=" * 80)
    print("工作目录诊断报告")
    print("=" * 80)
    print()

    # 1. 当前工作目录
    current_cwd = os.getcwd()
    print(f"📂 当前工作目录 (CWD): {current_cwd}")
    print()

    # 2. 项目根目录
    project_root = Path(__file__).parent
    print(f"📁 项目根目录: {project_root.resolve()}")
    print()

    # 3. 检查配置文件
    config_file = project_root / "config.yaml"
    if config_file.exists():
        print(f"✅ 找到配置文件: {config_file}")
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 查找 work_dir 配置
        work_dir_settings = {}

        if 'work_dir' in config:
            work_dir_settings['global'] = config['work_dir']

        if 'team' in config and 'work_dir' in config['team']:
            work_dir_settings['team'] = config['team']['work_dir']

        if 'leader' in config and 'work_dir' in config['leader']:
            work_dir_settings['leader'] = config['leader']['work_dir']

        if work_dir_settings:
            print("\n📋 配置文件中的 work_dir 设置:")
            for key, value in work_dir_settings.items():
                print(f"   {key}: {value}")
                # 解析相对路径
                if not os.path.isabs(value):
                    abs_path = (project_root / value).resolve()
                    print(f"      → 绝对路径: {abs_path}")
                    print(f"      → 存在: {'✅' if abs_path.exists() else '❌'}")
        else:
            print("\n⚠️ 配置文件中未找到 work_dir 设置")
    else:
        print(f"❌ 配置文件不存在: {config_file}")

    print()

    # 4. 检查可能的工作目录
    possible_work_dirs = [
        "demo_act",
        "work",
        "output",
        "workspace",
    ]

    print("📂 检查可能的工作目录:")
    for dirname in possible_work_dirs:
        dirpath = project_root / dirname
        exists = dirpath.exists()
        symbol = "✅" if exists else "❌"
        print(f"   {symbol} {dirpath}")

        if exists and dirpath.is_dir():
            # 列出目录内容
            files = list(dirpath.glob("*"))
            if files:
                print(f"      包含 {len(files)} 个文件:")
                for file in files[:5]:  # 只显示前5个
                    print(f"         - {file.name}")
                if len(files) > 5:
                    print(f"         ... 还有 {len(files) - 5} 个文件")

    print()

    # 5. 搜索所有可能生成的报告文件
    print("🔍 搜索生成的报告文件:")
    report_patterns = [
        "market-research.md",
        "creative_exploration_report.md",
        "*research*.md",
        "*report*.md"
    ]

    found_files = []
    for pattern in report_patterns:
        matches = list(project_root.rglob(pattern))
        if matches:
            print(f"\n   模式 '{pattern}':")
            for match in matches:
                rel_path = match.relative_to(project_root)
                print(f"      ✅ {rel_path}")
                found_files.append(match)

    if not found_files:
        print("   ❌ 未找到任何报告文件")

    print()

    # 6. 建议
    print("=" * 80)
    print("💡 诊断建议")
    print("=" * 80)

    if not work_dir_settings:
        print("\n⚠️ 问题：配置文件中未设置 work_dir")
        print("   建议：在 config.yaml 中添加明确的 work_dir 配置")
        print("   示例：")
        print("     team:")
        print("       work_dir: 'demo_act'")
    else:
        print("\n✅ 配置文件中有 work_dir 设置")
        print("   下一步：检查 RoleExecutor 是否正确使用此配置")

    if found_files:
        print(f"\n✅ 找到 {len(found_files)} 个报告文件")
        print("   这些文件的位置可能揭示了实际的工作目录")
    else:
        print("\n⚠️ 未找到任何报告文件")
        print("   可能原因：")
        print("   1. 文件被创建在了系统的其他位置")
        print("   2. 文件名与预期不符")
        print("   3. 执行过程中出现错误，文件未被创建")

    print()

if __name__ == "__main__":
    diagnose_workdir_config()
