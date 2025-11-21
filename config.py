"""
配置管理模块
使用 pydantic 进行配置验证，支持从 YAML 文件和环境变量读取
"""
from typing import List, Literal
from pathlib import Path
import yaml
import os
from pydantic import BaseModel, Field, field_validator


class DirectoriesConfig(BaseModel):
    """目录配置"""
    work_dir: str = Field(default="demo_act", description="工作目录")
    mirror_dir: str = Field(default="demo_mirror", description="镜像目录")
    state_file: str = Field(default="workflow_state.json", description="状态文件")
    logs_dir: str = Field(default="logs", description="日志目录")


class TaskConfig(BaseModel):
    """任务配置"""
    goal: str = Field(..., description="任务目标")
    initial_prompt: str = Field(..., description="初始提示词")


class SafetyConfig(BaseModel):
    """安全限制配置"""
    max_iterations: int = Field(default=50, ge=1, le=1000, description="最大迭代次数")
    max_duration_hours: int = Field(default=8, ge=1, le=168, description="最大执行时长")
    emergency_stop_file: str = Field(default=".emergency_stop", description="紧急停止文件")
    iteration_timeout_minutes: int = Field(default=30, ge=1, description="单次迭代超时")


class ErrorHandlingConfig(BaseModel):
    """错误处理配置"""
    max_retries: int = Field(default=3, ge=0, le=10, description="最大重试次数")
    retry_delay_seconds: int = Field(default=5, ge=1, le=60, description="重试延迟")
    continue_on_error: bool = Field(default=False, description="错误时是否继续")
    save_error_logs: bool = Field(default=True, description="是否保存错误日志")


class SessionConfig(BaseModel):
    """会话管理配置"""
    session_id_file: str = Field(default="session_id.txt", description="会话ID文件")
    backup_session_file: str = Field(default="session_id.backup.txt", description="备份文件")
    session_timeout_hours: int = Field(default=24, ge=1, description="会话超时时间")


class JsonParserConfig(BaseModel):
    """JSON解析配置"""
    max_parse_retries: int = Field(default=3, ge=1, le=10, description="解析重试次数")
    strict_mode: bool = Field(default=False, description="严格模式")
    default_confidence: float = Field(default=0.5, ge=0, le=1, description="默认置信度")


class LoggingConfig(BaseModel):
    """日志配置"""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    format: Literal["simple", "detailed", "json"] = Field(default="detailed")
    console_output: bool = Field(default=True, description="控制台输出")
    file_output: bool = Field(default=True, description="文件输出")
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="单文件最大大小")
    backup_count: int = Field(default=5, ge=1, le=20, description="保留文件数")


class ClaudeConfig(BaseModel):
    """Claude SDK 配置"""
    permission_mode: str = Field(default="bypassPermissions", description="权限模式")
    model: str = Field(default="claude-sonnet-4-5", description="模型版本")
    timeout_seconds: int = Field(default=300, ge=30, le=3600, description="API超时")


class PerformanceConfig(BaseModel):
    """性能优化配置"""
    use_incremental_sync: bool = Field(default=True, description="增量同步")
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["*.pyc", "__pycache__", ".git", "*.log"],
        description="排除模式"
    )


class WorkflowConfig(BaseModel):
    """完整的工作流配置"""
    directories: DirectoriesConfig
    task: TaskConfig
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    json_parser: JsonParserConfig = Field(default_factory=JsonParserConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    @field_validator('directories')
    def validate_directories(cls, v):
        """验证并创建必要的目录"""
        # 注意：这里只验证，不创建目录（创建在运行时进行）
        return v

    def ensure_directories(self):
        """确保所有必要的目录存在"""
        Path(self.directories.work_dir).mkdir(parents=True, exist_ok=True)
        Path(self.directories.mirror_dir).mkdir(parents=True, exist_ok=True)
        Path(self.directories.logs_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "WorkflowConfig":
        """从 YAML 文件加载配置"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # 支持环境变量覆盖
        config_data = cls._apply_env_overrides(config_data)

        return cls(**config_data)

    @staticmethod
    def _apply_env_overrides(config_data: dict) -> dict:
        """应用环境变量覆盖"""
        # 支持的环境变量：
        # WORKFLOW_MAX_ITERATIONS, WORKFLOW_WORK_DIR, etc.

        env_mappings = {
            'WORKFLOW_MAX_ITERATIONS': ('safety', 'max_iterations', int),
            'WORKFLOW_WORK_DIR': ('directories', 'work_dir', str),
            'WORKFLOW_GOAL': ('task', 'goal', str),
            'WORKFLOW_LOG_LEVEL': ('logging', 'level', str),
        }

        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if section not in config_data:
                    config_data[section] = {}
                config_data[section][key] = type_func(value)

        return config_data

    def get_work_dir_path(self) -> Path:
        """获取工作目录的 Path 对象"""
        return Path(self.directories.work_dir)

    def get_mirror_dir_path(self) -> Path:
        """获取镜像目录的 Path 对象"""
        return Path(self.directories.mirror_dir)

    def get_state_file_path(self) -> Path:
        """获取状态文件的 Path 对象"""
        return self.get_work_dir_path() / self.directories.state_file

    def get_session_file_path(self) -> Path:
        """获取会话文件的 Path 对象"""
        return self.get_work_dir_path() / self.session.session_id_file

    def get_backup_session_file_path(self) -> Path:
        """获取备份会话文件的 Path 对象"""
        return self.get_work_dir_path() / self.session.backup_session_file

    def get_emergency_stop_file_path(self) -> Path:
        """获取紧急停止文件的 Path 对象"""
        return Path(self.safety.emergency_stop_file)


# 全局配置实例（延迟初始化）
_config: WorkflowConfig = None


def get_config(config_path: str = "config.yaml") -> WorkflowConfig:
    """获取全局配置实例（单例模式）"""
    global _config
    if _config is None:
        _config = WorkflowConfig.from_yaml(config_path)
    return _config


def reload_config(config_path: str = "config.yaml") -> WorkflowConfig:
    """重新加载配置"""
    global _config
    _config = WorkflowConfig.from_yaml(config_path)
    return _config


if __name__ == "__main__":
    # 测试配置加载
    try:
        config = get_config()
        print("✅ 配置加载成功！")
        print(f"工作目录: {config.directories.work_dir}")
        print(f"最大迭代次数: {config.safety.max_iterations}")
        print(f"任务目标: {config.task.goal}")
        config.ensure_directories()
        print("✅ 目录创建成功！")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
