"""
Dynamic Team Assembly System

This module provides the infrastructure for dynamic team formation and execution.
"""

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == "Role":
        from src.core.team.role_registry import Role
        return Role
    elif name == "RoleRegistry":
        from src.core.team.role_registry import RoleRegistry
        return RoleRegistry
    elif name == "ValidationRule":
        from src.core.team.role_registry import ValidationRule
        return ValidationRule
    elif name == "Mission":
        from src.core.team.role_registry import Mission
        return Mission
    elif name == "OutputStandard":
        from src.core.team.role_registry import OutputStandard
        return OutputStandard
    elif name == "TeamAssembler":
        from src.core.team.team_assembler import TeamAssembler
        return TeamAssembler
    elif name == "RoleExecutor":
        from src.core.team.role_executor import RoleExecutor
        return RoleExecutor
    elif name == "TeamOrchestrator":
        from src.core.team.team_orchestrator import TeamOrchestrator
        return TeamOrchestrator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    'Role',
    'RoleRegistry',
    'ValidationRule',
    'Mission',
    'OutputStandard',
    'TeamAssembler',
    'RoleExecutor',
    'TeamOrchestrator',
]
