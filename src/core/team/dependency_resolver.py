"""
Dependency Resolver for Team Mode

Implements topological sorting to ensure roles execute in correct dependency order.
Uses Kahn's algorithm for cycle detection and ordering.
"""

from typing import List, Dict, Set, Optional
from collections import defaultdict, deque
from dataclasses import dataclass

from src.core.team.role_registry import Role
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class ValidationResult:
    """Result of dependency validation"""
    valid: bool
    error: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class CircularDependencyError(Exception):
    """Raised when circular dependencies are detected"""
    pass


class MissingRoleError(Exception):
    """Raised when a dependency references a non-existent role"""
    pass


class DependencyResolver:
    """
    Resolves role dependencies and ensures deterministic execution order.

    Features:
    - Topological sorting using Kahn's algorithm
    - Circular dependency detection
    - Missing role validation
    - Detailed error messages for debugging
    """

    def __init__(self):
        self.logger = logger

    def topological_sort(self, roles: List[Role]) -> List[Role]:
        """
        Sort roles in dependency order using Kahn's algorithm.

        Algorithm:
        1. Calculate in-degree (number of dependencies) for each role
        2. Start with roles having zero dependencies
        3. Process roles level by level, removing edges
        4. Detect cycles if any roles remain unprocessed

        Args:
            roles: List of Role objects with dependencies

        Returns:
            List of roles in execution order (dependencies first)

        Raises:
            CircularDependencyError: If circular dependencies exist
            MissingRoleError: If a dependency references non-existent role
        """
        if not roles:
            return []

        # Build role name to role object mapping
        role_map = {role.name: role for role in roles}

        # Validate all dependencies exist
        validation = self.validate_dependencies(roles)
        if not validation.valid:
            raise MissingRoleError(validation.error)

        # Build dependency graph: role_name -> list of dependents
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        # Initialize all roles with zero in-degree
        for role in roles:
            if role.name not in in_degree:
                in_degree[role.name] = 0

        # Build graph and calculate in-degrees
        for role in roles:
            for dependency in role.dependencies:
                # dependency -> role (dependency must come before role)
                graph[dependency].append(role.name)
                in_degree[role.name] += 1

        # Find all roles with no dependencies (in-degree = 0)
        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        sorted_names = []

        # Kahn's algorithm
        while queue:
            # Process role with no remaining dependencies
            current = queue.popleft()
            sorted_names.append(current)

            # Reduce in-degree for all dependents
            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles
        if len(sorted_names) != len(roles):
            # Identify roles involved in cycle
            unprocessed = [name for name in in_degree.keys() if name not in sorted_names]
            cycle_info = self._find_cycle(roles, unprocessed)
            raise CircularDependencyError(
                f"Circular dependency detected: {cycle_info}"
            )

        # Convert sorted names back to Role objects
        sorted_roles = [role_map[name] for name in sorted_names]

        self.logger.info(f"✅ Dependency resolution complete. Order: {sorted_names}")
        return sorted_roles

    def validate_dependencies(self, roles: List[Role]) -> ValidationResult:
        """
        Validate that all dependencies are satisfied.

        Checks:
        1. All referenced dependencies exist in the role list
        2. No self-dependencies

        Args:
            roles: List of roles to validate

        Returns:
            ValidationResult with status and error details
        """
        role_names = {role.name for role in roles}
        warnings = []

        for role in roles:
            # Check for self-dependency
            if role.name in role.dependencies:
                return ValidationResult(
                    valid=False,
                    error=f"Role '{role.name}' depends on itself"
                )

            # Check for missing dependencies
            for dependency in role.dependencies:
                if dependency not in role_names:
                    return ValidationResult(
                        valid=False,
                        error=f"Role '{role.name}' depends on non-existent role '{dependency}'"
                    )

        return ValidationResult(valid=True, warnings=warnings)

    def _find_cycle(self, roles: List[Role], suspects: List[str]) -> str:
        """
        Find and describe a cycle in the dependency graph.

        Args:
            roles: All roles
            suspects: Role names suspected to be in a cycle

        Returns:
            String description of the cycle
        """
        role_map = {role.name: role for role in roles}

        # Use DFS to find cycle
        visited = set()
        path = []

        def dfs(role_name: str) -> Optional[List[str]]:
            if role_name in path:
                # Found cycle
                cycle_start = path.index(role_name)
                return path[cycle_start:] + [role_name]

            if role_name in visited:
                return None

            visited.add(role_name)
            path.append(role_name)

            role = role_map.get(role_name)
            if role:
                for dep in role.dependencies:
                    if dep in suspects:
                        cycle = dfs(dep)
                        if cycle:
                            return cycle

            path.pop()
            return None

        # Try to find cycle starting from each suspect
        for suspect in suspects:
            cycle = dfs(suspect)
            if cycle:
                return " → ".join(cycle)

        return f"Cycle involves: {', '.join(suspects)}"

    def _has_cycle(self, roles: List[Role]) -> bool:
        """
        Check if dependency graph has cycles using DFS.

        Args:
            roles: List of roles to check

        Returns:
            True if cycle exists, False otherwise
        """
        try:
            self.topological_sort(roles)
            return False
        except CircularDependencyError:
            return True

    def get_dependency_levels(self, roles: List[Role]) -> Dict[str, int]:
        """
        Calculate dependency level for each role.
        Level 0 = no dependencies, Level 1 = depends on Level 0, etc.

        Useful for:
        - Visualizing dependency hierarchy
        - Identifying parallel execution opportunities

        Args:
            roles: List of roles

        Returns:
            Dict mapping role name to dependency level
        """
        sorted_roles = self.topological_sort(roles)
        role_map = {role.name: role for role in roles}
        levels = {}

        for role in sorted_roles:
            if not role.dependencies:
                levels[role.name] = 0
            else:
                # Level = max(dependency levels) + 1
                dep_levels = [levels[dep] for dep in role.dependencies]
                levels[role.name] = max(dep_levels) + 1

        return levels

    def format_execution_plan(self, roles: List[Role]) -> str:
        """
        Generate a human-readable execution plan.

        Args:
            roles: List of roles (unsorted)

        Returns:
            Formatted string showing execution order and levels
        """
        sorted_roles = self.topological_sort(roles)
        levels = self.get_dependency_levels(roles)

        lines = ["📋 Execution Plan:", ""]

        for i, role in enumerate(sorted_roles, 1):
            level = levels[role.name]
            deps = ", ".join(role.dependencies) if role.dependencies else "None"
            lines.append(f"  {i}. [{role.name}]")
            lines.append(f"     Level: {level} | Dependencies: {deps}")

        lines.append("")
        lines.append(f"Total Roles: {len(roles)} | Max Depth: {max(levels.values())}")

        return "\n".join(lines)
