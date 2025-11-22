"""
Mission Decomposer - Breaks down user goals into sub-missions.

Uses LLM to analyze complex goals and create actionable sub-tasks
with clear success criteria.
"""
from typing import List, Dict, Any
from dataclasses import dataclass, field
import json

from src.core.agents.sdk_client import run_claude_prompt
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class SubMission:
    """
    Sub-mission definition.

    Represents a single sub-task that can be assigned to a role.
    """
    id: str
    type: str  # "market_research", "code_generation", "documentation", etc.
    goal: str
    requirements: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # IDs of dependent missions
    priority: int = 1
    estimated_cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "type": self.type,
            "goal": self.goal,
            "requirements": self.requirements,
            "success_criteria": self.success_criteria,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "estimated_cost_usd": self.estimated_cost_usd
        }


class MissionDecomposer:
    """
    Mission Decomposer - Uses LLM to break down complex goals.

    Analyzes user goals and creates structured sub-missions that can be
    executed by specialized roles.
    """

    DECOMPOSITION_PROMPT = """You are an expert project manager analyzing a complex goal.

Your task: Break down the goal into concrete, executable sub-missions.

Guidelines:
1. Each sub-mission should be independent and actionable
2. Identify mission type: "market_research", "documentation", "code_generation", "architecture_design", "seo_strategy", etc.
3. Define clear success criteria (measurable outcomes)
4. Specify requirements (what's needed to complete)
5. Identify dependencies (which missions must complete first)
6. Estimate relative priority (1=low, 5=high)

Output Format (JSON):
{{
  "missions": [
    {{
      "id": "mission_1",
      "type": "market_research",
      "goal": "Complete in-depth market research...",
      "requirements": ["web access", "search capability"],
      "success_criteria": ["Identify 3+ user segments", "Analyze 5+ competitors"],
      "dependencies": [],
      "priority": 5
    }},
    ...
  ]
}}

User Goal:
{goal}

Analyze and decompose this goal into sub-missions:"""

    def __init__(self, model: str = "sonnet", work_dir: str = "."):
        self.model = model
        self.work_dir = work_dir

    async def decompose(self, goal: str) -> List[SubMission]:
        """
        Decompose a complex goal into sub-missions.

        Args:
            goal: User's high-level goal

        Returns:
            List of SubMission objects
        """
        logger.info(f"🎯 Decomposing goal: {goal}")

        # Prepare prompt
        prompt = self.DECOMPOSITION_PROMPT.format(goal=goal)

        # Call LLM using Claude Code SDK
        try:
            response, _ = await run_claude_prompt(
                prompt=prompt,
                work_dir=self.work_dir,
                model=self.model,
                permission_mode="bypassPermissions",
                timeout=120,
                max_retries=3
            )

            logger.debug(f"LLM Response:\n{response}")

            # Parse JSON response
            missions_data = self._parse_llm_response(response)

            # Convert to SubMission objects
            missions = []
            for data in missions_data:
                mission = SubMission(
                    id=data.get("id", f"mission_{len(missions)+1}"),
                    type=data.get("type", "general"),
                    goal=data.get("goal", ""),
                    requirements=data.get("requirements", []),
                    success_criteria=data.get("success_criteria", []),
                    dependencies=data.get("dependencies", []),
                    priority=data.get("priority", 1),
                    estimated_cost_usd=data.get("estimated_cost_usd", 0.0)
                )
                missions.append(mission)

            logger.info(f"✅ Decomposed into {len(missions)} missions")
            for i, m in enumerate(missions, 1):
                logger.info(f"   {i}. [{m.type}] {m.goal[:60]}...")

            return missions

        except Exception as e:
            logger.error(f"❌ Mission decomposition failed: {e}")
            # Fallback: Create single mission from goal
            return self._create_fallback_mission(goal)

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response to extract missions.

        Handles both JSON and markdown code blocks.
        """
        # Try to find JSON in code block
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()

        # Try to parse JSON
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "missions" in data:
                return data["missions"]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("Unexpected JSON structure")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            logger.warning(f"Response: {response[:200]}...")
            return []

    def _create_fallback_mission(self, goal: str) -> List[SubMission]:
        """
        Create a fallback mission when decomposition fails.
        """
        logger.warning("Using fallback: Single mission mode")

        return [SubMission(
            id="mission_1",
            type="general",
            goal=goal,
            requirements=["general purpose tools"],
            success_criteria=["Task completed"],
            dependencies=[],
            priority=5,
            estimated_cost_usd=0.0
        )]

    def validate_dependencies(self, missions: List[SubMission]) -> bool:
        """
        Validate that all dependencies exist and there are no cycles.

        Returns:
            True if valid, False otherwise
        """
        mission_ids = {m.id for m in missions}

        # Check all dependencies exist
        for mission in missions:
            for dep_id in mission.dependencies:
                if dep_id not in mission_ids:
                    logger.error(f"Mission {mission.id} has invalid dependency: {dep_id}")
                    return False

        # Check for circular dependencies (simple check)
        # TODO: Implement proper cycle detection if needed

        return True
