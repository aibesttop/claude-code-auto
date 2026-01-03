"""
Skill Version Comparison Test Script

Tests v1.0 vs v2.0 skill prompts on the same task to compare quality.
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.resources.resource_registry import ResourceRegistry
from src.utils.logger import get_logger, setup_logger

logger = get_logger()


# Test tasks for different skill categories
TEST_TASKS = {
    "python_expert": {
        "task": "Write a Python function to parse a CSV file and calculate the average of a numeric column, with proper error handling and type hints.",
        "expected_elements": [
            "Type hints",
            "Error handling (FileNotFoundError, ValueError)",
            "Docstring",
            "Unit test examples"
        ]
    },
    "market_analyst": {
        "task": "Research the market size and trends for AI-powered code assistants in 2024, focusing on developer adoption rates.",
        "expected_elements": [
            "Market size (TAM/SAM/SOM)",
            "Growth trends",
            "Data sources",
            "Quantitative metrics"
        ]
    },
    "technical_writer": {
        "task": "Write documentation for a Python API endpoint: POST /api/users that creates a new user with email and password validation.",
        "expected_elements": [
            "Clear structure",
            "Code examples",
            "No [TODO] markers",
            "Usage examples"
        ]
    },
    "system_architect": {
        "task": "Design the architecture for a scalable URL shortener service that can handle 10M requests per day with 99.9% uptime.",
        "expected_elements": [
            "System components",
            "Database design",
            "Scaling strategy",
            "Trade-off analysis"
        ]
    }
}


def format_skill_prompt(skill) -> str:
    """Format skill prompt for display"""
    output = f"\n{'='*80}\n"
    output += f"Skill: {skill.name} (v{skill.version})\n"
    output += f"Category: {skill.category}\n"
    output += f"{'='*80}\n"

    if skill.version == "2.0":
        output += f"\n📋 Role: {skill.role}\n"
        output += f"\n🎯 Capabilities:\n"
        for cap in skill.capabilities:
            output += f"  - {cap}\n"
        output += f"\n⚙️ Logic Flow Preview:\n"
        # Show first 300 chars of logic flow
        preview = skill.logic_flow[:300] + "..." if len(skill.logic_flow) > 300 else skill.logic_flow
        output += f"  {preview}\n"
        output += f"\n🔒 Constraints ({len(skill.constraints)} items)\n"
        output += f"🤔 Reflection Questions ({len(skill.reflection)} items)\n"
        output += f"🛠️ Tool Preferences: {list(skill.tool_preference.keys())}\n"
        if skill.suggested_models:
            output += f"🧠 Suggested Models: {', '.join(skill.suggested_models)}\n"
    else:
        # v1.0 - show prompt preview
        preview = skill.prompt[:400] + "..." if len(skill.prompt) > 400 else skill.prompt
        output += f"\n📝 Prompt Preview:\n{preview}\n"

    output += f"\n{'='*80}\n"
    return output


def compare_skills(skill_v1, skill_v2) -> dict:
    """Compare v1.0 and v2.0 skill prompts"""
    comparison = {
        "skill_name": skill_v1.name,
        "version_v1": skill_v1.version,
        "version_v2": skill_v2.version,
        "v1_prompt_length": len(skill_v1.prompt),
        "v2_prompt_length": len(skill_v2.prompt),
        "v2_has_logic_flow": bool(skill_v2.logic_flow),
        "v2_has_constraints": len(skill_v2.constraints) > 0,
        "v2_has_reflection": len(skill_v2.reflection) > 0,
        "v2_has_tool_preference": len(skill.tool_preference) > 0,
        "v2_has_suggested_models": len(skill_v2.suggested_models) > 0
    }

    # Calculate structure score for v2.0
    structure_score = 0
    if skill_v2.logic_flow:
        structure_score += 25
    if skill_v2.constraints:
        structure_score += 25
    if skill_v2.reflection:
        structure_score += 25
    if skill_v2.tool_preference:
        structure_score += 15
    if skill_v2.suggested_models:
        structure_score += 10

    comparison["v2_structure_score"] = structure_score
    comparison["prompt_size_increase_pct"] = (
        (comparison["v2_prompt_length"] - comparison["v1_prompt_length"]) /
        comparison["v1_prompt_length"] * 100
    ) if comparison["v1_prompt_length"] > 0 else 0

    return comparison


async def test_skill_version(skill_version: str):
    """Test a specific skill version"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing Skill Prompts v{skill_version}")
    logger.info(f"{'='*80}\n")

    # Initialize resource registry with specified version
    registry = ResourceRegistry(config_dir="resources", skill_version=skill_version)

    results = {
        "version": skill_version,
        "skills_loaded": len(registry.skills),
        "skills": {}
    }

    # Display each skill
    for skill_name, skill in registry.skills.items():
        if skill_name in TEST_TASKS:
            logger.info(format_skill_prompt(skill))

            results["skills"][skill_name] = {
                "name": skill.name,
                "category": skill.category,
                "has_logic_flow": bool(skill.logic_flow) if skill.version == "2.0" else False,
                "has_reflection": len(skill.reflection) > 0 if skill.version == "2.0" else False,
                "prompt_length": len(skill.prompt)
            }

    return results


