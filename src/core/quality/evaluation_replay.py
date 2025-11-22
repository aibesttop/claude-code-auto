"""
Evaluation Replay - 评估结果重放器

提供评估结果的保存、加载、重放和对比功能
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from src.utils.logger import get_logger
from .multi_dim_evaluator import MultiDimEvaluation, MultiDimEvaluator, DimensionScore

logger = get_logger()


class EvaluationReplay:
    """评估结果重放器"""

    def __init__(self, replay_dir: Path):
        """
        初始化评估重放器

        Args:
            replay_dir: 重放文件存储目录
        """
        self.replay_dir = Path(replay_dir)
        self.replay_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"EvaluationReplay initialized: {replay_dir}")

    def save_evaluation(
        self,
        evaluation: MultiDimEvaluation,
        mission_id: str
    ) -> Path:
        """
        保存评估结果用于重放

        格式: logs/evaluations/{mission_id}_{timestamp}.json

        Args:
            evaluation: 评估结果
            mission_id: 任务ID

        Returns:
            保存的文件路径
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{mission_id}_{timestamp}.json"

        eval_data = {
            "mission_id": mission_id,
            "timestamp": timestamp,
            "overall_score": evaluation.overall_score,
            "passed": evaluation.passed,
            "threshold": evaluation.threshold,
            "evaluator_version": evaluation.evaluator_version,
            "dimension_scores": [
                {
                    "dimension": ds.dimension,
                    "score": ds.score,
                    "weight": ds.weight,
                    "evidence": ds.evidence,
                    "issues": ds.issues,
                    "suggestions": ds.suggestions
                }
                for ds in evaluation.dimension_scores
            ],
            "replay_context": evaluation.replay_context
        }

        path = self.replay_dir / filename
        with open(path, 'w') as f:
            json.dump(eval_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved evaluation to {path}")
        return path

    def load_evaluation(self, path: Path) -> Optional[dict]:
        """
        加载历史评估结果

        Args:
            path: 评估文件路径

        Returns:
            评估数据字典或None
        """
        if not path.exists():
            logger.warning(f"Evaluation file not found: {path}")
            return None

        try:
            with open(path) as f:
                eval_data = json.load(f)

            logger.info(f"Loaded evaluation from {path}")
            return eval_data

        except Exception as e:
            logger.error(f"Failed to load evaluation: {e}")
            return None

    async def replay_evaluation(
        self,
        eval_data: dict,
        evaluator: MultiDimEvaluator
    ) -> MultiDimEvaluation:
        """
        重放评估 (重新执行)

        使用相同的配置和输入重新评估

        Args:
            eval_data: 评估数据
            evaluator: 评估器实例

        Returns:
            新的评估结果
        """
        replay_ctx = eval_data.get("replay_context", {})

        logger.info(
            f"Replaying evaluation for mission {replay_ctx.get('mission_id')}"
        )

        # 恢复评估器配置
        eval_config = replay_ctx.get("evaluator_config", {})
        evaluator.enable_tests = eval_config.get("enable_tests", True)
        evaluator.enable_static = eval_config.get("enable_static", True)
        evaluator.enable_security = eval_config.get("enable_security", False)

        # 重新执行评估
        mission = {
            "id": replay_ctx.get("mission_id"),
            "version": replay_ctx.get("mission_version")
        }

        result = await evaluator.evaluate(
            mission=mission,
            outputs=replay_ctx.get("outputs", []),
            work_dir=Path(replay_ctx.get("work_dir", "."))
        )

        logger.info("Replay completed")
        return result

    def compare_evaluations(
        self,
        eval1: dict,
        eval2: dict
    ) -> dict:
        """
        对比两次评估结果

        用于验证评估的一致性或分析改进

        Args:
            eval1: 第一次评估数据
            eval2: 第二次评估数据

        Returns:
            对比结果字典
        """
        comparison = {
            "score_diff": eval2["overall_score"] - eval1["overall_score"],
            "passed_changed": eval1["passed"] != eval2["passed"],
            "dimension_diffs": [],
            "issues_resolved": [],
            "issues_new": []
        }

        # 对比各维度分数
        dims1 = {d["dimension"]: d for d in eval1.get("dimension_scores", [])}
        dims2 = {d["dimension"]: d for d in eval2.get("dimension_scores", [])}

        for dim_name in set(dims1.keys()) | set(dims2.keys()):
            if dim_name in dims1 and dim_name in dims2:
                diff = dims2[dim_name]["score"] - dims1[dim_name]["score"]
                comparison["dimension_diffs"].append({
                    "dimension": dim_name,
                    "diff": diff,
                    "before": dims1[dim_name]["score"],
                    "after": dims2[dim_name]["score"]
                })

        # 对比issues
        issues1_set = set(
            issue
            for d in eval1.get("dimension_scores", [])
            for issue in d.get("issues", [])
        )
        issues2_set = set(
            issue
            for d in eval2.get("dimension_scores", [])
            for issue in d.get("issues", [])
        )

        comparison["issues_resolved"] = list(issues1_set - issues2_set)
        comparison["issues_new"] = list(issues2_set - issues1_set)

        logger.info(
            f"Comparison completed: score_diff={comparison['score_diff']:.1f}, "
            f"issues_resolved={len(comparison['issues_resolved'])}, "
            f"issues_new={len(comparison['issues_new'])}"
        )

        return comparison

    def list_evaluations(self, mission_id: str = None) -> list:
        """
        列出所有评估记录

        Args:
            mission_id: 可选的任务ID过滤

        Returns:
            评估文件路径列表
        """
        if mission_id:
            pattern = f"{mission_id}_*.json"
        else:
            pattern = "*.json"

        files = sorted(self.replay_dir.glob(pattern), reverse=True)
        logger.info(f"Found {len(files)} evaluation files")
        return files


# 全局单例
_replay_instance: Optional[EvaluationReplay] = None


def get_replay_manager(replay_dir: Path = None) -> EvaluationReplay:
    """
    获取全局重放管理器实例

    Args:
        replay_dir: 重放文件目录 (仅在首次调用时使用)

    Returns:
        EvaluationReplay实例
    """
    global _replay_instance

    if _replay_instance is None:
        if replay_dir is None:
            # 默认使用项目下的logs/evaluations目录
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            replay_dir = project_root / "logs" / "evaluations"

        _replay_instance = EvaluationReplay(replay_dir)

    return _replay_instance
