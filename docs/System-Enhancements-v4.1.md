# 系统增强方案 v4.1 - 生产级健壮性增强

## 📋 概述

本文档基于v4.0架构重构，提出8个关键维度的系统增强方案，旨在提升系统的**健壮性、可观测性、可恢复性和资源管理能力**，使其达到生产级标准。

---

## 🎯 增强维度总览

| 维度 | 核心问题 | 增强方案 | 优先级 |
|------|----------|----------|--------|
| **1. 结构化协议** | SubMission/Context定义不规范 | JSON Schema + 版本化 | P0 |
| **2. 评估强化** | 质量评估依赖单一LLM | 多维度评估 + 可重放 | P0 |
| **3. 成本与节流** | 缺乏细粒度预算控制 | 动态预算 + 熔断 | P0 |
| **4. 幂等与恢复** | 不支持断点续跑 | 状态持久化 + 幂等性 | P1 |
| **5. 资源隔离** | 工具权限缺乏限制 | 最小权限 + 速率限制 | P1 |
| **6. 观测与追踪** | 缺乏结构化追踪 | trace_id + 结构化日志 | P0 |
| **7. 终态策略** | 失败时缺乏恢复指南 | 部分交付 + 风险报告 | P2 |
| **8. 辅助角色治理** | AddHelper可能无限扩张 | 退场条件 + 退避策略 | P1 |

---

## 1️⃣ 结构化协议定义

### 问题分析

**当前问题**：
- SubMission定义松散，缺乏强制校验
- Context传递格式不统一，容易信息漂移
- 缺乏版本化机制，难以追溯变更

### 解决方案

#### 1.1 SubMission Schema定义

```yaml
# schemas/sub_mission.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: SubMission
description: Leader分解的子任务定义

type: object
required:
  - id
  - type
  - goal
  - success_criteria
  - priority
  - dependencies
  - version

properties:
  id:
    type: string
    pattern: "^mission-[0-9a-f]{8}$"
    description: "任务唯一标识 (如 mission-1a2b3c4d)"

  version:
    type: string
    pattern: "^v[0-9]+\\.[0-9]+$"
    description: "任务定义版本 (如 v1.0, v1.1 用于ENHANCE)"

  type:
    type: string
    enum: [research, documentation, development, testing, deployment]
    description: "任务类型"

  goal:
    type: string
    minLength: 50
    maxLength: 1000
    description: "任务目标描述"

  success_criteria:
    type: array
    minItems: 1
    maxItems: 10
    items:
      type: object
      required: [criterion, weight, validation_type]
      properties:
        criterion:
          type: string
          description: "成功标准描述"
        weight:
          type: number
          minimum: 0.0
          maximum: 1.0
          description: "权重 (所有标准总和=1.0)"
        validation_type:
          type: string
          enum: [file_exists, content_check, test_pass, llm_quality, custom]
        validation_config:
          type: object
          description: "验证配置 (根据validation_type不同)"

  priority:
    type: integer
    minimum: 1
    maximum: 10
    description: "优先级 (1=最高, 10=最低)"

  dependencies:
    type: array
    items:
      type: string
      pattern: "^mission-[0-9a-f]{8}$"
    description: "依赖的任务ID列表"

  resources:
    type: object
    properties:
      tools:
        type: array
        items:
          type: string
        description: "允许使用的工具列表"
      mcp_servers:
        type: array
        items:
          type: string
        description: "允许使用的MCP服务器"
      max_tokens:
        type: integer
        minimum: 1000
        description: "最大token预算"
      max_duration_minutes:
        type: integer
        minimum: 1
        description: "最大执行时长"

  budget:
    type: object
    required: [max_cost_usd, max_retries]
    properties:
      max_cost_usd:
        type: number
        minimum: 0.01
        description: "最大成本预算"
      max_retries:
        type: integer
        minimum: 0
        maximum: 5
        description: "最大重试次数"
      retry_backoff:
        type: string
        enum: [linear, exponential, fibonacci]
        default: exponential
        description: "重试退避策略"

  metadata:
    type: object
    properties:
      created_at:
        type: string
        format: date-time
      created_by:
        type: string
        enum: [leader, user, enhanced]
      parent_mission:
        type: string
        description: "父任务ID (如果是ENHANCE/ESCALATE产生)"
      tags:
        type: array
        items:
          type: string

additionalProperties: false
```

#### 1.2 Context传递协议

```yaml
# schemas/execution_context.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: ExecutionContext
description: 角色间传递的上下文快照

type: object
required:
  - context_id
  - version
  - source_mission
  - target_mission
  - snapshot_time
  - content_type
  - content

properties:
  context_id:
    type: string
    pattern: "^ctx-[0-9a-f]{8}$"

  version:
    type: string
    pattern: "^v[0-9]+\\.[0-9]+$"
    description: "上下文版本 (每次传递递增)"

  source_mission:
    type: string
    description: "来源任务ID"

  target_mission:
    type: string
    description: "目标任务ID"

  snapshot_time:
    type: string
    format: date-time

  content_type:
    type: string
    enum: [full, summary, reference]
    description: "内容类型"

  content:
    oneOf:
      - type: object  # full
        properties:
          files:
            type: array
            items:
              type: object
              properties:
                path:
                  type: string
                content:
                  type: string
                hash:
                  type: string
                  description: "SHA256 hash用于验证"

      - type: object  # summary
        properties:
          summary_text:
            type: string
            maxLength: 2000
          reference_path:
            type: string
            description: "完整内容存储路径"
          hash:
            type: string

      - type: object  # reference
        properties:
          reference_path:
            type: string
          hash:
            type: string

  metadata:
    type: object
    properties:
      total_files:
        type: integer
      total_size_bytes:
        type: integer
      compression:
        type: string
        enum: [none, gzip, zstd]
      encryption:
        type: boolean
```

#### 1.3 实现建议

```python
# src/core/schemas/validator.py
from jsonschema import validate, ValidationError
import yaml
from pathlib import Path

class SchemaValidator:
    """Schema验证器"""

    def __init__(self):
        schema_dir = Path(__file__).parent / "schemas"

        # 加载所有schema
        self.schemas = {
            "sub_mission": self._load_schema(schema_dir / "sub_mission.schema.yaml"),
            "execution_context": self._load_schema(schema_dir / "execution_context.schema.yaml"),
            "quality_score": self._load_schema(schema_dir / "quality_score.schema.yaml"),
        }

    def _load_schema(self, path: Path) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    def validate_sub_mission(self, mission: dict) -> tuple[bool, str]:
        """
        验证SubMission定义

        Returns:
            (is_valid, error_message)
        """
        try:
            validate(instance=mission, schema=self.schemas["sub_mission"])

            # 额外业务校验
            if not self._validate_success_criteria_weights(mission):
                return False, "Success criteria weights must sum to 1.0"

            if not self._validate_dependencies_acyclic(mission):
                return False, "Circular dependency detected"

            return True, ""

        except ValidationError as e:
            return False, f"Schema validation failed: {e.message}"

    def _validate_success_criteria_weights(self, mission: dict) -> bool:
        """验证成功标准权重总和为1.0"""
        total_weight = sum(
            criterion["weight"]
            for criterion in mission.get("success_criteria", [])
        )
        return abs(total_weight - 1.0) < 0.01  # 允许浮点误差

    def _validate_dependencies_acyclic(self, mission: dict) -> bool:
        """验证依赖关系无环 (简化检查)"""
        # 实际实现需要全局依赖图
        return mission["id"] not in mission.get("dependencies", [])
```

#### 1.4 版本化上下文传递策略

