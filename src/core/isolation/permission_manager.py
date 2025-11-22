"""
Permission Manager - 权限管理器

基于角色的最小权限管理
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Set, Optional, List

from src.utils.logger import get_logger

logger = get_logger()


class PermissionLevel(str, Enum):
    """权限级别"""
    NONE = "none"          # 无权限
    READ = "read"          # 只读
    WRITE = "write"        # 读写
    EXECUTE = "execute"    # 执行
    ADMIN = "admin"        # 管理员


@dataclass
class Permission:
    """权限定义"""
    resource_type: str  # file, tool, api, network
    resource_path: str  # 资源路径或标识符
    level: PermissionLevel
    description: str = ""

    def __hash__(self):
        return hash((self.resource_type, self.resource_path, self.level))


class PermissionManager:
    """权限管理器"""

    def __init__(self):
        """初始化权限管理器"""
        # 角色权限映射
        self.role_permissions: Dict[str, Set[Permission]] = {}

        # 预定义角色权限
        self._initialize_default_permissions()

        logger.info("PermissionManager initialized")

    def _initialize_default_permissions(self):
        """初始化默认角色权限"""

        # Coder: 代码读写权限
        self.role_permissions["Coder"] = {
            Permission("file", "src/**/*.py", PermissionLevel.WRITE, "源码读写"),
            Permission("file", "tests/**/*.py", PermissionLevel.WRITE, "测试代码读写"),
            Permission("tool", "git", PermissionLevel.EXECUTE, "Git操作"),
            Permission("tool", "pytest", PermissionLevel.EXECUTE, "运行测试"),
            Permission("tool", "flake8", PermissionLevel.EXECUTE, "代码检查"),
        }

        # Tester: 测试相关权限
        self.role_permissions["Tester"] = {
            Permission("file", "tests/**/*", PermissionLevel.WRITE, "测试文件读写"),
            Permission("file", "src/**/*.py", PermissionLevel.READ, "源码只读"),
            Permission("tool", "pytest", PermissionLevel.EXECUTE, "运行测试"),
            Permission("tool", "coverage", PermissionLevel.EXECUTE, "覆盖率分析"),
        }

        # DocWriter: 文档权限
        self.role_permissions["DocWriter"] = {
            Permission("file", "docs/**/*", PermissionLevel.WRITE, "文档读写"),
            Permission("file", "*.md", PermissionLevel.WRITE, "Markdown文件读写"),
            Permission("file", "src/**/*.py", PermissionLevel.READ, "源码只读"),
        }

        # Reviewer: 审查权限 (只读 + 评论)
        self.role_permissions["Reviewer"] = {
            Permission("file", "**/*", PermissionLevel.READ, "全局只读"),
            Permission("tool", "git", PermissionLevel.READ, "Git只读操作"),
        }

        # Debugger: 调试权限
        self.role_permissions["Debugger"] = {
            Permission("file", "src/**/*.py", PermissionLevel.READ, "源码只读"),
            Permission("file", "logs/**/*", PermissionLevel.READ, "日志只读"),
            Permission("tool", "debugger", PermissionLevel.EXECUTE, "调试工具"),
        }

        # Architect: 架构设计权限
        self.role_permissions["Architect"] = {
            Permission("file", "**/*", PermissionLevel.READ, "全局只读"),
            Permission("file", "docs/architecture/**/*", PermissionLevel.WRITE, "架构文档读写"),
        }

        # SecurityExpert: 安全审计权限
        self.role_permissions["SecurityExpert"] = {
            Permission("file", "**/*", PermissionLevel.READ, "全局只读"),
            Permission("tool", "bandit", PermissionLevel.EXECUTE, "安全扫描"),
            Permission("tool", "safety", PermissionLevel.EXECUTE, "依赖安全检查"),
        }

        # PerfAnalyzer: 性能分析权限
        self.role_permissions["PerfAnalyzer"] = {
            Permission("file", "src/**/*.py", PermissionLevel.READ, "源码只读"),
            Permission("tool", "profiler", PermissionLevel.EXECUTE, "性能分析工具"),
        }

        # Leader: 管理员权限
        self.role_permissions["Leader"] = {
            Permission("file", "**/*", PermissionLevel.ADMIN, "全局管理权限"),
            Permission("tool", "*", PermissionLevel.ADMIN, "所有工具"),
            Permission("api", "*", PermissionLevel.ADMIN, "所有API"),
        }

        logger.info(
            f"Initialized default permissions for {len(self.role_permissions)} roles"
        )

    def grant_permission(
        self,
        role_name: str,
        permission: Permission
    ):
        """
        授予权限

        Args:
            role_name: 角色名称
            permission: 权限对象
        """
        if role_name not in self.role_permissions:
            self.role_permissions[role_name] = set()

        self.role_permissions[role_name].add(permission)

        logger.info(
            f"Granted permission to {role_name}: "
            f"{permission.resource_type}:{permission.resource_path} [{permission.level.value}]"
        )

    def revoke_permission(
        self,
        role_name: str,
        permission: Permission
    ) -> bool:
        """
        撤销权限

        Args:
            role_name: 角色名称
            permission: 权限对象

        Returns:
            True if revocation successful
        """
        if role_name not in self.role_permissions:
            return False

        if permission in self.role_permissions[role_name]:
            self.role_permissions[role_name].remove(permission)
            logger.info(
                f"Revoked permission from {role_name}: "
                f"{permission.resource_type}:{permission.resource_path}"
            )
            return True

        return False

    def check_permission(
        self,
        role_name: str,
        resource_type: str,
        resource_path: str,
        required_level: PermissionLevel
    ) -> bool:
        """
        检查权限

        Args:
            role_name: 角色名称
            resource_type: 资源类型
            resource_path: 资源路径
            required_level: 需要的权限级别

        Returns:
            True if permission granted
        """
        if role_name not in self.role_permissions:
            logger.warning(f"Role not found: {role_name}")
            return False

        permissions = self.role_permissions[role_name]

        # 检查精确匹配
        for perm in permissions:
            if perm.resource_type == resource_type:
                # 支持通配符匹配
                if self._match_path(perm.resource_path, resource_path):
                    # 检查权限级别
                    if self._is_level_sufficient(perm.level, required_level):
                        return True

        logger.debug(
            f"Permission denied for {role_name}: "
            f"{resource_type}:{resource_path} [{required_level.value}]"
        )
        return False

    def _match_path(self, pattern: str, path: str) -> bool:
        """
        路径匹配 (支持简单通配符)

        Args:
            pattern: 权限模式
            path: 资源路径

        Returns:
            True if matches
        """
        # 完全匹配
        if pattern == path:
            return True

        # 通配符匹配
        if pattern == "*" or pattern == "**/*":
            return True

        # 简化的glob匹配
        if "**" in pattern:
            # 递归匹配
            prefix = pattern.split("**")[0]
            suffix = pattern.split("**")[-1].lstrip("/")

            if path.startswith(prefix):
                if not suffix or path.endswith(suffix.replace("*", "")):
                    return True

        elif "*" in pattern:
            # 单层通配符
            import re
            regex_pattern = pattern.replace("*", ".*")
            if re.match(f"^{regex_pattern}$", path):
                return True

        return False

    def _is_level_sufficient(
        self,
        granted_level: PermissionLevel,
        required_level: PermissionLevel
    ) -> bool:
        """
        检查权限级别是否足够

        权限级别层次: NONE < READ < WRITE < EXECUTE < ADMIN

        Args:
            granted_level: 授予的权限级别
            required_level: 需要的权限级别

        Returns:
            True if sufficient
        """
        level_hierarchy = {
            PermissionLevel.NONE: 0,
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4
        }

        granted_value = level_hierarchy.get(granted_level, 0)
        required_value = level_hierarchy.get(required_level, 0)

        return granted_value >= required_value

    def get_role_permissions(self, role_name: str) -> List[Permission]:
        """
        获取角色的所有权限

        Args:
            role_name: 角色名称

        Returns:
            权限列表
        """
        if role_name not in self.role_permissions:
            return []

        return list(self.role_permissions[role_name])

    def list_roles(self) -> List[str]:
        """列出所有角色"""
        return list(self.role_permissions.keys())

    def get_permission_summary(self, role_name: str) -> Dict:
        """
        获取角色权限摘要

        Args:
            role_name: 角色名称

        Returns:
            权限摘要字典
        """
        if role_name not in self.role_permissions:
            return {
                "role": role_name,
                "total_permissions": 0,
                "by_resource_type": {},
                "by_level": {}
            }

        permissions = self.role_permissions[role_name]

        # 统计
        by_resource_type = {}
        by_level = {}

        for perm in permissions:
            # 按资源类型
            by_resource_type[perm.resource_type] = \
                by_resource_type.get(perm.resource_type, 0) + 1

            # 按权限级别
            by_level[perm.level.value] = \
                by_level.get(perm.level.value, 0) + 1

        return {
            "role": role_name,
            "total_permissions": len(permissions),
            "by_resource_type": by_resource_type,
            "by_level": by_level
        }


# 全局单例
_permission_manager_instance: Optional[PermissionManager] = None


def get_permission_manager() -> PermissionManager:
    """获取全局权限管理器实例"""
    global _permission_manager_instance
    if _permission_manager_instance is None:
        _permission_manager_instance = PermissionManager()
    return _permission_manager_instance
