"""
Recovery Guide Generator - 恢复指南生成器

基于终态生成详细的恢复指南和行动建议
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path

from src.utils.logger import get_logger
from .terminal_state_manager import TerminalState, TerminalStateType

logger = get_logger()


@dataclass
class RecoveryGuide:
    """恢复指南"""
    mission_id: str
    terminal_state_type: TerminalStateType

    # 诊断分析
    diagnosis: str
    root_cause: str

    # 恢复步骤
    recovery_steps: List[Dict[str, str]] = field(default_factory=list)

    # 资源需求
    estimated_cost_usd: float = 0.0
    estimated_duration_minutes: float = 0.0

    # 风险和注意事项
    risks: List[str] = field(default_factory=list)
    precautions: List[str] = field(default_factory=list)

    # 替代方案
    alternatives: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md_lines = [
            f"# Recovery Guide: {self.mission_id}",
            "",
            f"## Status: {self.terminal_state_type.value}",
            "",
            "## Diagnosis",
            "",
            self.diagnosis,
            "",
            "## Root Cause",
            "",
            self.root_cause,
            "",
            "## Recovery Steps",
            ""
        ]

        # 恢复步骤
        for i, step in enumerate(self.recovery_steps, 1):
            md_lines.append(f"### Step {i}: {step['title']}")
            md_lines.append("")
            md_lines.append(step['description'])
            md_lines.append("")
            if 'command' in step:
                md_lines.append("```bash")
                md_lines.append(step['command'])
                md_lines.append("```")
                md_lines.append("")

        # 资源估计
        md_lines.extend([
            "## Resource Estimation",
            "",
            f"- **Estimated Cost**: ${self.estimated_cost_usd:.4f}",
            f"- **Estimated Duration**: {self.estimated_duration_minutes:.0f} minutes",
            ""
        ])

        # 风险
        if self.risks:
            md_lines.extend([
                "## Risks",
                ""
            ])
            for risk in self.risks:
                md_lines.append(f"- {risk}")
            md_lines.append("")

        # 注意事项
        if self.precautions:
            md_lines.extend([
                "## Precautions",
                ""
            ])
            for precaution in self.precautions:
                md_lines.append(f"- {precaution}")
            md_lines.append("")

        # 替代方案
        if self.alternatives:
            md_lines.extend([
                "## Alternative Approaches",
                ""
            ])
            for alt in self.alternatives:
                md_lines.append(f"- {alt}")
            md_lines.append("")

        return "\n".join(md_lines)


class RecoveryGuideGenerator:
    """恢复指南生成器"""

    def __init__(self):
        """初始化恢复指南生成器"""
        logger.info("RecoveryGuideGenerator initialized")

    def generate_guide(
        self,
        terminal_state: TerminalState,
        checkpoint_available: bool = False
    ) -> RecoveryGuide:
        """
        生成恢复指南

        Args:
            terminal_state: 终态
            checkpoint_available: 是否有检查点可用

        Returns:
            RecoveryGuide实例
        """
        logger.info(
            f"Generating recovery guide for {terminal_state.mission_id}, "
            f"state={terminal_state.state_type.value}"
        )

        guide = RecoveryGuide(
            mission_id=terminal_state.mission_id,
            terminal_state_type=terminal_state.state_type
        )

        # 根据终态类型生成不同的指南
        if terminal_state.state_type == TerminalStateType.PARTIAL_SUCCESS:
            self._generate_partial_success_guide(guide, terminal_state, checkpoint_available)

        elif terminal_state.state_type == TerminalStateType.TIMEOUT:
            self._generate_timeout_guide(guide, terminal_state)

        elif terminal_state.state_type == TerminalStateType.BUDGET_EXCEEDED:
            self._generate_budget_exceeded_guide(guide, terminal_state)

        elif terminal_state.state_type == TerminalStateType.BLOCKED:
            self._generate_blocked_guide(guide, terminal_state)

        elif terminal_state.state_type == TerminalStateType.FAILED:
            self._generate_failed_guide(guide, terminal_state)

        else:
            self._generate_generic_guide(guide, terminal_state)

        logger.info(
            f"Generated recovery guide with {len(guide.recovery_steps)} steps"
        )

        return guide

    def _generate_partial_success_guide(
        self,
        guide: RecoveryGuide,
        state: TerminalState,
        checkpoint_available: bool
    ):
        """生成部分成功恢复指南"""
        guide.diagnosis = (
            f"任务已完成 {state.completion_ratio:.1%}，产出了部分可用结果。"
        )

        guide.root_cause = state.termination_reason or "任务未能完全完成"

        # 恢复步骤
        if checkpoint_available:
            guide.recovery_steps.append({
                "title": "从检查点恢复",
                "description": "使用CheckpointManager加载最新检查点并继续执行",
                "command": f"python -m src.core.recovery.checkpoint_manager resume {state.mission_id}"
            })
        else:
            guide.recovery_steps.append({
                "title": "分析已完成步骤",
                "description": f"已完成: {', '.join(state.completed_steps[:5])}"
            })

        guide.recovery_steps.append({
            "title": "继续执行剩余步骤",
            "description": f"待完成步骤: {', '.join(state.pending_steps[:5])}"
        })

        if state.partial_outputs:
            guide.recovery_steps.append({
                "title": "验证部分输出",
                "description": f"检查并验证 {len(state.partial_outputs)} 个部分输出的正确性"
            })

        # 资源估计
        remaining_ratio = 1.0 - state.completion_ratio
        guide.estimated_cost_usd = state.total_cost_usd * remaining_ratio
        guide.estimated_duration_minutes = state.duration_seconds / 60 * remaining_ratio

        # 注意事项
        guide.precautions.append("确保已保存的部分结果可用")
        guide.precautions.append("检查是否有依赖关系需要满足")

        # 替代方案
        guide.alternatives.append("从头重新执行整个任务")
        guide.alternatives.append("手动完成剩余步骤")

    def _generate_timeout_guide(
        self,
        guide: RecoveryGuide,
        state: TerminalState
    ):
        """生成超时恢复指南"""
        guide.diagnosis = "任务因超时而终止"

        guide.root_cause = (
            f"执行时间超过限制 ({state.duration_seconds:.0f}秒)"
        )

        # 恢复步骤
        guide.recovery_steps.append({
            "title": "增加时间限制",
            "description": "在任务配置中增加timeout_seconds参数"
        })

        guide.recovery_steps.append({
            "title": "分析性能瓶颈",
            "description": "检查日志找出耗时最长的操作"
        })

        guide.recovery_steps.append({
            "title": "优化执行流程",
            "description": "考虑并行执行、缓存或简化步骤"
        })

        guide.recovery_steps.append({
            "title": "重新执行",
            "description": "使用优化后的配置重新执行任务"
        })

        # 风险
        guide.risks.append("即使增加时间限制，可能仍会超时")
        guide.risks.append("性能瓶颈可能无法轻易解决")

        # 替代方案
        guide.alternatives.append("将任务拆分为多个小任务")
        guide.alternatives.append("使用更快的模型或工具")

    def _generate_budget_exceeded_guide(
        self,
        guide: RecoveryGuide,
        state: TerminalState
    ):
        """生成预算超支恢复指南"""
        guide.diagnosis = "任务因预算超支而终止"

        guide.root_cause = (
            f"成本 ${state.total_cost_usd:.4f} 超过预算限制"
        )

        # 恢复步骤
        guide.recovery_steps.append({
            "title": "增加预算",
            "description": "在预算控制器中为该任务分配更多预算"
        })

        guide.recovery_steps.append({
            "title": "分析成本分布",
            "description": "查看哪些角色或操作消耗了最多成本"
        })

        guide.recovery_steps.append({
            "title": "优化成本",
            "description": "使用更便宜的模型、减少API调用次数或优化提示词"
        })

        guide.recovery_steps.append({
            "title": "重新执行",
            "description": "使用优化后的配置重新执行任务"
        })

        # 资源估计
        guide.estimated_cost_usd = state.total_cost_usd * 0.5  # 估计还需50%成本

        # 风险
        guide.risks.append("优化后仍可能超预算")

        # 替代方案
        guide.alternatives.append("降低任务复杂度")
        guide.alternatives.append("使用本地工具替代API调用")

    def _generate_blocked_guide(
        self,
        guide: RecoveryGuide,
        state: TerminalState
    ):
        """生成阻塞恢复指南"""
        guide.diagnosis = "任务被阻塞，无法继续执行"

        guide.root_cause = state.termination_reason or "依赖关系未满足或资源不可用"

        # 恢复步骤
        guide.recovery_steps.append({
            "title": "检查依赖",
            "description": "确认所有依赖的任务是否已完成"
        })

        if state.failed_steps:
            guide.recovery_steps.append({
                "title": "修复失败步骤",
                "description": f"修复以下失败步骤: {', '.join(state.failed_steps)}"
            })

        guide.recovery_steps.append({
            "title": "验证资源可用性",
            "description": "检查文件、API、工具等资源是否可访问"
        })

        guide.recovery_steps.append({
            "title": "重新执行",
            "description": "解决阻塞问题后重新执行任务"
        })

        # 风险
        guide.risks.append("阻塞问题可能难以快速解决")

        # 替代方案
        guide.alternatives.append("跳过阻塞步骤，手动完成")
        guide.alternatives.append("调整任务依赖关系")

    def _generate_failed_guide(
        self,
        guide: RecoveryGuide,
        state: TerminalState
    ):
        """生成失败恢复指南"""
        guide.diagnosis = "任务执行失败"

        guide.root_cause = (
            state.error_details or state.termination_reason or "未知错误"
        )

        # 恢复步骤
        guide.recovery_steps.append({
            "title": "分析错误日志",
            "description": "查看详细的错误堆栈和日志"
        })

        guide.recovery_steps.append({
            "title": "修复问题",
            "description": "根据错误信息修复代码、配置或数据问题"
        })

        guide.recovery_steps.append({
            "title": "验证修复",
            "description": "在小范围内测试修复是否有效"
        })

        guide.recovery_steps.append({
            "title": "重新执行",
            "description": "修复后重新执行任务"
        })

        # 风险
        guide.risks.append("修复可能引入新问题")

        # 注意事项
        guide.precautions.append("在重试前先进行小规模测试")

        # 替代方案
        guide.alternatives.append("使用不同的工具或方法")
        guide.alternatives.append("寻求人工介入")

    def _generate_generic_guide(
        self,
        guide: RecoveryGuide,
        state: TerminalState
    ):
        """生成通用恢复指南"""
        guide.diagnosis = f"任务以 {state.state_type.value} 状态结束"

        guide.root_cause = state.termination_reason or "未知原因"

        guide.recovery_steps.append({
            "title": "检查任务状态",
            "description": "查看任务的详细状态和日志"
        })

        guide.recovery_steps.append({
            "title": "评估下一步",
            "description": "根据具体情况决定是否需要重试或调整"
        })

    def save_guide(
        self,
        guide: RecoveryGuide,
        output_path: Path
    ):
        """
        保存恢复指南到文件

        Args:
            guide: 恢复指南
            output_path: 输出路径
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(guide.to_markdown())

            logger.info(f"Saved recovery guide to {output_path}")

        except Exception as e:
            logger.error(f"Failed to save recovery guide: {e}")


# 全局单例
_recovery_guide_generator_instance: Optional[RecoveryGuideGenerator] = None


def get_recovery_guide_generator() -> RecoveryGuideGenerator:
    """获取全局恢复指南生成器实例"""
    global _recovery_guide_generator_instance
    if _recovery_guide_generator_instance is None:
        _recovery_guide_generator_instance = RecoveryGuideGenerator()
    return _recovery_guide_generator_instance
