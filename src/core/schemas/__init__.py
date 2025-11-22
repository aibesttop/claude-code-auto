"""
Schemas Module - 结构化协议定义和验证

提供SubMission、ExecutionContext、QualityScore等的Schema定义和验证
"""
from .validator import SchemaValidator, get_validator

__all__ = ["SchemaValidator", "get_validator"]
