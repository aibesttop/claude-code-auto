"""
Role Registry

Manages loading and accessing role definitions from YAML files.

Enhanced for Tier-3 Agentic Workflow with:
- Reflection/Review loops (self-correction)
- Workflow state machine (dynamic transitions)
- Prompt template composition
"""

from pathlib import Path
from typing import Dict, Optional, List
from enum import Enum
import yaml
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class NextStepStrategy(str, Enum):
    """Strategy for determining next workflow state"""
    FIXED = "fixed"  # Always go to a fixed next state
    CONDITIONAL = "conditional"  # Based on content keywords/patterns
    LLM_DECIDE = "llm_decide"  # LeaderAgent decides dynamically


class ReviewConfig(BaseModel):
    """
    Reflection and review layer configuration (Tier-3 feature).

    Enables roles to self-correct by switching to a "critic" mode
    after generating initial output.
    """
    enabled: bool = Field(default=False, description="Enable reflection loop")
    reviewer_role: Optional[str] = Field(
        default=None,
        description="Role to review output (e.g., 'SRE-Auditor', 'Reviewer'). If None, self-review."
    )
    aspects: List[str] = Field(
        default_factory=list,
        description="Review dimensions: e.g., ['logic', 'security', 'scalability', 'compliance']"
    )
    max_retries: int = Field(default=3, description="Maximum review iterations")
    critic_prompt_template: Optional[str] = Field(
        default=None,
        description="Template for critic prompt. Use {aspects}, {output} placeholders."
    )


class WorkflowConfig(BaseModel):
    """
    Workflow state machine configuration (Tier-3 feature).

    Defines how roles transition to next states based on their output.
    """
    next_state: Optional[str] = Field(
        default=None,
        description="Next role/state to execute after completion"
    )
    strategy: NextStepStrategy = Field(
        default=NextStepStrategy.FIXED,
        description="How to determine next state"
    )
    transition_rules: Dict[str, str] = Field(
        default_factory=dict,
        description="Conditional transitions: {'contains_keyword': 'target_state'}"
    )
    # Example: {"needs_architecture": "Architect", "needs_research": "Market-Researcher"}


class ValidationRule(BaseModel):
    """Validation rule for role outputs"""
    type: str
    file: Optional[str] = None
    files: Optional[List[str]] = None
    must_contain: Optional[List[str]] = None
    patterns: Optional[List[str]] = None
    forbidden_patterns: Optional[List[str]] = None
    min_chars: Optional[int] = None
    criteria: Optional[List[str]] = None
    threshold: Optional[float] = None
    must_reference: Optional[List[str]] = None
    # Adaptive validation (v3.1)
    base_chars: Optional[int] = None  # Base value for adaptive min_length
    adaptive: bool = Field(default=False, description="Enable adaptive adjustment based on complexity")

    def get_effective_min_chars(self, task_complexity: str = "medium") -> int:
        """
        Calculate effective minimum character count based on task complexity.

        Args:
            task_complexity: Task complexity level (simple, medium, complex, expert)

        Returns:
            Effective minimum character count
        """
        if not self.adaptive or self.base_chars is None:
            # Non-adaptive or no base value: use static min_chars
            return self.min_chars if self.min_chars is not None else 0

        # Complexity multipliers
        multipliers = {
            "simple": 0.7,
            "medium": 1.0,
            "complex": 1.5,
            "expert": 2.0
        }

        multiplier = multipliers.get(task_complexity, 1.0)
        return int(self.base_chars * multiplier)


class Mission(BaseModel):
    """Role's mission definition"""
    goal: str
    success_criteria: List[str]
    max_iterations: int = 10


class OutputStandard(BaseModel):
    """Output standard for a role"""
    template: Optional[str] = None
    required_files: List[str]
    validation_rules: List[ValidationRule]


