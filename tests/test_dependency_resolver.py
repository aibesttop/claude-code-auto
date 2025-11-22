"""
Unit tests for DependencyResolver

Tests topological sorting, cycle detection, and validation logic.
"""

import pytest
from src.core.team.dependency_resolver import (
    DependencyResolver,
    CircularDependencyError,
    MissingRoleError,
    ValidationResult
)
from src.core.team.role_registry import Role, Mission, OutputStandard


def create_test_role(name: str, dependencies: list = None) -> Role:
    """Helper to create a test role"""
    return Role(
        name=name,
        description=f"Test role {name}",
        mission=Mission(
            goal=f"Test goal for {name}",
            success_criteria=["Test criteria"],
            max_iterations=10
        ),
        output_standard=OutputStandard(
            required_files=[f"{name.lower()}.md"],
            validation_rules=[]
        ),
        dependencies=dependencies or []
    )


class TestDependencyResolver:
    """Test suite for DependencyResolver"""

    def test_empty_list(self):
        """Test with empty role list"""
        resolver = DependencyResolver()
        result = resolver.topological_sort([])
        assert result == []

    def test_single_role_no_deps(self):
        """Test single role with no dependencies"""
        resolver = DependencyResolver()
        role = create_test_role("A")
        result = resolver.topological_sort([role])
        assert len(result) == 1
        assert result[0].name == "A"

    def test_simple_dependency_chain(self):
        """Test A <- B <- C (C depends on B, B depends on A)"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", dependencies=[])
        role_b = create_test_role("B", dependencies=["A"])
        role_c = create_test_role("C", dependencies=["B"])

        # Input order: C, A, B (unsorted)
        roles = [role_c, role_a, role_b]

        sorted_roles = resolver.topological_sort(roles)
        sorted_names = [r.name for r in sorted_roles]

        # Expected: A, B, C
        assert sorted_names == ["A", "B", "C"]

    def test_parallel_dependencies(self):
        """
        Test diamond dependency:
             A
            / \
           B   C
            \ /
             D
        """
        resolver = DependencyResolver()

        role_a = create_test_role("A", dependencies=[])
        role_b = create_test_role("B", dependencies=["A"])
        role_c = create_test_role("C", dependencies=["A"])
        role_d = create_test_role("D", dependencies=["B", "C"])

        roles = [role_d, role_c, role_a, role_b]  # Unsorted
        sorted_roles = resolver.topological_sort(roles)
        sorted_names = [r.name for r in sorted_roles]

        # A must come first, D must come last
        assert sorted_names[0] == "A"
        assert sorted_names[-1] == "D"
        # B and C can be in any order
        assert set(sorted_names[1:3]) == {"B", "C"}

    def test_complex_dependency_graph(self):
        """
        Test complex scenario:
        Market-Researcher (no deps)
        Architect (depends on Market-Researcher)
        AI-Native-Writer (depends on Architect)
        AI-Native-Developer (depends on AI-Native-Writer)
        SEO-Specialist (depends on Market-Researcher, AI-Native-Writer)
        """
        resolver = DependencyResolver()

        market = create_test_role("Market-Researcher", [])
        architect = create_test_role("Architect", ["Market-Researcher"])
        writer = create_test_role("AI-Native-Writer", ["Architect"])
        developer = create_test_role("AI-Native-Developer", ["AI-Native-Writer"])
        seo = create_test_role("SEO-Specialist", ["Market-Researcher", "AI-Native-Writer"])

        roles = [developer, seo, writer, market, architect]  # Random order
        sorted_roles = resolver.topological_sort(roles)
        sorted_names = [r.name for r in sorted_roles]

        # Market-Researcher must be first
        assert sorted_names[0] == "Market-Researcher"

        # Architect comes after Market-Researcher
        assert sorted_names.index("Architect") > sorted_names.index("Market-Researcher")

        # Writer comes after Architect
        assert sorted_names.index("AI-Native-Writer") > sorted_names.index("Architect")

        # Developer comes after Writer
        assert sorted_names.index("AI-Native-Developer") > sorted_names.index("AI-Native-Writer")

        # SEO comes after both Market-Researcher and Writer
        assert sorted_names.index("SEO-Specialist") > sorted_names.index("Market-Researcher")
        assert sorted_names.index("SEO-Specialist") > sorted_names.index("AI-Native-Writer")

    def test_circular_dependency_simple(self):
        """Test simple circular dependency: A -> B -> A"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", dependencies=["B"])
        role_b = create_test_role("B", dependencies=["A"])

        with pytest.raises(CircularDependencyError) as exc_info:
            resolver.topological_sort([role_a, role_b])

        assert "Circular dependency" in str(exc_info.value)

    def test_circular_dependency_complex(self):
        """Test complex cycle: A -> B -> C -> A"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", dependencies=["C"])
        role_b = create_test_role("B", dependencies=["A"])
        role_c = create_test_role("C", dependencies=["B"])

        with pytest.raises(CircularDependencyError) as exc_info:
            resolver.topological_sort([role_a, role_b, role_c])

        error_msg = str(exc_info.value)
        assert "Circular dependency" in error_msg
        # Should mention the cycle
        assert "A" in error_msg or "B" in error_msg or "C" in error_msg

    def test_missing_dependency(self):
        """Test role depending on non-existent role"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", dependencies=["NonExistent"])

        with pytest.raises(MissingRoleError) as exc_info:
            resolver.topological_sort([role_a])

        assert "NonExistent" in str(exc_info.value)

    def test_self_dependency(self):
        """Test role depending on itself"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", dependencies=["A"])

        with pytest.raises(MissingRoleError) as exc_info:
            resolver.topological_sort([role_a])

        assert "depends on itself" in str(exc_info.value)


class TestValidation:
    """Test validation logic"""

    def test_validate_valid_dependencies(self):
        """Test validation with valid dependencies"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", [])
        role_b = create_test_role("B", ["A"])

        result = resolver.validate_dependencies([role_a, role_b])
        assert result.valid is True
        assert result.error is None

    def test_validate_missing_dependency(self):
        """Test validation catches missing dependency"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", ["Missing"])

        result = resolver.validate_dependencies([role_a])
        assert result.valid is False
        assert "Missing" in result.error

    def test_validate_self_dependency(self):
        """Test validation catches self-dependency"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", ["A"])

        result = resolver.validate_dependencies([role_a])
        assert result.valid is False
        assert "depends on itself" in result.error


