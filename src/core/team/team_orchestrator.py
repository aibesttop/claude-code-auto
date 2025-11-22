"""
Team Orchestrator

Orchestrates linear execution of a team of roles.
"""

from typing import List, Dict, Any
from src.core.team.role_registry import Role
from src.core.team.role_executor import RoleExecutor
from src.core.agents.executor import ExecutorAgent
from src.utils.state_helper import StateManagerHelper
from src.utils.state_manager import NodeStatus
import logging

logger = logging.getLogger(__name__)


class TeamOrchestrator:
    """
    Orchestrates linear execution of a team of roles.

    Each role completes its mission before the next one starts.
    Context is passed from one role to the next.
    """

    def __init__(
        self,
        roles: List[Role],
        executor_agent: ExecutorAgent,
        work_dir: str,
        state_manager=None
    ):
        """
        Initialize the team orchestrator.

        Args:
            roles: List of roles in execution order
            executor_agent: Existing ExecutorAgent instance
            work_dir: Working directory
            state_manager: Optional StateManager for visualization updates
        """
        self.roles = roles
        self.executor = executor_agent
        self.work_dir = work_dir
        self.state_manager = state_manager

        # State management helper (eliminates code duplication)
        self.state_helper = StateManagerHelper(state_manager)

        # Context storage (outputs from completed roles)
        self.context: Dict[str, Any] = {}
    
    async def execute(self, goal: str) -> Dict[str, Any]:
        """
        Execute team workflow linearly.

        Args:
            goal: Overall goal to achieve

        Returns:
            {
                "success": bool,
                "completed_roles": int,
                "results": Dict[role_name, result]
            }
        """
        logger.info(f"🎯 Team Goal: {goal}")
        logger.info(f"👥 Team Size: {len(self.roles)}")
        logger.info(f"📋 Role Sequence: {[r.name for r in self.roles]}")

        results = {}

        for i, role in enumerate(self.roles):
            logger.info(f"\n{'='*60}")
            logger.info(f"Role {i+1}/{len(self.roles)}: {role.name}")
            logger.info(f"{'='*60}")

            # Update role status to IN_PROGRESS
            self.state_helper.update_role_status(role.name, NodeStatus.IN_PROGRESS)

            # Create role executor
            role_executor = RoleExecutor(
                role=role,
                executor_agent=self.executor,
                work_dir=self.work_dir
            )

            # Execute role mission (small loop)
            result = await role_executor.execute(context=self.context)

            # Save result
            results[role.name] = result

            # Update role status based on result
            final_status = NodeStatus.COMPLETED if result['success'] else NodeStatus.FAILED
            self.state_helper.update_role_status(
                role.name,
                final_status,
                iterations=result.get('iterations', 0),
                outputs=result.get('outputs', [])
            )

            # Add validation errors if failed
            if not result['success'] and 'validation_errors' in result:
                self.state_helper.add_role_validation_errors(
                    role.name,
                    result['validation_errors']
                )

            # Check success
            if not result['success']:
                logger.error(f"❌ {role.name} failed. Stopping team execution.")
                return {
                    "success": False,
                    "completed_roles": i,
                    "results": results
                }

            # Add to context for next role
            self.context[role.name] = result

            logger.info(f"✅ {role.name} completed in {result['iterations']} iterations")

        # Clear current role
        if self.state_manager:
            state = self.state_manager.get_state()
            state.current_role = None
            self.state_manager.save()

        logger.info(f"\n🎉 All {len(self.roles)} roles completed successfully!")

        return {
            "success": True,
            "completed_roles": len(self.roles),
            "results": results
        }
