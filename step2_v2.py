"""
Step2 优化版本 - 智能决策引擎
改进点:
- P0-2: 使用强化的 JSON 解析器
- P0-3: 完善异常处理
- P2-8: 支持增量同步（可选）
- P2-9: 改进提示词工程
- P1-6: 使用统一日志系统
"""
import os
import shutil
from pathlib import Path
from typing import Tuple
import filecmp
from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions, AssistantMessage, TextBlock
import asyncio

from config import get_config
from logger import get_logger
from json_parser import parse_decision_response, DecisionResponse, JsonParseError


# 改进的提示词模板
DECISION_PROMPT_TEMPLATE = """
你是一个任务执行评估专家。请分析当前工作目录中的文件，判断以下任务的完成状态。

**任务目标**: {goal}

**当前迭代**: {current_iteration}/{max_iterations}

**评估标准**:
1. 检查是否有相关文件生成（文档/代码/数据等）
2. 文件内容是否完整且符合要求
3. 是否有明显的遗漏或错误

**决策指南**:
- 如果任务 >80% 完成，设置 completed=true
- 如果需要继续，在 next_prompt 中明确指出缺失内容
- 使用 confidence 字段表示你的确定程度（0-1）

**输出格式** (必须严格遵守JSON格式，使用 ```json 代码块):
```json
{{
    "completed": true/false,
    "next_prompt": "具体的下一步指令，如果完成则留空",
    "analysis": "详细分析当前状态、已完成内容、剩余工作",
    "confidence": 0.9
}}
```

**示例1** (未完成):
```json
{{
    "completed": false,
    "next_prompt": "请补充文档的第3章节'实施方案'，需包含时间线和资源分配",
    "analysis": "已完成文档框架和前2章，缺少第3章内容",
    "confidence": 0.95
}}
```

**示例2** (已完成):
```json
{{
    "completed": true,
    "next_prompt": "",
    "analysis": "文档已完整生成，包含所有必要章节，格式规范",
    "confidence": 0.9
}}
```

现在开始评估:
"""


def incremental_sync(
    src: Path,
    dst: Path,
    exclude_patterns: list
) -> int:
    """
    增量同步文件（只复制变更的文件）

    Args:
        src: 源目录
        dst: 目标目录
        exclude_patterns: 排除模式列表

    Returns:
        int: 复制的文件数量
    """
    logger = get_logger()
    copied_files = 0

    # 确保目标目录存在
    dst.mkdir(parents=True, exist_ok=True)

    def should_exclude(file_path: Path) -> bool:
        """检查文件是否应该被排除"""
        name = file_path.name
        for pattern in exclude_patterns:
            if pattern.startswith('*.'):
                # 扩展名匹配
                ext = pattern[1:]  # 去掉 *
                if name.endswith(ext):
                    return True
            elif pattern == name or pattern in str(file_path):
                return True
        return False

    # 遍历源目录
    for src_file in src.rglob('*'):
        if src_file.is_file():
            # 检查是否排除
            if should_exclude(src_file):
                continue

            # 计算相对路径
            rel_path = src_file.relative_to(src)
            dst_file = dst / rel_path

            # 确保目标文件的父目录存在
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            # 检查是否需要复制
            need_copy = False
            if not dst_file.exists():
                need_copy = True
            else:
                # 比较修改时间和大小
                src_stat = src_file.stat()
                dst_stat = dst_file.stat()
                if src_stat.st_mtime > dst_stat.st_mtime or src_stat.st_size != dst_stat.st_size:
                    need_copy = True

            if need_copy:
                shutil.copy2(src_file, dst_file)
                copied_files += 1
                logger.debug(f"已复制: {rel_path}")

    return copied_files


