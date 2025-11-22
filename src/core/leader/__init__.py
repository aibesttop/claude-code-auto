"""
Leader Module - Meta-level orchestration for dynamic team management.

This module provides the Leader Agent that replaces static team assembly
with dynamic, stateful coordination.
"""

from src.core.leader.leader_agent import LeaderAgent
from src.core.leader.mission_decomposer import MissionDecomposer, SubMission

__all__ = [
    'LeaderAgent',
    'MissionDecomposer',
    'SubMission',
]