```python
# src/core/context/versioned_context.py
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

@dataclass
class ContextSnapshot:
    """版本化上下文快照"""
    context_id: str
    version: str
    source_mission: str
    target_mission: str
    snapshot_time: datetime
    content_type: str  # full, summary, reference
    content: dict
    hash: str  # 用于验证完整性

class VersionedContextManager:
    """版本化上下文管理器"""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.version_counter = 0

    def create_snapshot(
        self,
        source_mission: str,
        target_mission: str,
        content: dict,
        threshold_bytes: int = 50000  # 50KB阈值
    ) -> ContextSnapshot:
        """
        创建上下文快照

        策略：
        - < 50KB: full (完整嵌入)
        - >= 50KB: summary + reference (摘要+引用)
        """
        self.version_counter += 1
        version = f"v1.{self.version_counter}"
        context_id = f"ctx-{hashlib.md5(f'{source_mission}-{target_mission}-{version}'.encode()).hexdigest()[:8]}"

        # 计算内容大小
        content_json = json.dumps(content, ensure_ascii=False)
        content_bytes = len(content_json.encode('utf-8'))

        if content_bytes < threshold_bytes:
            # 策略1: 完整嵌入
            snapshot = ContextSnapshot(
                context_id=context_id,
                version=version,
                source_mission=source_mission,
                target_mission=target_mission,
                snapshot_time=datetime.utcnow(),
                content_type="full",
                content=content,
                hash=hashlib.sha256(content_json.encode()).hexdigest()
            )
        else:
            # 策略2: 摘要+引用
            summary = self._generate_summary(content)
            reference_path = self._save_full_content(context_id, content)

            snapshot = ContextSnapshot(
                context_id=context_id,
                version=version,
                source_mission=source_mission,
                target_mission=target_mission,
                snapshot_time=datetime.utcnow(),
                content_type="summary",
                content={
                    "summary_text": summary,
                    "reference_path": str(reference_path),
                    "hash": hashlib.sha256(content_json.encode()).hexdigest()
                },
                hash=hashlib.sha256(content_json.encode()).hexdigest()
            )

        # 持久化快照元数据
        self._save_snapshot_metadata(snapshot)

        return snapshot

    def _generate_summary(self, content: dict) -> str:
        """生成内容摘要 (前300字 + 后100字)"""
        content_str = json.dumps(content, ensure_ascii=False, indent=2)
        if len(content_str) <= 400:
            return content_str
        return content_str[:300] + "\n...\n" + content_str[-100:]

    def _save_full_content(self, context_id: str, content: dict) -> Path:
        """保存完整内容到文件"""
        path = self.storage_dir / f"{context_id}_full.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        return path

    def _save_snapshot_metadata(self, snapshot: ContextSnapshot):
        """保存快照元数据"""
        metadata_path = self.storage_dir / f"{snapshot.context_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump({
                "context_id": snapshot.context_id,
                "version": snapshot.version,
                "source_mission": snapshot.source_mission,
                "target_mission": snapshot.target_mission,
                "snapshot_time": snapshot.snapshot_time.isoformat(),
                "content_type": snapshot.content_type,
                "hash": snapshot.hash
            }, f, indent=2)

    def verify_integrity(self, snapshot: ContextSnapshot) -> bool:
        """验证快照完整性"""
        if snapshot.content_type == "full":
            current_hash = hashlib.sha256(
                json.dumps(snapshot.content, ensure_ascii=False).encode()
            ).hexdigest()
        else:
            # 从引用路径读取完整内容验证
            reference_path = Path(snapshot.content["reference_path"])
            with open(reference_path) as f:
                full_content = f.read()
            current_hash = hashlib.sha256(full_content.encode()).hexdigest()

        return current_hash == snapshot.hash
```

---

## 2️⃣ 评估强化

### 问题分析

**当前问题**：
- 质量评估仅依赖单一LLM语义评分
- 缺乏客观度量（测试覆盖率、静态检查）
- 判分理由不可追溯，难以重放验证

### 解决方案

#### 2.1 多维度评估框架

```python
# src/core/quality/multi_dim_evaluator.py
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class EvaluationDimension(Enum):
    """评估维度"""
    FORMAT = "format"              # 格式验证
    CONTENT = "content"            # 内容完整性
    QUALITY_LLM = "quality_llm"    # LLM语义质量
    TESTS = "tests"                # 自动化测试
    STATIC_CHECKS = "static"       # 静态检查 (lint, type)
    SECURITY = "security"          # 安全检查
    PERFORMANCE = "performance"    # 性能指标

@dataclass
class DimensionScore:
    """单个维度的评分"""
    dimension: EvaluationDimension
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
        overall_score = sum(
            ds.score * self.dimension_weights.get(ds.dimension, 0.0)
            for ds in dimension_scores
        )

        # 生成重放上下文
        replay_context = {
            "mission_id": mission["id"],
            "mission_version": mission["version"],
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

        return MultiDimEvaluation(
            overall_score=overall_score,
            dimension_scores=dimension_scores,
            passed=overall_score >= threshold,
            threshold=threshold,
            evaluation_time=datetime.utcnow().isoformat(),
            evaluator_version="v1.0",
            replay_context=replay_context
        )

    async def _evaluate_tests(
        self,
        mission: dict,
        work_dir: Path
    ) -> DimensionScore:
        """
        评估维度: 自动化测试

        运行pytest并分析覆盖率
        """
        import subprocess

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
            if coverage_path.exists():
                import json
                with open(coverage_path) as f:
                    coverage_data = json.load(f)
                    coverage_percent = coverage_data["totals"]["percent_covered"]
                    evidence["coverage_percent"] = coverage_percent
            else:
                coverage_percent = 0.0

            # 解析测试结果
            if "passed" in result.stdout:
                # 提取通过/失败数量
                import re
                match = re.search(r'(\d+) passed', result.stdout)
                passed = int(match.group(1)) if match else 0
                match = re.search(r'(\d+) failed', result.stdout)
                failed = int(match.group(1)) if match else 0

                evidence["tests_passed"] = passed
                evidence["tests_failed"] = failed

                if failed > 0:
                    issues.append(f"{failed} tests failed")
                    suggestions.append("Fix failing tests before proceeding")

            # 评分逻辑
            # 基础分: 测试通过率 * 50
            # 覆盖率加分: (coverage / 80) * 50
            test_pass_rate = passed / (passed + failed) if (passed + failed) > 0 else 0
            score = (test_pass_rate * 50) + (min(coverage_percent / 80, 1.0) * 50)

            if coverage_percent < 70:
                issues.append(f"Test coverage is {coverage_percent:.1f}% (target: 70%+)")
                suggestions.append("Increase test coverage")

        except subprocess.TimeoutExpired:
            score = 0.0
            issues.append("Test execution timeout (>5min)")
            suggestions.append("Optimize test execution time")
        except Exception as e:
            score = 0.0
            issues.append(f"Test execution failed: {e}")

        return DimensionScore(
            dimension=EvaluationDimension.TESTS,
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
        """
        评估维度: 静态检查

        运行 flake8 (linting) + mypy (type checking)
        """
        import subprocess

        issues = []
        suggestions = []
        evidence = {}

        # 1. Flake8 linting
        try:
            result = subprocess.run(
                ["flake8", ".", "--count", "--select=E9,F63,F7,F82", "--show-source"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            lint_errors = result.stdout.count('\n')
            evidence["lint_errors"] = lint_errors

            if lint_errors > 0:
                issues.append(f"{lint_errors} linting errors")
                suggestions.append("Run 'flake8 .' to see detailed errors")

        except Exception as e:
            evidence["lint_errors"] = -1  # 未执行

        # 2. Mypy type checking
        try:
            result = subprocess.run(
                ["mypy", ".", "--strict"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=60
            )

            type_errors = result.stdout.count('error:')
            evidence["type_errors"] = type_errors

            if type_errors > 0:
                issues.append(f"{type_errors} type errors")
                suggestions.append("Add type hints and fix type errors")

        except Exception as e:
            evidence["type_errors"] = -1

        # 评分逻辑
        lint_score = max(0, 100 - lint_errors * 5)  # 每个错误扣5分
        type_score = max(0, 100 - type_errors * 2)  # 每个错误扣2分
        score = (lint_score * 0.6 + type_score * 0.4)

        return DimensionScore(
            dimension=EvaluationDimension.STATIC_CHECKS,
            score=score,
            weight=self.dimension_weights[EvaluationDimension.STATIC_CHECKS],
            evidence=evidence,
            issues=issues,
            suggestions=suggestions
        )
```

