"""
结构化事件流与成本追踪系统
定义事件类型、事件模型、成本追踪器和事件存储
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
import json


class EventType(str, Enum):
    """事件类型枚举"""
    # 会话级事件
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    SESSION_PAUSE = "session_pause"
    SESSION_RESUME = "session_resume"

    # 迭代级事件
    ITERATION_START = "iteration_start"
    ITERATION_END = "iteration_end"

    # Agent事件
    PLANNER_START = "planner_start"
    PLANNER_COMPLETE = "planner_complete"
    PLANNER_ERROR = "planner_error"

    EXECUTOR_START = "executor_start"
    EXECUTOR_COMPLETE = "executor_complete"
    EXECUTOR_ERROR = "executor_error"

    RESEARCHER_START = "researcher_start"
    RESEARCHER_COMPLETE = "researcher_complete"
    RESEARCHER_ERROR = "researcher_error"
    RESEARCHER_CACHE_HIT = "researcher_cache_hit"

    # Persona事件
    PERSONA_SWITCH = "persona_switch"
    PERSONA_RECOMMEND = "persona_recommend"

    # 工具事件
    TOOL_CALL = "tool_call"
    TOOL_SUCCESS = "tool_success"
    TOOL_ERROR = "tool_error"

    # 成本事件
    API_CALL = "api_call"
    COST_RECORDED = "cost_recorded"

    # 安全事件
    EMERGENCY_STOP = "emergency_stop"
    TIMEOUT = "timeout"
    MAX_RETRIES_EXCEEDED = "max_retries_exceeded"


class Event(BaseModel):
    """结构化事件模型"""
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str
    iteration: Optional[int] = None
    data: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "iteration": self.iteration,
            "data": self.data
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Event":
        """从字典创建事件"""
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            session_id=data["session_id"],
            iteration=data.get("iteration"),
            data=data.get("data", {})
        )


class TokenUsage(BaseModel):
    """Token使用统计"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def to_dict(self) -> Dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "total_tokens": self.total_tokens
        }


class CostRecord(BaseModel):
    """成本记录"""
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: str
    iteration: Optional[int] = None
    agent_type: str  # planner, executor, researcher
    model: str
    token_usage: TokenUsage
    duration_seconds: float
    estimated_cost_usd: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "iteration": self.iteration,
            "agent_type": self.agent_type,
            "model": self.model,
            "token_usage": self.token_usage.to_dict(),
            "duration_seconds": self.duration_seconds,
            "estimated_cost_usd": self.estimated_cost_usd
        }


