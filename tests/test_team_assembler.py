"""
Unit tests for TeamAssembler
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.team.team_assembler import TeamAssembler
from src.core.team.role_registry import RoleRegistry, Role, Mission, OutputStandard, ValidationRule


@pytest.fixture
def mock_registry():
    """Create a mock RoleRegistry with test roles"""
    registry = MagicMock(spec=RoleRegistry)
    
    # Create test roles
    role1 = Role(
        name="Role-1",
        description="First test role",
        mission=Mission(
            goal="Goal 1",
            success_criteria=["Criterion 1"],
            max_iterations=5
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
        description="Second test role",
        mission=Mission(
            goal="Goal 2",
            success_criteria=["Criterion 2"],
            max_iterations=5
        ),
        output_standard=OutputStandard(
            required_files=["output2.md"],
            validation_rules=[
                ValidationRule(type="file_exists", file="output2.md")
            ]
        )
    )
    
    registry.roles = {
        "Role-1": role1,
        "Role-2": role2
    }
    registry.get_role = lambda name: registry.roles.get(name)
    
    return registry


@pytest.mark.asyncio
async def test_assemble_team_success(mock_registry):
    """Test successful team assembly"""
    assembler = TeamAssembler(mock_registry)
    
    # Mock LLM response
    mock_response = '''
    {
        "roles": ["Role-1", "Role-2"],
        "reasoning": "Need both roles for this task"
    }
    '''
    
    with patch('src.core.team.team_assembler.run_claude_prompt', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = (mock_response, None)
        
        team = await assembler.assemble_team(
            initial_prompt="Test prompt",
            goal="Test goal"
        )
    
    assert len(team) == 2
    assert team[0].name == "Role-1"
    assert team[1].name == "Role-2"


@pytest.mark.asyncio
async def test_assemble_team_with_nonexistent_role(mock_registry):
    """Test team assembly with a nonexistent role"""
    assembler = TeamAssembler(mock_registry)
    
    # Mock LLM response with nonexistent role
    mock_response = '''
    {
        "roles": ["Role-1", "Nonexistent-Role"],
        "reasoning": "Test reasoning"
    }
    '''
    
    with patch('src.core.team.team_assembler.run_claude_prompt', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = (mock_response, None)
        
        team = await assembler.assemble_team(
            initial_prompt="Test prompt",
            goal="Test goal"
        )
    
    # Should only include the existing role
    assert len(team) == 1
    assert team[0].name == "Role-1"


@pytest.mark.asyncio
async def test_assemble_team_llm_failure(mock_registry):
    """Test team assembly when LLM call fails"""
    assembler = TeamAssembler(mock_registry)
    
    with patch('src.core.team.team_assembler.run_claude_prompt', new_callable=AsyncMock) as mock_llm:
        mock_llm.side_effect = Exception("LLM error")
        
        team = await assembler.assemble_team(
            initial_prompt="Test prompt",
            goal="Test goal"
        )
    
    assert len(team) == 0


@pytest.mark.asyncio
async def test_assemble_team_invalid_json(mock_registry):
    """Test team assembly with invalid JSON response"""
    assembler = TeamAssembler(mock_registry)
    
    # Mock invalid JSON response
    mock_response = "This is not valid JSON"
    
    with patch('src.core.team.team_assembler.run_claude_prompt', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = (mock_response, None)
        
        team = await assembler.assemble_team(
            initial_prompt="Test prompt",
            goal="Test goal"
        )
    
    assert len(team) == 0


def test_format_available_roles(mock_registry):
    """Test formatting of available roles"""
    assembler = TeamAssembler(mock_registry)
    
    formatted = assembler._format_available_roles()
    
    assert "Role-1" in formatted
    assert "Role-2" in formatted
    assert "First test role" in formatted
    assert "Second test role" in formatted


def test_build_analysis_prompt(mock_registry):
    """Test building the analysis prompt"""
    assembler = TeamAssembler(mock_registry)
    
    prompt = assembler._build_analysis_prompt(
        initial_prompt="Test initial prompt",
        goal="Test goal"
    )
    
    assert "Test initial prompt" in prompt
    assert "Test goal" in prompt
    assert "Role-1" in prompt
    assert "Role-2" in prompt
    assert "JSON" in prompt
