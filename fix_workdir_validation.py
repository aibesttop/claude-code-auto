#!/usr/bin/env python3
"""
修复工作目录验证问题

添加详细的调试日志，帮助追踪 work_dir 在整个执行流程中的变化。
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def patch_role_executor():
    """
    为 RoleExecutor 添加调试日志，追踪工作目录问题
    """

    # 读取 role_executor.py
    role_executor_file = Path("src/core/team/role_executor.py")

    if not role_executor_file.exists():
        print(f"❌ 文件不存在: {role_executor_file}")
        return False

    content = role_executor_file.read_text(encoding='utf-8')

    # 查找 _validate_format 方法中的 file_exists 检查
    target_line = '            if rule_type == "file_exists":'

    if target_line not in content:
        print("❌ 无法找到目标代码行")
        return False

    # 添加调试日志的补丁
    patch = '''            if rule_type == "file_exists":
                file_path = self.work_dir / rule.file

                # DEBUG: 添加详细的路径调试信息
                logger.debug(f"🔍 Validating file_exists:")
                logger.debug(f"   self.work_dir type: {type(self.work_dir)}")
                logger.debug(f"   self.work_dir value: {self.work_dir}")
                logger.debug(f"   rule.file: {rule.file}")
                logger.debug(f"   file_path (combined): {file_path}")
                logger.debug(f"   file_path (absolute): {file_path.resolve()}")
                logger.debug(f"   file_path.exists(): {file_path.exists()}")
                logger.debug(f"   Current CWD: {os.getcwd()}")

                # 列出 work_dir 中的文件
                if Path(self.work_dir).exists():
                    files_in_workdir = list(Path(self.work_dir).glob("*"))
                    logger.debug(f"   Files in work_dir: {[f.name for f in files_in_workdir]}")
                else:
                    logger.debug(f"   ⚠️ work_dir does not exist!")

                if not file_path.exists():
                    errors.append(f"Missing required file: {rule.file}")'''

    # 替换
    replacement = patch
    original = '''            if rule_type == "file_exists":
                file_path = self.work_dir / rule.file
                if not file_path.exists():
                    errors.append(f"Missing required file: {rule.file}")'''

    if original in content:
        new_content = content.replace(original, replacement)

        # 确保导入 os
        if "import os" not in new_content:
            # 在文件开头的导入部分添加
            import_section_end = new_content.find("logger = logging.getLogger(__name__)")
            if import_section_end > 0:
                # 在 logger 定义之前添加 import os
                lines = new_content[:import_section_end].split('\n')
                # 找到最后一个 import 行
                last_import_idx = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')):
                        last_import_idx = i

                if last_import_idx >= 0:
                    lines.insert(last_import_idx + 1, "import os")
                    new_content = '\n'.join(lines) + '\n' + new_content[import_section_end:]

        # 写回文件
        role_executor_file.write_text(new_content, encoding='utf-8')
        print("✅ 已添加调试日志到 role_executor.py")
        print("   下次运行时将显示详细的路径信息")
        return True
    else:
        print("⚠️ 无法找到精确匹配的代码块")
        print("   可能文件已经被修改过")
        return False

def add_workdir_tracking_to_executor():
    """
    在 ExecutorAgent 中添加工作目录追踪
    """
    executor_file = Path("src/core/agents/executor.py")

    if not executor_file.exists():
        print(f"❌ 文件不存在: {executor_file}")
        return False

    content = executor_file.read_text(encoding='utf-8')

    # 查找 os.chdir(work_dir_path) 行
    target_line = "        os.chdir(work_dir_path)"

    if target_line in content:
        # 添加更详细的日志
        patch = """        os.chdir(work_dir_path)
        logger.info(f"📂 Changed CWD from {original_cwd} to {work_dir_path}")
        logger.info(f"📂 work_dir_path type: {type(work_dir_path)}")
        logger.info(f"📂 work_dir_path.resolve(): {work_dir_path.resolve()}")
        logger.info(f"📂 Files in work_dir: {list(work_dir_path.glob('*'))[:10]}")"""

        original = f"{target_line}\n        logger.info(f\"📂 Changed CWD from {{original_cwd}} to {{work_dir_path}}\")"

        if original in content:
            new_content = content.replace(original, patch)
            executor_file.write_text(new_content, encoding='utf-8')
            print("✅ 已添加工作目录追踪到 executor.py")
            return True

    print("⚠️ executor.py 中未找到需要修改的代码")
    return False

def main():
    print("=" * 80)
    print("工作目录验证问题修复脚本")
    print("=" * 80)
    print()

    print("📋 修复步骤:")
    print("1. 为 RoleExecutor 添加详细的验证调试日志")
    print("2. 为 ExecutorAgent 添加工作目录追踪日志")
    print()

    # 执行修复
    success1 = patch_role_executor()
    success2 = add_workdir_tracking_to_executor()

    print()
    print("=" * 80)

    if success1 or success2:
        print("✅ 修复完成！")
        print()
        print("📌 下一步:")
        print("1. 重新运行你的任务")
        print("2. 查看日志中的调试信息")
        print("3. 特别关注：")
        print("   - self.work_dir 的值")
        print("   - file_path (combined) 的值")
        print("   - Files in work_dir 列表")
        print("   - Current CWD 的值")
        print()
        print("💡 这些信息将帮助我们确定文件在哪里被创建，")
        print("   以及验证时在哪里查找")
    else:
        print("⚠️ 修复过程中遇到问题")
        print("   可能文件已经被修改过，或代码结构发生了变化")

    print("=" * 80)

if __name__ == "__main__":
    main()
