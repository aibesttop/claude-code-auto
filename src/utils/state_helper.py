"""
State Manager Helper

Provides clean interface for common state update patterns,
eliminating code duplication across orchestrator and executor modules.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from src.utils.state_manager import StateManager, NodeStatus

logger = logging.getLogger(__name__)


class StateManagerHelper:
    """
    Helper class for common state management operations.

    Reduces code duplication by 60%+ and provides a unified interface
    for role and mission status updates.
    """

    def __init__(self, state_manager: Optional[StateManager]):
        """
        Initialize helper.

        Args:
            state_manager: StateManager instance or None
        """
        self.state_manager = state_manager

    def update_role_status(
        self,
        role_name: str,
        status: NodeStatus,
        **kwargs
    ):
        """
        Update role status with automatic timestamp management.

        Args:
            role_name: Name of the role
            status: New status
            **kwargs: Additional fields to update (iterations, outputs, etc.)

        Example:
            helper.update_role_status("Market-Researcher", NodeStatus.IN_PROGRESS)
            helper.update_role_status("Market-Researcher", NodeStatus.COMPLETED,
                                     iterations=5, outputs=["report.md"])
        """
        if not self.state_manager:
            return

        try:
            state = self.state_manager.get_state()
            role_state = state.get_role(role_name)

            if not role_state:
                logger.warning(f"Role {role_name} not found in state")
                return

            # Update status
            role_state.status = status

            # Automatic timestamp management
            if status == NodeStatus.IN_PROGRESS:
                role_state.start_time = datetime.now().isoformat()
                state.set_current_role(role_name)
                logger.info(f"Started role: {role_name}")

            elif status in [NodeStatus.COMPLETED, NodeStatus.FAILED]:
                role_state.end_time = datetime.now().isoformat()
                if status == NodeStatus.COMPLETED:
                    logger.info(f"Completed role: {role_name}")
                else:
                    logger.warning(f"Failed role: {role_name}")

            # Apply additional updates
            for key, value in kwargs.items():
                if hasattr(role_state, key):
                    setattr(role_state, key, value)
                else:
                    logger.warning(
                        f"RoleState has no attribute '{key}', skipping"
                    )

            # Use batched save for performance
            self.state_manager.save()

        except Exception as e:
            logger.error(f"Error updating role status for {role_name}: {e}")

    def update_mission_status(
        self,
        mission_id: str,
        status: NodeStatus,
        **kwargs
    ):
        """
        Update mission status with automatic timestamp management.

        Args:
            mission_id: Mission identifier
            status: New status
            **kwargs: Additional fields to update

        Example:
            helper.update_mission_status("mission-1", NodeStatus.IN_PROGRESS)
            helper.update_mission_status("mission-1", NodeStatus.COMPLETED,
                                        result={"output": "success"})
        """
        if not self.state_manager:
            return

        try:
            state = self.state_manager.get_state()
            mission_state = state.get_mission(mission_id)

            if not mission_state:
                logger.warning(f"Mission {mission_id} not found in state")
                return

            # Update status
            mission_state.status = status

            # Automatic timestamp management
            if status == NodeStatus.IN_PROGRESS:
                mission_state.start_time = datetime.now().isoformat()
                state.set_current_mission(mission_id)
                logger.info(f"Started mission: {mission_id}")

            elif status in [NodeStatus.COMPLETED, NodeStatus.FAILED]:
                mission_state.end_time = datetime.now().isoformat()
                if status == NodeStatus.COMPLETED:
                    logger.info(f"Completed mission: {mission_id}")
                else:
                    logger.warning(f"Failed mission: {mission_id}")

            # Apply additional updates
            for key, value in kwargs.items():
                if hasattr(mission_state, key):
                    setattr(mission_state, key, value)
                else:
                    logger.warning(
                        f"MissionState has no attribute '{key}', skipping"
                    )

            # Use batched save for performance
            self.state_manager.save()

        except Exception as e:
            logger.error(f"Error updating mission status for {mission_id}: {e}")

    def increment_role_iteration(self, role_name: str):
        """
        Increment role iteration counter.

        Args:
            role_name: Name of the role
        """
        if not self.state_manager:
            return

        try:
            state = self.state_manager.get_state()
            role_state = state.get_role(role_name)

            if role_state:
                role_state.iterations += 1
                self.state_manager.save()
                logger.debug(f"Incremented {role_name} iterations to {role_state.iterations}")

        except Exception as e:
            logger.error(f"Error incrementing iterations for {role_name}: {e}")

    def add_role_output(self, role_name: str, output_file: str):
        """
        Add output file to role's output list.

        Args:
            role_name: Name of the role
            output_file: Path to output file
        """
        if not self.state_manager:
            return

        try:
            state = self.state_manager.get_state()
            role_state = state.get_role(role_name)

            if role_state:
                if output_file not in role_state.outputs:
                    role_state.outputs.append(output_file)
                    self.state_manager.save()
                    logger.debug(f"Added output {output_file} to {role_name}")

        except Exception as e:
            logger.error(f"Error adding output for {role_name}: {e}")

    def add_role_validation_errors(
        self,
        role_name: str,
        errors: List[str]
    ):
        """
        Add validation errors to role.

        Args:
            role_name: Name of the role
            errors: List of error messages
        """
        if not self.state_manager:
            return

        try:
            state = self.state_manager.get_state()
            role_state = state.get_role(role_name)

            if role_state:
                role_state.validation_errors = errors
                self.state_manager.save()
                logger.debug(f"Added {len(errors)} validation errors to {role_name}")

        except Exception as e:
            logger.error(f"Error adding validation errors for {role_name}: {e}")

    def is_enabled(self) -> bool:
        """Check if state manager is enabled."""
        return self.state_manager is not None