class CostTracker:
    """成本追踪器"""

    # Claude API定价（每百万tokens，美元）
    PRICING = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,
            "output": 15.00,
            "cache_read": 0.30,
            "cache_creation": 3.75
        },
        "claude-3-opus-20240229": {
            "input": 15.00,
            "output": 75.00,
            "cache_read": 1.50,
            "cache_creation": 18.75
        },
        "claude-3-haiku-20240307": {
            "input": 0.25,
            "output": 1.25,
            "cache_read": 0.03,
            "cache_creation": 0.30
        }
    }

    def __init__(self):
        self.records: List[CostRecord] = []

    def calculate_cost(self, model: str, token_usage: TokenUsage) -> float:
        """计算API调用成本"""
        pricing = self.PRICING.get(model, self.PRICING["claude-3-5-sonnet-20241022"])

        cost = (
            (token_usage.input_tokens / 1_000_000) * pricing["input"] +
            (token_usage.output_tokens / 1_000_000) * pricing["output"] +
            (token_usage.cache_read_tokens / 1_000_000) * pricing["cache_read"] +
            (token_usage.cache_creation_tokens / 1_000_000) * pricing["cache_creation"]
        )
        return cost

    def record_cost(
        self,
        session_id: str,
        agent_type: str,
        model: str,
        token_usage: TokenUsage,
        duration_seconds: float,
        iteration: Optional[int] = None
    ) -> CostRecord:
        """记录成本"""
        estimated_cost = self.calculate_cost(model, token_usage)

        record = CostRecord(
            session_id=session_id,
            iteration=iteration,
            agent_type=agent_type,
            model=model,
            token_usage=token_usage,
            duration_seconds=duration_seconds,
            estimated_cost_usd=estimated_cost
        )

        self.records.append(record)
        return record

    def get_session_cost(self, session_id: str) -> float:
        """获取会话总成本"""
        return sum(r.estimated_cost_usd for r in self.records if r.session_id == session_id)

    def get_iteration_cost(self, session_id: str, iteration: int) -> float:
        """获取迭代成本"""
        return sum(
            r.estimated_cost_usd
            for r in self.records
            if r.session_id == session_id and r.iteration == iteration
        )

    def get_agent_cost(self, session_id: str, agent_type: str) -> float:
        """获取特定Agent的成本"""
        return sum(
            r.estimated_cost_usd
            for r in self.records
            if r.session_id == session_id and r.agent_type == agent_type
        )

    def get_total_tokens(self, session_id: str) -> TokenUsage:
        """获取会话总token使用"""
        total = TokenUsage()
        for r in self.records:
            if r.session_id == session_id:
                total.input_tokens += r.token_usage.input_tokens
                total.output_tokens += r.token_usage.output_tokens
                total.cache_read_tokens += r.token_usage.cache_read_tokens
                total.cache_creation_tokens += r.token_usage.cache_creation_tokens
        return total

    def generate_report(self, session_id: str) -> Dict:
        """生成成本报告"""
        session_records = [r for r in self.records if r.session_id == session_id]

        if not session_records:
            return {"error": "No records found for session"}

        total_cost = self.get_session_cost(session_id)
        total_tokens = self.get_total_tokens(session_id)

        agent_breakdown = {}
        for agent_type in set(r.agent_type for r in session_records):
            agent_breakdown[agent_type] = {
                "cost_usd": self.get_agent_cost(session_id, agent_type),
                "calls": len([r for r in session_records if r.agent_type == agent_type])
            }

        return {
            "session_id": session_id,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens.to_dict(),
            "total_calls": len(session_records),
            "agent_breakdown": agent_breakdown,
            "records": [r.to_dict() for r in session_records]
        }


class EventStore:
    """事件存储"""

    def __init__(self, storage_dir: str = "logs/events"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.events: List[Event] = []

    def add_event(self, event: Event):
        """添加事件"""
        self.events.append(event)

    def create_event(
        self,
        event_type: EventType,
        session_id: str,
        iteration: Optional[int] = None,
        **data
    ) -> Event:
        """创建并添加事件"""
        event = Event(
            event_type=event_type,
            session_id=session_id,
            iteration=iteration,
            data=data
        )
        self.add_event(event)
        return event

    def get_events_by_type(self, event_type: EventType, session_id: Optional[str] = None) -> List[Event]:
        """按类型获取事件"""
        events = [e for e in self.events if e.event_type == event_type]
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        return events

    def get_session_events(self, session_id: str) -> List[Event]:
        """获取会话的所有事件"""
        return [e for e in self.events if e.session_id == session_id]

    def get_iteration_events(self, session_id: str, iteration: int) -> List[Event]:
        """获取迭代的所有事件"""
        return [e for e in self.events if e.session_id == session_id and e.iteration == iteration]

    def save_to_file(self, session_id: str, filename: Optional[str] = None):
        """保存事件到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"events_{session_id[:8]}_{timestamp}.json"

        filepath = self.storage_dir / filename
        session_events = self.get_session_events(session_id)

        data = {
            "session_id": session_id,
            "event_count": len(session_events),
            "timestamp": datetime.now().isoformat(),
            "events": [e.to_dict() for e in session_events]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return filepath

    def load_from_file(self, filepath: str):
        """从文件加载事件"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for event_data in data.get("events", []):
            event = Event.from_dict(event_data)
            self.events.append(event)

    def get_event_statistics(self, session_id: str) -> Dict:
        """获取事件统计"""
        session_events = self.get_session_events(session_id)

        if not session_events:
            return {"error": "No events found for session"}

        event_type_counts = {}
        for event in session_events:
            event_type = event.event_type.value
            event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

        iterations = set(e.iteration for e in session_events if e.iteration is not None)

        return {
            "session_id": session_id,
            "total_events": len(session_events),
            "event_type_counts": event_type_counts,
            "iterations_count": len(iterations),
            "first_event": session_events[0].timestamp.isoformat() if session_events else None,
            "last_event": session_events[-1].timestamp.isoformat() if session_events else None
        }
