"""
Step1 优化版本 - 任务初始化模块
改进点:
- P0-3: 完善异常处理和重试机制
- P1-5: 会话ID备份和验证
- P1-6: 使用统一日志系统
- P1-7: 使用配置文件
"""
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock, ResultMessage
import asyncio
from pathlib import Path
from typing import Tuple, Optional
import shutil

from config import get_config
from logger import setup_logger
from state_manager import StateManager, WorkflowStatus


async def step1_initialize(
    config_path: str = "config.yaml"
) -> Tuple[bool, str]:
    """
    执行任务初始化并建立会话

    Args:
        config_path: 配置文件路径

    Returns:
        tuple: (success: bool, session_id: str)

    Raises:
        RuntimeError: 初始化失败
    """
    # 加载配置
    config = get_config(config_path)

    # 设置日志
    logger = setup_logger(
        name="step1",
        log_dir=config.directories.logs_dir,
        level=config.logging.level,
        format_type=config.logging.format,
        console_output=config.logging.console_output,
        file_output=config.logging.file_output,
        max_file_size_mb=config.logging.max_file_size_mb,
        backup_count=config.logging.backup_count
    )

    logger.info("=" * 60)
    logger.info("开始任务初始化 (Step 1)")
    logger.info("=" * 60)

    # 确保目录存在
    config.ensure_directories()
    work_dir_path = config.get_work_dir_path()

    logger.info(f"工作目录: {work_dir_path}")
    logger.info(f"任务目标: {config.task.goal}")

    # 初始化状态管理器
    state_manager = StateManager(config.get_state_file_path())

    session_id = None
    success = False
    retry_count = 0
    max_retries = config.error_handling.max_retries

    while retry_count <= max_retries:
        try:
            # 配置 Claude SDK
            options = ClaudeCodeOptions(
                permission_mode=config.claude.permission_mode,
                cwd=str(work_dir_path)
            )

            async with ClaudeSDKClient(options=options) as client:
                logger.info(f"发送初始化请求 (尝试 {retry_count + 1}/{max_retries + 1})")
                logger.debug(f"初始提示词: {config.task.initial_prompt}")

                # 发送查询
                await client.query(config.task.initial_prompt)

                # 处理响应
                conversation_complete = False
                message_count = 0

                async for message in client.receive_response():
                    message_count += 1
                    logger.debug(f"收到第 {message_count} 条响应消息")

                    # 检查是否为初始化消息（获取 session_id）
                    if hasattr(message, 'subtype') and message.subtype == 'init':
                        session_id = message.data.get('session_id')
                        if session_id:
                            logger.info(f"✅ 获取到会话ID: {session_id[:16]}...")

                            # 保存会话ID到主文件
                            session_file = config.get_session_file_path()
                            session_file.write_text(session_id, encoding='utf-8')
                            logger.debug(f"会话ID已保存至: {session_file}")

                            # P1-5: 备份会话ID
                            backup_file = config.get_backup_session_file_path()
                            backup_file.write_text(session_id, encoding='utf-8')
                            logger.debug(f"会话ID备份至: {backup_file}")

                    # 处理助手消息
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                logger.debug(f"Claude 回复: {block.text[:100]}...")

                    # 检查是否完成
                    elif isinstance(message, ResultMessage):
                        logger.info("✅ 会话初始化完成")
                        conversation_complete = True
                        success = True
                        break

                if not conversation_complete:
                    logger.warning("⚠️  会话未正常完成")

                # 如果成功，跳出重试循环
                if success and session_id:
                    break

        except Exception as e:
            retry_count += 1
            logger.error(f"初始化失败 (尝试 {retry_count}/{max_retries + 1}): {e}")

            if retry_count <= max_retries:
                delay = config.error_handling.retry_delay_seconds
                logger.info(f"等待 {delay} 秒后重试...")
                await asyncio.sleep(delay)
            else:
                logger.critical("❌ 达到最大重试次数，初始化失败")
                raise RuntimeError(f"初始化失败: {e}")

    # 创建初始状态
    if session_id:
        state = state_manager.load_or_create(
            session_id=session_id,
            goal=config.task.goal,
            work_dir=str(work_dir_path),
            max_iterations=config.safety.max_iterations,
            force_new=True
        )
        state.status = WorkflowStatus.INITIALIZED
        state_manager.save()
        logger.info(f"✅ 状态已保存至: {config.get_state_file_path()}")

    logger.info("=" * 60)
    logger.info(f"初始化结果: {'成功' if success else '失败'}")
    if session_id:
        logger.info(f"会话ID: {session_id}")
    logger.info("=" * 60)

    return success, session_id or ""


async def validate_session(session_id: str, config_path: str = "config.yaml") -> bool:
    """
    验证会话ID是否有效

    Args:
        session_id: 会话ID
        config_path: 配置文件路径

    Returns:
        bool: 会话是否有效
    """
    # TODO: 实现会话有效性验证逻辑
    # 可以通过尝试恢复会话来验证
    return bool(session_id and len(session_id) > 0)


async def main():
    """主函数"""
    import sys

    try:
        success, session_id = await step1_initialize()

        # 输出结果
        if "--json" in sys.argv:
            import json
            output = {
                "success": success,
                "session_id": session_id,
                "result": "Yes" if success else "No"
            }
            print(json.dumps(output, ensure_ascii=False))
        else:
            print(f"\n会话ID: {session_id}")
            print(f"结果: {'Yes' if success else 'No'}")

        return success

    except Exception as e:
        logger = setup_logger()
        logger.exception(f"❌ 发生致命错误: {e}")

        if "--json" in sys.argv:
            import json
            output = {
                "success": False,
                "error": str(e),
                "result": "No"
            }
            print(json.dumps(output, ensure_ascii=False))
        else:
            print(f"错误: {e}")
            print("No")

        return False


if __name__ == "__main__":
    import sys

    # 支持命令行参数
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Step1 - 任务初始化模块

用法:
    python step1_v2.py [选项]

选项:
    --help, -h     显示帮助信息
    --json         以 JSON 格式输出结果
    --config PATH  指定配置文件路径（默认: config.yaml）

示例:
    python step1_v2.py
    python step1_v2.py --json
    python step1_v2.py --config custom_config.yaml
        """)
        sys.exit(0)

    asyncio.run(main())