async def main():
    """Main test function"""
    setup_logger("INFO")

    logger.info("\n" + "="*80)
    logger.info("🧪 Skill Version Comparison Test (v1.0 vs v2.0)")
    logger.info("="*80)

    # Test v1.0
    results_v1 = await test_skill_version("1.0")

    # Test v2.0
    results_v2 = await test_skill_version("2.0")

    # Compare
    logger.info("\n" + "="*80)
    logger.info("📊 Comparison Results")
    logger.info("="*80)

    comparison_report = []
    comparison_report.append(f"\n## Overall Summary")
    comparison_report.append(f"- v1.0 Skills Loaded: {results_v1['skills_loaded']}")
    comparison_report.append(f"- v2.0 Skills Loaded: {results_v2['skills_loaded']}")

    comparison_report.append(f"\n## Skill-by-Skill Comparison")

    for skill_name in TEST_TASKS.keys():
        if skill_name in results_v1["skills"] and skill_name in results_v2["skills"]:
            skill_v1 = results_v1["skills"][skill_name]
            skill_v2 = results_v2["skills"][skill_name]

            size_increase = (
                (skill_v2["prompt_length"] - skill_v1["prompt_length"]) /
                skill_v1["prompt_length"] * 100
            ) if skill_v1["prompt_length"] > 0 else 0

            comparison_report.append(f"\n### {skill_name}")
            comparison_report.append(f"- v1.0 Prompt Length: {skill_v1['prompt_length']} chars")
            comparison_report.append(f"- v2.0 Prompt Length: {skill_v2['prompt_length']} chars")
            comparison_report.append(f"- Size Increase: {size_increase:.1f}%")
            comparison_report.append(f"- v2.0 Has Logic Flow: {'✅' if skill_v2['has_logic_flow'] else '❌'}")
            comparison_report.append(f"- v2.0 Has Reflection: {'✅' if skill_v2['has_reflection'] else '❌'}")

    # Print report
    logger.info("\n" + "\n".join(comparison_report))

    # Save report to file
    report_path = Path("test_results") / f"skill_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.parent.mkdir(exist_ok=True)

    full_report = "# Skill Version Comparison Report\n\n"
    full_report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    full_report += "\n".join(comparison_report)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(full_report)

    logger.info(f"\n✅ Comparison report saved to: {report_path}")

    logger.info("\n" + "="*80)
    logger.info("🎯 Next Steps:")
    logger.info("="*80)
    logger.info("1. Review the comparison report")
    logger.info("2. Test actual task execution with both versions:")
    logger.info(f"   - v1.0: SKILL_VERSION=1.0 python src/main.py")
    logger.info(f"   - v2.0: SKILL_VERSION=2.0 python src/main.py")
    logger.info("3. Compare output quality, token usage, and execution time")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
