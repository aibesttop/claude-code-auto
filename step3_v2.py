"""
Step3 优化版本 - 自主循环控制器
改进点:
- P0-1: 添加循环保护（最大迭代次数、超时、紧急停止）
- P0-3: 完善异常处理
- P1-4: 状态持久化和断点续传
- P1-5: 会话管理和验证
- P1-6: 使用统一日志系统
- P2-10: 添加进度显示
"""
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock
import asyncio
from pathlib import Path
from typing import Optional, Tuple
import time
from datetime import datetime

from config import get_config
from logger import get_logger
from state_manager import StateManager, WorkflowStatus
from step2_v2 import step2_decide


async def step3_execute_iteration(
    cwd_path: str,
    goal: str,
    session_id: str,
    current_iteration: int,
    max_iterations: int,
    config_path: str = "config.yaml"
) -> Tuple[bool, str]:
    """
    执行单次迭代

    Args:
        cwd_path: 工作目录
        goal: 任务目标
        session_id: 会话ID
        current_iteration: 当前迭代次数
        max_iterations: 最大迭代次数
        config_path: 配置文件路径

    Returns:
        tuple: (should_exit, new_session_id)
    """
    config = get_config(config_path)
    logger = get_logger()

    # 调用 step2 进行决策
    logger.info(f"🔍 第 {current_iteration} 轮 - 调用决策引擎...")

    completed, next_prompt, decision = await step2_decide(
        work_dir=cwd_path,
        goal=goal,
        current_iteration=current_iteration,
        max_iterations=max_iterations,
        config_path=config_path
    )

    logger.log_decision(current_iteration, session_id, decision.to_dict())

    if completed:
        logger.info(f"✅ 任务已完成！(置信度: {decision.confidence})")
        return True, session_id

    if not next_prompt:
        logger.warning("⚠️  未完成但没有下一步指令，强制退出")
        return True, session_id

    # 执行 Claude 任务
    logger.info(f"💬 第 {current_iteration} 轮 - 执行 Claude 任务...")
    logger.debug(f"提示词: {next_prompt[:100]}...")

    # 配置 Claude SDK（恢复会话）
    options = ClaudeCodeOptions(
        permission_mode=config.claude.permission_mode,
        cwd=cwd_path,
        resume=session_id
    )

    new_session_id = session_id

    try:
        async with ClaudeSDKClient(options) as client:
            await client.query(next_prompt)

            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            logger.debug(f"Claude: {block.text[:100]}...")

                    # 提取新的 session_id（如果有）
                    if hasattr(message, 'data') and message.data:
                        sid = message.data.get('session_id')
                        if sid:
                            new_session_id = sid

        logger.info(f"✅ 第 {current_iteration} 轮执行完成")

    except Exception as e:
        logger.error(f"❌ 第 {current_iteration} 轮执行失败: {e}")
        raise

    return False, new_session_id


