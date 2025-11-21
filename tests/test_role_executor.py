"""
Unit tests for RoleExecutor
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import AsyncMock, MagicMock
from src.core.team.role_executor import RoleExecutor
from src.core.team.role_registry import Role, Mission, OutputStandard, ValidationRule


@pytest.fixture
def temp_work_dir():
    """Create a temporary working directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_role():
    """Create a test role"""
    return Role(
        name="Test-Role",
        description="Test role",
        mission=Mission(
            goal="Generate test output",
            success_criteria=["Create output.md file"],
            max_iterations=3
        ),
        output_standard=OutputStandard(
            required_files=["output.md"],
            validation_rules=[
                ValidationRule(type="file_exists", file="output.md"),
                ValidationRule(
                    type="min_length",
                    file="output.md",
                    min_chars=10
                )
            ]
        ),
        recommended_persona="default"
    )


@pytest.fixture
def mock_executor():
    """Create a mock ExecutorAgent"""
    executor = MagicMock()
    executor.persona_engine = MagicMock()
    executor.persona_engine.switch_persona = MagicMock()
    executor.execute_task = AsyncMock()
    return executor


@pytest.mark.asyncio
async def test_role_executor_success(test_role, mock_executor, temp_work_dir):
    """Test successful role execution"""
    # Create the expected output file
    output_file = Path(temp_work_dir) / "output.md"
    output_file.write_text("This is test output content")
    
    # Mock executor to return success
    mock_executor.execute_task.return_value = "Task completed"
    
    role_executor = RoleExecutor(test_role, mock_executor, temp_work_dir)
    result = await role_executor.execute()
    
    assert result['success'] == True
    assert result['iterations'] >= 1
    assert 'output.md' in result['outputs']
    assert result['validation_result']['passed'] == True


@pytest.mark.asyncio
async def test_role_executor_validation_failure(test_role, mock_executor, temp_work_dir):
    """Test role execution with validation failure"""
    # Don't create the output file, so validation fails
    mock_executor.execute_task.return_value = "Task completed"
    
    role_executor = RoleExecutor(test_role, mock_executor, temp_work_dir)
    result = await role_executor.execute()
    
    assert result['success'] == False
    assert result['iterations'] == test_role.mission.max_iterations
    assert result['validation_result']['passed'] == False
    assert len(result['validation_result']['errors']) > 0


@pytest.mark.asyncio
async def test_role_executor_retry_logic(test_role, mock_executor, temp_work_dir):
    """Test role executor retry logic"""
    output_file = Path(temp_work_dir) / "output.md"
    
    call_count = 0
    
    async def mock_execute_task(task):
        nonlocal call_count
        call_count += 1
        
        # Create file on second attempt
        if call_count == 2:
            output_file.write_text("This is test output content")
        
        return "Task completed"
    
    mock_executor.execute_task = mock_execute_task
    
    role_executor = RoleExecutor(test_role, mock_executor, temp_work_dir)
    result = await role_executor.execute()
    
    assert result['success'] == True
    assert result['iterations'] == 2


def test_validate_file_exists(test_role, mock_executor, temp_work_dir):
    """Test file_exists validation"""
    role_executor = RoleExecutor(test_role, mock_executor, temp_work_dir)
    
    # File doesn't exist
    validation = role_executor._validate_outputs()
    assert validation['passed'] == False
    assert any("Missing required file" in error for error in validation['errors'])
    
    # Create file
    output_file = Path(temp_work_dir) / "output.md"
    output_file.write_text("Test content that is long enough")
    
    # File exists
    validation = role_executor._validate_outputs()
    assert validation['passed'] == True


def test_validate_min_length(mock_executor, temp_work_dir):
    """Test min_length validation"""
    role = Role(
        name="Test-Role",
        description="Test",
        mission=Mission(
            goal="Test",
            success_criteria=["Test"],
            max_iterations=3
        ),
        output_standard=OutputStandard(
            required_files=["output.md"],
            validation_rules=[
                ValidationRule(
                    type="min_length",
                    file="output.md",
                    min_chars=100
                )
            ]
        )
    )
    
    role_executor = RoleExecutor(role, mock_executor, temp_work_dir)
    
    # Create file with insufficient content
    output_file = Path(temp_work_dir) / "output.md"
    output_file.write_text("Short")
    
    validation = role_executor._validate_outputs()
    assert validation['passed'] == False
    assert any("too short" in error for error in validation['errors'])
    
    # Create file with sufficient content
    output_file.write_text("A" * 150)
    
    validation = role_executor._validate_outputs()
    assert validation['passed'] == True


def test_validate_content_check(mock_executor, temp_work_dir):
    """Test content_check validation"""
    role = Role(
        name="Test-Role",
        description="Test",
        mission=Mission(
            goal="Test",
            success_criteria=["Test"],
            max_iterations=3
        ),
        output_standard=OutputStandard(
            required_files=["output.md"],
            validation_rules=[
                ValidationRule(
                    type="content_check",
                    file="output.md",
                    must_contain=["## Section 1", "## Section 2"]
                )
            ]
        )
    )
    
    role_executor = RoleExecutor(role, mock_executor, temp_work_dir)
    
    # Create file without required sections
    output_file = Path(temp_work_dir) / "output.md"
    output_file.write_text("Some content")
    
    validation = role_executor._validate_outputs()
    assert validation['passed'] == False
    
    # Create file with required sections
    output_file.write_text("## Section 1\nContent\n## Section 2\nMore content")
    
    validation = role_executor._validate_outputs()
    assert validation['passed'] == True


def test_validate_no_placeholders(mock_executor, temp_work_dir):
    """Test no_placeholders validation"""
    role = Role(
        name="Test-Role",
        description="Test",
        mission=Mission(
            goal="Test",
            success_criteria=["Test"],
            max_iterations=3
        ),
        output_standard=OutputStandard(
            required_files=["output.md"],
            validation_rules=[
                ValidationRule(
                    type="no_placeholders",
                    files=["output.md"],
                    forbidden_patterns=[r"\[TODO\]", r"\[PLACEHOLDER\]"]
                )
            ]
        )
    )
    
    role_executor = RoleExecutor(role, mock_executor, temp_work_dir)
    
    # Create file with placeholder
    output_file = Path(temp_work_dir) / "output.md"
    output_file.write_text("Content with [TODO] placeholder")
    
    validation = role_executor._validate_outputs()
    assert validation['passed'] == False
    
    # Create file without placeholders
    output_file.write_text("Content without placeholders")
    
    validation = role_executor._validate_outputs()
    assert validation['passed'] == True


def test_collect_outputs(test_role, mock_executor, temp_work_dir):
    """Test collecting outputs"""
    role_executor = RoleExecutor(test_role, mock_executor, temp_work_dir)
    
    # Create output file
    output_file = Path(temp_work_dir) / "output.md"
    test_content = "Test output content"
    output_file.write_text(test_content)
    
    outputs = role_executor._collect_outputs()
    
    assert "output.md" in outputs
    assert outputs["output.md"] == test_content


def test_persona_switching(test_role, mock_executor, temp_work_dir):
    """Test that persona is switched correctly"""
    role_executor = RoleExecutor(test_role, mock_executor, temp_work_dir)
    
    mock_executor.persona_engine.switch_persona.assert_called_once_with(
        "default",
        reason="role_requirement: Test-Role"
    )
