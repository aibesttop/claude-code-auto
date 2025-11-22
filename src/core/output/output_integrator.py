"""
Output Integrator - 输出集成器

整合所有任务输出，生成统一的交付物和报告
"""
import json
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger()


class OutputFormat(str, Enum):
    """输出格式"""
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"
    TEXT = "text"


@dataclass
class MissionOutput:
    """单个任务的输出"""
    mission_id: str
    mission_type: str
    goal: str
    role: str

    # 输出文件
    files: Dict[str, str] = field(default_factory=dict)  # filename -> content

    # 元数据
    iterations: int = 1
    quality_score: float = 0.0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0

    # 状态
    success: bool = True
    validation_passed: bool = True
    validation_errors: List[str] = field(default_factory=list)


@dataclass
class IntegratedOutput:
    """集成后的最终输出"""
    session_id: str
    goal: str

    # 任务输出
    mission_outputs: List[MissionOutput] = field(default_factory=list)

    # 汇总信息
    summary: Dict[str, Any] = field(default_factory=dict)

    # 时间信息
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    # 生成的报告文件
    reports: Dict[OutputFormat, Path] = field(default_factory=dict)

    # 干预历史（Leader模式）
    intervention_history: List[Dict[str, Any]] = field(default_factory=list)


class OutputIntegrator:
    """
    输出集成器

    功能：
    1. 收集所有任务输出
    2. 生成多格式报告
    3. 创建项目总结
    4. 组织输出文件结构
    """

    def __init__(self, work_dir: Path):
        """
        初始化输出集成器

        Args:
            work_dir: 工作目录
        """
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)

        # 创建输出目录结构
        self.deliverables_dir = self.work_dir / "deliverables"
        self.deliverables_dir.mkdir(exist_ok=True)

        self.reports_dir = self.work_dir / "reports"
        self.reports_dir.mkdir(exist_ok=True)

        logger.info(f"OutputIntegrator initialized: {self.work_dir}")

    def integrate(
        self,
        session_id: str,
        goal: str,
        mission_results: Dict[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        intervention_history: Optional[List[Dict[str, Any]]] = None
    ) -> IntegratedOutput:
        """
        集成所有任务输出

        Args:
            session_id: 会话ID
            goal: 总目标
            mission_results: 任务结果字典 {mission_id: result}
            metadata: 额外元数据
            intervention_history: 干预历史（Leader模式）

        Returns:
            IntegratedOutput对象
        """
        logger.info(f"🔧 Integrating outputs for session: {session_id}")

        # 创建集成输出对象
        integrated = IntegratedOutput(
            session_id=session_id,
            goal=goal,
            intervention_history=intervention_history or []
        )

        # 收集所有任务输出
        for mission_id, result in mission_results.items():
            mission_output = self._create_mission_output(mission_id, result)
            integrated.mission_outputs.append(mission_output)

        # 生成汇总信息
        integrated.summary = self._generate_summary(integrated, metadata)

        # 标记结束时间
        integrated.end_time = time.time()

        logger.info(f"✅ Integration complete: {len(integrated.mission_outputs)} missions")
        if intervention_history:
            logger.info(f"   Interventions recorded: {len(intervention_history)}")

        return integrated

    def _create_mission_output(
        self,
        mission_id: str,
        result: Dict[str, Any]
    ) -> MissionOutput:
        """
        创建单个任务的输出对象

        Args:
            mission_id: 任务ID
            result: 任务结果

        Returns:
            MissionOutput对象
        """
        return MissionOutput(
            mission_id=mission_id,
            mission_type=result.get('mission_type', 'unknown'),
            goal=result.get('goal', ''),
            role=result.get('role', 'unknown'),
            files=result.get('outputs', {}),
            iterations=result.get('iterations', 1),
            quality_score=result.get('quality_score', 0.0),
            cost_usd=result.get('cost_usd', 0.0),
            duration_seconds=result.get('duration_seconds', 0.0),
            success=result.get('success', True),
            validation_passed=result.get('validation_passed', True),
            validation_errors=result.get('validation_errors', [])
        )

    def _generate_summary(
        self,
        integrated: IntegratedOutput,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        生成汇总信息

        Args:
            integrated: 集成输出对象
            metadata: 额外元数据

        Returns:
            汇总信息字典
        """
        total_missions = len(integrated.mission_outputs)
        successful_missions = sum(1 for m in integrated.mission_outputs if m.success)

        total_cost = sum(m.cost_usd for m in integrated.mission_outputs)
        total_duration = integrated.end_time - integrated.start_time if integrated.end_time else 0

        total_files = sum(len(m.files) for m in integrated.mission_outputs)
        avg_quality = (
            sum(m.quality_score for m in integrated.mission_outputs) / total_missions
            if total_missions > 0 else 0.0
        )

        summary = {
            "total_missions": total_missions,
            "successful_missions": successful_missions,
            "failed_missions": total_missions - successful_missions,
            "success_rate": successful_missions / total_missions if total_missions > 0 else 0.0,

            "total_files_generated": total_files,
            "average_quality_score": round(avg_quality, 2),

            "total_cost_usd": round(total_cost, 4),
            "total_duration_seconds": round(total_duration, 1),

            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # 合并额外元数据
        if metadata:
            summary.update(metadata)

        return summary

    def generate_reports(
        self,
        integrated: IntegratedOutput,
        formats: List[OutputFormat] = None
    ) -> Dict[OutputFormat, Path]:
        """
        生成多格式报告

        Args:
            integrated: 集成输出对象
            formats: 要生成的格式列表（默认全部）

        Returns:
            格式 -> 文件路径的映射
        """
        if formats is None:
            formats = [OutputFormat.MARKDOWN, OutputFormat.JSON]

        reports = {}

        for fmt in formats:
            if fmt == OutputFormat.MARKDOWN:
                report_path = self._generate_markdown_report(integrated)
                reports[fmt] = report_path

            elif fmt == OutputFormat.JSON:
                report_path = self._generate_json_report(integrated)
                reports[fmt] = report_path

            elif fmt == OutputFormat.HTML:
                report_path = self._generate_html_report(integrated)
                reports[fmt] = report_path

            elif fmt == OutputFormat.TEXT:
                report_path = self._generate_text_report(integrated)
                reports[fmt] = report_path

        integrated.reports = reports

        logger.info(f"📊 Generated {len(reports)} report(s)")
        for fmt, path in reports.items():
            logger.info(f"   {fmt.value}: {path}")

        return reports

    def _generate_markdown_report(self, integrated: IntegratedOutput) -> Path:
        """生成Markdown报告"""
        from .report_generator import ReportGenerator, ReportTemplate

        generator = ReportGenerator()
        content = generator.generate(integrated, ReportTemplate.COMPREHENSIVE)

        report_path = self.reports_dir / f"{integrated.session_id}_report.md"
        report_path.write_text(content, encoding='utf-8')

        return report_path

    def _generate_json_report(self, integrated: IntegratedOutput) -> Path:
        """生成JSON报告"""
        report_data = {
            "session_id": integrated.session_id,
            "goal": integrated.goal,
            "summary": integrated.summary,
            "missions": [
                {
                    "mission_id": m.mission_id,
                    "type": m.mission_type,
                    "goal": m.goal,
                    "role": m.role,
                    "success": m.success,
                    "quality_score": m.quality_score,
                    "iterations": m.iterations,
                    "files": list(m.files.keys()),
                    "cost_usd": m.cost_usd,
                    "duration_seconds": m.duration_seconds
                }
                for m in integrated.mission_outputs
            ],
            "start_time": integrated.start_time,
            "end_time": integrated.end_time,
            "duration_seconds": integrated.summary.get('total_duration_seconds', 0)
        }

        report_path = self.reports_dir / f"{integrated.session_id}_report.json"
        report_path.write_text(
            json.dumps(report_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

        return report_path

    def _generate_html_report(self, integrated: IntegratedOutput) -> Path:
        """生成HTML报告"""
        from .report_generator import ReportGenerator, ReportTemplate

        # 生成Markdown内容
        generator = ReportGenerator()
        md_content = generator.generate(integrated, ReportTemplate.COMPREHENSIVE)

        # 转换Markdown为HTML（简单实现，保留格式）
        html_body = self._markdown_to_html(md_content)

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>任务执行报告 - {integrated.session_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #1a202c;
            font-size: 2.5em;
            margin-bottom: 10px;
            padding-bottom: 15px;
            border-bottom: 4px solid #3498db;
        }}

        h2 {{
            color: #2d3748;
            font-size: 1.8em;
            margin-top: 40px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}

        h3 {{
            color: #4a5568;
            font-size: 1.4em;
            margin-top: 25px;
            margin-bottom: 10px;
        }}

        h4 {{
            color: #718096;
            font-size: 1.1em;
            margin-top: 15px;
            margin-bottom: 8px;
        }}

        p {{
            margin-bottom: 15px;
        }}

        ul, ol {{
            margin-left: 25px;
            margin-bottom: 15px;
        }}

        li {{
            margin-bottom: 8px;
        }}

        code {{
            background: #f7fafc;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Monaco", "Menlo", "Courier New", monospace;
            font-size: 0.9em;
            color: #e53e3e;
        }}

        pre {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        th {{
            background: #4299e1;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
        }}

        tr:hover {{
            background: #f7fafc;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-success {{
            background: #c6f6d5;
            color: #22543d;
        }}

        .badge-warning {{
            background: #feebc8;
            color: #7c2d12;
        }}

        .badge-error {{
            background: #fed7d7;
            color: #742a2a;
        }}

        .badge-info {{
            background: #bee3f8;
            color: #2c5282;
        }}

        .progress-bar {{
            display: inline-block;
            font-family: monospace;
            background: #e2e8f0;
            padding: 2px;
            border-radius: 3px;
        }}

        .metric-card {{
            background: #edf2f7;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            border-left: 4px solid #4299e1;
        }}

        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            color: #718096;
            text-align: center;
            font-size: 0.9em;
        }}

        hr {{
            border: none;
            border-top: 1px solid #e2e8f0;
            margin: 30px 0;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>
"""

        report_path = self.reports_dir / f"{integrated.session_id}_report.html"
        report_path.write_text(html_content, encoding='utf-8')

        return report_path

    def _markdown_to_html(self, md_content: str) -> str:
        """
        简单的Markdown到HTML转换

        基础实现，处理常见的Markdown元素
        """
        import re

        html_lines = []
        lines = md_content.split('\n')
        in_code_block = False
        in_table = False

        i = 0
        while i < len(lines):
            line = lines[i]

            # 代码块
            if line.strip().startswith('```'):
                if in_code_block:
                    html_lines.append('</pre>')
                    in_code_block = False
                else:
                    html_lines.append('<pre>')
                    in_code_block = True
                i += 1
                continue

            if in_code_block:
                html_lines.append(line)
                i += 1
                continue

            # 标题
            if line.startswith('# '):
                html_lines.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('#### '):
                html_lines.append(f'<h4>{line[5:]}</h4>')

            # 表格
            elif line.strip().startswith('|'):
                if not in_table:
                    html_lines.append('<table>')
                    in_table = True

                cells = [c.strip() for c in line.split('|')[1:-1]]

                # 检查是否为分隔行
                if all(set(c) <= {'-', ' '} for c in cells):
                    i += 1
                    continue

                # 判断是否为表头（查看下一行是否为分隔行）
                is_header = False
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if next_line.strip().startswith('|'):
                        next_cells = [c.strip() for c in next_line.split('|')[1:-1]]
                        if all(set(c) <= {{'-', ' '}} for c in next_cells):
                            is_header = True

                if is_header:
                    html_lines.append('<tr>')
                    for cell in cells:
                        html_lines.append(f'<th>{self._format_inline(cell)}</th>')
                    html_lines.append('</tr>')
                else:
                    html_lines.append('<tr>')
                    for cell in cells:
                        html_lines.append(f'<td>{self._format_inline(cell)}</td>')
                    html_lines.append('</tr>')

            elif in_table and not line.strip().startswith('|'):
                html_lines.append('</table>')
                in_table = False

            # 水平线
            elif line.strip() in ['---', '***', '___']:
                html_lines.append('<hr>')

            # 无序列表
            elif line.strip().startswith('- '):
                if i == 0 or not lines[i-1].strip().startswith('- '):
                    html_lines.append('<ul>')
                html_lines.append(f'<li>{self._format_inline(line.strip()[2:])}</li>')
                if i == len(lines) - 1 or not lines[i+1].strip().startswith('- '):
                    html_lines.append('</ul>')

            # 空行
            elif not line.strip():
                if html_lines and html_lines[-1] not in ['<ul>', '<ol>', '</table>']:
                    html_lines.append('<br>')

            # 普通段落
            else:
                html_lines.append(f'<p>{self._format_inline(line)}</p>')

            i += 1

        if in_table:
            html_lines.append('</table>')
        if in_code_block:
            html_lines.append('</pre>')

        return '\n'.join(html_lines)

    def _format_inline(self, text: str) -> str:
        """格式化行内元素"""
        import re

        # 加粗 **text**
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

        # 斜体 *text*
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)

        # 行内代码 `code`
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)

        # 链接 [text](url)
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)

        return text

    def _generate_text_report(self, integrated: IntegratedOutput) -> Path:
        """生成纯文本报告"""
        lines = [
            "=" * 70,
            f"任务执行报告",
            "=" * 70,
            "",
            f"会话ID: {integrated.session_id}",
            f"目标: {integrated.goal}",
            "",
            "-" * 70,
            "执行汇总",
            "-" * 70,
            f"总任务数: {integrated.summary['total_missions']}",
            f"成功任务: {integrated.summary['successful_missions']}",
            f"失败任务: {integrated.summary['failed_missions']}",
            f"成功率: {integrated.summary['success_rate']:.1%}",
            f"总成本: ${integrated.summary['total_cost_usd']:.4f}",
            f"总耗时: {integrated.summary['total_duration_seconds']:.1f}秒",
            "",
            "-" * 70,
            "任务详情",
            "-" * 70,
            ""
        ]

        for i, mission in enumerate(integrated.mission_outputs, 1):
            status = "✓ 成功" if mission.success else "✗ 失败"
            lines.extend([
                f"{i}. [{mission.mission_type}] {status}",
                f"   任务ID: {mission.mission_id}",
                f"   目标: {mission.goal}",
                f"   角色: {mission.role}",
                f"   质量分数: {mission.quality_score:.1f}",
                f"   迭代次数: {mission.iterations}",
                f"   生成文件: {len(mission.files)}个",
                ""
            ])

        lines.extend([
            "=" * 70,
            f"报告生成时间: {integrated.summary['timestamp']}",
            "=" * 70
        ])

        report_path = self.reports_dir / f"{integrated.session_id}_report.txt"
        report_path.write_text("\n".join(lines), encoding='utf-8')

        return report_path

    def organize_deliverables(self, integrated: IntegratedOutput):
        """
        组织交付物文件结构

        将所有生成的文件整理到deliverables目录
        """
        logger.info("📦 Organizing deliverables...")

        session_dir = self.deliverables_dir / integrated.session_id
        session_dir.mkdir(exist_ok=True)

        # 为每个任务创建子目录
        for mission in integrated.mission_outputs:
            mission_dir = session_dir / mission.mission_id
            mission_dir.mkdir(exist_ok=True)

            # 保存任务的输出文件
            for filename, content in mission.files.items():
                file_path = mission_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding='utf-8')

        # 在根目录创建README
        readme_path = session_dir / "README.md"
        readme_content = self._generate_deliverables_readme(integrated)
        readme_path.write_text(readme_content, encoding='utf-8')

        logger.info(f"✅ Deliverables organized: {session_dir}")

    def _generate_deliverables_readme(self, integrated: IntegratedOutput) -> str:
        """生成交付物README"""
        lines = [
            f"# 项目交付物",
            "",
            f"**会话ID**: {integrated.session_id}  ",
            f"**目标**: {integrated.goal}  ",
            f"**生成时间**: {integrated.summary['timestamp']}  ",
            "",
            "## 📊 执行汇总",
            "",
            f"- **总任务数**: {integrated.summary['total_missions']}",
            f"- **成功任务**: {integrated.summary['successful_missions']}",
            f"- **成功率**: {integrated.summary['success_rate']:.1%}",
            f"- **总成本**: ${integrated.summary['total_cost_usd']:.4f}",
            f"- **总耗时**: {integrated.summary['total_duration_seconds']:.1f}秒",
            "",
            "## 📁 目录结构",
            "",
            "```"
        ]

        # 添加目录树
        for mission in integrated.mission_outputs:
            lines.append(f"{mission.mission_id}/")
            for filename in mission.files.keys():
                lines.append(f"  ├── {filename}")

        lines.extend([
            "```",
            "",
            "## 📋 任务清单",
            ""
        ])

        for i, mission in enumerate(integrated.mission_outputs, 1):
            status_icon = "✅" if mission.success else "❌"
            lines.extend([
                f"### {i}. {status_icon} {mission.mission_id}",
                "",
                f"- **类型**: {mission.mission_type}",
                f"- **角色**: {mission.role}",
                f"- **目标**: {mission.goal}",
                f"- **质量分数**: {mission.quality_score:.1f}/100",
                f"- **生成文件**: {len(mission.files)}个",
                ""
            ])

        lines.extend([
            "---",
            "",
            f"*本文档由 Claude Code Auto v4.0 自动生成*"
        ])

        return "\n".join(lines)


# 全局单例
_output_integrator_instance: Optional[OutputIntegrator] = None


def get_output_integrator(work_dir: Path = None) -> OutputIntegrator:
    """
    获取全局输出集成器实例

    Args:
        work_dir: 工作目录 (仅在首次调用时使用)

    Returns:
        OutputIntegrator实例
    """
    global _output_integrator_instance

    if _output_integrator_instance is None:
        if work_dir is None:
            from pathlib import Path
            work_dir = Path(".")

        _output_integrator_instance = OutputIntegrator(work_dir)

    return _output_integrator_instance
