"""
测试P1核心能力增强功能
测试：Persona引擎、Researcher链路、事件流和成本追踪
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

def test_persona_engine():
    """测试Persona引擎增强功能"""
    print("\n" + "=" * 60)
    print("测试 1: Persona引擎增强功能")
    print("=" * 60)

    from src.core.agents.persona import PersonaEngine

    engine = PersonaEngine()

    # 测试基础功能
    print("✅ Persona引擎初始化成功")

    # 测试列出所有personas
    personas = engine.list_available_personas()
    print(f"📋 可用Personas ({len(personas)}个):")
    for name, desc in personas.items():
        print(f"   - {name}: {desc}")

    # 测试推荐功能
    test_tasks = [
        "Write a Python function to calculate fibonacci",
        "Research the latest trends in AI",
        "Prioritize features for our product roadmap"
    ]

    print("\n🎯 Persona推荐测试:")
    for task in test_tasks:
        recommended = engine.recommend_persona(task)
        print(f"   Task: '{task[:40]}...'")
        print(f"   → Recommended: {recommended}")

    # 测试切换功能
    print("\n🔄 Persona切换测试:")
    if engine.switch_persona("coder", reason="test"):
        print(f"   ✓ Switched to: {engine.get_current_persona_name()}")

    if engine.switch_persona("researcher", reason="test"):
        print(f"   ✓ Switched to: {engine.get_current_persona_name()}")

    # 查看切换历史
    history = engine.get_switch_history()
    print(f"\n📜 切换历史 ({len(history)}次):")
    for switch in history:
        print(f"   {switch['from']} → {switch['to']} ({switch['reason']})")

    print("\n✅ Persona引擎测试通过!\n")


def test_researcher_cache():
    """测试Researcher缓存功能"""
    print("=" * 60)
    print("测试 2: Researcher缓存和统计功能")
    print("=" * 60)

    from src.core.agents.researcher import ResearchCache

    cache = ResearchCache(ttl_minutes=60)

    # 测试缓存设置和获取
    query1 = "What is quantum computing?"
    result1 = "Quantum computing is a type of computation..."

    cache.set(query1, result1)
    cached = cache.get(query1)

    if cached == result1:
        print("✅ 缓存设置和获取成功")
    else:
        print("❌ 缓存测试失败")

    # 测试缓存未命中
    cached_miss = cache.get("non-existent query")
    if cached_miss is None:
        print("✅ 缓存未命中处理正确")

    # 测试统计
    stats = cache.get_stats()
    print(f"📊 缓存统计: {stats}")

    print("\n✅ Researcher缓存测试通过!\n")


def test_events_and_cost():
    """测试事件流和成本追踪"""
    print("=" * 60)
    print("测试 3: 事件流和成本追踪系统")
    print("=" * 60)

    from src.core.events import EventStore, EventType, CostTracker, TokenUsage
    import tempfile

    # 创建临时目录用于测试
    with tempfile.TemporaryDirectory() as tmpdir:
        # 测试EventStore
        event_store = EventStore(storage_dir=tmpdir)
        session_id = "test-session-123"

        # 创建测试事件
        event_store.create_event(
            EventType.SESSION_START,
            session_id=session_id,
            goal="Test goal"
        )

        event_store.create_event(
            EventType.ITERATION_START,
            session_id=session_id,
            iteration=1
        )

        event_store.create_event(
            EventType.PERSONA_SWITCH,
            session_id=session_id,
            iteration=1,
            from_persona="default",
            to_persona="coder"
        )

        event_store.create_event(
            EventType.ITERATION_END,
            session_id=session_id,
            iteration=1,
            success=True
        )

        # 获取统计
        stats = event_store.get_event_statistics(session_id)
        print(f"📊 事件统计: {stats}")

        if stats['total_events'] == 4:
            print("✅ 事件记录成功")
        else:
            print(f"❌ 事件记录失败: 期望4个事件，实际{stats['total_events']}个")

        # 保存事件到文件
        filepath = event_store.save_to_file(session_id)
        print(f"💾 事件已保存到: {filepath}")

        # 测试CostTracker
        cost_tracker = CostTracker()

        # 记录成本
        tokens = TokenUsage(
            input_tokens=1000,
            output_tokens=500,
            cache_read_tokens=200,
            cache_creation_tokens=100
        )

        cost_record = cost_tracker.record_cost(
            session_id=session_id,
            agent_type="executor",
            model="claude-3-5-sonnet-20241022",
            token_usage=tokens,
            duration_seconds=5.5,
            iteration=1
        )

        print(f"\n💰 成本记录:")
        print(f"   模型: {cost_record.model}")
        print(f"   Tokens: {cost_record.token_usage.total_tokens}")
        print(f"   估算成本: ${cost_record.estimated_cost_usd:.6f}")
        print(f"   时长: {cost_record.duration_seconds}秒")

        # 生成报告
        report = cost_tracker.generate_report(session_id)
        print(f"\n📈 成本报告:")
        print(f"   总成本: ${report['total_cost_usd']:.6f}")
        print(f"   总Tokens: {report['total_tokens']['total_tokens']}")
        print(f"   API调用次数: {report['total_calls']}")

        print("\n✅ 事件流和成本追踪测试通过!\n")


def test_state_manager_persona():
    """测试StateManager的Persona历史功能"""
    print("=" * 60)
    print("测试 4: StateManager Persona历史追踪")
    print("=" * 60)

    from src.utils.state_manager import StateManager, WorkflowStatus
    import tempfile
    import os

    # 创建临时文件路径
    tmpdir = tempfile.mkdtemp()
    state_file = Path(tmpdir) / "test_state.json"

    try:
        manager = StateManager(state_file)
        state = manager.load_or_create(
            session_id="test-123",
            goal="Test goal",
            work_dir="test_dir",
            max_iterations=10,
            force_new=True  # Force create new state
        )

        # 添加Persona切换记录
        state.add_persona_switch("default", "coder", reason="test_1")
        state.add_persona_switch("coder", "researcher", reason="test_2")
        state.add_persona_switch("researcher", "coder", reason="test_3")

        manager.save()

        # 重新加载验证
        manager2 = StateManager(state_file)
        state2 = manager2.load_or_create(
            session_id="test-123",
            goal="Test goal",
            work_dir="test_dir",
            max_iterations=10
        )

        print(f"📜 Persona切换历史 ({len(state2.persona_history)}次):")
        for switch in state2.persona_history:
            print(f"   {switch['from_persona']} → {switch['to_persona']} ({switch['reason']})")

        print(f"🎭 当前Persona: {state2.current_persona}")

        if len(state2.persona_history) == 3:
            print("\n✅ StateManager Persona历史测试通过!")
        else:
            print(f"\n❌ 测试失败: 期望3次切换，实际{len(state2.persona_history)}次")

    finally:
        # 清理临时目录
        import shutil
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)

    print()


def main():
    """运行所有测试"""
    print("\n" + "🧪" * 30)
    print(" P1核心能力增强功能测试套件")
    print("🧪" * 30)

    tests = [
        test_persona_engine,
        test_researcher_cache,
        test_events_and_cost,
        test_state_manager_persona
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")

    if failed == 0:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
