"""
Test case to verify the improved content_check validation with whitespace tolerance
"""
import pytest
import tempfile
from pathlib import Path
from src.core.team.role_registry import Role, Mission, OutputStandard, ValidationRule
from src.core.team.role_executor import RoleExecutor
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_content_check_whitespace_tolerance():
    """Test that content_check handles whitespace variations correctly"""
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        # Create test file with various whitespace patterns
        test_file = work_dir / "test.md"
        test_file.write_text("""
# Document

## Target Users

Some content here

## Competitor  Analysis

More content

##  Opportunities

Final content
""", encoding='utf-8')
        
        # Create role with content_check validation
        role = Role(
            name="Test-Role",
            description="Test role",
            category="test",
            mission=Mission(
                goal="Test goal",
                success_criteria=["Test"],
                max_iterations=1
            ),
            output_standard=OutputStandard(
                required_files=["test.md"],
                validation_rules=[
                    ValidationRule(
                        type="content_check",
                        file="test.md",
                        must_contain=[
                            "## Target Users",      # Exact match
                            "## Competitor Analysis",  # Extra space in file
                            "## Opportunities"      # Extra space before in file
                        ]
                    )
                ]
            ),
            recommended_persona="coder",
            tools=["write_file"],
            dependencies=[]
        )
        
        # Create mock executor
        mock_executor = MagicMock()
        mock_executor.persona_engine = MagicMock()
        mock_executor.persona_engine.switch_persona = MagicMock()
        
        # Create RoleExecutor
        executor = RoleExecutor(
            role=role,
            executor_agent=mock_executor,
            work_dir=str(work_dir)
        )
        
        # Run validation
        validation = executor._validate_outputs()
        
        # Should pass despite whitespace variations
        assert validation['passed'] == True, f"Validation should pass, but got errors: {validation['errors']}"
        assert len(validation['errors']) == 0


@pytest.mark.asyncio
async def test_content_check_case_sensitive():
    """Test that content_check remains case-sensitive"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        work_dir = Path(tmpdir)
        
        test_file = work_dir / "test.md"
        test_file.write_text("## target users", encoding='utf-8')
        
        role = Role(
            name="Test-Role",
            description="Test role",
            category="test",
            mission=Mission(
                goal="Test goal",
                success_criteria=["Test"],
                max_iterations=1
            ),
            output_standard=OutputStandard(
                required_files=["test.md"],
                validation_rules=[
                    ValidationRule(
                        type="content_check",
                        file="test.md",
                        must_contain=["## Target Users"]  # Capital T and U
                    )
                ]
            ),
            recommended_persona="coder",
            tools=["write_file"],
            dependencies=[]
        )
        
        mock_executor = MagicMock()
        mock_executor.persona_engine = MagicMock()
        mock_executor.persona_engine.switch_persona = MagicMock()
        
        executor = RoleExecutor(
            role=role,
            executor_agent=mock_executor,
            work_dir=str(work_dir)
        )
        
        validation = executor._validate_outputs()
        
        # Should fail due to case mismatch
        assert validation['passed'] == False
        assert len(validation['errors']) == 1
        assert "missing section" in validation['errors'][0]


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_content_check_whitespace_tolerance())
    asyncio.run(test_content_check_case_sensitive())
    print("✅ All whitespace tolerance tests passed!")