class Role(BaseModel):
    """Role definition with Tier-3 Agentic Workflow features"""
    name: str
    description: str
    category: Optional[str] = None
    mission: Mission
    output_standard: OutputStandard
    recommended_persona: Optional[str] = None
    tools: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

    # Quality validation (v3.1)
    enable_quality_check: bool = Field(default=False, description="Enable semantic quality validation")
    quality_threshold: float = Field(default=70.0, ge=0, le=100, description="Minimum quality score (0-100)")

    # Tier-3 Agentic Workflow features (v4.0)
    reflection: Optional[ReviewConfig] = Field(
        default=None,
        description="Reflection/review loop configuration"
    )
    workflow: Optional[WorkflowConfig] = Field(
        default=None,
        description="Workflow state machine configuration"
    )
    instructions_path: Optional[str] = Field(
        default=None,
        description="Path to custom system prompt instructions file (relative to roles/)"
    )
    base_instructions: Optional[str] = Field(
        default=None,
        description="Base system prompt instructions (inline)"
    )

    # Error handling strategies (v4.1)
    error_handling: Optional[Dict[str, str]] = Field(
        default=None,
        description="Error handling strategies for different failure scenarios"
    )


class RoleRegistry:
    """
    Registry for all available roles.

    Loads role definitions from YAML files and provides access to them.

    Enhanced for Tier-3 with prompt composition and workflow support.
    """

    def __init__(self, roles_dir: str = "roles"):
        """
        Initialize the role registry.

        Args:
            roles_dir: Directory containing role YAML files
        """
        self.roles_dir = Path(roles_dir)
        self.roles: Dict[str, Role] = {}
        self._load_roles()

    def load_instructions(self, role: Role) -> Optional[str]:
        """
        Load custom instructions for a role from file or inline.

        Args:
            role: Role object

        Returns:
            Instructions string or None if not found
        """
        # Inline instructions take priority
        if role.base_instructions:
            return role.base_instructions

        # Load from file if specified
        if role.instructions_path:
            instructions_file = self.roles_dir / role.instructions_path
            if instructions_file.exists():
                try:
                    content = instructions_file.read_text(encoding='utf-8')
                    logger.debug(f"Loaded instructions from {instructions_file}")
                    return content
                except Exception as e:
                    logger.error(f"Failed to load instructions from {instructions_file}: {e}")
            else:
                logger.warning(f"Instructions file not found: {instructions_file}")

        return None

    def get_full_prompt(self, role_name: str, context: str = None) -> str:
        """
        Compose full system prompt for a role.

        Combines:
        1. Custom instructions (if any)
        2. Mission and success criteria
        3. Output standards and validation rules
        4. Context (if provided)

        Args:
            role_name: Name of the role
            context: Optional additional context

        Returns:
            Composed system prompt string
        """
        role = self.get_role(role_name)
        if not role:
            return ""

        # Build prompt sections
        sections = []

        # Section 1: Role definition
        sections.append(f"# Role: {role.name}")
        sections.append(f"{role.description}\n")

        # Section 2: Custom instructions (if any)
        custom_instructions = self.load_instructions(role)
        if custom_instructions:
            sections.append("# Instructions")
            sections.append(f"{custom_instructions}\n")

        # Section 3: Persona (if specified)
        if role.recommended_persona:
            sections.append(f"# Persona")
            sections.append(f"You are acting as: {role.recommended_persona}\n")

        # Section 4: Mission
        sections.append("# Mission")
        sections.append(f"Goal: {role.mission.goal}")
        sections.append("Success Criteria:")
        for criterion in role.mission.success_criteria:
            sections.append(f"- {criterion}")
        sections.append("")

        # Section 5: Output Standards
        sections.append("# Output Standards")
        sections.append(f"Required Files: {', '.join(role.output_standard.required_files)}")

        # Translate validation rules into prompt instructions
        if role.output_standard.validation_rules:
            sections.append("\nValidation Requirements:")

            # Extract must_contain rules for emphasis
            must_contain_sections = []
            for rule in role.output_standard.validation_rules:
                if rule.must_contain:
                    must_contain_sections.extend(rule.must_contain)
                    sections.append(f"- Must contain: {', '.join(rule.must_contain)}")
                if rule.type == "regex_check" and rule.patterns:
                    rule_file = rule.file or "unspecified file"
                    sections.append(f"- Regex check ({rule_file}): {', '.join(rule.patterns)}")
                if rule.type == "reference_check" and rule.must_reference:
                    rule_file = rule.file or "unspecified file"
                    sections.append(f"- Must reference in {rule_file}: {', '.join(rule.must_reference)}")
                if rule.type == "semantic_judge" and rule.criteria:
                    rule_file = rule.file or "unspecified file"
                    threshold = rule.threshold if rule.threshold is not None else 0.7
                    sections.append(
                        f"- Semantic check ({rule_file}, threshold {threshold}): {', '.join(rule.criteria)}"
                    )
                if rule.forbidden_patterns:
                    sections.append(f"- Must NOT contain: {', '.join(rule.forbidden_patterns)}")
                if rule.min_chars or rule.base_chars:
                    min_chars = rule.min_chars or rule.base_chars
                    adaptive_note = " (adaptive based on complexity)" if rule.adaptive else ""
                    sections.append(f"- Minimum length: {min_chars} characters{adaptive_note}")

            # CRITICAL: Explicitly warn about exact section titles
            if must_contain_sections:
                sections.append("\n⚠️ CRITICAL: Section Title Requirements")
                sections.append("You MUST use these EXACT section titles (case-sensitive):")
                for section in must_contain_sections:
                    sections.append(f"  • {section}")
                sections.append("\n🚫 DO NOT use variations like:")
                sections.append("  • 'Market Size and Growth' instead of '## Market Size'")
                sections.append("  • 'User Segments' instead of '## Target Users'")
                sections.append("  • 'Market Opportunities' instead of '## Opportunities'")
                sections.append("\n❌ Using incorrect titles will cause validation failure!")
                sections.append("✅ Copy the exact titles from the list above to avoid retries.")

        # Section 6: Reflection/Review (Tier-3 feature)
        if role.reflection and role.reflection.enabled:
            sections.append("\n# Self-Review Process")
            sections.append("After completing your output, you MUST:")
            if role.reflection.aspects:
                aspects_str = ', '.join(role.reflection.aspects)
                sections.append(f"- Review your work for: {aspects_str}")
            sections.append(f"- Perform up to {role.reflection.max_retries} refinement iterations")
            sections.append("- Address any issues found during review")

        # Section 7: Error Handling Strategies (v4.1)
        if role.error_handling:
            sections.append("\n# Error Handling Strategies")
            sections.append("When encountering failures, follow these recovery strategies:")
            for scenario, strategy in role.error_handling.items():
                # Convert snake_case to readable format
                # e.g., "on_tool_failure" -> "Tool Failure"
                # Step 1: Replace underscores with spaces
                step1 = scenario.replace('_', ' ')
                # Step 2: Remove leading "on " if present
                step2 = step1[3:] if step1.startswith('on ') else step1
                # Step 3: Title case
                scenario_readable = step2.strip().title()
                sections.append(f"- **{scenario_readable}**: {strategy}")
            sections.append("\nThese strategies distinguish you from simple scripts - actively recover and adapt!")

        # Section 8: Context (if provided)
        if context:
            sections.append(f"\n# Context")
            sections.append(context)

        return "\n".join(sections)
    
    def _load_roles(self):
        """Load all role definitions from YAML files"""
        if not self.roles_dir.exists():
            logger.warning(f"Roles directory not found: {self.roles_dir}")
            self.roles_dir.mkdir(parents=True, exist_ok=True)
            return
        
        for role_file in self.roles_dir.glob("*.yaml"):
            try:
                with open(role_file, encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    role = Role(**config)
                    self.roles[role.name] = role
                    logger.info(f"Loaded role: {role.name}")
            except Exception as e:
                logger.error(f"Failed to load role from {role_file}: {e}")
    
    def get_role(self, name: str) -> Optional[Role]:
        """
        Get role by name.
        
        Args:
            name: Role name
            
        Returns:
            Role object or None if not found
        """
        return self.roles.get(name)
    
    def list_roles(self) -> List[str]:
        """
        List all available role names.
        
        Returns:
            List of role names
        """
        return list(self.roles.keys())
    
    def get_roles_by_category(self, category: str) -> List[Role]:
        """
        Get all roles in a category.
        
        Args:
            category: Category name
            
        Returns:
            List of Role objects
        """
        return [r for r in self.roles.values() if r.category == category]
    
    def reload(self):
        """Reload all roles from disk"""
        self.roles.clear()
        self._load_roles()
