"""
主程序 - 优化版本
整合所有优化后的模块，提供完整的自主工作流系统
"""
import asyncio
import sys
from pathlib import Path

from config import get_config, reload_config
from logger import setup_logger
from state_manager import StateManager, WorkflowStatus
from step1_v2 import step1_initialize
from step3_v2 import step3_main_loop


async def main(
    config_path: str = "config.yaml",
    skip_init: bool = False,
    resume: bool = True
):
    """
    主工作流程

    Args:
        config_path: 配置文件路径
        skip_init: 跳过初始化（假设已经运行过 step1）
        resume: 是否恢复之前的状态

    Returns:
        bool: 是否成功完成
    """
    # 加载配置
    try:
        config = get_config(config_path)
    except FileNotFoundError:
        print(f"❌ 配置文件不存在: {config_path}")
        print("请创建 config.yaml 配置文件")
        return False
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

    # 设置日志
    logger = setup_logger(
        name="main",
        log_dir=config.directories.logs_dir,
        level=config.logging.level,
        format_type=config.logging.format,
        console_output=config.logging.console_output,
        file_output=config.logging.file_output,
        max_file_size_mb=config.logging.max_file_size_mb,
        backup_count=config.logging.backup_count
    )

    logger.info("\n" + "=" * 70)
    logger.info("Claude Code 自主工作流系统 - 优化版本 v2.0")
    logger.info("=" * 70)
    logger.info(f"配置文件: {config_path}")
    logger.info(f"任务目标: {config.task.goal}")
    logger.info(f"工作目录: {config.directories.work_dir}")
    logger.info("=" * 70 + "\n")

    # 确保目录存在
    config.ensure_directories()

    # Step 1: 初始化任务（如果需要）
    if not skip_init:
        logger.info("📝 阶段 1: 任务初始化")
        logger.info("-" * 70)

        try:
            success, session_id = await step1_initialize(config_path)

            if not success:
                logger.error("❌ 任务初始化失败")
                return False

            logger.info(f"✅ 初始化成功，会话ID: {session_id[:16]}...")

        except Exception as e:
            logger.exception("❌ 初始化过程中发生错误")
            return False

    else:
        logger.info("⏭️  跳过初始化步骤")

        # 验证会话文件是否存在
        session_file = config.get_session_file_path()
        if not session_file.exists():
            logger.error(f"❌ 会话文件不存在: {session_file}")
            logger.error("请先运行完整流程（不使用 --skip-init）")
            return False

    # Step 3: 自主循环
    logger.info("\n🔄 阶段 2: 启动自主循环")
    logger.info("-" * 70)

    try:
        success = await step3_main_loop(
            cwd_path=config.directories.work_dir,
            goal=config.task.goal,
            config_path=config_path,
            resume=resume
        )

        if success:
            logger.info("\n" + "=" * 70)
            logger.info("🎉 任务成功完成！")
            logger.info("=" * 70)
        else:
            logger.warning("\n" + "=" * 70)
            logger.warning("⚠️  任务未完成或失败")
            logger.warning("=" * 70)

        # 显示最终状态
        state_manager = StateManager(config.get_state_file_path())
        try:
            state = state_manager.get_state()
            state.print_summary()
        except:
            pass

        return success

    except KeyboardInterrupt:
        logger.warning("\n⚠️  检测到 Ctrl+C，正在安全退出...")

        # 更新状态
        try:
            state_manager = StateManager(config.get_state_file_path())
            state = state_manager.get_state()
            state.status = WorkflowStatus.PAUSED
            state_manager.save()
            logger.info("✅ 状态已保存，可以稍后恢复")
        except:
            pass

        return False

    except Exception as e:
        logger.exception("❌ 执行过程中发生错误")
        return False


def print_usage():
    """打印使用说明"""
    print("""
Claude Code 自主工作流系统 v2.0

用法:
    python main_v2.py [选项]

选项:
    --help, -h           显示此帮助信息
    --config PATH        指定配置文件路径（默认: config.yaml）
    --skip-init          跳过 Step1 初始化（假设已运行过）
    --no-resume          不恢复之前的状态，从头开始
    --show-config        显示当前配置并退出
    --show-status        显示当前状态并退出

示例:
    # 完整运行（初始化 + 循环）
    python main_v2.py

    # 只运行循环（跳过初始化）
    python main_v2.py --skip-init

    # 从头开始（不恢复状态）
    python main_v2.py --no-resume

    # 使用自定义配置
    python main_v2.py --config my_config.yaml

紧急停止:
    创建文件 .emergency_stop 可以安全地停止循环

配置文件:
    config.yaml - 主配置文件，包含所有参数

日志文件:
    logs/main.log       - 主日志
    logs/main_error.log - 错误日志

状态文件:
    demo_act/workflow_state.json - 执行状态（用于断点续传）
    demo_act/session_id.txt      - 会话ID

更多信息:
    查看 UPGRADE_GUIDE.md 了解优化详情
    """)


def show_config(config_path: str = "config.yaml"):
    """显示当前配置"""
    try:
        config = get_config(config_path)
        import yaml
        print("\n" + "=" * 60)
        print("当前配置:")
        print("=" * 60)
        print(yaml.dump(config.model_dump(), allow_unicode=True, default_flow_style=False))
        print("=" * 60)
    except Exception as e:
        print(f"❌ 无法加载配置: {e}")


def show_status(config_path: str = "config.yaml"):
    """显示当前状态"""
    try:
        config = get_config(config_path)
        state_manager = StateManager(config.get_state_file_path())
        state = state_manager.get_state()
        state.print_summary()
    except FileNotFoundError:
        print("⚠️  状态文件不存在，可能尚未运行过工作流")
    except Exception as e:
        print(f"❌ 无法加载状态: {e}")


if __name__ == "__main__":
    # 解析命令行参数
    if "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        sys.exit(0)

    if "--show-config" in sys.argv:
        config_path = "config.yaml"
        for i, arg in enumerate(sys.argv):
            if arg == "--config" and i + 1 < len(sys.argv):
                config_path = sys.argv[i + 1]
        show_config(config_path)
        sys.exit(0)

    if "--show-status" in sys.argv:
        config_path = "config.yaml"
        for i, arg in enumerate(sys.argv):
            if arg == "--config" and i + 1 < len(sys.argv):
                config_path = sys.argv[i + 1]
        show_status(config_path)
        sys.exit(0)

    # 提取参数
    config_path = "config.yaml"
    skip_init = "--skip-init" in sys.argv
    resume = "--no-resume" not in sys.argv

    for i, arg in enumerate(sys.argv):
        if arg == "--config" and i + 1 < len(sys.argv):
            config_path = sys.argv[i + 1]

    # 运行主程序
    try:
        success = asyncio.run(main(
            config_path=config_path,
            skip_init=skip_init,
            resume=resume
        ))

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n👋 再见！")
        sys.exit(130)  # 标准的 Ctrl+C 退出码