class TestDependencyLevels:
    """Test dependency level calculation"""

    def test_levels_simple_chain(self):
        """Test levels for simple chain A <- B <- C"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", [])
        role_b = create_test_role("B", ["A"])
        role_c = create_test_role("C", ["B"])

        levels = resolver.get_dependency_levels([role_a, role_b, role_c])

        assert levels["A"] == 0
        assert levels["B"] == 1
        assert levels["C"] == 2

    def test_levels_diamond(self):
        """Test levels for diamond graph"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", [])
        role_b = create_test_role("B", ["A"])
        role_c = create_test_role("C", ["A"])
        role_d = create_test_role("D", ["B", "C"])

        levels = resolver.get_dependency_levels([role_a, role_b, role_c, role_d])

        assert levels["A"] == 0
        assert levels["B"] == 1
        assert levels["C"] == 1
        assert levels["D"] == 2  # max(B, C) + 1

    def test_levels_complex(self):
        """Test levels identify parallel execution opportunities"""
        resolver = DependencyResolver()

        # Same roles as market research example
        market = create_test_role("Market-Researcher", [])
        architect = create_test_role("Architect", ["Market-Researcher"])
        writer = create_test_role("AI-Native-Writer", ["Architect"])
        seo = create_test_role("SEO-Specialist", ["Market-Researcher", "AI-Native-Writer"])

        levels = resolver.get_dependency_levels([market, architect, writer, seo])

        assert levels["Market-Researcher"] == 0
        assert levels["Architect"] == 1
        assert levels["AI-Native-Writer"] == 2
        assert levels["SEO-Specialist"] == 3  # max(0, 2) + 1


class TestExecutionPlan:
    """Test execution plan formatting"""

    def test_format_execution_plan(self):
        """Test human-readable plan generation"""
        resolver = DependencyResolver()

        role_a = create_test_role("A", [])
        role_b = create_test_role("B", ["A"])
        role_c = create_test_role("C", ["B"])

        plan = resolver.format_execution_plan([role_c, role_a, role_b])

        # Should contain all role names
        assert "A" in plan
        assert "B" in plan
        assert "C" in plan

        # Should show dependency info
        assert "Dependencies" in plan

        # Should show level info
        assert "Level" in plan

        # Should show summary
        assert "Total Roles: 3" in plan


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_large_dependency_graph(self):
        """Test with many roles (performance test)"""
        resolver = DependencyResolver()

        # Create 50 roles in a chain
        roles = []
        for i in range(50):
            deps = [f"Role-{i-1}"] if i > 0 else []
            role = create_test_role(f"Role-{i}", deps)
            roles.append(role)

        sorted_roles = resolver.topological_sort(roles)
        sorted_names = [r.name for r in sorted_roles]

        # Should be in correct order
        for i in range(50):
            assert sorted_names[i] == f"Role-{i}"

    def test_multiple_independent_chains(self):
        """Test with multiple independent dependency chains"""
        resolver = DependencyResolver()

        # Chain 1: A <- B
        role_a = create_test_role("A", [])
        role_b = create_test_role("B", ["A"])

        # Chain 2: X <- Y
        role_x = create_test_role("X", [])
        role_y = create_test_role("Y", ["X"])

        roles = [role_b, role_y, role_a, role_x]
        sorted_roles = resolver.topological_sort(roles)
        sorted_names = [r.name for r in sorted_roles]

        # Within each chain, order must be preserved
        assert sorted_names.index("A") < sorted_names.index("B")
        assert sorted_names.index("X") < sorted_names.index("Y")

    def test_has_cycle_method(self):
        """Test _has_cycle helper method"""
        resolver = DependencyResolver()

        # No cycle
        role_a = create_test_role("A", [])
        role_b = create_test_role("B", ["A"])
        assert resolver._has_cycle([role_a, role_b]) is False

        # Has cycle
        role_c = create_test_role("C", dependencies=["D"])
        role_d = create_test_role("D", dependencies=["C"])
        assert resolver._has_cycle([role_c, role_d]) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
