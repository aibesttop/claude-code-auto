"""
Test OutputIntegrator - 测试输出集成器

演示OutputIntegrator的功能和多格式报告生成
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.output.output_integrator import (
    OutputIntegrator,
    OutputFormat,
    MissionOutput
)


def test_output_integrator():
    """测试OutputIntegrator"""
    print("🧪 Testing OutputIntegrator...")
    print("=" * 70)

    # 创建测试目录
    test_dir = Path("test_output")
    test_dir.mkdir(exist_ok=True)

    # 初始化OutputIntegrator
    integrator = OutputIntegrator(test_dir)

    # 模拟任务结果
    mission_results = {
        "mission_1": {
            "mission_type": "market_research",
            "goal": "分析漫画市场的两个app机会",
            "role": "Market-Researcher",
            "outputs": {
                "market_analysis.md": "# 市场分析报告\n\n## 调研结果...",
                "competitors.md": "# 竞品分析\n\n1. App A\n2. App B..."
            },
            "iterations": 2,
            "quality_score": 85.5,
            "cost_usd": 0.25,
            "duration_seconds": 45.3,
            "success": True,
            "validation_passed": True
        },
        "mission_2": {
            "mission_type": "documentation",
            "goal": "撰写第一个app的需求文档",
            "role": "AI-Native-Writer",
            "outputs": {
                "app1_requirements.md": "# App 1 需求文档\n\n## 功能需求...",
                "app1_wireframes.md": "# App 1 线框图\n\n..."
            },
            "iterations": 3,
            "quality_score": 92.0,
            "cost_usd": 0.35,
            "duration_seconds": 67.8,
            "success": True,
            "validation_passed": True
        },
        "mission_3": {
            "mission_type": "documentation",
            "goal": "撰写第二个app的需求文档",
            "role": "AI-Native-Writer",
            "outputs": {
                "app2_requirements.md": "# App 2 需求文档\n\n## 功能需求..."
            },
            "iterations": 2,
            "quality_score": 78.0,
            "cost_usd": 0.20,
            "duration_seconds": 52.1,
            "success": True,
            "validation_passed": False,
            "validation_errors": ["缺少技术栈说明"]
        }
    }

    # 集成输出
    print("\n📊 Integrating outputs...")
    integrated = integrator.integrate(
        session_id="test-session-001",
        goal="挖掘出2个在漫画这个利基市场的app机会，最终输出分别输出两份详细的app需求文档",
        mission_results=mission_results,
        metadata={
            "intervention_count": 1,
            "model": "claude-sonnet-4-5"
        }
    )

    print(f"✅ Integration complete: {len(integrated.mission_outputs)} missions")

    # 生成多格式报告
    print("\n📝 Generating reports...")
    reports = integrator.generate_reports(
        integrated,
        formats=[
            OutputFormat.MARKDOWN,
            OutputFormat.JSON,
            OutputFormat.HTML,
            OutputFormat.TEXT
        ]
    )

    print(f"\n✅ Generated {len(reports)} reports:")
    for fmt, path in reports.items():
        print(f"   {fmt.value:10s}: {path}")

    # 组织交付物
    print("\n📦 Organizing deliverables...")
    integrator.organize_deliverables(integrated)

    # 显示汇总信息
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    summary = integrated.summary
    print(f"Total Missions:     {summary['total_missions']}")
    print(f"Successful:         {summary['successful_missions']}")
    print(f"Success Rate:       {summary['success_rate']:.1%}")
    print(f"Files Generated:    {summary['total_files_generated']}")
    print(f"Average Quality:    {summary['average_quality_score']:.1f}/100")
    print(f"Total Cost:         ${summary['total_cost_usd']:.4f}")
    print(f"Total Duration:     {summary['total_duration_seconds']:.1f}s")
    print("=" * 70)

    # 显示生成的文件结构
    print("\n📁 Generated File Structure:")
    print("=" * 70)

    def print_tree(path: Path, prefix: str = ""):
        """递归打印目录树"""
        if path.is_file():
            size = path.stat().st_size
            print(f"{prefix}├── {path.name} ({size} bytes)")
        elif path.is_dir():
            print(f"{prefix}{path.name}/")
            items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for i, item in enumerate(items):
                is_last = (i == len(items) - 1)
                new_prefix = prefix + ("    " if is_last else "│   ")
                print_tree(item, new_prefix)

    print_tree(test_dir)
    print("=" * 70)

    # 显示Markdown报告预览
    print("\n📄 Markdown Report Preview (first 50 lines):")
    print("=" * 70)
    md_report = reports[OutputFormat.MARKDOWN]
    with open(md_report, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:3d}: {line}", end='')
    if len(lines) > 50:
        print(f"\n... ({len(lines) - 50} more lines)")
    print("\n" + "=" * 70)

    print("\n✅ Test complete!")
    print(f"\n💡 Check generated files in: {test_dir.absolute()}")
    print(f"   - Reports:       {test_dir / 'reports'}")
    print(f"   - Deliverables:  {test_dir / 'deliverables'}")


if __name__ == "__main__":
    test_output_integrator()