#### 2.2 评估结果可重放

```python
# src/core/quality/evaluation_replay.py
import json
from pathlib import Path
from datetime import datetime

class EvaluationReplay:
    """评估结果重放器"""

    def __init__(self, replay_dir: Path):
        self.replay_dir = replay_dir
        self.replay_dir.mkdir(parents=True, exist_ok=True)

    def save_evaluation(
        self,
        evaluation: MultiDimEvaluation,
        mission_id: str
    ):
        """
        保存评估结果用于重放

        格式: logs/evaluations/{mission_id}_{timestamp}.json
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
                    "dimension": ds.dimension.value,
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

        return path

    def load_evaluation(self, path: Path) -> dict:
        """加载历史评估结果"""
        with open(path) as f:
            return json.load(f)

    async def replay_evaluation(
        self,
        eval_data: dict,
        evaluator: MultiDimEvaluator
    ) -> MultiDimEvaluation:
        """
        重放评估 (重新执行)

        使用相同的配置和输入重新评估
        """
        replay_ctx = eval_data["replay_context"]

        # 恢复评估器配置
        evaluator.enable_tests = replay_ctx["evaluator_config"]["enable_tests"]
        evaluator.enable_static = replay_ctx["evaluator_config"]["enable_static"]
        evaluator.enable_security = replay_ctx["evaluator_config"]["enable_security"]

        # 重新执行评估
        mission = {
            "id": replay_ctx["mission_id"],
            "version": replay_ctx["mission_version"]
        }

        result = await evaluator.evaluate(
            mission=mission,
            outputs=replay_ctx["outputs"],
            work_dir=Path(replay_ctx["work_dir"])
        )

        return result

    def compare_evaluations(
        self,
        eval1: dict,
        eval2: dict
    ) -> dict:
        """
        对比两次评估结果

        用于验证评估的一致性或分析改进
        """
        comparison = {
            "score_diff": eval2["overall_score"] - eval1["overall_score"],
            "dimension_diffs": [],
            "issues_resolved": [],
            "issues_new": []
        }

        # 对比各维度分数
        dims1 = {d["dimension"]: d for d in eval1["dimension_scores"]}
        dims2 = {d["dimension"]: d for d in eval2["dimension_scores"]}

        for dim_name in dims1:
            if dim_name in dims2:
                diff = dims2[dim_name]["score"] - dims1[dim_name]["score"]
                comparison["dimension_diffs"].append({
                    "dimension": dim_name,
                    "diff": diff,
                    "before": dims1[dim_name]["score"],
                    "after": dims2[dim_name]["score"]
                })

        # 对比issues
        issues1_set = set(sum([d["issues"] for d in eval1["dimension_scores"]], []))
        issues2_set = set(sum([d["issues"] for d in eval2["dimension_scores"]], []))

        comparison["issues_resolved"] = list(issues1_set - issues2_set)
        comparison["issues_new"] = list(issues2_set - issues1_set)

        return comparison
```

---

## 3️⃣ 成本与节流控制

### 问题分析

**当前问题**：
- 仅有全局预算限制，缺乏任务级/角色级预算
- Retry/Enhance/AddHelper没有成本限制
- 缺乏动态预算分配和优先级降级机制

### 解决方案

#### 3.1 分层预算控制

```python
# src/core/budget/hierarchical_budget.py
from dataclasses import dataclass
from typing import Dict, Optional
from enum import Enum

class BudgetLevel(Enum):
    """预算层级"""
    SESSION = "session"      # 会话级
    MISSION = "mission"      # 任务级
    ROLE = "role"           # 角色级
    ACTION = "action"       # 动作级 (Retry/Enhance/Escalate)

@dataclass
class BudgetAllocation:
    """预算分配"""
    level: BudgetLevel
    entity_id: str
    max_cost_usd: float
    max_tokens: int
    max_duration_minutes: int
    priority: int  # 1-10, 用于降级决策

    # 当前使用情况
    used_cost_usd: float = 0.0
    used_tokens: int = 0
    used_duration_minutes: float = 0.0

    # 熔断阈值
    warning_threshold: float = 0.8  # 80%警告
    critical_threshold: float = 0.95  # 95%熔断

class HierarchicalBudgetController:
    """分层预算控制器"""

    def __init__(
        self,
        session_budget_usd: float,
        default_mission_budget_ratio: float = 0.3,
        default_role_budget_ratio: float = 0.15
    ):
        self.session_budget = BudgetAllocation(
            level=BudgetLevel.SESSION,
            entity_id="session",
            max_cost_usd=session_budget_usd,
            max_tokens=1000000,  # 1M tokens
            max_duration_minutes=480,  # 8 hours
            priority=1
        )

        self.default_mission_budget_ratio = default_mission_budget_ratio
        self.default_role_budget_ratio = default_role_budget_ratio

        # 预算分配表
        self.allocations: Dict[str, BudgetAllocation] = {
            "session": self.session_budget
        }

    def allocate_mission_budget(
        self,
        mission_id: str,
        priority: int,
        custom_ratio: Optional[float] = None
    ) -> BudgetAllocation:
        """
        为任务分配预算

        策略:
        - 高优先级任务 (1-3): 30% session预算
        - 中优先级任务 (4-7): 20% session预算
        - 低优先级任务 (8-10): 10% session预算
        """
        if custom_ratio:
            ratio = custom_ratio
        else:
            if priority <= 3:
                ratio = 0.30
            elif priority <= 7:
                ratio = 0.20
            else:
                ratio = 0.10

        mission_budget = BudgetAllocation(
            level=BudgetLevel.MISSION,
            entity_id=mission_id,
            max_cost_usd=self.session_budget.max_cost_usd * ratio,
            max_tokens=int(self.session_budget.max_tokens * ratio),
            max_duration_minutes=int(self.session_budget.max_duration_minutes * ratio),
            priority=priority
        )

        self.allocations[mission_id] = mission_budget
        return mission_budget

    def allocate_role_budget(
        self,
        mission_id: str,
        role_id: str,
        custom_ratio: Optional[float] = None
    ) -> BudgetAllocation:
        """为角色分配预算 (从任务预算中分配)"""
        mission_budget = self.allocations.get(mission_id)
        if not mission_budget:
            raise ValueError(f"Mission {mission_id} budget not found")

        ratio = custom_ratio or self.default_role_budget_ratio

        role_budget = BudgetAllocation(
            level=BudgetLevel.ROLE,
            entity_id=role_id,
            max_cost_usd=mission_budget.max_cost_usd * ratio,
            max_tokens=int(mission_budget.max_tokens * ratio),
            max_duration_minutes=int(mission_budget.max_duration_minutes * ratio),
            priority=mission_budget.priority
        )

        self.allocations[role_id] = role_budget
        return role_budget

    def allocate_action_budget(
        self,
        role_id: str,
        action_type: str,  # "retry", "enhance", "escalate"
        attempt_number: int
    ) -> BudgetAllocation:
        """
        为干预动作分配预算

        策略:
        - Retry: 逐次递减 (50% -> 30% -> 10%)
        - Enhance: 固定20%
        - Escalate: 固定50% (添加辅助角色)
        """
        role_budget = self.allocations.get(role_id)
        if not role_budget:
            raise ValueError(f"Role {role_id} budget not found")

        if action_type == "retry":
            ratios = [0.5, 0.3, 0.1, 0.05]
            ratio = ratios[min(attempt_number - 1, len(ratios) - 1)]
        elif action_type == "enhance":
            ratio = 0.2
        elif action_type == "escalate":
            ratio = 0.5
        else:
            ratio = 0.1

        action_id = f"{role_id}_{action_type}_{attempt_number}"

        action_budget = BudgetAllocation(
            level=BudgetLevel.ACTION,
            entity_id=action_id,
            max_cost_usd=role_budget.max_cost_usd * ratio,
            max_tokens=int(role_budget.max_tokens * ratio),
            max_duration_minutes=int(role_budget.max_duration_minutes * ratio),
            priority=role_budget.priority
        )

        self.allocations[action_id] = action_budget
        return action_budget

    def check_budget(
        self,
        entity_id: str,
        cost_delta: float = 0.0,
        tokens_delta: int = 0
    ) -> tuple[str, float]:
        """
        检查预算状态

        Returns:
            (status, usage_ratio)
            status: "ok", "warning", "critical", "exceeded"
        """
        budget = self.allocations.get(entity_id)
        if not budget:
            return "ok", 0.0

        # 计算使用率
        cost_usage = (budget.used_cost_usd + cost_delta) / budget.max_cost_usd
        token_usage = (budget.used_tokens + tokens_delta) / budget.max_tokens

        max_usage = max(cost_usage, token_usage)

        if max_usage >= 1.0:
            return "exceeded", max_usage
        elif max_usage >= budget.critical_threshold:
            return "critical", max_usage
        elif max_usage >= budget.warning_threshold:
            return "warning", max_usage
        else:
            return "ok", max_usage

    def record_usage(
        self,
        entity_id: str,
        cost_usd: float,
        tokens: int,
        duration_minutes: float
    ):
        """记录资源使用"""
        budget = self.allocations.get(entity_id)
        if not budget:
            return

        budget.used_cost_usd += cost_usd
        budget.used_tokens += tokens
        budget.used_duration_minutes += duration_minutes

        # 同时更新父级预算
        if budget.level == BudgetLevel.ACTION:
            # Action -> Role -> Mission -> Session
            role_id = "_".join(entity_id.split("_")[:-2])
            self.record_usage(role_id, cost_usd, tokens, duration_minutes)

        elif budget.level == BudgetLevel.ROLE:
            # Role -> Mission -> Session
            mission_id = budget.entity_id.split("_role_")[0]  # 假设role_id格式: mission-xxx_role_yyy
            self.record_usage(mission_id, cost_usd, tokens, duration_minutes)

        elif budget.level == BudgetLevel.MISSION:
            # Mission -> Session
            self.record_usage("session", cost_usd, tokens, duration_minutes)

    def get_priority_sorted_missions(self) -> List[str]:
        """
        获取按优先级排序的任务列表

        用于预算紧张时的降级决策
        """
        mission_budgets = [
            (entity_id, budget)
            for entity_id, budget in self.allocations.items()
            if budget.level == BudgetLevel.MISSION
        ]

        # 按优先级排序 (低优先级在前，用于降级)
        sorted_missions = sorted(
            mission_budgets,
            key=lambda x: x[1].priority,
            reverse=True
        )

        return [entity_id for entity_id, _ in sorted_missions]
```

