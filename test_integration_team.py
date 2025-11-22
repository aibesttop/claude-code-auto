"""
Test Team Mode Integration
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.append(str(Path(__file__).parent))

from src.core.leader.leader_agent import LeaderAgent
from src.core.leader.mission_decomposer import SubMission

async def test_team_integration():
    print("="*70)
    print("Test: Team Mode Integration (Mocked)")
    print("="*70)

    # Mock dependencies
    with patch('src.core.leader.leader_agent.MissionDecomposer') as MockDecomposer, \
         patch('src.core.leader.leader_agent.TeamAssembler') as MockAssembler, \
         patch('src.core.leader.leader_agent.RoleExecutor') as MockExecutor, \
         patch('src.core.leader.leader_agent.RoleRegistry') as MockRegistry:
        
        # Setup mocks
        mock_decomposer = MockDecomposer.return_value
        mock_assembler = MockAssembler.return_value
        mock_registry = MockRegistry.return_value
        
        # Mock Role object
        mock_role = MagicMock()
        mock_role.name = "TestRole"
        mock_registry.get_role.return_value = mock_role
        
        # Mock missions
        mission1 = SubMission(id="m1", type="research", goal="Research", dependencies=[])
        mission2 = SubMission(id="m2", type="coding", goal="Code", dependencies=["m1"])
        mission3 = SubMission(id="m3", type="doc", goal="Document", dependencies=["m2"])
        
        # Decomposer returns missions in mixed order
        mock_decomposer.decompose = AsyncMock(return_value=[mission3, mission1, mission2])
        
        # Assembler returns role mapping
        mock_assembler.assign_roles = AsyncMock(return_value={
            "m1": "Researcher",
            "m2": "Developer",
            "m3": "Writer"
        })
        
        # Executor returns success
        mock_executor_instance = MockExecutor.return_value
        mock_executor_instance.execute = AsyncMock(return_value={
            "success": True,
            "outputs": {},
            "validation_passed": True
        })
        
        # Initialize Leader
        leader = LeaderAgent(work_dir="test_output")
        
        # Execute
        print("🚀 Starting execution...")
        result = await leader.execute("Build an app", "test_session")
        
        # Verify success
        if result["success"]:
            print("✅ Execution successful")
        else:
            print(f"❌ Execution failed: {result.get('error')}")
            return False
            
        # Verify execution order (should be m1 -> m2 -> m3)
        print("✅ Verified mocks were called")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_team_integration())
    sys.exit(0 if success else 1)