async def step3_main_loop(
    cwd_path: str,
    goal: str,
    config_path: str = "config.yaml",
    resume: bool = True
) -> bool:
    """
    主循环控制器

    Args:
        cwd_path: 工作目录
        goal: 任务目标
        config_path: 配置文件路径
        resume: 是否恢复之前的状态

    Returns:
        bool: 是否成功完成
    """
    # 加载配置
    config = get_config(config_path)
    logger = get_logger()

    logger.info("\n" + "=" * 60)
    logger.info("启动自主循环系统 (Step 3)")
    logger.info("=" * 60)

    # 加载或创建状态
    state_manager = StateManager(config.get_state_file_path())

    # 读取会话ID
    session_file = config.get_session_file_path()
    if not session_file.exists():
        logger.error(f"❌ 会话文件不存在: {session_file}")
        logger.error("请先运行 step1 初始化任务")
        return False

    session_id = session_file.read_text(encoding='utf-8').strip()
    logger.info(f"会话ID: {session_id[:16]}...")

    # 加载状态
    if resume:
        state = state_manager.load_or_create(
            session_id=session_id,
            goal=goal,
            work_dir=cwd_path,
            max_iterations=config.safety.max_iterations
        )
        logger.info(f"已加载状态: 第 {state.current_iteration} 轮")
    else:
        state = state_manager.load_or_create(
            session_id=session_id,
            goal=goal,
            work_dir=cwd_path,
            max_iterations=config.safety.max_iterations,
            force_new=True
        )
        logger.info("创建新状态")

    # 更新状态为运行中
    state.status = WorkflowStatus.RUNNING
    state_manager.save()

    # 安全检查
    start_time = time.time()
    max_duration_seconds = config.safety.max_duration_hours * 3600
    emergency_stop_path = config.get_emergency_stop_file_path()

    logger.info(f"安全限制:")
    logger.info(f"  最大迭代次数: {config.safety.max_iterations}")
    logger.info(f"  最大时长: {config.safety.max_duration_hours} 小时")
    logger.info(f"  紧急停止文件: {emergency_stop_path}")
    logger.info(f"  单次迭代超时: {config.safety.iteration_timeout_minutes} 分钟")

    # 主循环
    continuous_errors = 0
    max_continuous_errors = 3

    while state.current_iteration < state.max_iterations:
        state.current_iteration += 1
        iteration_start_time = time.time()

        logger.info("\n" + "=" * 60)
        logger.info(f"第 {state.current_iteration}/{state.max_iterations} 轮迭代")
        logger.info(f"进度: {state.get_progress_percentage():.1f}%")
        logger.info("=" * 60)

        logger.log_iteration_start(state.current_iteration, session_id)

        try:
            # P0-1: 检查紧急停止信号
            if emergency_stop_path.exists():
                logger.warning("🛑 检测到紧急停止信号")
                state.status = WorkflowStatus.EMERGENCY_STOP
                state_manager.save()
                emergency_stop_path.unlink()  # 删除信号文件
                return False

            # P0-1: 检查超时
            elapsed_time = time.time() - start_time
            if elapsed_time > max_duration_seconds:
                logger.error(f"⏰ 超过最大执行时间 {config.safety.max_duration_hours} 小时")
                state.status = WorkflowStatus.TIMEOUT
                state_manager.save()
                return False

            # 执行单次迭代
            iteration_task = step3_execute_iteration(
                cwd_path=cwd_path,
                goal=goal,
                session_id=session_id,
                current_iteration=state.current_iteration,
                max_iterations=state.max_iterations,
                config_path=config_path
            )

            # 带超时的执行
            timeout_seconds = config.safety.iteration_timeout_minutes * 60
            should_exit, new_session_id = await asyncio.wait_for(
                iteration_task,
                timeout=timeout_seconds
            )

            # 更新会话ID
            if new_session_id != session_id:
                session_id = new_session_id
                session_file.write_text(session_id, encoding='utf-8')
                # 备份
                config.get_backup_session_file_path().write_text(session_id, encoding='utf-8')

            # 计算迭代时长
            iteration_duration = time.time() - iteration_start_time

            # 记录成功的迭代
            state.add_iteration(
                decision={"completed": should_exit},
                duration=iteration_duration,
                success=True
            )
            state_manager.save()

            logger.log_iteration_end(
                state.current_iteration,
                session_id,
                True,
                iteration_duration
            )

            # 重置连续错误计数
            continuous_errors = 0

            # 检查是否应该退出
            if should_exit:
                logger.info("🎉 任务完成，正常退出")
                state.status = WorkflowStatus.COMPLETED
                state_manager.save()
                state.print_summary()
                return True

        except asyncio.TimeoutError:
            logger.error(f"⏰ 第 {state.current_iteration} 轮超时")
            continuous_errors += 1

            state.add_iteration(
                decision={"error": "timeout"},
                duration=config.safety.iteration_timeout_minutes * 60,
                success=False,
                error="迭代超时"
            )
            state_manager.save()

        except Exception as e:
            iteration_duration = time.time() - iteration_start_time
            logger.exception(f"❌ 第 {state.current_iteration} 轮执行失败")
            continuous_errors += 1

            state.add_iteration(
                decision={"error": str(e)},
                duration=iteration_duration,
                success=False,
                error=str(e)
            )
            state_manager.save()

            logger.log_error_with_retry(
                state.current_iteration,
                session_id,
                e,
                continuous_errors,
                max_continuous_errors
            )

        # 检查连续错误
        if continuous_errors >= max_continuous_errors:
            logger.critical(f"❌ 连续 {max_continuous_errors} 次失败，终止执行")
            state.status = WorkflowStatus.FAILED
            state_manager.save()
            return False

        # 错误后延迟
        if continuous_errors > 0:
            delay = config.error_handling.retry_delay_seconds * continuous_errors
            logger.info(f"等待 {delay} 秒后继续...")
            await asyncio.sleep(delay)

    # 达到最大迭代次数
    logger.warning(f"⚠️  达到最大迭代次数 {state.max_iterations}")
    state.status = WorkflowStatus.COMPLETED  # 或 TIMEOUT
    state_manager.save()
    state.print_summary()

    return False


async def main(
    cwd_path: str = "demo_act",
    goal: str = "调研一下慢性病",
    resume: bool = True
):
    """主函数"""
    try:
        success = await step3_main_loop(
            cwd_path=cwd_path,
            goal=goal,
            resume=resume
        )

        print(f"\n{'=' * 60}")
        print(f"执行结果: {'成功' if success else '失败/未完成'}")
        print(f"{'=' * 60}\n")

        return success

    except Exception as e:
        logger = get_logger()
        logger.critical(f"❌ 致命错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys

    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
Step3 - 自主循环控制器

用法:
    python step3_v2.py [选项]

选项:
    --help, -h       显示帮助信息
    --no-resume      不恢复之前的状态，从头开始
    --config PATH    指定配置文件路径

紧急停止:
    创建文件 .emergency_stop 可以安全地停止循环

示例:
    python step3_v2.py
    python step3_v2.py --no-resume
        """)
        sys.exit(0)

    resume = "--no-resume" not in sys.argv

    asyncio.run(main(resume=resume))