#### 3.2 动态预算调整和熔断

```python
# src/core/budget/circuit_breaker.py
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"       # 正常运行
    OPEN = "open"           # 熔断开启
    HALF_OPEN = "half_open" # 半开 (尝试恢复)

@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 3  # 失败阈值
    success_threshold: int = 2  # 恢复阈值
    timeout_seconds: int = 300  # 熔断超时 (5分钟后尝试恢复)

class BudgetCircuitBreaker:
    """预算熔断器"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None

    def on_budget_exceeded(self, entity_id: str, usage_ratio: float):
        """预算超限事件"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.critical(
                f"Circuit breaker OPEN for {entity_id} "
                f"(failures: {self.failure_count}, usage: {usage_ratio:.1%})"
            )

    def on_budget_ok(self):
        """预算正常事件"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker CLOSED (recovered)")

    def should_allow_execution(self) -> bool:
        """是否允许执行"""
        if self.state == CircuitState.CLOSED:
            return True

        elif self.state == CircuitState.OPEN:
            # 检查是否可以尝试恢复
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= self.config.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker HALF_OPEN (attempting recovery)")
                    return True
            return False

        elif self.state == CircuitState.HALF_OPEN:
            # 半开状态允许少量请求通过
            return True

        return False
```

---

## 4️⃣ 幂等与恢复机制

### 问题分析

**当前问题**：
- 执行器不支持幂等性，重复执行会产生重复文件
- 没有执行状态持久化，无法断点续跑
- 系统崩溃后需要从头开始

### 解决方案

#### 4.1 幂等执行器设计

```python
# src/core/execution/idempotent_executor.py
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ExecutionCheckpoint:
    """执行检查点"""
    mission_id: str
    role_id: str
    iteration: int
    state: str  # "pending", "running", "completed", "failed"
    outputs: List[str]
    context_snapshot_id: str
    timestamp: datetime
    hash: str  # 用于验证幂等性

class IdempotentExecutor:
    """幂等执行器"""

    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def compute_execution_hash(
        self,
        mission: dict,
        context: dict
    ) -> str:
        """
        计算执行哈希

        基于任务定义和输入上下文，确保相同输入产生相同输出
        """
        hash_input = json.dumps({
            "mission_id": mission["id"],
            "mission_version": mission["version"],
            "mission_goal": mission["goal"],
            "context_hash": hashlib.sha256(
                json.dumps(context, sort_keys=True).encode()
            ).hexdigest()
        }, sort_keys=True)

        return hashlib.sha256(hash_input.encode()).hexdigest()

    def load_checkpoint(
        self,
        mission_id: str,
        role_id: str
    ) -> Optional[ExecutionCheckpoint]:
        """加载检查点"""
        checkpoint_path = self.checkpoint_dir / f"{mission_id}_{role_id}.json"

        if not checkpoint_path.exists():
            return None

        with open(checkpoint_path) as f:
            data = json.load(f)

        return ExecutionCheckpoint(
            mission_id=data["mission_id"],
            role_id=data["role_id"],
            iteration=data["iteration"],
            state=data["state"],
            outputs=data["outputs"],
            context_snapshot_id=data["context_snapshot_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            hash=data["hash"]
        )

    def save_checkpoint(self, checkpoint: ExecutionCheckpoint):
        """保存检查点"""
        checkpoint_path = self.checkpoint_dir / f"{checkpoint.mission_id}_{checkpoint.role_id}.json"

        with open(checkpoint_path, 'w') as f:
            json.dump({
                "mission_id": checkpoint.mission_id,
                "role_id": checkpoint.role_id,
                "iteration": checkpoint.iteration,
                "state": checkpoint.state,
                "outputs": checkpoint.outputs,
                "context_snapshot_id": checkpoint.context_snapshot_id,
                "timestamp": checkpoint.timestamp.isoformat(),
                "hash": checkpoint.hash
            }, f, indent=2)

    async def execute_idempotent(
        self,
        mission: dict,
        role: dict,
        context: dict,
        executor_func: Callable
    ) -> dict:
        """
        幂等执行

        流程:
        1. 计算执行哈希
        2. 检查是否已有相同哈希的完成检查点
        3. 如果有，直接返回缓存结果
        4. 如果没有，执行并保存检查点
        """
        mission_id = mission["id"]
        role_id = role["name"]
        execution_hash = self.compute_execution_hash(mission, context)

        # 加载检查点
        checkpoint = self.load_checkpoint(mission_id, role_id)

        # 检查幂等性
        if checkpoint and checkpoint.hash == execution_hash:
            if checkpoint.state == "completed":
                logger.info(
                    f"Idempotent cache hit for {role_id} "
                    f"(hash: {execution_hash[:8]})"
                )
                return {
                    "success": True,
                    "outputs": checkpoint.outputs,
                    "from_cache": True
                }
            elif checkpoint.state == "running":
                logger.warning(
                    f"Detected interrupted execution for {role_id}, resuming..."
                )
                # 可以尝试从中断点恢复

        # 创建新检查点 (running状态)
        checkpoint = ExecutionCheckpoint(
            mission_id=mission_id,
            role_id=role_id,
            iteration=0,
            state="running",
            outputs=[],
            context_snapshot_id=context.get("context_id", ""),
            timestamp=datetime.utcnow(),
            hash=execution_hash
        )
        self.save_checkpoint(checkpoint)

        try:
            # 执行
            result = await executor_func(mission, role, context)

            # 更新检查点 (completed状态)
            checkpoint.state = "completed"
            checkpoint.outputs = result.get("outputs", [])
            checkpoint.timestamp = datetime.utcnow()
            self.save_checkpoint(checkpoint)

            return result

        except Exception as e:
            # 更新检查点 (failed状态)
            checkpoint.state = "failed"
            checkpoint.timestamp = datetime.utcnow()
            self.save_checkpoint(checkpoint)

            raise e
```

