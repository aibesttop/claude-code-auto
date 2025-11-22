"""
Role Registry

Manages loading and accessing role definitions from YAML files.
"""

from pathlib import Path
from typing import Dict, Optional, List
import yaml
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ValidationRule(BaseModel):
    """Validation rule for role outputs"""
    type: str
    file: Optional[str] = None
    files: Optional[List[str]] = None
    must_contain: Optional[List[str]] = None
    forbidden_patterns: Optional[List[str]] = None
    min_chars: Optional[int] = None


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
    """Role definition"""
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


class RoleRegistry:
    """
    Registry for all available roles.
    
    Loads role definitions from YAML files and provides access to them.
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
