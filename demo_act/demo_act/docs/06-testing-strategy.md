# Testing Strategy: Claude Code Auto v4.0

## Document Information
- **Version**: 1.0.0
- **Last Updated**: 2025-01-03
- **Status**: Final
- **Author**: Team Mode Documentation Team

---

## Overview

Claude Code Auto uses a multi-layered testing approach to ensure reliability and correctness.

---

## Testing Levels

### 1. Unit Tests

**Purpose**: Test individual functions and classes in isolation

**Framework**: pytest

**Coverage Target**: 80%+

#### Example Unit Test

```python
# tests/test_dependency_resolver.py
import pytest
from src.core.team.dependency_resolver import DependencyResolver
from src.core.team.role_registry import Role

def test_no_dependencies():
    """Test resolver with roles having no dependencies"""
    role1 = Role(name="Role1", dependencies=[])
    role2 = Role(name="Role2", dependencies=[])

    resolver = DependencyResolver()
    result = resolver.resolve([role1, role2])

    assert len(result) == 1
    assert set(result[0]) == {role1, role2}

def test_simple_dependencies():
    """Test resolver with simple dependency chain"""
    role1 = Role(name="Role1", dependencies=[])
    role2 = Role(name="Role2", dependencies=["Role1"])
    role3 = Role(name="Role3", dependencies=["Role2"])

    resolver = DependencyResolver()
    result = resolver.resolve([role1, role2, role3])

    assert len(result) == 3
    assert result[0] == [role1]
    assert result[1] == [role2]
    assert result[2] == [role3]

def test_circular_dependency_detection():
    """Test that circular dependencies are detected"""
    role1 = Role(name="Role1", dependencies=["Role2"])
    role2 = Role(name="Role2", dependencies=["Role1"])

    resolver = DependencyResolver()

    with pytest.raises(CircularDependencyError):
        resolver.resolve([role1, role2])
```

---

### 2. Integration Tests

**Purpose**: Test interactions between components

#### Example Integration Test

```python
# tests/test_team_orchestration.py
import pytest
from src.core.leader.leader_agent import LeaderAgent
from src.config import load_config

@pytest.mark.asyncio
async def test_full_team_execution():
    """Test end-to-end team execution"""
    config = load_config("test_config.yaml")

    leader = LeaderAgent(config)
    result = await leader.orchestrate(
        goal="Research elderly care market"
    )

    assert result.status == "COMPLETED"
    assert len(result.completed_roles) > 0
    assert result.total_cost_usd > 0
```

---

### 3. Validation Tests

**Purpose**: Test validation rules for all roles

#### Example Validation Test

```python
# tests/test_validation.py
import pytest
from src.core.team.role_executor import RoleExecutor
from pathlib import Path

def test_market_researcher_validation():
    """Test Market-Researcher role validation"""
    role = load_role("roles/market_researcher.yaml")

    # Create valid output
    Path("demo_act/market-research.md").write_text("""
    ## Executive Summary
    Market is growing...

    ## Market Size
    TAM: $100B...
    """)

    executor = RoleExecutor(role)
    result = executor.validate_format("market-research.md")

    assert result.passed

def test_placeholder_detection():
    """Test that placeholders are detected"""
    role = load_role("roles/ai_native_writer.yaml")

    # Create output with placeholders
    Path("demo_act/doc.md").write_text("""
    # Documentation
    [TODO: Add more details here]
    """)

    executor = RoleExecutor(role)
    result = executor.validate_format("doc.md")

    assert not result.passed
    assert "TODO" in result.errors[0]
```

---

### 4. End-to-End Tests

**Purpose**: Test complete workflows from config to output

#### Example E2E Test

```python
# tests/test_e2e.py
import pytest
import subprocess
from pathlib import Path

def test_original_mode():
    """Test Original Mode execution"""
    # Create test config
    config = {
        "task": {
            "goal": "Write a hello world program"
        }
    }
    save_config("test_config.yaml", config)

    # Run agent
    result = subprocess.run(
        ["python", "-m", "src.main", "--config", "test_config.yaml"],
        capture_output=True
    )

    assert result.returncode == 0
    assert Path("demo_act/hello.py").exists()

def test_team_mode():
    """Test Team Mode execution"""
    config = {
        "task": {
            "goal": "Research elderly care market",
            "initial_prompt": "You are a market research specialist"
        },
        "leader": {
            "enabled": True
        }
    }
    save_config("test_config.yaml", config)

    result = subprocess.run(
        ["python", "-m", "src.main", "--config", "test_config.yaml"],
        capture_output=True,
        timeout=600  # 10 min timeout
    )

    assert result.returncode == 0
    assert Path("demo_act/market-research.md").exists()
```