#### 4.2 执行状态持久化

```python
# src/core/execution/execution_state.py
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import json
from pathlib import Path

@dataclass
class MissionState:
    """任务状态"""
    mission_id: str
    status: str  # "pending", "running", "completed", "failed", "paused"
    assigned_role: str
    progress: float  # 0.0 - 1.0
    current_iteration: int
    max_iterations: int
    outputs: List[str]
    last_checkpoint: str  # ISO timestamp

@dataclass
class TeamExecutionState:
    """团队执行状态"""
    session_id: str
    execution_order: List[str]  # 任务执行顺序
    completed_missions: List[str]
    current_mission_index: int
    mission_states: Dict[str, MissionState]
    total_cost_usd: float
    start_time: str
    last_update_time: str

class ExecutionStateManager:
    """执行状态管理器"""

    def __init__(self, state_file: Path):
        self.state_file = state_file

    def save_state(self, state: TeamExecutionState):
        """保存执行状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # 转换为可序列化格式
        state_dict = {
            "session_id": state.session_id,
            "execution_order": state.execution_order,
            "completed_missions": state.completed_missions,
            "current_mission_index": state.current_mission_index,
            "mission_states": {
                mid: asdict(ms) for mid, ms in state.mission_states.items()
            },
            "total_cost_usd": state.total_cost_usd,
            "start_time": state.start_time,
            "last_update_time": datetime.utcnow().isoformat()
        }

        # 原子写入 (使用临时文件)
        temp_file = self.state_file.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            json.dump(state_dict, f, indent=2)

        temp_file.replace(self.state_file)

    def load_state(self) -> Optional[TeamExecutionState]:
        """加载执行状态"""
        if not self.state_file.exists():
            return None

        with open(self.state_file) as f:
            state_dict = json.load(f)

        return TeamExecutionState(
            session_id=state_dict["session_id"],
            execution_order=state_dict["execution_order"],
            completed_missions=state_dict["completed_missions"],
            current_mission_index=state_dict["current_mission_index"],
            mission_states={
                mid: MissionState(**ms)
                for mid, ms in state_dict["mission_states"].items()
            },
            total_cost_usd=state_dict["total_cost_usd"],
            start_time=state_dict["start_time"],
            last_update_time=state_dict["last_update_time"]
        )

    def resume_execution(self) -> Optional[TeamExecutionState]:
        """
        恢复执行

        Returns:
            如果存在可恢复的状态，返回状态对象；否则返回None
        """
        state = self.load_state()

        if not state:
            return None

        # 检查是否可以恢复
        if state.current_mission_index >= len(state.execution_order):
            logger.info("All missions completed, nothing to resume")
            return None

        logger.info(
            f"Resuming execution from mission {state.current_mission_index + 1}/"
            f"{len(state.execution_order)}"
        )

        return state
```

---

## 5️⃣ 资源隔离与权限控制

### 问题分析

**当前问题**：
- 工具权限缺乏限制，所有角色可访问所有工具
- MCP服务器连接无速率限制，可能被滥用
- 缺乏沙箱隔离机制

### 解决方案

#### 5.1 最小权限工具访问

```python
# src/core/tools/permission_manager.py
from dataclasses import dataclass
from typing import List, Set
from enum import Enum

class ToolPermission(Enum):
    """工具权限"""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXECUTE_COMMAND = "execute_command"
    WEB_SEARCH = "web_search"
    WEB_FETCH = "web_fetch"
    MCP_CALL = "mcp_call"

@dataclass
class ToolAccessPolicy:
    """工具访问策略"""
    role_id: str
    allowed_tools: Set[str]
    allowed_permissions: Set[ToolPermission]
    denied_patterns: List[str]  # 文件路径拒绝模式 (如 "/etc/*", "~/.ssh/*")
    rate_limits: Dict[str, int]  # 工具速率限制 (calls/minute)

class PermissionManager:
    """权限管理器"""

    def __init__(self):
        self.policies: Dict[str, ToolAccessPolicy] = {}

        # 默认策略 (最小权限)
        self.default_policy = ToolAccessPolicy(
            role_id="default",
            allowed_tools={"read_file", "write_file"},
            allowed_permissions={
                ToolPermission.READ_FILE,
                ToolPermission.WRITE_FILE
            },
            denied_patterns=[
                "/etc/*",
                "~/.ssh/*",
                "~/.aws/*",
                "/root/*",
                "*.key",
                "*.pem"
            ],
            rate_limits={
                "web_search": 10,  # 10/min
                "mcp_call": 20     # 20/min
            }
        )

    def create_policy_from_role(self, role: dict) -> ToolAccessPolicy:
        """
        从角色定义创建访问策略

        基于角色的 resources.tools 字段
        """
        role_id = role["name"]
        allowed_tools = set(role.get("resources", {}).get("tools", []))

        # 映射工具到权限
        permissions = set()
        for tool in allowed_tools:
            if tool in ["read_file", "glob", "grep"]:
                permissions.add(ToolPermission.READ_FILE)
            elif tool in ["write_file", "edit_file"]:
                permissions.add(ToolPermission.WRITE_FILE)
            elif tool in ["run_command", "bash"]:
                permissions.add(ToolPermission.EXECUTE_COMMAND)
            elif tool == "web_search":
                permissions.add(ToolPermission.WEB_SEARCH)
            elif tool == "web_fetch":
                permissions.add(ToolPermission.WEB_FETCH)

        # 角色特定的拒绝模式
        denied_patterns = self.default_policy.denied_patterns.copy()

        # 开发者角色可能需要更多权限，但仍然拒绝敏感路径
        if "developer" in role_id.lower():
            # 允许更多路径，但保留核心安全限制
            denied_patterns = [p for p in denied_patterns if "/etc" in p or ".ssh" in p]

        policy = ToolAccessPolicy(
            role_id=role_id,
            allowed_tools=allowed_tools,
            allowed_permissions=permissions,
            denied_patterns=denied_patterns,
            rate_limits=self.default_policy.rate_limits.copy()
        )

        self.policies[role_id] = policy
        return policy

    def check_permission(
        self,
        role_id: str,
        tool_name: str,
        permission: ToolPermission,
        file_path: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        检查权限

        Returns:
            (allowed, reason)
        """
        policy = self.policies.get(role_id, self.default_policy)

        # 检查工具是否在允许列表
        if tool_name not in policy.allowed_tools:
            return False, f"Tool '{tool_name}' not allowed for role '{role_id}'"

        # 检查权限
        if permission not in policy.allowed_permissions:
            return False, f"Permission '{permission.value}' denied for role '{role_id}'"

        # 检查文件路径 (如果提供)
        if file_path:
            import fnmatch
            for pattern in policy.denied_patterns:
                if fnmatch.fnmatch(file_path, pattern):
                    return False, f"Access to path '{file_path}' denied (pattern: '{pattern}')"

        return True, ""
```

