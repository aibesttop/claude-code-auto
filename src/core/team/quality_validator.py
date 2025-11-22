"""
Semantic Quality Validator

Uses LLM to evaluate output quality against success criteria.
Provides numerical scoring and actionable feedback.
"""

from typing import List, Dict
from pathlib import Path
from pydantic import BaseModel, Field
import logging

from src.core.agents.sdk_client import run_claude_prompt
from src.utils.json_utils import extract_json

logger = logging.getLogger(__name__)


class QualityScore(BaseModel):
    """Quality evaluation result"""
    overall_score: float = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    criteria_scores: Dict[str, float] = Field(default_factory=dict, description="Scores per criterion")
    issues: List[str] = Field(default_factory=list, description="Identified issues")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")


class SemanticQualityValidator:
    """
    Validates output quality using LLM-based semantic analysis.

    Features:
    - Evaluates content against success criteria
    - Provides numerical scoring (0-100)
    - Identifies specific issues
    - Suggests improvements
    """

    def __init__(
        self,
        work_dir: str,
        model: str = "claude-3-haiku-20240307",
        timeout_seconds: int = 30
    ):
        """
        Initialize quality validator.

        Args:
            work_dir: Working directory
            model: Model to use (default: haiku for cost efficiency)
            timeout_seconds: Timeout for validation calls
        """
        self.work_dir = work_dir
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def score_output(
        self,
        content: str,
        success_criteria: List[str],
        file_type: str = "markdown"
    ) -> QualityScore:
        """
        Evaluate output quality against success criteria.

        Args:
            content: Content to evaluate
            success_criteria: List of success criteria
            file_type: Type of file (for context)

        Returns:
            QualityScore object with scoring and feedback
        """
        # Build criteria list for prompt
        criteria_list = "\n".join(f"- {c}" for c in success_criteria)

        # Limit content length to avoid token overflow
        content_preview = content[:3000]
        if len(content) > 3000:
            content_preview += "\n\n... [content truncated for evaluation]"

        prompt = f"""You are a quality auditor. Evaluate the following {file_type} content against these criteria:

CRITERIA:
{criteria_list}

CONTENT:
{content_preview}

Evaluate the content and respond ONLY with a valid JSON object (no explanatory text):
{{
    "overall_score": <number 0-100>,
    "criteria_scores": {{
        "<criterion_1>": <score 0-100>,
        "<criterion_2>": <score 0-100>
    }},
    "issues": [
        "<specific issue 1>",
        "<specific issue 2>"
    ],
    "suggestions": [
        "<actionable suggestion 1>",
        "<actionable suggestion 2>"
    ]
}}

Scoring guide:
- 90-100: Excellent, exceeds all criteria
- 70-89: Good, meets all criteria with minor issues
- 50-69: Acceptable, meets most criteria but has gaps
- 30-49: Poor, significant gaps in criteria
- 0-29: Unacceptable, fails to meet criteria

Be objective and specific in your evaluation."""

        try:
            logger.info("🔍 Running semantic quality validation...")

            response, _ = await run_claude_prompt(
                prompt,
                self.work_dir,
                model=self.model,
                timeout=self.timeout_seconds,
                permission_mode="bypassPermissions"
            )

            # Extract JSON from response
            score_data = extract_json(response)

            if not score_data or not isinstance(score_data, dict):
                logger.error(f"Failed to parse quality score: {response[:200]}")
                return QualityScore(
                    overall_score=50.0,
                    criteria_scores={},
                    issues=["Quality validation failed to parse response"],
                    suggestions=["Re-run validation manually"]
                )

            # Validate and construct QualityScore
            quality_score = QualityScore(
                overall_score=float(score_data.get("overall_score", 50.0)),
                criteria_scores=score_data.get("criteria_scores", {}),
                issues=score_data.get("issues", []),
                suggestions=score_data.get("suggestions", [])
            )

            logger.info(f"✅ Quality score: {quality_score.overall_score}/100")
            return quality_score

        except Exception as e:
            logger.error(f"Quality validation failed: {e}")
            return QualityScore(
                overall_score=50.0,
                criteria_scores={},
                issues=[f"Validation error: {str(e)}"],
                suggestions=["Check validator configuration and retry"]
            )

    async def batch_score_outputs(
        self,
        files: List[str],
        success_criteria: List[str]
    ) -> Dict[str, QualityScore]:
        """
        Score multiple output files.

        Args:
            files: List of file paths relative to work_dir
            success_criteria: Success criteria to evaluate against

        Returns:
            Dict mapping filename to QualityScore
        """
        results = {}

        for file_path in files:
            full_path = Path(self.work_dir) / file_path

            if not full_path.exists():
                logger.warning(f"File not found for quality check: {file_path}")
                results[file_path] = QualityScore(
                    overall_score=0.0,
                    issues=[f"File not found: {file_path}"],
                    suggestions=["Ensure file is generated before validation"]
                )
                continue

            try:
                content = full_path.read_text(encoding='utf-8')
                score = await self.score_output(content, success_criteria)
                results[file_path] = score
            except Exception as e:
                logger.error(f"Failed to score {file_path}: {e}")
                results[file_path] = QualityScore(
                    overall_score=0.0,
                    issues=[f"Error reading file: {str(e)}"],
                    suggestions=["Check file permissions and encoding"]
                )

        return results