---

## Test Coverage

### Target Coverage by Module

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| `dependency_resolver.py` | 90%+ | P0 |
| `role_executor.py` | 85%+ | P0 |
| `quality_validator.py` | 80%+ | P0 |
| `leader_agent.py` | 75%+ | P1 |
| `mission_decomposer.py` | 70%+ | P1 |
| `team_assembler.py` | 70%+ | P1 |
| `planner.py` | 60%+ | P2 |
| `executor.py` | 60%+ | P2 |
| `tool_registry.py` | 80%+ | P1 |
| `events.py` | 85%+ | P1 |
| `state_manager.py` | 85%+ | P1 |

---

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_dependency_resolver.py -v
```

### Run with Coverage

```bash
pytest --cov=src --cov-report=html tests/
```

View coverage report:
```bash
open htmlcov/index.html
```

### Run Integration Tests Only

```bash
pytest -m integration -v
```

### Run E2E Tests Only

```bash
pytest -m e2e -v
```

---

## Test Data Management

### Test Fixtures

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace for testing"""
    workspace = tmp_path / "demo_act"
    workspace.mkdir()
    return workspace

@pytest.fixture
def sample_role():
    """Load sample role for testing"""
    return Role(
        name="Test-Role",
        mission=Mission(
            goal="Test mission",
            success_criteria=["Output exists"]
        ),
        output_standard=OutputStandard(
            required_files=["test.md"],
            validation_rules=[
                {"type": "file_exists", "file": "test.md"}
            ]
        )
    )
```

---

## Mocking and Patching

### Mock LLM Calls

```python
# tests/test_mission_decomposer.py
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_mission_decomposition():
    """Test mission decomposer with mocked LLM"""
    decomposer = MissionDecomposer()

    # Mock LLM response
    with patch.object(decomposer, 'call_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = """[
            {
                "mission_id": "mission_1",
                "goal": "Research market",
                "success_criteria": ["Report created"],
                "dependencies": [],
                "priority": "HIGH"
            }
        ]"""

        missions = await decomposer.decompose("Research elderly care market")

        assert len(missions) == 1
        assert missions[0].goal == "Research market"
        mock_llm.assert_called_once()
```

### Mock Tool Calls

```python
# tests/test_executor.py
from unittest.mock import Mock

def test_executor_with_mocked_tools():
    """Test executor with mocked tools"""
    executor = ExecutorAgent(role=sample_role)

    # Mock tool registry
    executor.tool_registry.get_tool = Mock(return_value=Mock(
        handler=AsyncMock(return_value="File written successfully")
    ))

    result = executor.execute(mission, context)

    assert result.success
    executor.tool_registry.get_tool.assert_called()
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov pytest-asyncio
      - run: pytest --cov=src --cov-report=xml
      - uses: codecov/codecov-action@v3
```

---

## Performance Testing

### Load Testing

```python
# tests/test_performance.py
import pytest
import time

def test_dependency_resolver_performance():
    """Test resolver performance with large graphs"""
    roles = create_roles(n=100)  # 100 roles

    resolver = DependencyResolver()
    start = time.time()
    result = resolver.resolve(roles)
    duration = time.time() - start

    # Should complete in < 1 second for 100 roles
    assert duration < 1.0
    assert len(flatten(result)) == 100
```

---

## Troubleshooting Tests

### Common Issues

1. **Flaky Tests**: Tests that pass/fail intermittently
   - **Cause**: Race conditions, timing issues, external dependencies
   - **Solution**: Use mocking, add retries, increase timeouts

2. **Slow Tests**: Tests taking too long
   - **Cause**: Real API calls, large fixtures
   - **Solution**: Mock external APIs, use smaller fixtures

3. **Test Isolation**: Tests affecting each other
   - **Cause**: Shared state, file system pollution
   - **Solution**: Use temp directories, clean up after tests

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-03 | Initial testing strategy documentation | Team Mode Documentation Team |

---

*This document is part of the comprehensive documentation suite for Claude Code Auto v4.0.*