#### 5.2 MCP速率限制

```python
# src/core/tools/rate_limiter.py
from collections import defaultdict
from datetime import datetime, timedelta
from threading import Lock

class RateLimiter:
    """速率限制器"""

    def __init__(self):
        self.call_history: Dict[str, List[datetime]] = defaultdict(list)
        self.lock = Lock()

    def check_rate_limit(
        self,
        role_id: str,
        tool_name: str,
        limit_per_minute: int
    ) -> tuple[bool, int]:
        """
        检查速率限制

        Returns:
            (allowed, remaining_calls)
        """
        with self.lock:
            key = f"{role_id}:{tool_name}"
            now = datetime.utcnow()

            # 清理1分钟前的记录
            self.call_history[key] = [
                ts for ts in self.call_history[key]
                if now - ts < timedelta(minutes=1)
            ]

            # 检查是否超过限制
            current_calls = len(self.call_history[key])

            if current_calls >= limit_per_minute:
                return False, 0

            # 记录本次调用
            self.call_history[key].append(now)

            remaining = limit_per_minute - current_calls - 1
            return True, remaining
```

---

## 6️⃣ 观测与追踪

### 问题分析

**当前问题**：
- 缺乏统一的trace_id追踪
- 日志格式不统一，难以分析
- 无法关联任务、角色、干预决策的完整链路

### 解决方案

#### 6.1 结构化追踪系统

```python
# src/core/observability/structured_tracer.py
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
import json
from pathlib import Path

@dataclass
class TraceSpan:
    """追踪span"""
    trace_id: str          # 全局追踪ID
    span_id: str           # 当前span ID
    parent_span_id: Optional[str]  # 父span ID
    mission_id: Optional[str]
    role_id: Optional[str]
    operation: str         # 操作类型
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: Optional[float]
    status: str            # "running", "completed", "failed"
    metadata: Dict[str, Any]
    cost_usd: float
    tokens_used: int
    tags: Dict[str, str]

class StructuredTracer:
    """结构化追踪器"""

    def __init__(self, trace_dir: Path):
        self.trace_dir = trace_dir
        self.trace_dir.mkdir(parents=True, exist_ok=True)

        # 当前trace上下文
        self.current_trace_id: Optional[str] = None
        self.span_stack: List[TraceSpan] = []

    def start_trace(self, session_id: str) -> str:
        """开始新的追踪"""
        self.current_trace_id = f"trace-{uuid.uuid4().hex[:16]}"

        logger.info(
            f"Started trace: {self.current_trace_id} (session: {session_id})"
        )

        return self.current_trace_id

    def start_span(
        self,
        operation: str,
        mission_id: Optional[str] = None,
        role_id: Optional[str] = None,
        **metadata
    ) -> str:
        """开始新的span"""
        span_id = f"span-{uuid.uuid4().hex[:12]}"
        parent_span_id = self.span_stack[-1].span_id if self.span_stack else None

        span = TraceSpan(
            trace_id=self.current_trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            mission_id=mission_id,
            role_id=role_id,
            operation=operation,
            start_time=datetime.utcnow(),
            end_time=None,
            duration_ms=None,
            status="running",
            metadata=metadata,
            cost_usd=0.0,
            tokens_used=0,
            tags={}
        )

        self.span_stack.append(span)

        # 实时写入 (streaming trace)
        self._write_span_event(span, "start")

        return span_id

    def end_span(
        self,
        status: str = "completed",
        cost_usd: float = 0.0,
        tokens_used: int = 0,
        **metadata
    ):
        """结束当前span"""
        if not self.span_stack:
            return

        span = self.span_stack.pop()
        span.end_time = datetime.utcnow()
        span.duration_ms = (span.end_time - span.start_time).total_seconds() * 1000
        span.status = status
        span.cost_usd = cost_usd
        span.tokens_used = tokens_used
        span.metadata.update(metadata)

        # 写入完成事件
        self._write_span_event(span, "end")

    def add_span_tag(self, key: str, value: str):
        """添加span标签"""
        if self.span_stack:
            self.span_stack[-1].tags[key] = value

    def _write_span_event(self, span: TraceSpan, event_type: str):
        """写入span事件 (JSONL格式)"""
        trace_file = self.trace_dir / f"{self.current_trace_id}.jsonl"

        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **asdict(span)
        }

        # 序列化datetime
        event["start_time"] = span.start_time.isoformat()
        if span.end_time:
            event["end_time"] = span.end_time.isoformat()

        # 追加到JSONL
        with open(trace_file, 'a') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')

    def query_spans(
        self,
        trace_id: str,
        mission_id: Optional[str] = None,
        role_id: Optional[str] = None,
        operation: Optional[str] = None
    ) -> List[TraceSpan]:
        """查询spans"""
        trace_file = self.trace_dir / f"{trace_id}.jsonl"

        if not trace_file.exists():
            return []

        spans = []
        with open(trace_file) as f:
            for line in f:
                event = json.loads(line)
                if event["event_type"] == "end":  # 只取完成的span
                    # 过滤条件
                    if mission_id and event["mission_id"] != mission_id:
                        continue
                    if role_id and event["role_id"] != role_id:
                        continue
                    if operation and event["operation"] != operation:
                        continue

                    spans.append(event)

        return spans
```

#### 6.2 结构化日志

```python
# src/core/observability/structured_logger.py
import logging
import json
from datetime import datetime
from typing import Optional

class StructuredLogger:
    """结构化日志器"""

    def __init__(self, log_file: Path):
        self.log_file = log_file

        # 配置JSON日志handler
        self.logger = logging.getLogger("structured")
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    def log(
        self,
        level: str,
        message: str,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        mission_id: Optional[str] = None,
        role_id: Optional[str] = None,
        **extra
    ):
        """记录结构化日志"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level.upper(),
            "message": message,
            "trace_id": trace_id,
            "span_id": span_id,
            "mission_id": mission_id,
            "role_id": role_id,
            **extra
        }

        self.logger.info(json.dumps(log_entry, ensure_ascii=False))

    def log_intervention(
        self,
        trace_id: str,
        mission_id: str,
        role_id: str,
        action: str,
        reason: str,
        score: float,
        cost_usd: float,
        **extra
    ):
        """记录干预决策"""
        self.log(
            level="INFO",
            message=f"Leader intervention: {action}",
            trace_id=trace_id,
            mission_id=mission_id,
            role_id=role_id,
            event_type="intervention",
            action=action,
            reason=reason,
            quality_score=score,
            cost_usd=cost_usd,
            **extra
        )
```

---

## 7️⃣ 终态策略与恢复指南

### 问题分析

**当前问题**：
- 预算超限/任务失败时直接终止，缺乏部分交付
- 没有残余风险报告和恢复指南
- 缺乏一致性检查机制

### 解决方案

#### 7.1 部分交付处理

