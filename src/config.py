"""
Configuration management using pydantic. Supports YAML + env overrides.
Includes persona, observability, and research settings.
"""
from typing import List, Literal, Dict
from pathlib import Path
import yaml
import os
from pydantic import BaseModel, Field, field_validator


class DirectoriesConfig(BaseModel):
    work_dir: str = Field(default="demo_act", description="Work directory")
    mirror_dir: str = Field(default="demo_mirror", description="Mirror directory")
    state_file: str = Field(default="workflow_state.json", description="State file name")
    logs_dir: str = Field(default="logs", description="Logs directory")


class TaskConfig(BaseModel):
    goal: str = Field(..., description="Task goal")
    initial_prompt: str = Field(..., description="Initial prompt for step1")


class SafetyConfig(BaseModel):
    max_iterations: int = Field(default=50, ge=1, le=1000, description="Max iterations")
    max_duration_hours: int = Field(default=8, ge=1, le=168, description="Max duration hours")
    emergency_stop_file: str = Field(default=".emergency_stop", description="Emergency stop file")
    iteration_timeout_minutes: int = Field(default=30, ge=1, description="Per-iteration timeout (minutes)")


class ErrorHandlingConfig(BaseModel):
    max_retries: int = Field(default=3, ge=0, le=10, description="Max continuous retries before fail")
    retry_delay_seconds: int = Field(default=5, ge=1, le=60, description="Delay between retries")
    continue_on_error: bool = Field(default=False, description="Continue when error")
    save_error_logs: bool = Field(default=True, description="Persist error logs")


class SessionConfig(BaseModel):
    session_id_file: str = Field(default="session_id.txt", description="Session id file")
    backup_session_file: str = Field(default="session_id.backup.txt", description="Backup session file")
    session_timeout_hours: int = Field(default=24, ge=1, description="Session timeout hours")


class JsonParserConfig(BaseModel):
    max_parse_retries: int = Field(default=3, ge=1, le=10, description="JSON parse retries")
    strict_mode: bool = Field(default=False, description="Strict JSON validation")
    default_confidence: float = Field(default=0.5, ge=0, le=1, description="Default confidence on parse fail")


class LoggingConfig(BaseModel):
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    format: Literal["simple", "detailed", "json"] = Field(default="detailed")
    console_output: bool = Field(default=True, description="Output to console")
    file_output: bool = Field(default=True, description="Output to file")
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="Max log file size MB")
    backup_count: int = Field(default=5, ge=1, le=20, description="Backup file count")


class ClaudeConfig(BaseModel):
    permission_mode: str = Field(default="bypassPermissions", description="Permission mode")
    model: str = Field(default="claude-sonnet-4-5", description="Model version")
    timeout_seconds: int = Field(default=300, ge=30, le=3600, description="API timeout")


class PerformanceConfig(BaseModel):
    use_incremental_sync: bool = Field(default=True, description="Use incremental sync")
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["*.pyc", "__pycache__", ".git", "*.log"],
        description="Exclude patterns"
    )


class PersonaConfig(BaseModel):
    default_persona: str = Field(default="default", description="Default persona name for executor")
    personas: Dict[str, Dict[str, str]] = Field(
        default_factory=dict,
        description="Custom persona definitions {name: {description, system_prompt}}"
    )


class ObservabilityConfig(BaseModel):
    enable_event_log: bool = Field(default=True, description="Enable structured event logs")
    enable_cost_log: bool = Field(default=True, description="Log cost/time per iteration (best-effort)")


class ResearchConfig(BaseModel):
    provider: str = Field(default="tavily", description="Search provider")
    enabled: bool = Field(default=True, description="Enable research agent features")


class CostControlConfig(BaseModel):
    """Cost budget control configuration"""
    enabled: bool = Field(default=False, description="Enable cost control")
    max_budget_usd: float = Field(default=10.0, ge=0, description="Maximum budget in USD")
    warning_threshold: float = Field(default=0.8, ge=0, le=1, description="Warning threshold (0-1)")
    auto_stop_on_exceed: bool = Field(default=True, description="Auto stop when budget exceeded")


class LeaderConfig(BaseModel):
    """Leader Agent configuration (v4.0)"""
    enabled: bool = Field(default=False, description="Enable Leader mode (dynamic orchestration)")
    max_mission_retries: int = Field(default=3, ge=1, le=10, description="Max retries per mission")
    quality_threshold: float = Field(default=70.0, ge=0, le=100, description="Minimum quality score (0-100)")
    enable_intervention: bool = Field(default=True, description="Enable intelligent intervention")
    resource_config_dir: str = Field(default="resources", description="Resource configuration directory")


class WorkflowConfig(BaseModel):
    directories: DirectoriesConfig
    task: TaskConfig
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    error_handling: ErrorHandlingConfig = Field(default_factory=ErrorHandlingConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    json_parser: JsonParserConfig = Field(default_factory=JsonParserConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    persona: PersonaConfig = Field(default_factory=PersonaConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    cost_control: CostControlConfig = Field(default_factory=CostControlConfig)
    leader: LeaderConfig = Field(default_factory=LeaderConfig)

    @field_validator('directories')
    def validate_directories(cls, v):
        return v

    def ensure_directories(self):
        Path(self.directories.work_dir).mkdir(parents=True, exist_ok=True)
        Path(self.directories.mirror_dir).mkdir(parents=True, exist_ok=True)
        Path(self.directories.logs_dir).mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "WorkflowConfig":
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在 {config_path}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        config_data = cls._apply_env_overrides(config_data)
        return cls(**config_data)

    @staticmethod
    def _apply_env_overrides(config_data: dict) -> dict:
        env_mappings = {
            'WORKFLOW_MAX_ITERATIONS': ('safety', 'max_iterations', int),
            'WORKFLOW_WORK_DIR': ('directories', 'work_dir', str),
            'WORKFLOW_GOAL': ('task', 'goal', str),
            'WORKFLOW_LOG_LEVEL': ('logging', 'level', str),
            'WORKFLOW_PERSONA': ('persona', 'default_persona', str),
        }
        for env_var, (section, key, type_func) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                if section not in config_data:
                    config_data[section] = {}
                config_data[section][key] = type_func(value)
        return config_data

    def get_work_dir_path(self) -> Path:
        return Path(self.directories.work_dir)

    def get_mirror_dir_path(self) -> Path:
        return Path(self.directories.mirror_dir)

    def get_state_file_path(self) -> Path:
        return self.get_work_dir_path() / self.directories.state_file

    def get_session_file_path(self) -> Path:
        return self.get_work_dir_path() / self.session.session_id_file

    def get_backup_session_file_path(self) -> Path:
        return self.get_work_dir_path() / self.session.backup_session_file

    def get_emergency_stop_file_path(self) -> Path:
        return Path(self.safety.emergency_stop_file)


_config: "WorkflowConfig" = None


def get_config(config_path: str = "config.yaml") -> WorkflowConfig:
    global _config
    if _config is None:
        _config = WorkflowConfig.from_yaml(config_path)
    return _config


def reload_config(config_path: str = "config.yaml") -> WorkflowConfig:
    global _config
    _config = WorkflowConfig.from_yaml(config_path)
    return _config


if __name__ == "__main__":
    try:
        config = get_config()
        print("配置加载成功")
        print(f"工作目录: {config.directories.work_dir}")
        print(f"最大迭代: {config.safety.max_iterations}")
        print(f"任务目标: {config.task.goal}")
        config.ensure_directories()
        print("目录创建成功")
    except Exception as e:
        print(f"配置加载失败: {e}")
