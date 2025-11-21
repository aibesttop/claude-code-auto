"""
Unit tests for RoleRegistry
"""

import pytest
from pathlib import Path
import yaml
import tempfile
import shutil
from src.core.team.role_registry import (
    RoleRegistry,
    Role,
    Mission,
    OutputStandard,
    ValidationRule
)


@pytest.fixture
def temp_roles_dir():
    """Create a temporary roles directory with test roles"""
    temp_dir = tempfile.mkdtemp()
    roles_dir = Path(temp_dir) / "roles"
    roles_dir.mkdir()
    
    # Create a test role YAML
    test_role = {
        "name": "Test-Role",
        "description": "A test role for unit testing",
        "category": "testing",
        "mission": {
            "goal": "Complete test mission",
            "success_criteria": [
                "Generate test output",
                "Pass validation"
            ],
            "max_iterations": 5
        },
        "output_standard": {
            "required_files": ["test-output.md"],
            "validation_rules": [
                {
                    "type": "file_exists",
                    "file": "test-output.md"
                }
            ]
        },
        "recommended_persona": "default",
        "tools": ["write_file", "read_file"],
        "dependencies": []
    }
    
    with open(roles_dir / "test_role.yaml", 'w') as f:
        yaml.dump(test_role, f)
    
    yield str(roles_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir)


def test_role_registry_init(temp_roles_dir):
    """Test RoleRegistry initialization"""
    registry = RoleRegistry(roles_dir=temp_roles_dir)
    
    assert len(registry.roles) == 1
    assert "Test-Role" in registry.roles


def test_role_registry_get_role(temp_roles_dir):
    """Test getting a role by name"""
    registry = RoleRegistry(roles_dir=temp_roles_dir)
    
    role = registry.get_role("Test-Role")
    
    assert role is not None
    assert role.name == "Test-Role"
    assert role.description == "A test role for unit testing"
    assert role.category == "testing"
    assert role.mission.goal == "Complete test mission"
    assert len(role.mission.success_criteria) == 2
    assert role.mission.max_iterations == 5


def test_role_registry_get_nonexistent_role(temp_roles_dir):
    """Test getting a role that doesn't exist"""
    registry = RoleRegistry(roles_dir=temp_roles_dir)
    
    role = registry.get_role("Nonexistent-Role")
    
    assert role is None


def test_role_registry_list_roles(temp_roles_dir):
    """Test listing all roles"""
    registry = RoleRegistry(roles_dir=temp_roles_dir)
    
    roles = registry.list_roles()
    
    assert len(roles) == 1
    assert "Test-Role" in roles


def test_role_registry_get_roles_by_category(temp_roles_dir):
    """Test getting roles by category"""
    registry = RoleRegistry(roles_dir=temp_roles_dir)
    
    roles = registry.get_roles_by_category("testing")
    
    assert len(roles) == 1
    assert roles[0].name == "Test-Role"


def test_role_registry_empty_directory():
    """Test RoleRegistry with empty directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        roles_dir = Path(temp_dir) / "empty_roles"
        roles_dir.mkdir()
        
        registry = RoleRegistry(roles_dir=str(roles_dir))
        
        assert len(registry.roles) == 0
        assert registry.list_roles() == []


def test_role_registry_nonexistent_directory():
    """Test RoleRegistry with nonexistent directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        roles_dir = Path(temp_dir) / "nonexistent"
        
        registry = RoleRegistry(roles_dir=str(roles_dir))
        
        assert len(registry.roles) == 0
        assert roles_dir.exists()  # Should create the directory


def test_role_validation_rule_model():
    """Test ValidationRule Pydantic model"""
    rule = ValidationRule(
        type="file_exists",
        file="test.md"
    )
    
    assert rule.type == "file_exists"
    assert rule.file == "test.md"


def test_mission_model():
    """Test Mission Pydantic model"""
    mission = Mission(
        goal="Test goal",
        success_criteria=["Criterion 1", "Criterion 2"],
        max_iterations=10
    )
    
    assert mission.goal == "Test goal"
    assert len(mission.success_criteria) == 2
    assert mission.max_iterations == 10


def test_output_standard_model():
    """Test OutputStandard Pydantic model"""
    output_standard = OutputStandard(
        required_files=["file1.md", "file2.md"],
        validation_rules=[
            ValidationRule(type="file_exists", file="file1.md")
        ]
    )
    
    assert len(output_standard.required_files) == 2
    assert len(output_standard.validation_rules) == 1


def test_role_model():
    """Test Role Pydantic model"""
    role = Role(
        name="Test-Role",
        description="Test description",
        mission=Mission(
            goal="Test goal",
            success_criteria=["Criterion 1"],
            max_iterations=5
        ),
        output_standard=OutputStandard(
            required_files=["output.md"],
            validation_rules=[
                ValidationRule(type="file_exists", file="output.md")
            ]
        )
    )
    
    assert role.name == "Test-Role"
    assert role.description == "Test description"
    assert role.mission.goal == "Test goal"
    assert len(role.output_standard.required_files) == 1