```python
# src/core/termination/partial_delivery.py
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path
import json

@dataclass
class PartialDeliverable:
    """部分交付物"""
    completed_missions: List[str]
    incomplete_missions: List[str]
    deliverables: Dict[str, List[str]]  # mission_id -> file paths
    quality_scores: Dict[str, float]
    total_cost_usd: float
    completion_ratio: float  # 0.0 - 1.0

@dataclass
class ResidualRisk:
    """残余风险"""
    risk_type: str  # "incomplete", "low_quality", "untested"
    severity: str   # "low", "medium", "high", "critical"
    affected_missions: List[str]
    description: str
    mitigation: str

@dataclass
class RecoveryGuide:
    """恢复指南"""
    termination_reason: str
    checkpoint_path: str
    resume_from_mission: str
    required_actions: List[str]
    estimated_cost_to_complete: float
    estimated_time_minutes: int

class PartialDeliveryHandler:
    """部分交付处理器"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_partial_delivery(
        self,
        execution_state: TeamExecutionState,
        termination_reason: str
    ) -> PartialDeliverable:
        """生成部分交付物"""
        completed = execution_state.completed_missions
        incomplete = [
            mid for mid in execution_state.execution_order
            if mid not in completed
        ]

        deliverables = {}
        quality_scores = {}

        for mission_id in completed:
            mission_state = execution_state.mission_states.get(mission_id)
            if mission_state:
                deliverables[mission_id] = mission_state.outputs
                quality_scores[mission_id] = self._get_quality_score(mission_id)

        completion_ratio = len(completed) / len(execution_state.execution_order)

        partial = PartialDeliverable(
            completed_missions=completed,
            incomplete_missions=incomplete,
            deliverables=deliverables,
            quality_scores=quality_scores,
            total_cost_usd=execution_state.total_cost_usd,
            completion_ratio=completion_ratio
        )

        # 保存部分交付说明
        self._save_partial_delivery_doc(partial, termination_reason)

        return partial

    def analyze_residual_risks(
        self,
        partial: PartialDeliverable
    ) -> List[ResidualRisk]:
        """分析残余风险"""
        risks = []

        # 风险1: 未完成的任务
        if partial.incomplete_missions:
            risks.append(ResidualRisk(
                risk_type="incomplete",
                severity="high" if partial.completion_ratio < 0.5 else "medium",
                affected_missions=partial.incomplete_missions,
                description=f"{len(partial.incomplete_missions)} missions not completed",
                mitigation="Resume execution from checkpoint or manually complete tasks"
            ))

        # 风险2: 低质量交付
        low_quality_missions = [
            mid for mid, score in partial.quality_scores.items()
            if score < 70.0
        ]
        if low_quality_missions:
            risks.append(ResidualRisk(
                risk_type="low_quality",
                severity="medium",
                affected_missions=low_quality_missions,
                description=f"{len(low_quality_missions)} missions have quality < 70%",
                mitigation="Review and improve deliverables manually"
            ))

        # 风险3: 未经测试 (检查是否有测试文件)
        untested_missions = [
            mid for mid in partial.completed_missions
            if not self._has_tests(partial.deliverables.get(mid, []))
        ]
        if untested_missions:
            risks.append(ResidualRisk(
                risk_type="untested",
                severity="high",
                affected_missions=untested_missions,
                description=f"{len(untested_missions)} missions lack test coverage",
                mitigation="Add tests before deployment"
            ))

        return risks

    def generate_recovery_guide(
        self,
        execution_state: TeamExecutionState,
        termination_reason: str,
        partial: PartialDeliverable
    ) -> RecoveryGuide:
        """生成恢复指南"""
        resume_mission = (
            partial.incomplete_missions[0]
            if partial.incomplete_missions
            else None
        )

        required_actions = []

        if "budget" in termination_reason.lower():
            required_actions.append("Increase budget allocation")
            required_actions.append(f"Current cost: ${partial.total_cost_usd:.2f}")

        if "quality" in termination_reason.lower():
            required_actions.append("Review quality thresholds")
            required_actions.append("Consider enhancing task definitions")

        required_actions.append(f"Resume from mission: {resume_mission}")

        # 估算完成成本
        avg_cost_per_mission = partial.total_cost_usd / max(len(partial.completed_missions), 1)
        estimated_cost = avg_cost_per_mission * len(partial.incomplete_missions)

        guide = RecoveryGuide(
            termination_reason=termination_reason,
            checkpoint_path=str(execution_state.state_file),
            resume_from_mission=resume_mission,
            required_actions=required_actions,
            estimated_cost_to_complete=estimated_cost,
            estimated_time_minutes=len(partial.incomplete_missions) * 30  # 估算
        )

        self._save_recovery_guide(guide)

        return guide

    def _save_partial_delivery_doc(
        self,
        partial: PartialDeliverable,
        reason: str
    ):
        """保存部分交付说明文档"""
        doc_path = self.output_dir / "PARTIAL_DELIVERY.md"

        content = f"""# Partial Delivery Report

## Termination Reason
{reason}

## Completion Status
- **Completion Ratio**: {partial.completion_ratio:.1%}
- **Completed Missions**: {len(partial.completed_missions)}
- **Incomplete Missions**: {len(partial.incomplete_missions)}
- **Total Cost**: ${partial.total_cost_usd:.2f}

## Completed Missions

"""

        for mission_id in partial.completed_missions:
            quality = partial.quality_scores.get(mission_id, 0.0)
            files = partial.deliverables.get(mission_id, [])

            content += f"""### {mission_id}
- **Quality Score**: {quality:.1f}/100
- **Deliverables** ({len(files)} files):
"""
            for file_path in files:
                content += f"  - `{file_path}`\n"
            content += "\n"

        content += f"""## Incomplete Missions

"""
        for mission_id in partial.incomplete_missions:
            content += f"- {mission_id}\n"

        with open(doc_path, 'w') as f:
            f.write(content)

    def _save_recovery_guide(self, guide: RecoveryGuide):
        """保存恢复指南"""
        guide_path = self.output_dir / "RECOVERY_GUIDE.md"

        content = f"""# Recovery Guide

## Termination Reason
{guide.termination_reason}

## Checkpoint Information
- **Checkpoint Path**: `{guide.checkpoint_path}`
- **Resume From Mission**: `{guide.resume_from_mission}`

## Required Actions

"""
        for action in guide.required_actions:
            content += f"- [ ] {action}\n"

        content += f"""
## Estimated Resources to Complete
- **Cost**: ${guide.estimated_cost_to_complete:.2f}
- **Time**: ~{guide.estimated_time_minutes} minutes

## How to Resume

1. Review the required actions above
2. Update configuration if needed (budget, thresholds, etc.)
3. Run the following command:

```bash
python -m src.main --resume {guide.checkpoint_path}
```

## Support
For assistance, contact the team or check logs in `logs/` directory.
"""

        with open(guide_path, 'w') as f:
            f.write(content)
```

---

## 8️⃣ 辅助角色治理

### 问题分析

**当前问题**：
- AddHelper可能无限添加辅助角色，导致成本失控
- 缺乏退场条件，辅助角色可能长期占用资源
- 重试策略缺乏退避机制

### 解决方案

#### 8.1 辅助角色管理