async def step2_decide(
    work_dir: str,
    goal: str,
    current_iteration: int = 1,
    max_iterations: int = 50,
    config_path: str = "config.yaml"
) -> Tuple[bool, str, DecisionResponse]:
    """
    执行决策分析

    Args:
        work_dir: 工作目录
        goal: 任务目标
        current_iteration: 当前迭代次数
        max_iterations: 最大迭代次数
        config_path: 配置文件路径

    Returns:
        tuple: (is_completed, next_prompt, full_decision)

    Raises:
        RuntimeError: 决策失败
    """
    # 加载配置
    config = get_config(config_path)
    logger = get_logger()

    logger.info("=" * 60)
    logger.info(f"开始决策分析 (Step 2) - 第 {current_iteration} 轮")
    logger.info("=" * 60)

    work_dir_path = Path(work_dir)
    mirror_dir_path = config.get_mirror_dir_path()

    # 计算镜像目录名称
    base_name = work_dir_path.name
    mirror_path = mirror_dir_path / f"{base_name}_mirror"

    logger.info(f"工作目录: {work_dir_path}")
    logger.info(f"镜像目录: {mirror_path}")

    retry_count = 0
    max_retries = config.error_handling.max_retries

    while retry_count <= max_retries:
        try:
            # 同步文件到镜像目录
            logger.info("开始同步文件...")

            if config.performance.use_incremental_sync and mirror_path.exists():
                # 使用增量同步
                copied = incremental_sync(
                    work_dir_path,
                    mirror_path,
                    config.performance.exclude_patterns
                )
                logger.info(f"✅ 增量同步完成，复制了 {copied} 个文件")
            else:
                # 完整复制
                if mirror_path.exists():
                    logger.debug(f"删除旧镜像: {mirror_path}")
                    shutil.rmtree(mirror_path)

                logger.debug(f"完整复制: {work_dir_path} -> {mirror_path}")
                shutil.copytree(
                    work_dir_path,
                    mirror_path,
                    ignore=shutil.ignore_patterns(*config.performance.exclude_patterns)
                )
                logger.info("✅ 完整复制完成")

            # 构建提示词
            prompt = DECISION_PROMPT_TEMPLATE.format(
                goal=goal,
                current_iteration=current_iteration,
                max_iterations=max_iterations
            )

            logger.debug(f"提示词长度: {len(prompt)} 字符")

            # 配置 Claude SDK
            options = ClaudeCodeOptions(
                permission_mode=config.claude.permission_mode,
                cwd=str(mirror_path)
            )

            # 调用 Claude 进行分析
            logger.info("调用 Claude 进行决策分析...")
            response_text = ""

            async with ClaudeSDKClient(options) as client:
                await client.query(prompt)

                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                response_text += block.text + "\n"
                                logger.debug(f"Claude: {block.text[:100]}...")

            # 解析 JSON 响应
            logger.info("解析决策结果...")
            decision = parse_decision_response(
                response_text,
                max_retries=config.json_parser.max_parse_retries,
                strict_mode=config.json_parser.strict_mode
            )

            logger.info(f"✅ 解析成功:")
            logger.info(f"   completed: {decision.completed}")
            logger.info(f"   confidence: {decision.confidence}")
            logger.info(f"   next_prompt: {decision.next_prompt[:100] if decision.next_prompt else '(空)'}")

            # 验证决策合理性
            if decision.completed and decision.confidence < 0.7:
                logger.warning(f"⚠️  决策置信度较低: {decision.confidence}")

            return decision.completed, decision.next_prompt, decision

        except JsonParseError as e:
            retry_count += 1
            logger.error(f"JSON 解析失败 (尝试 {retry_count}/{max_retries + 1}): {e}")

            if retry_count <= max_retries:
                delay = config.error_handling.retry_delay_seconds
                logger.info(f"等待 {delay} 秒后重试...")
                await asyncio.sleep(delay)
            else:
                logger.critical("❌ 达到最大重试次数，决策失败")
                raise RuntimeError(f"JSON 解析失败: {e}")

        except Exception as e:
            retry_count += 1
            logger.error(f"决策失败 (尝试 {retry_count}/{max_retries + 1}): {e}")

            if retry_count <= max_retries:
                delay = config.error_handling.retry_delay_seconds
                logger.info(f"等待 {delay} 秒后重试...")
                await asyncio.sleep(delay)
            else:
                logger.critical(f"❌ 达到最大重试次数: {e}")
                raise RuntimeError(f"决策失败: {e}")

    # 不应该到这里
    raise RuntimeError("未知错误")


# 示例调用
if __name__ == "__main__":
    import asyncio

    async def main():
        try:
            completed, next_prompt, decision = await step2_decide(
                work_dir="demo_act",
                goal="调研一下慢性病",
                current_iteration=1,
                max_iterations=50
            )

            print(f"\n{'=' * 60}")
            print(f"决策结果:")
            print(f"  完成状态: {completed}")
            print(f"  置信度: {decision.confidence}")
            print(f"  下一步: {next_prompt}")
            print(f"  分析: {decision.analysis}")
            print(f"{'=' * 60}")

        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

    asyncio.run(main())
