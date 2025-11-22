"""
诊断MissionDecomposer - 检查任务分解是否偏离主题
"""
import asyncio
from src.core.leader.mission_decomposer import MissionDecomposer
from src.utils.logger import get_logger
import yaml

logger = get_logger()


async def diagnose():
    """诊断任务分解"""
    # 加载配置
    with open("config.yaml", 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    goal = config['task']['goal']
    initial_prompt = config['task']['initial_prompt']

    print("=" * 80)
    print("🔍 诊断任务分解")
    print("=" * 80)
    print(f"\n📋 用户目标:\n{goal}\n")
    print(f"📋 初始提示:\n{initial_prompt}\n")
    print("=" * 80)

    # 创建分解器
    decomposer = MissionDecomposer(model="sonnet", work_dir="demo_act")

    # 分解任务
    print("\n🎯 正在分解任务...\n")
    missions = await decomposer.decompose(goal, context=initial_prompt)

    # 显示结果
    print(f"\n✅ 分解为 {len(missions)} 个子任务\n")
    print("=" * 80)

    for i, mission in enumerate(missions, 1):
        print(f"\n### Mission {i}: {mission.id}")
        print(f"**类型**: {mission.type}")
        print(f"**目标**: {mission.goal}")
        print(f"**需求**:")
        for req in mission.requirements:
            print(f"  - {req}")
        print(f"**成功标准**:")
        for crit in mission.success_criteria:
            print(f"  - {crit}")
        print(f"**依赖**: {mission.dependencies if mission.dependencies else '无'}")
        print(f"**优先级**: {mission.priority}")
        print("-" * 80)

    # 主题检查
    print("\n🔍 主题相关性检查:")
    print("=" * 80)

    keywords_expected = ["漫画", "comic", "manga", "app", "应用"]
    keywords_wrong = ["AI", "agent", "LLM", "Claude", "GPT", "model"]

    for i, mission in enumerate(missions, 1):
        goal_lower = mission.goal.lower()

        # 检查是否包含预期关键词
        expected_found = [kw for kw in keywords_expected if kw in goal_lower]

        # 检查是否包含错误关键词
        wrong_found = [kw for kw in keywords_wrong if kw.lower() in goal_lower]

        status = "✅" if expected_found else "⚠️"
        if wrong_found:
            status = "❌"

        print(f"{status} Mission {i} ({mission.id})")
        if expected_found:
            print(f"   ✓ 包含预期关键词: {', '.join(expected_found)}")
        if wrong_found:
            print(f"   ✗ 包含无关关键词: {', '.join(wrong_found)}")
        if not expected_found and not wrong_found:
            print(f"   ? 未检测到明确主题关键词")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(diagnose())