```python
# src/core/intervention/helper_governance.py
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class HelperExitCondition(Enum):
    """辅助角色退场条件"""
    TASK_COMPLETED = "task_completed"
    QUALITY_THRESHOLD_MET = "quality_met"
    MAX_ITERATIONS = "max_iterations"
    BUDGET_EXHAUSTED = "budget_exhausted"
    REDUNDANT = "redundant"  # 与主角色重复

@dataclass
class HelperRole:
    """辅助角色"""
    helper_id: str
    role_name: str
    parent_mission_id: str
    assigned_task: str
    max_iterations: int
    current_iteration: int
    budget_allocation: BudgetAllocation
    exit_conditions: List[HelperExitCondition]
    quality_threshold: float

class HelperGovernor:
    """辅助角色治理器"""

    def __init__(
        self,
        max_helpers_per_mission: int = 2,
        max_total_helpers: int = 5
    ):
        self.max_helpers_per_mission = max_helpers_per_mission
        self.max_total_helpers = max_total_helpers

        self.active_helpers: Dict[str, HelperRole] = {}
        self.helpers_by_mission: Dict[str, List[str]] = defaultdict(list)

    def can_add_helper(
        self,
        mission_id: str
    ) -> tuple[bool, str]:
        """
        检查是否可以添加辅助角色

        Returns:
            (allowed, reason)
        """
        # 检查总数限制
        if len(self.active_helpers) >= self.max_total_helpers:
            return False, f"Max total helpers reached ({self.max_total_helpers})"

        # 检查任务级限制
        mission_helpers = self.helpers_by_mission.get(mission_id, [])
        if len(mission_helpers) >= self.max_helpers_per_mission:
            return False, f"Max helpers per mission reached ({self.max_helpers_per_mission})"

        return True, ""

    def add_helper(
        self,
        mission_id: str,
        role_name: str,
        task: str,
        budget: BudgetAllocation
    ) -> HelperRole:
        """添加辅助角色"""
        helper_id = f"helper-{uuid.uuid4().hex[:8]}"

        helper = HelperRole(
            helper_id=helper_id,
            role_name=role_name,
            parent_mission_id=mission_id,
            assigned_task=task,
            max_iterations=3,  # 辅助角色限制更严格
            current_iteration=0,
            budget_allocation=budget,
            exit_conditions=[
                HelperExitCondition.QUALITY_THRESHOLD_MET,
                HelperExitCondition.MAX_ITERATIONS,
                HelperExitCondition.BUDGET_EXHAUSTED
            ],
            quality_threshold=80.0  # 辅助角色要求更高质量
        )

        self.active_helpers[helper_id] = helper
        self.helpers_by_mission[mission_id].append(helper_id)

        logger.info(
            f"Added helper {helper_id} ({role_name}) for mission {mission_id}"
        )

        return helper

    def should_exit_helper(
        self,
        helper_id: str,
        quality_score: float,
        is_redundant: bool = False
    ) -> tuple[bool, HelperExitCondition]:
        """
        检查辅助角色是否应该退场

        Returns:
            (should_exit, exit_condition)
        """
        helper = self.active_helpers.get(helper_id)
        if not helper:
            return False, None

        # 检查质量阈值
        if (HelperExitCondition.QUALITY_THRESHOLD_MET in helper.exit_conditions and
            quality_score >= helper.quality_threshold):
            return True, HelperExitCondition.QUALITY_THRESHOLD_MET

        # 检查迭代次数
        if (HelperExitCondition.MAX_ITERATIONS in helper.exit_conditions and
            helper.current_iteration >= helper.max_iterations):
            return True, HelperExitCondition.MAX_ITERATIONS

        # 检查预算
        budget_status, _ = budget_controller.check_budget(helper_id)
        if (HelperExitCondition.BUDGET_EXHAUSTED in helper.exit_conditions and
            budget_status in ["critical", "exceeded"]):
            return True, HelperExitCondition.BUDGET_EXHAUSTED

        # 检查冗余
        if (HelperExitCondition.REDUNDANT in helper.exit_conditions and
            is_redundant):
            return True, HelperExitCondition.REDUNDANT

        return False, None

    def remove_helper(
        self,
        helper_id: str,
        exit_condition: HelperExitCondition
    ):
        """移除辅助角色"""
        helper = self.active_helpers.get(helper_id)
        if not helper:
            return

        mission_id = helper.parent_mission_id

        del self.active_helpers[helper_id]
        self.helpers_by_mission[mission_id].remove(helper_id)

        logger.info(
            f"Removed helper {helper_id} from mission {mission_id} "
            f"(reason: {exit_condition.value})"
        )
```

#### 8.2 退避策略

```python
# src/core/intervention/backoff_strategy.py
import time
from enum import Enum
from typing import Callable

class BackoffStrategy(Enum):
    """退避策略"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIBONACCI = "fibonacci"

class RetryBackoff:
    """重试退避器"""

    def __init__(
        self,
        strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
        base_delay_seconds: float = 2.0,
        max_delay_seconds: float = 60.0
    ):
        self.strategy = strategy
        self.base_delay = base_delay_seconds
        self.max_delay = max_delay_seconds

    def get_delay(self, attempt: int) -> float:
        """
        获取延迟时间 (秒)

        Args:
            attempt: 重试次数 (1-based)
        """
        if self.strategy == BackoffStrategy.LINEAR:
            delay = self.base_delay * attempt

        elif self.strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.base_delay * (2 ** (attempt - 1))

        elif self.strategy == BackoffStrategy.FIBONACCI:
            delay = self.base_delay * self._fibonacci(attempt)

        else:
            delay = self.base_delay

        return min(delay, self.max_delay)

    def _fibonacci(self, n: int) -> int:
        """计算斐波那契数"""
        if n <= 1:
            return 1
        a, b = 1, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return a

    async def retry_with_backoff(
        self,
        func: Callable,
        max_retries: int,
        *args,
        **kwargs
    ):
        """
        带退避的重试

        Example:
            result = await backoff.retry_with_backoff(
                execute_role,
                max_retries=3,
                mission=mission,
                role=role
            )
        """
        for attempt in range(1, max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                return result

            except Exception as e:
                if attempt == max_retries:
                    raise e

                delay = self.get_delay(attempt)
                logger.warning(
                    f"Retry attempt {attempt}/{max_retries} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )

                time.sleep(delay)
```

---

## 📊 实施优先级与路线图

### Phase 1 (P0 - 立即实施)

**目标**: 关键健壮性增强

1. **结构化协议** (1周)
   - SubMission Schema定义
   - ExecutionContext Schema
   - SchemaValidator实现

2. **多维度评估** (1周)
   - MultiDimEvaluator框架
   - 测试维度集成
   - 静态检查维度

3. **分层预算控制** (1周)
   - HierarchicalBudgetController
   - CircuitBreaker实现
   - 动态预算分配

4. **结构化追踪** (1周)
   - StructuredTracer实现
   - TraceSpan设计
   - JSONL追踪日志

### Phase 2 (P1 - 近期实施)

**目标**: 可恢复性和资源治理

1. **幂等与恢复** (1.5周)
   - IdempotentExecutor
   - ExecutionStateManager
   - 断点续跑功能

2. **资源隔离** (1周)
   - PermissionManager
   - 最小权限工具访问
   - MCP速率限制

3. **辅助角色治理** (1周)
   - HelperGovernor
   - 退场条件实现
   - RetryBackoff策略

### Phase 3 (P2 - 后续优化)

**目标**: 用户体验和可观测性

1. **终态策略** (1周)
   - PartialDeliveryHandler
   - ResidualRisk分析
   - RecoveryGuide生成

2. **可观测性增强** (1周)
   - 追踪查询API
   - 可视化Dashboard
   - 告警系统

3. **文档和测试** (1周)
   - API文档
   - 集成测试
   - 性能测试

---

## ✅ 验收标准

### 结构化协议
- [ ] 所有SubMission通过Schema验证
- [ ] Context传递哈希验证通过率 100%
- [ ] 版本化机制可追溯所有变更

### 评估强化
- [ ] 多维度评估覆盖所有角色
- [ ] 测试维度覆盖率 ≥ 80%
- [ ] 评估结果可重放，误差 < 5%

### 成本与节流
- [ ] 预算控制准确率 100%
- [ ] 熔断器响应时间 < 1秒
- [ ] 优先级降级策略有效

### 幂等与恢复
- [ ] 幂等性测试通过率 100%
- [ ] 断点续跑成功率 ≥ 95%
- [ ] 状态持久化零数据丢失

### 资源隔离
- [ ] 权限违规检测率 100%
- [ ] MCP速率限制准确
- [ ] 敏感路径访问拦截率 100%

### 观测与追踪
- [ ] 所有操作有trace_id
- [ ] 追踪链路完整性 100%
- [ ] 日志查询响应时间 < 500ms

### 终态策略
- [ ] 部分交付生成成功率 100%
- [ ] 恢复指南准确性 ≥ 90%
- [ ] 一致性检查覆盖所有场景

### 辅助角色治理
- [ ] 辅助角色数量限制有效
- [ ] 退场条件触发准确
- [ ] 退避策略符合预期

---

## 📚 相关文档

- **架构重构方案**: `docs/Architecture-Refactor-v4.0.md`
- **工作流程图**: `AI-Native-Team-Workflow.md`
- **版本历史**: `CHANGELOG.md`

---

**文档版本**: v4.1-enhancements
**创建日期**: 2025-01-22
**状态**: 设计完成，待实施
