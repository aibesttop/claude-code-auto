"""
Report Generator - 报告生成器

提供多种报告模板和生成策略
"""
from enum import Enum
from typing import Optional
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger()


class ReportTemplate(str, Enum):
    """报告模板类型"""
    COMPREHENSIVE = "comprehensive"  # 综合报告（完整详细）
    EXECUTIVE = "executive"          # 执行摘要（高层概览）
    TECHNICAL = "technical"          # 技术报告（开发者视角）
    SIMPLE = "simple"                # 简单报告（基础信息）


class ReportGenerator:
    """
    报告生成器

    支持多种报告模板和样式
    """

    def __init__(self):
        """初始化报告生成器"""
        logger.info("ReportGenerator initialized")

    def generate(
        self,
        integrated_output,
        template: ReportTemplate = ReportTemplate.COMPREHENSIVE
    ) -> str:
        """
        生成报告

        Args:
            integrated_output: IntegratedOutput对象
            template: 报告模板类型

        Returns:
            Markdown格式的报告内容
        """
        if template == ReportTemplate.COMPREHENSIVE:
            return self._generate_comprehensive_report(integrated_output)
        elif template == ReportTemplate.EXECUTIVE:
            return self._generate_executive_report(integrated_output)
        elif template == ReportTemplate.TECHNICAL:
            return self._generate_technical_report(integrated_output)
        else:  # SIMPLE
            return self._generate_simple_report(integrated_output)

    def _generate_comprehensive_report(self, output) -> str:
        """生成综合报告（最详细）"""
        lines = []

        # 标题和元信息
        lines.extend(self._generate_header(output))

        # 执行摘要
        lines.extend(self._generate_executive_summary(output))

        # 关键指标
        lines.extend(self._generate_key_metrics(output))

        # 任务详情
        lines.extend(self._generate_mission_details(output))

        # 质量分析
        lines.extend(self._generate_quality_analysis(output))

        # 成本分析
        lines.extend(self._generate_cost_analysis(output))

        # 时间线
        lines.extend(self._generate_timeline(output))

        # 交付物清单
        lines.extend(self._generate_deliverables_list(output))

        # 建议和下一步
        lines.extend(self._generate_recommendations(output))

        # 页脚
        lines.extend(self._generate_footer(output))

        return "\n".join(lines)

    def _generate_executive_report(self, output) -> str:
        """生成执行摘要报告"""
        lines = []

        lines.extend(self._generate_header(output))
        lines.extend(self._generate_executive_summary(output))
        lines.extend(self._generate_key_metrics(output))
        lines.extend(self._generate_deliverables_list(output))
        lines.extend(self._generate_footer(output))

        return "\n".join(lines)

    def _generate_technical_report(self, output) -> str:
        """生成技术报告"""
        lines = []

        lines.extend(self._generate_header(output))
        lines.extend(self._generate_mission_details(output))
        lines.extend(self._generate_quality_analysis(output))
        lines.extend(self._generate_cost_analysis(output))
        lines.extend(self._generate_timeline(output))
        lines.extend(self._generate_footer(output))

        return "\n".join(lines)

    def _generate_simple_report(self, output) -> str:
        """生成简单报告"""
        lines = []

        lines.extend(self._generate_header(output))
        lines.extend(self._generate_key_metrics(output))
        lines.extend([
            "## 📋 任务列表",
            ""
        ])

        for i, mission in enumerate(output.mission_outputs, 1):
            status = "✅" if mission.success else "❌"
            lines.append(f"{i}. {status} **{mission.mission_id}** - {mission.goal}")

        lines.extend(["", "---", ""])
        lines.extend(self._generate_footer(output))

        return "\n".join(lines)

    def _generate_header(self, output) -> list:
        """生成报告头部"""
        return [
            f"# 🎯 任务执行报告",
            "",
            f"**会话ID**: `{output.session_id}`  ",
            f"**生成时间**: {output.summary.get('timestamp', 'N/A')}  ",
            "",
            "---",
            ""
        ]

    def _generate_executive_summary(self, output) -> list:
        """生成执行摘要"""
        summary = output.summary
        success_rate = summary.get('success_rate', 0.0)

        # 状态徽章
        if success_rate >= 0.9:
            status_badge = "🟢 **优秀**"
        elif success_rate >= 0.7:
            status_badge = "🟡 **良好**"
        elif success_rate >= 0.5:
            status_badge = "🟠 **一般**"
        else:
            status_badge = "🔴 **需改进**"

        return [
            "## 📊 执行摘要",
            "",
            f"**目标**: {output.goal}",
            "",
            f"**整体状态**: {status_badge} (成功率: {success_rate:.1%})",
            "",
            "### 快速统计",
            "",
            f"- 📦 **总任务数**: {summary.get('total_missions', 0)}",
            f"- ✅ **成功任务**: {summary.get('successful_missions', 0)}",
            f"- ❌ **失败任务**: {summary.get('failed_missions', 0)}",
            f"- 📄 **生成文件**: {summary.get('total_files_generated', 0)}个",
            f"- ⭐ **平均质量**: {summary.get('average_quality_score', 0):.1f}/100",
            f"- 💰 **总成本**: ${summary.get('total_cost_usd', 0):.4f}",
            f"- ⏱️ **总耗时**: {summary.get('total_duration_seconds', 0):.1f}秒",
            "",
            "---",
            ""
        ]

    def _generate_key_metrics(self, output) -> list:
        """生成关键指标"""
        summary = output.summary

        total = summary.get('total_missions', 1)
        successful = summary.get('successful_missions', 0)
        failed = summary.get('failed_missions', 0)

        # 计算百分比
        success_pct = (successful / total * 100) if total > 0 else 0
        fail_pct = (failed / total * 100) if total > 0 else 0

        # 生成进度条
        success_bar = self._generate_progress_bar(success_pct, 20)
        fail_bar = self._generate_progress_bar(fail_pct, 20)

        return [
            "## 📈 关键指标",
            "",
            "### 任务完成率",
            "",
            f"**成功** ({successful}/{total}): {success_bar} {success_pct:.1f}%  ",
            f"**失败** ({failed}/{total}): {fail_bar} {fail_pct:.1f}%  ",
            "",
            "### 资源消耗",
            "",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 💰 总成本 | ${summary.get('total_cost_usd', 0):.4f} |",
            f"| ⏱️ 总耗时 | {summary.get('total_duration_seconds', 0):.1f}秒 |",
            f"| 📄 生成文件 | {summary.get('total_files_generated', 0)}个 |",
            f"| ⭐ 平均质量 | {summary.get('average_quality_score', 0):.1f}/100 |",
            "",
            "---",
            ""
        ]

    def _generate_mission_details(self, output) -> list:
        """生成任务详情"""
        lines = [
            "## 📋 任务详情",
            ""
        ]

        for i, mission in enumerate(output.mission_outputs, 1):
            # 状态徽章
            if mission.success:
                status_badge = "✅ 成功"
                status_color = "🟢"
            else:
                status_badge = "❌ 失败"
                status_color = "🔴"

            # 质量等级
            quality_grade = self._get_quality_grade(mission.quality_score)

            lines.extend([
                f"### {i}. {status_color} {mission.mission_id}",
                "",
                f"**状态**: {status_badge}  ",
                f"**类型**: {mission.mission_type}  ",
                f"**角色**: {mission.role}  ",
                "",
                f"**目标**: {mission.goal}",
                "",
                "**执行指标**:",
                "",
                f"- 🔄 迭代次数: {mission.iterations}",
                f"- ⭐ 质量分数: {mission.quality_score:.1f}/100 ({quality_grade})",
                f"- 💰 成本: ${mission.cost_usd:.4f}",
                f"- ⏱️ 耗时: {mission.duration_seconds:.1f}秒",
                ""
            ])

            # 输出文件
            if mission.files:
                lines.extend([
                    "**生成文件**:",
                    ""
                ])
                for filename in mission.files.keys():
                    lines.append(f"- 📄 `{filename}`")
                lines.append("")

            # 验证错误
            if mission.validation_errors:
                lines.extend([
                    "**验证问题**:",
                    ""
                ])
                for error in mission.validation_errors:
                    lines.append(f"- ⚠️ {error}")
                lines.append("")

            lines.extend(["---", ""])

        return lines

    def _generate_quality_analysis(self, output) -> list:
        """生成质量分析"""
        lines = [
            "## 🎯 质量分析",
            ""
        ]

        # 质量分布
        quality_distribution = {
            "优秀 (90-100)": 0,
            "良好 (70-89)": 0,
            "一般 (50-69)": 0,
            "较差 (<50)": 0
        }

        for mission in output.mission_outputs:
            score = mission.quality_score
            if score >= 90:
                quality_distribution["优秀 (90-100)"] += 1
            elif score >= 70:
                quality_distribution["良好 (70-89)"] += 1
            elif score >= 50:
                quality_distribution["一般 (50-69)"] += 1
            else:
                quality_distribution["较差 (<50)"] += 1

        lines.extend([
            "### 质量分布",
            "",
            "| 等级 | 数量 |",
            "|------|------|"
        ])

        for grade, count in quality_distribution.items():
            lines.append(f"| {grade} | {count} |")

        lines.extend([
            "",
            "### 质量趋势",
            ""
        ])

        # 按任务顺序显示质量分数
        for i, mission in enumerate(output.mission_outputs, 1):
            quality_bar = self._generate_progress_bar(mission.quality_score, 10)
            lines.append(
                f"{i}. {mission.mission_id}: {quality_bar} {mission.quality_score:.1f}"
            )

        lines.extend(["", "---", ""])

        return lines

    def _generate_cost_analysis(self, output) -> list:
        """生成成本分析"""
        lines = [
            "## 💰 成本分析",
            ""
        ]

        total_cost = output.summary.get('total_cost_usd', 0)

        if total_cost > 0:
            lines.extend([
                f"**总成本**: ${total_cost:.4f}",
                "",
                "### 按任务分解",
                "",
                "| 任务 | 成本 | 占比 |",
                "|------|------|------|"
            ])

            for mission in output.mission_outputs:
                cost_pct = (mission.cost_usd / total_cost * 100) if total_cost > 0 else 0
                lines.append(
                    f"| {mission.mission_id} | ${mission.cost_usd:.4f} | {cost_pct:.1f}% |"
                )
        else:
            lines.append("*成本数据不可用*")

        lines.extend(["", "---", ""])

        return lines

    def _generate_timeline(self, output) -> list:
        """生成时间线"""
        lines = [
            "## ⏱️ 执行时间线",
            "",
            f"**开始时间**: {datetime.fromtimestamp(output.start_time).strftime('%Y-%m-%d %H:%M:%S')}  ",
        ]

        if output.end_time:
            lines.append(
                f"**结束时间**: {datetime.fromtimestamp(output.end_time).strftime('%Y-%m-%d %H:%M:%S')}  "
            )

        lines.extend([
            f"**总耗时**: {output.summary.get('total_duration_seconds', 0):.1f}秒",
            "",
            "### 任务耗时分解",
            "",
            "| 任务 | 耗时(秒) | 迭代次数 |",
            "|------|----------|----------|"
        ])

        for mission in output.mission_outputs:
            lines.append(
                f"| {mission.mission_id} | {mission.duration_seconds:.1f} | {mission.iterations} |"
            )

        lines.extend(["", "---", ""])

        return lines

    def _generate_deliverables_list(self, output) -> list:
        """生成交付物清单"""
        lines = [
            "## 📦 交付物清单",
            ""
        ]

        total_files = 0
        for mission in output.mission_outputs:
            if mission.files:
                lines.extend([
                    f"### {mission.mission_id}",
                    ""
                ])
                for filename in mission.files.keys():
                    lines.append(f"- 📄 `{filename}`")
                    total_files += 1
                lines.append("")

        if total_files == 0:
            lines.append("*无生成文件*")

        lines.extend(["", "---", ""])

        return lines

    def _generate_recommendations(self, output) -> list:
        """生成建议和下一步"""
        lines = [
            "## 💡 建议和下一步",
            ""
        ]

        summary = output.summary
        success_rate = summary.get('success_rate', 0)

        # 根据成功率给出建议
        if success_rate < 0.7:
            lines.extend([
                "### ⚠️ 需要关注",
                "",
                "任务成功率较低，建议：",
                "",
                "1. 检查失败任务的验证错误",
                "2. 调整质量阈值或增加重试次数",
                "3. 优化任务分解策略",
                ""
            ])

        # 质量改进建议
        avg_quality = summary.get('average_quality_score', 0)
        if avg_quality < 70:
            lines.extend([
                "### 📈 质量改进",
                "",
                "平均质量分数较低，建议：",
                "",
                "1. 明确化成功标准",
                "2. 增强角色prompt指导",
                "3. 加入更多验证规则",
                ""
            ])

        # 成本优化建议
        total_cost = summary.get('total_cost_usd', 0)
        if total_cost > 5.0:
            lines.extend([
                "### 💰 成本优化",
                "",
                "总成本较高，建议：",
                "",
                "1. 使用更便宜的模型（如Haiku）",
                "2. 减少不必要的迭代",
                "3. 优化prompt长度",
                ""
            ])

        if success_rate >= 0.9:
            lines.extend([
                "### ✅ 执行优秀",
                "",
                "任务执行非常成功！继续保持：",
                "",
                "1. 当前的角色配置",
                "2. 质量验证策略",
                "3. 成本控制措施",
                ""
            ])

        lines.extend(["---", ""])

        return lines

    def _generate_footer(self, output) -> list:
        """生成报告页脚"""
        return [
            "",
            "---",
            "",
            f"*本报告由 **Claude Code Auto v4.0** 自动生成*  ",
            f"*会话ID: `{output.session_id}`*  ",
            f"*生成时间: {output.summary.get('timestamp', 'N/A')}*",
            ""
        ]

    def _generate_progress_bar(self, percentage: float, length: int = 20) -> str:
        """
        生成进度条

        Args:
            percentage: 百分比 (0-100)
            length: 进度条长度

        Returns:
            进度条字符串
        """
        filled_length = int(length * percentage / 100)
        bar = "█" * filled_length + "░" * (length - filled_length)
        return f"[{bar}]"

    def _get_quality_grade(self, score: float) -> str:
        """
        获取质量等级

        Args:
            score: 质量分数 (0-100)

        Returns:
            等级字符串
        """
        if score >= 90:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 50:
            return "一般"
        else:
            return "较差"


# 全局单例
_report_generator_instance: Optional[ReportGenerator] = None


def get_report_generator() -> ReportGenerator:
    """获取全局报告生成器实例"""
    global _report_generator_instance
    if _report_generator_instance is None:
        _report_generator_instance = ReportGenerator()
    return _report_generator_instance
