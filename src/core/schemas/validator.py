"""
Schema Validator - JSON Schema验证器

用于验证SubMission、ExecutionContext等结构化数据的合法性
"""
from typing import Tuple, Dict, Any
from pathlib import Path
import yaml

try:
    from jsonschema import validate, ValidationError, Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("Warning: jsonschema not installed. Schema validation will be skipped.")

from src.utils.logger import get_logger

logger = get_logger()


class SchemaValidator:
    """Schema验证器"""

    def __init__(self, schema_dir: Path = None):
        """
        初始化Schema验证器

        Args:
            schema_dir: Schema文件目录 (默认: project_root/schemas)
        """
        if schema_dir is None:
            # 默认使用项目根目录下的schemas
            project_root = Path(__file__).parent.parent.parent.parent
            schema_dir = project_root / "schemas"

        self.schema_dir = Path(schema_dir)
        self.schemas: Dict[str, dict] = {}

        if not self.schema_dir.exists():
            logger.warning(f"Schema directory not found: {self.schema_dir}")
            return

        # 加载所有schema
        self._load_schemas()

    def _load_schemas(self):
        """加载所有YAML schema文件"""
        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema not available, skipping schema loading")
            return

        schema_files = {
            "sub_mission": "sub_mission.schema.yaml",
            "execution_context": "execution_context.schema.yaml",
            "quality_score": "quality_score.schema.yaml",
        }

        for name, filename in schema_files.items():
            schema_path = self.schema_dir / filename
            if schema_path.exists():
                try:
                    with open(schema_path) as f:
                        self.schemas[name] = yaml.safe_load(f)
                    logger.info(f"Loaded schema: {name}")
                except Exception as e:
                    logger.error(f"Failed to load schema {name}: {e}")
            else:
                logger.warning(f"Schema file not found: {schema_path}")

    def validate_sub_mission(self, mission: dict) -> Tuple[bool, str]:
        """
        验证SubMission定义

        Args:
            mission: SubMission字典

        Returns:
            (is_valid, error_message)
        """
        if not JSONSCHEMA_AVAILABLE:
            return True, "Schema validation skipped (jsonschema not installed)"

        if "sub_mission" not in self.schemas:
            return True, "Schema not loaded"

        try:
            # JSON Schema验证
            validate(instance=mission, schema=self.schemas["sub_mission"])

            # 额外业务校验
            if not self._validate_success_criteria_weights(mission):
                return False, "Success criteria weights must sum to 1.0"

            if not self._validate_dependencies_acyclic(mission):
                return False, "Circular dependency detected (self-reference)"

            return True, ""

        except ValidationError as e:
            return False, f"Schema validation failed: {e.message}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_execution_context(self, context: dict) -> Tuple[bool, str]:
        """
        验证ExecutionContext

        Args:
            context: ExecutionContext字典

        Returns:
            (is_valid, error_message)
        """
        if not JSONSCHEMA_AVAILABLE:
            return True, "Schema validation skipped"

        if "execution_context" not in self.schemas:
            return True, "Schema not loaded"

        try:
            validate(instance=context, schema=self.schemas["execution_context"])
            return True, ""
        except ValidationError as e:
            return False, f"Schema validation failed: {e.message}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_quality_score(self, score: dict) -> Tuple[bool, str]:
        """
        验证QualityScore

        Args:
            score: QualityScore字典

        Returns:
            (is_valid, error_message)
        """
        if not JSONSCHEMA_AVAILABLE:
            return True, "Schema validation skipped"

        if "quality_score" not in self.schemas:
            return True, "Schema not loaded"

        try:
            validate(instance=score, schema=self.schemas["quality_score"])

            # 额外校验：维度权重总和应为1.0
            total_weight = sum(
                dim["weight"] for dim in score.get("dimension_scores", [])
            )
            if abs(total_weight - 1.0) > 0.01:
                return False, f"Dimension weights sum to {total_weight:.2f}, expected 1.0"

            return True, ""
        except ValidationError as e:
            return False, f"Schema validation failed: {e.message}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def _validate_success_criteria_weights(self, mission: dict) -> bool:
        """验证成功标准权重总和为1.0"""
        try:
            total_weight = sum(
                criterion["weight"]
                for criterion in mission.get("success_criteria", [])
            )
            return abs(total_weight - 1.0) < 0.01  # 允许浮点误差
        except (KeyError, TypeError):
            return False

    def _validate_dependencies_acyclic(self, mission: dict) -> bool:
        """验证依赖关系无环 (简化检查: 不能依赖自己)"""
        mission_id = mission.get("id", "")
        dependencies = mission.get("dependencies", [])
        return mission_id not in dependencies


# 全局单例
_validator_instance = None


def get_validator() -> SchemaValidator:
    """获取全局Schema验证器实例"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = SchemaValidator()
    return _validator_instance
