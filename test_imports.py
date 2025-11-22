#!/usr/bin/env python3
"""
Quick import and initialization test for v3.1
"""
import sys
import traceback

print("=" * 60)
print("v3.1 Import Test")
print("=" * 60)

# Test 1: Basic imports
print("\n1. Testing basic imports...")
try:
    from src.config import get_config
    print("   ✅ src.config")
except Exception as e:
    print(f"   ❌ src.config: {e}")
    traceback.print_exc()

try:
    from src.core.agents.planner import PlannerAgent
    print("   ✅ src.core.agents.planner")
except Exception as e:
    print(f"   ❌ src.core.agents.planner: {e}")
    traceback.print_exc()

try:
    from src.core.agents.executor import ExecutorAgent
    print("   ✅ src.core.agents.executor")
except Exception as e:
    print(f"   ❌ src.core.agents.executor: {e}")
    traceback.print_exc()

try:
    from src.core.agents.researcher import ResearcherAgent
    print("   ✅ src.core.agents.researcher")
except Exception as e:
    print(f"   ❌ src.core.agents.researcher: {e}")
    traceback.print_exc()

# Test 2: Tool imports
print("\n2. Testing tool imports...")
try:
    from src.core.tools import quick_research, deep_research
    print("   ✅ src.core.tools.research_tools")
except Exception as e:
    print(f"   ❌ src.core.tools.research_tools: {e}")
    traceback.print_exc()

# Test 3: Team components
print("\n3. Testing team components...")
try:
    from src.core.team.dependency_resolver import DependencyResolver
    print("   ✅ src.core.team.dependency_resolver")
except Exception as e:
    print(f"   ❌ src.core.team.dependency_resolver: {e}")
    traceback.print_exc()

try:
    from src.core.team.quality_validator import SemanticQualityValidator
    print("   ✅ src.core.team.quality_validator")
except Exception as e:
    print(f"   ❌ src.core.team.quality_validator: {e}")
    traceback.print_exc()

try:
    from src.core.team.role_executor import RoleExecutor
    print("   ✅ src.core.team.role_executor")
except Exception as e:
    print(f"   ❌ src.core.team.role_executor: {e}")
    traceback.print_exc()

# Test 4: Config loading
print("\n4. Testing config loading...")
try:
    config = get_config("config.yaml")
    print(f"   ✅ Config loaded")
    print(f"   - Goal: {config.task.goal[:50]}...")
    print(f"   - Cost control enabled: {config.cost_control.enabled}")
    print(f"   - Work dir: {config.directories.work_dir}")
except Exception as e:
    print(f"   ❌ Config loading failed: {e}")
    traceback.print_exc()

# Test 5: Event and cost tracking
print("\n5. Testing event/cost tracking...")
try:
    from src.core.events import EventStore, CostTracker, TokenUsage
    event_store = EventStore()
    cost_tracker = CostTracker(max_budget_usd=10.0)
    print("   ✅ EventStore initialized")
    print("   ✅ CostTracker initialized")

    # Test budget check
    status = cost_tracker.check_budget("test_session")
    print(f"   ✅ Budget check works: {status['budget_enabled']}")
except Exception as e:
    print(f"   ❌ Event/cost tracking: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("Import Test Complete!")
print("=" * 60)
