"""
Mirror Analysis Module - v1.0 Core Feature

Creates isolated mirror environments for AI to analyze task progress
without polluting the actual working directory.

This is the "soul" of v1.0 autonomous system.
"""
import os
import shutil
import json
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

from src.core.agents.sdk_client import run_claude_prompt

logger = logging.getLogger(__name__)


class MirrorAnalyzer:
    """
    镜像分析器 - v1.0核心机制

    在隔离的镜像环境中让AI分析任务进度，
    返回AI的自主判断而非规则验证。
    """

    def __init__(self, work_dir: str, mirror_base: str = None):
        """
        Initialize mirror analyzer.

        Args:
            work_dir: Working directory to analyze
            mirror_base: Base directory for mirrors (default: work_dir/../mirror)
        """
        self.work_dir = Path(work_dir)

        if mirror_base:
            self.mirror_base = Path(mirror_base)
        else:
            self.mirror_base = self.work_dir.parent / "mirror"

        self.mirror_base.mkdir(parents=True, exist_ok=True)

    def create_mirror(self, mirror_name: str = None) -> Path:
        """
        Create a mirror copy of the working directory.

        Args:
            mirror_name: Name for the mirror (default: work_dir_name + _mirror)

        Returns:
            Path to the created mirror directory
        """
        if not mirror_name:
            mirror_name = f"{self.work_dir.name}_mirror"

        mirror_path = self.mirror_base / mirror_name

        # Remove existing mirror (with Windows compatibility)
        if mirror_path.exists():
            logger.debug(f"Removing existing mirror: {mirror_path}")
            self._remove_mirror_safe(mirror_path)

        # Copy work_dir to mirror
        logger.info(f"Creating mirror: {self.work_dir} -> {mirror_path}")
        shutil.copytree(self.work_dir, mirror_path)

        # Clean up sensitive files in mirror
        self._cleanup_mirror(mirror_path)

        logger.info(f"✅ Mirror created: {mirror_path}")
        return mirror_path

    def _remove_mirror_safe(self, path: Path, max_retries: int = 3):
        """
        Safely remove mirror directory with Windows file locking handling.

        Args:
            path: Path to remove
            max_retries: Maximum number of retry attempts
        """
        import time
        import stat

        def handle_remove_readonly(func, path, exc):
            """Error handler for Windows readonly files."""
            os.chmod(path, stat.S_IWRITE)
            func(path)

        for attempt in range(max_retries):
            try:
                # Try to remove with readonly handler for Windows
                shutil.rmtree(path, onerror=handle_remove_readonly)
                return
            except PermissionError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Mirror removal failed (attempt {attempt + 1}/{max_retries}): {e}")
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                else:
                    # Last resort: rename to .old instead of deleting
                    old_path = path.parent / f"{path.name}.old.{int(time.time())}"
                    logger.warning(f"Could not remove mirror, renaming to: {old_path}")
                    try:
                        path.rename(old_path)
                    except Exception as rename_error:
                        logger.error(f"Failed to rename mirror: {rename_error}")
                        raise
            except Exception as e:
                logger.error(f"Unexpected error removing mirror: {e}")
                raise

    def _cleanup_mirror(self, mirror_path: Path):
        """Remove sensitive files from mirror."""
        # Remove session files
        session_files = [
            "session_id.txt",
            ".session",
            "execution_state.json"
        ]

        for file_name in session_files:
            file_path = mirror_path / file_name
            if file_path.exists():
                file_path.unlink()
                logger.debug(f"Cleaned from mirror: {file_name}")

    async def ai_analyze_progress(
        self,
        goal: str,
        role_name: str = None,
        context: str = None,
        model: str = None,
        timeout: int = 120
    ) -> Tuple[bool, str, str]:
        """
        让AI在镜像环境中分析任务进度（v1.0核心机制）

        Args:
            goal: Task goal to evaluate
            role_name: Role name (for context)
            context: Additional context for AI
            model: Claude model to use
            timeout: Timeout in seconds

        Returns:
            Tuple of (completed, next_action, analysis)
            - completed: bool - AI判断任务是否完成得好
            - next_action: str - AI建议的下一步行动
            - analysis: str - AI的分析说明
        """
        # Create mirror for analysis
        mirror_name = f"{role_name}_mirror" if role_name else "analysis_mirror"

        logger.info(f"\n{'='*70}")
        logger.info(f"🔍 AI AUTONOMOUS ANALYSIS - Mirror Environment")
        logger.info(f"{'='*70}")
        logger.info(f"📁 Creating mirror for isolated analysis...")

        mirror_path = self.create_mirror(mirror_name)
        logger.info(f"✅ Mirror created: {mirror_path}")
        logger.info(f"🎯 Analyzing goal: {goal[:100]}{'...' if len(goal) > 100 else ''}")
        if role_name:
            logger.info(f"👤 Role: {role_name}")

        # Construct AI analysis prompt
        prompt = self._build_analysis_prompt(goal, role_name, context)
        logger.info(f"📝 AI analysis prompt prepared ({len(prompt)} chars)")

        try:
            logger.info(f"🤖 Invoking Claude AI for analysis...")
            # Run Claude in mirror environment
            response_text, _ = await run_claude_prompt(
                prompt=prompt,
                work_dir=str(mirror_path),  # ← Fixed: use work_dir instead of cwd
                model=model,
                permission_mode="bypassPermissions",
                timeout=timeout
            )

            logger.info(f"✅ AI analysis completed, parsing response...")

            # Parse AI's JSON response
            completed, next_action, analysis, result_dict = self._parse_ai_response(response_text)

            # Extract additional details
            quality_score = result_dict.get("quality_score", 0)
            improvement_suggestions = result_dict.get("improvement_suggestions", [])

            # Display detailed analysis results
            logger.info(f"\n{'─'*70}")
            logger.info(f"📊 AI JUDGMENT RESULTS")
            logger.info(f"{'─'*70}")
            logger.info(f"🎯 Quality Score: {quality_score}/10")

            if quality_score >= 8:
                logger.info(f"✅ Status: EXCELLENT - Task can be completed")
            elif quality_score >= 6:
                logger.info(f"⚠️  Status: GOOD - Minor improvements suggested")
            elif quality_score >= 4:
                logger.info(f"❌ Status: AVERAGE - Significant improvements needed")
            else:
                logger.info(f"🔴 Status: POOR - Major rework required")

            logger.info(f"")
            logger.info(f"AI Decision: {'✅ COMPLETED' if completed else '⏳ CONTINUE IMPROVING'}")
            logger.info(f"")
            logger.info(f"📝 AI Analysis:")
            # Format analysis text with indentation
            for line in analysis.split('\n'):
                if line.strip():
                    logger.info(f"   {line.strip()}")

            if not completed:
                logger.info(f"")
                logger.info(f"💡 Next Action Suggested:")
                logger.info(f"   {next_action}")

            if improvement_suggestions:
                logger.info(f"")
                logger.info(f"🔧 Improvement Suggestions:")
                for i, suggestion in enumerate(improvement_suggestions, 1):
                    logger.info(f"   {i}. {suggestion}")

            logger.info(f"{'='*70}\n")

            return completed, next_action, analysis

        except Exception as e:
            logger.error(f"\n{'!'*70}")
            logger.error(f"❌ AI ANALYSIS FAILED")
            logger.error(f"{'!'*70}")
            logger.error(f"Error: {e}")
            logger.error(f"{'!'*70}\n")
            # Fallback: assume not completed
            return False, "AI分析出错，请检查工作目录并继续", str(e)

    def _build_analysis_prompt(
        self,
        goal: str,
        role_name: str = None,
        context: str = None
    ) -> str:
        """
        构建AI分析提示词（v1.0风格）
        """
        role_context = f"作为 **{role_name}** 角色，" if role_name else ""
        additional_context = f"\n\n补充信息：\n{context}" if context else ""

        prompt = f"""
请分析当前工作目录中的文件和内容，判断以下任务的完成情况：

**任务目标**：{goal}

{role_context}你需要评估：
1. 当前任务是否已经完成得足够好？
2. 如果未完成或可以改进，下一步应该做什么？
3. 对当前工作成果的质量评价

{additional_context}

**重要**：请以JSON格式回复，包含以下字段：

```json
{{
    "completed": true/false,
    "next_action": "如果未完成，描述下一步具体行动；如果已完成，留空",
    "analysis": "对当前状态的详细分析和评价",
    "quality_score": 0-10,
    "improvement_suggestions": ["建议1", "建议2"]
}}
```

评分标准（quality_score）：
- 8-10分：优秀，可以完成
- 6-7分：良好，建议小幅改进
- 4-5分：一般，需要明显改进
- 0-3分：不合格，必须重做

**只有quality_score >= 8时，才设置completed=true**

请严格按照JSON格式回复，不要添加额外的说明文字。
"""
        return prompt

    def _parse_ai_response(self, response_text: str) -> Tuple[bool, str, str, Dict]:
        """
        解析AI的JSON响应

        Returns:
            (completed, next_action, analysis, result_dict)
        """
        try:
            # Extract JSON from response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                logger.warning("AI响应中未找到JSON格式")
                return False, "请检查并改进工作", "响应格式错误", {}

            json_str = response_text[start_idx:end_idx]
            result = json.loads(json_str)

            # Extract fields
            completed = result.get("completed", False)
            next_action = result.get("next_action", "")
            analysis = result.get("analysis", "")
            quality_score = result.get("quality_score", 0)

            # Ensure completed only if quality is high enough
            if completed and quality_score < 8:
                logger.debug(f"⚠️ Quality score {quality_score} < 8, overriding completed to False")
                completed = False
                if not next_action:
                    next_action = "提升质量至8分以上"

            return completed, next_action, analysis, result

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.debug(f"原始响应: {response_text[:500]}...")
            return False, "JSON解析错误，请继续工作", str(e), {}
        except Exception as e:
            logger.error(f"响应解析异常: {e}")
            return False, str(e), "解析异常", {}

    def cleanup_mirrors(self):
        """清理所有镜像目录"""
        if self.mirror_base.exists():
            shutil.rmtree(self.mirror_base)
            logger.info(f"🗑️ 已清理镜像目录: {self.mirror_base}")


# Convenience function
async def ai_judge_task_completion(
    work_dir: str,
    goal: str,
    role_name: str = None,
    context: str = None
) -> Dict:
    """
    便捷函数：使用AI判断任务完成情况（v1.0机制）

    Returns:
        {
            "completed": bool,
            "next_action": str,
            "analysis": str,
            "should_continue": bool  # True if should continue improving
        }
    """
    analyzer = MirrorAnalyzer(work_dir)

    completed, next_action, analysis, _ = await analyzer.ai_analyze_progress(
        goal=goal,
        role_name=role_name,
        context=context
    )

    return {
        "completed": completed,
        "next_action": next_action,
        "analysis": analysis,
        "should_continue": not completed
    }
