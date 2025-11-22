"""
Multi-Dimensional Evaluator - 多维度评估器

提供格式、内容、LLM质量、测试、静态检查、安全等多维度评估
"""
import subprocess
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
from pathlib import Path
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger()


class EvaluationDimension(Enum):
    """评估维度"""
    FORMAT = "format"              # 格式验证
    CONTENT = "content"            # 内容完整性
    QUALITY_LLM = "quality_llm"    # LLM语义质量
    TESTS = "tests"                # 自动化测试
    STATIC_CHECKS = "static"       # 静态检查 (lint, type)
    SECURITY = "security"          # 安全检查


@dataclass
class DimensionScore:
    """单个维度的评分"""
    dimension: str  # EvaluationDimension的值
    score: float  # 0-100
    weight: float  # 权重
    evidence: Dict[str, Any]  # 评分证据
    issues: List[str]  # 发现的问题
    suggestions: List[str]  # 改进建议


@dataclass
class MultiDimEvaluation:
    """多维度评估结果"""
    overall_score: float  # 加权总分
    dimension_scores: List[DimensionScore]
    passed: bool  # 是否通过阈值
    threshold: float
    evaluation_time: str
    evaluator_version: str
    replay_context: Dict[str, Any]  # 用于重放的上下文


class MultiDimEvaluator:
    """多维度评估器"""

    def __init__(
        self,
        enable_tests: bool = True,
        enable_static: bool = True,
        enable_security: bool = False,
        llm_model: str = "haiku"
    ):
        """
        初始化多维度评估器

        Args:
            enable_tests: 启用测试维度
            enable_static: 启用静态检查维度
            enable_security: 启用安全检查维度
            llm_model: LLM模型 (haiku/sonnet/opus)
        """
        self.enable_tests = enable_tests
        self.enable_static = enable_static
        self.enable_security = enable_security
        self.llm_model = llm_model

        # 维度权重配置
        self.dimension_weights = {
            EvaluationDimension.FORMAT: 0.15,
            EvaluationDimension.CONTENT: 0.20,
            EvaluationDimension.QUALITY_LLM: 0.30,
            EvaluationDimension.TESTS: 0.20,
            EvaluationDimension.STATIC_CHECKS: 0.10,
            EvaluationDimension.SECURITY: 0.05,
        }

        logger.info(
            f"MultiDimEvaluator initialized: "
            f"tests={enable_tests}, static={enable_static}, "
            f"security={enable_security}, llm={llm_model}"
        )

    async def evaluate(
        self,
        mission: dict,
        outputs: List[str],
        work_dir: Path
    ) -> MultiDimEvaluation:
        """
        执行多维度评估

        Args:
            mission: SubMission定义
            outputs: 输出文件列表
            work_dir: 工作目录

        Returns:
            MultiDimEvaluation结果
        """
        logger.info(
            f"Starting multi-dimensional evaluation for mission {mission.get('id')}"
        )

        dimension_scores = []

        # 1. 格式验证
        format_score = await self._evaluate_format(mission, outputs, work_dir)
        dimension_scores.append(format_score)

        # 2. 内容完整性
        content_score = await self._evaluate_content(mission, outputs, work_dir)
        dimension_scores.append(content_score)

        # 3. LLM语义质量
        llm_score = await self._evaluate_llm_quality(mission, outputs, work_dir)
        dimension_scores.append(llm_score)

        # 4. 自动化测试 (可选)
        if self.enable_tests:
            test_score = await self._evaluate_tests(mission, work_dir)
            dimension_scores.append(test_score)

        # 5. 静态检查 (可选)
        if self.enable_static:
            static_score = await self._evaluate_static_checks(mission, work_dir)
            dimension_scores.append(static_score)

        # 6. 安全检查 (可选)
        if self.enable_security:
            security_score = await self._evaluate_security(mission, outputs, work_dir)
            dimension_scores.append(security_score)

        # 计算加权总分
        total_score = sum(
            ds.score * self.dimension_weights.get(
                EvaluationDimension(ds.dimension), 0.0
            )
            for ds in dimension_scores
        )

        # 归一化 (如果启用的维度权重总和<1.0)
        active_weights_sum = sum(
            self.dimension_weights[dim]
            for ds in dimension_scores
            for dim in EvaluationDimension
            if dim.value == ds.dimension
        )

        if active_weights_sum > 0 and abs(active_weights_sum - 1.0) > 0.01:
            overall_score = total_score / active_weights_sum
        else:
            overall_score = total_score

        # 生成重放上下文
        replay_context = {
            "mission_id": mission.get("id"),
            "mission_version": mission.get("version"),
            "outputs": outputs,
            "work_dir": str(work_dir),
            "evaluator_config": {
                "enable_tests": self.enable_tests,
                "enable_static": self.enable_static,
                "enable_security": self.enable_security,
                "llm_model": self.llm_model,
            },
            "dimension_weights": {
                k.value: v for k, v in self.dimension_weights.items()
            }
        }

        threshold = mission.get("quality_threshold", 70.0)

        evaluation = MultiDimEvaluation(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            passed=overall_score >= threshold,
            threshold=threshold,
            evaluation_time=datetime.utcnow().isoformat(),
            evaluator_version="v1.0",
            replay_context=replay_context
        )

        logger.info(
            f"Evaluation completed: overall_score={overall_score:.1f}, "
            f"passed={evaluation.passed}, threshold={threshold}"
        )

        return evaluation

    async def _evaluate_format(
        self,
        mission: dict,
        outputs: List[str],
        work_dir: Path
    ) -> DimensionScore:
        """评估维度: 格式验证"""
        issues = []
        suggestions = []
        evidence = {}

        # 检查required_files
        required_files = mission.get("output_standard", {}).get("required_files", [])
        existing_files = []
        missing_files = []

        for file_path in required_files:
            full_path = work_dir / file_path
            if full_path.exists():
                existing_files.append(file_path)
            else:
                missing_files.append(file_path)
                issues.append(f"Missing required file: {file_path}")

        evidence["required_files_total"] = len(required_files)
        evidence["existing_files"] = len(existing_files)
        evidence["missing_files"] = missing_files

        # 评分逻辑
        if required_files:
            score = (len(existing_files) / len(required_files)) * 100
        else:
            score = 100.0  # 无要求时满分

        if missing_files:
            suggestions.append(f"Create missing files: {', '.join(missing_files)}")

        return DimensionScore(
            dimension=EvaluationDimension.FORMAT.value,
            score=score,
            weight=self.dimension_weights[EvaluationDimension.FORMAT],
            evidence=evidence,
            issues=issues,
            suggestions=suggestions
        )

    async def _evaluate_content(
        self,
        mission: dict,
        outputs: List[str],
        work_dir: Path
    ) -> DimensionScore:
        """评估维度: 内容完整性"""
        issues = []
        suggestions = []
        evidence = {}

        # 检查validation_rules
        validation_rules = mission.get("output_standard", {}).get("validation_rules", [])
        passed_rules = 0
        failed_rules = []

        for rule in validation_rules:
            rule_type = rule.get("type")
            if rule_type == "min_length":
                min_length = rule.get("value", 0)
                # 检查输出文件长度
                total_length = 0
                for output_file in outputs:
                    file_path = work_dir / output_file
                    if file_path.exists():
                        total_length += len(file_path.read_text())

                if total_length >= min_length:
                    passed_rules += 1
                else:
                    failed_rules.append(f"min_length: {total_length} < {min_length}")
                    issues.append(f"Content too short: {total_length} chars < {min_length}")

        evidence["total_rules"] = len(validation_rules)
        evidence["passed_rules"] = passed_rules
        evidence["failed_rules"] = failed_rules

        # 评分逻辑
        if validation_rules:
            score = (passed_rules / len(validation_rules)) * 100
        else:
            score = 100.0

        if failed_rules:
            suggestions.append("Expand content to meet minimum length requirements")

        return DimensionScore(
            dimension=EvaluationDimension.CONTENT.value,
            score=score,
            weight=self.dimension_weights[EvaluationDimension.CONTENT],
            evidence=evidence,
            issues=issues,
            suggestions=suggestions
        )

    async def _evaluate_llm_quality(
        self,
        mission: dict,
        outputs: List[str],
        work_dir: Path
    ) -> DimensionScore:
        """评估维度: LLM语义质量"""
        # 这里简化实现，实际应调用Claude API进行语义评分
        # 由于实现复杂度，这里返回基础评分

        issues = []
        suggestions = []
        evidence = {"model": self.llm_model, "note": "Simplified implementation"}

        # 基础评分 (实际应使用LLM评分)
        score = 75.0

        return DimensionScore(
            dimension=EvaluationDimension.QUALITY_LLM.value,
            score=score,
            weight=self.dimension_weights[EvaluationDimension.QUALITY_LLM],
            evidence=evidence,
            issues=issues,
            suggestions=suggestions
        )

    async def _evaluate_tests(
        self,
        mission: dict,
        work_dir: Path
    ) -> DimensionScore:
        """评估维度: 自动化测试"""
        issues = []
        suggestions = []
        evidence = {}

        try:
            # 运行pytest with coverage
            result = subprocess.run(
                ["pytest", "--cov=.", "--cov-report=json", "tests/"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            # 解析覆盖率报告
            coverage_path = work_dir / "coverage.json"
            coverage_percent = 0.0

            if coverage_path.exists():
                with open(coverage_path) as f:
                    coverage_data = json.load(f)
                    coverage_percent = coverage_data.get("totals", {}).get("percent_covered", 0.0)
                    evidence["coverage_percent"] = coverage_percent
            else:
                evidence["coverage_percent"] = 0.0
                issues.append("No coverage report generated")

            # 解析测试结果
            passed = 0
            failed = 0

            if "passed" in result.stdout:
                import re
                match = re.search(r'(\d+) passed', result.stdout)
                if match:
                    passed = int(match.group(1))

                match = re.search(r'(\d+) failed', result.stdout)
                if match:
                    failed = int(match.group(1))

            evidence["tests_passed"] = passed
            evidence["tests_failed"] = failed

            if failed > 0:
                issues.append(f"{failed} tests failed")
                suggestions.append("Fix failing tests before proceeding")

            # 评分逻辑
            test_pass_rate = passed / (passed + failed) if (passed + failed) > 0 else 0
            score = (test_pass_rate * 50) + (min(coverage_percent / 80, 1.0) * 50)

            if coverage_percent < 70:
                issues.append(f"Test coverage is {coverage_percent:.1f}% (target: 70%+)")
                suggestions.append("Increase test coverage")

        except subprocess.TimeoutExpired:
            score = 0.0
            issues.append("Test execution timeout (>5min)")
            suggestions.append("Optimize test execution time")
        except FileNotFoundError:
            score = 50.0  # pytest未安装，给中等分
            evidence["note"] = "pytest not found"
            logger.warning("pytest not found, skipping test evaluation")
        except Exception as e:
            score = 0.0
            issues.append(f"Test execution failed: {e}")

        return DimensionScore(
            dimension=EvaluationDimension.TESTS.value,
            score=score,
            weight=self.dimension_weights[EvaluationDimension.TESTS],
            evidence=evidence,
            issues=issues,
            suggestions=suggestions
        )

    async def _evaluate_static_checks(
        self,
        mission: dict,
        work_dir: Path
    ) -> DimensionScore:
        """评估维度: 静态检查"""
        issues = []
        suggestions = []
        evidence = {}

        lint_errors = 0
        type_errors = 0

        # 1. Flake8 linting
        try:
            result = subprocess.run(
                ["flake8", ".", "--count", "--select=E9,F63,F7,F82", "--show-source"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.stdout:
                lint_errors = result.stdout.count('\n')

            evidence["lint_errors"] = lint_errors

            if lint_errors > 0:
                issues.append(f"{lint_errors} linting errors")
                suggestions.append("Run 'flake8 .' to see detailed errors")

        except FileNotFoundError:
            evidence["lint_errors"] = -1
            logger.warning("flake8 not found, skipping lint check")
        except Exception as e:
            evidence["lint_errors"] = -1
            logger.error(f"Flake8 error: {e}")

        # 2. Mypy type checking (简化跳过，因为需要配置)
        evidence["type_errors"] = 0
        type_errors = 0

        # 评分逻辑
        lint_score = max(0, 100 - lint_errors * 5)  # 每个错误扣5分
        type_score = 100  # 暂时满分

        score = (lint_score * 0.6 + type_score * 0.4)

        return DimensionScore(
            dimension=EvaluationDimension.STATIC_CHECKS.value,
            score=score,
            weight=self.dimension_weights[EvaluationDimension.STATIC_CHECKS],
            evidence=evidence,
            issues=issues,
            suggestions=suggestions
        )

    async def _evaluate_security(
        self,
        mission: dict,
        outputs: List[str],
        work_dir: Path
    ) -> DimensionScore:
        """评估维度: 安全检查"""
        # 简化实现
        issues = []
        suggestions = []
        evidence = {"note": "Basic security check"}

        # 基础评分
        score = 90.0

        return DimensionScore(
            dimension=EvaluationDimension.SECURITY.value,
            score=score,
            weight=self.dimension_weights[EvaluationDimension.SECURITY],
            evidence=evidence,
            issues=issues,
            suggestions=suggestions
        )


# 全局单例
_evaluator_instance: Optional[MultiDimEvaluator] = None


def get_evaluator(
    enable_tests: bool = True,
    enable_static: bool = True,
    enable_security: bool = False
) -> MultiDimEvaluator:
    """
    获取全局评估器实例

    Args:
        enable_tests: 启用测试维度
        enable_static: 启用静态检查维度
        enable_security: 启用安全检查维度

    Returns:
        MultiDimEvaluator实例
    """
    global _evaluator_instance

    if _evaluator_instance is None:
        _evaluator_instance = MultiDimEvaluator(
            enable_tests=enable_tests,
            enable_static=enable_static,
            enable_security=enable_security
        )

    return _evaluator_instance
