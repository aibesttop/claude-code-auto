"""
Unit tests for TeamOrchestrator
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.team.team_orchestrator import TeamOrchestrator
from src.core.team.role_registry import Role, Mission, OutputStandard, ValidationRule


@pytest.fixture
def temp_work_dir():
    """Create a temporary working directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_roles():
    """Create test roles"""
    role1 = Role(
        name="Role-1",
        description="First role",
        mission=Mission(
            goal="Complete first task",
            success_criteria=["Generate output1.md"],
            max_iterations=3
        ),
        output_standard=OutputStandard(
            required_files=["output1.md"],
            validation_rules=[
                ValidationRule(type="file_exists", file="output1.md")
            ]
        )
    )
    
    role2 = Role(
        name="Role-2",
        description="Second role",
        mission=Mission(
            goal="Complete second task",
            success_criteria=["Generate output2.md"],
            max_iterations=3
        ),
        output_standard=OutputStandard(
            required_files=["output2.md"],
            validation_rules=[
                ValidationRule(type="file_exists", file="output2.md")
            ]
        ),
        dependencies=["Role-1"]
    )
    
    return [role1, role2]


@pytest.fixture
def mock_executor():
    """Create a mock ExecutorAgent"""
    executor = MagicMock()
    executor.persona_engine = MagicMock()
    executor.persona_engine.switch_persona = MagicMock()
    executor.execute_task = AsyncMock()
    return executor


@pytest.mark.asyncio
async def test_orchestrator_success(test_roles, mock_executor, temp_work_dir):
    """Test successful team orchestration"""
    # Create output files for validation
    (Path(temp_work_dir) / "output1.md").write_text("Output 1")
    (Path(temp_work_dir) / "output2.md").write_text("Output 2")
    
    mock_executor.execute_task.return_value = "Task completed"
    
    orchestrator = TeamOrchestrator(test_roles, mock_executor, temp_work_dir)
    result = await orchestrator.execute("Test goal")
    
    assert result['success'] == True
    assert result['completed_roles'] == 2
    assert "Role-1" in result['results']
    assert "Role-2" in result['results']


@pytest.mark.asyncio
async def test_orchestrator_first_role_fails(test_roles, mock_executor, temp_work_dir):
    """Test orchestration when first role fails"""
    # Don't create output files, so validation fails
    mock_executor.execute_task.return_value = "Task completed"
    
    orchestrator = TeamOrchestrator(test_roles, mock_executor, temp_work_dir)
    result = await orchestrator.execute("Test goal")
    
    assert result['success'] == False
    assert result['completed_roles'] == 0
    assert "Role-1" in result['results']
    assert result['results']['Role-1']['success'] == False


@pytest.mark.asyncio
async def test_orchestrator_second_role_fails(test_roles, mock_executor, temp_work_dir):
    """Test orchestration when second role fails"""
    # Create output for first role only
    (Path(temp_work_dir) / "output1.md").write_text("Output 1")
    
    mock_executor.execute_task.return_value = "Task completed"
    
    orchestrator = TeamOrchestrator(test_roles, mock_executor, temp_work_dir)
    result = await orchestrator.execute("Test goal")
    
    assert result['success'] == False
    assert result['completed_roles'] == 1
    assert result['results']['Role-1']['success'] == True
    assert result['results']['Role-2']['success'] == False


@pytest.mark.asyncio
async def test_orchestrator_context_passing(test_roles, mock_executor, temp_work_dir):
    """Test that context is passed between roles"""
    # Create output files
    (Path(temp_work_dir) / "output1.md").write_text("Output from Role 1")
    (Path(temp_work_dir) / "output2.md").write_text("Output from Role 2")
    
    mock_executor.execute_task.return_value = "Task completed"
    
    orchestrator = TeamOrchestrator(test_roles, mock_executor, temp_work_dir)
    result = await orchestrator.execute("Test goal")
    
    # Check that context was built
    assert len(orchestrator.context) == 2
    assert "Role-1" in orchestrator.context
    assert "Role-2" in orchestrator.context
    
    # Check that Role-1's output is in context
    assert "outputs" in orchestrator.context["Role-1"]
    assert "output1.md" in orchestrator.context["Role-1"]["outputs"]


@pytest.mark.asyncio
async def test_orchestrator_empty_team(mock_executor, temp_work_dir):
    """Test orchestration with empty team"""
    orchestrator = TeamOrchestrator([], mock_executor, temp_work_dir)
    result = await orchestrator.execute("Test goal")
    
    assert result['success'] == True
    assert result['completed_roles'] == 0
    assert len(result['results']) == 0


@pytest.mark.asyncio
async def test_orchestrator_linear_execution(test_roles, mock_executor, temp_work_dir):
    """Test that roles execute linearly (not in parallel)"""
    execution_order = []
    
    async def mock_execute_task(task):
        # Determine which role is executing based on task content
        if "first task" in task:
            execution_order.append("Role-1")
            (Path(temp_work_dir) / "output1.md").write_text("Output 1")
        elif "second task" in task:
            execution_order.append("Role-2")
            (Path(temp_work_dir) / "output2.md").write_text("Output 2")
        return "Task completed"
    
    mock_executor.execute_task = mock_execute_task
    
    orchestrator = TeamOrchestrator(test_roles, mock_executor, temp_work_dir)
    result = await orchestrator.execute("Test goal")
    
    # Verify execution order
    assert execution_order == ["Role-1", "Role-2"]
    assert result['success'] == True
