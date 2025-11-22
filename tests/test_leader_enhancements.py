"""
Tests for Leader Agent Enhancements (P0 and P1 improvements)

Tests for:
- Resource injection
- ENHANCE strategy
- ESCALATE strategy with HelperGovernor
- Intervention logging
"""
import pytest
from pathlib import Path
from src.core.leader.leader_agent import LeaderAgent, InterventionAction
from src.core.leader.mission_decomposer import SubMission


class TestLeaderEnhancements:
    """Test Leader Agent enhancements"""

    @pytest.fixture
    def leader_agent(self, tmp_path):
        """Create LeaderAgent instance"""
        return LeaderAgent(
            work_dir=str(tmp_path),
            model="haiku",
            max_mission_retries=3,
            quality_threshold=70.0
        )

    def test_leader_initialization(self, leader_agent):
        """Test that Leader Agent initializes with all components"""
        assert leader_agent.resource_registry is not None
        assert leader_agent.helper_governor is not None
        assert leader_agent.mission_decomposer is not None
        assert leader_agent.team_assembler is not None
        assert leader_agent.intervention_history == []

    def test_resource_registry_initialization(self, leader_agent):
        """Test that ResourceRegistry is properly initialized"""
        resources = leader_agent.resource_registry.list_all_resources()
        assert 'mcp_servers' in resources
        assert 'skills' in resources
        assert 'tool_mappings' in resources

    def test_helper_governor_initialization(self, leader_agent):
        """Test that HelperGovernor is properly initialized"""
        assert leader_agent.helper_governor is not None
        summary = leader_agent.helper_governor.get_summary()
        assert summary['active_helpers'] == 0
        assert summary['exited_helpers'] == 0

    def test_select_helper_role(self, leader_agent):
        """Test helper role selection based on errors"""
        # Security errors
        errors = ["security vulnerability detected", "unsafe code found"]
        helper = leader_agent._select_helper_role(errors)
        assert helper == "SecurityExpert"

        # Performance errors
        errors = ["performance issue detected", "code is too slow"]
        helper = leader_agent._select_helper_role(errors)
        assert helper == "PerfAnalyzer"

        # Quality errors
        errors = ["quality check failed", "needs review"]
        helper = leader_agent._select_helper_role(errors)
        assert helper == "Reviewer"

        # General errors
        errors = ["validation failed", "file not found"]
        helper = leader_agent._select_helper_role(errors)
        assert helper == "Debugger"

    @pytest.mark.asyncio
    async def test_enhance_mission_structure(self, leader_agent):
        """Test mission enhancement returns valid structure"""
        original_mission = SubMission(
            id="test_mission",
            type="documentation",
            goal="Create documentation",
            requirements=["Write README"],
            success_criteria=["README exists"],
            dependencies=[],
            priority=1,
            estimated_cost_usd=0.1
        )

        quality_issues = ["File not found", "Content too short"]

        # Note: This will call actual LLM, so we test structure only
        # In real tests, we would mock the LLM call
        enhanced = await leader_agent._enhance_mission(original_mission, quality_issues)

        # Check structure is preserved
        assert enhanced.id == original_mission.id
        assert enhanced.type == original_mission.type
        assert enhanced.dependencies == original_mission.dependencies
        assert enhanced.priority == original_mission.priority

        # Goal should exist (might be enhanced or original)
        assert enhanced.goal is not None
        assert len(enhanced.goal) > 0

    def test_intervention_recording(self, leader_agent, tmp_path):
        """Test intervention decision recording"""
        from src.core.leader.mission_decomposer import SubMission
        from src.core.team.role_registry import Role, Mission, OutputStandard

        mission = SubMission(
            id="test",
            type="test",
            goal="test goal",
            requirements=[],
            success_criteria=[],
            dependencies=[],
            priority=1,
            estimated_cost_usd=0.1
        )

        # Create a dummy role
        role = Role(
            name="TestRole",
            description="Test",
            category="test",
            mission=Mission(
                goal="test",
                success_criteria=[],
                max_iterations=5
            ),
            output_standard=OutputStandard(
                required_files=[],
                validation_rules=[]
            ),
            recommended_persona="coder",
            tools=[],
            dependencies=[],
            enable_quality_check=False,
            quality_threshold=70.0
        )

        from src.core.leader.leader_agent import InterventionDecision

        decision = InterventionDecision(
            action=InterventionAction.RETRY,
            reason="Test retry",
            enhancements=None,
            adjustments=None
        )

        leader_agent.context = leader_agent.ExecutionContext(
            session_id="test_session",
            goal="test",
            missions=[mission],
            completed_missions={},
            active_roles=[],
            total_cost_usd=0.0,
            start_time=0.0,
            intervention_count=0
        )

        leader_agent._record_intervention(mission, role, decision, 1)

        assert len(leader_agent.intervention_history) == 1
        assert leader_agent.intervention_history[0]['action'] == 'retry'
        assert leader_agent.intervention_history[0]['reason'] == 'Test retry'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
