# V3 生产级完善计划 (Production-Ready V3 Roadmap)

> 基于现有代码分析和 2024/2025 最佳实践的可执行完善计划
>
> 版本: V3.1
> 创建时间: 2025-11-21
> 目标: 将 V3 从原型提升到生产级质量

---

## 📋 现状评估 (Current State Assessment)

### ✅ 已实现的核心能力

| 模块 | 实现状态 | 文件位置 | 质量评级 |
|------|---------|----------|---------|
| Persona Engine | ✅ 基础版 | `core/agents/persona.py` | ⭐⭐⭐ (可用) |
| Researcher Agent | ✅ 带缓存 | `core/agents/researcher.py` | ⭐⭐⭐⭐ (良好) |
| Event Store | ✅ 完整 | `core/events.py` | ⭐⭐⭐⭐ (良好) |
| Cost Tracker | ✅ 完整 | `core/events.py` | ⭐⭐⭐⭐ (良好) |
| State Manager | ✅ 完整 | `state_manager.py` | ⭐⭐⭐⭐ (良好) |
| Tool Registry | ✅ 基础版 | `core/tool_registry.py` | ⭐⭐⭐ (可用) |
| Config System | ✅ Pydantic | `config.py` | ⭐⭐⭐⭐⭐ (优秀) |

### ❌ 缺失的关键能力

| 能力 | 优先级 | 风险等级 | 预计工作量 |
|-----|-------|---------|-----------|
| **Persona 优化与压缩** | 🔴 P0 | 🟡 中 | 2-3 天 |
| **预算管理系统** | 🔴 P0 | 🟠 高 | 2-3 天 |
| **OpenTelemetry 分布式追踪** | 🟠 P1 | 🟢 低 | 3-4 天 |
| **状态 Checkpoint/Rollback** | 🟠 P1 | 🟡 中 | 2-3 天 |
| **Researcher NLI 验证** | 🟠 P1 | 🟡 中 | 3-4 天 |
| **Tool Composer (安全版)** | 🟠 P1 | 🟠 高 | 4-5 天 |
| **Sub-Agent Orchestrator** | 🟡 P2 | 🟠 高 | 5-7 天 |
| **沙箱执行系统** | 🟡 P2 | 🔴 极高 | 5-7 天 |
| **冲突检测与解决** | 🟡 P2 | 🟡 中 | 3-4 天 |

---

## 🎯 开发路线图 (Development Roadmap)

### Phase 0: 基础设施强化 (Foundation) - 1 周

**目标**: 为生产级运行打下坚实基础

#### Task 0.1: 预算管理系统 (2 天)
**实现文件**: `core/budget_manager.py`

```python
class BudgetManager:
    """智能预算管理器，支持多粒度成本控制"""

    def __init__(self, daily_budget: float = 100.0):
        self.daily_budget = daily_budget
        self.budgets = {
            "daily": daily_budget,
            "per_iteration": daily_budget / 10,  # 单次迭代预算
            "researcher": daily_budget * 0.3,     # 研究占比30%
            "executor": daily_budget * 0.6,       # 执行占比60%
        }
        self.cost_tracker = None  # 注入 CostTracker

    async def check_budget(self, operation: str, estimated_cost: float) -> Dict:
        """预算检查 + 降级策略"""
        if not self._has_budget(operation, estimated_cost):
            return await self._apply_fallback(operation)
        return {"allowed": True, "strategy": "primary"}

    def _apply_fallback(self, operation: str) -> Dict:
        """降级策略"""
        if operation == "web_search":
            return {"allowed": True, "strategy": "cache_only"}
        elif operation == "llm_call":
            return {"allowed": True, "strategy": "smaller_model"}
        return {"allowed": False, "strategy": "blocked"}
```

**集成点**:
- 在 `main_v3.py` 初始化时创建 `BudgetManager`
- 在每次 LLM 调用前检查预算
- 在 `ResearcherAgent.research()` 中集成
- 添加实时预算监控到 Web UI

**验收标准**:
- ✅ 单元测试覆盖率 > 80%
- ✅ 成本超标时自动降级到 Haiku
- ✅ 研究查询超预算时使用缓存
- ✅ 实时预算仪表盘可视化

---

#### Task 0.2: OpenTelemetry 分布式追踪 (3 天)
**实现文件**: `core/observability.py`

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger import JaegerExporter

class ObservabilityLayer:
    """统一的可观测性层"""

    def __init__(self, service_name: str = "claude-code-auto"):
        # 初始化 OpenTelemetry
        trace.set_tracer_provider(TracerProvider())
        self.tracer = trace.get_tracer(__name__)

        # Jaeger exporter (可选，开发环境使用)
        if os.getenv("JAEGER_ENABLED", "false") == "true":
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )

    def trace_agent(self, agent_name: str):
        """Agent执行追踪装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                with self.tracer.start_as_current_span(
                    f"agent.{agent_name}",
                    attributes={
                        "agent.name": agent_name,
                        "agent.type": type(args[0]).__name__
                    }
                ) as span:
                    try:
                        result = await func(*args, **kwargs)
                        span.set_attribute("status", "success")
                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_attribute("status", "error")
                        raise
            return wrapper
        return decorator
```

**集成点**:
- 装饰所有 Agent 的主要方法 (`planner.get_next_step`, `executor.execute_task`, `researcher.research`)
- 在 `main_v3.py` 中初始化
- 导出到 Jaeger UI (开发) 或 JSON (生产)

**可选依赖**:
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger
```

**验收标准**:
- ✅ 所有 Agent 调用链路可视化
- ✅ 异常自动捕获到 span
- ✅ 端到端延迟可追踪

---

#### Task 0.3: 状态 Checkpoint 与 Rollback (2 天)
**增强文件**: `state_manager.py`

在现有 `StateManager` 中添加:

```python
class StateManager:
    # ... 现有代码 ...

    def __init__(self, state_file_path: Path, max_checkpoints: int = 10):
        self.state_file_path = state_file_path
        self.checkpoint_dir = state_file_path.parent / "checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.max_checkpoints = max_checkpoints
        self._state: Optional[ExecutionState] = None

    def create_checkpoint(self, label: str = None) -> Path:
        """创建状态快照"""
        if self._state is None:
            raise RuntimeError("没有可保存的状态")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label_suffix = f"_{label}" if label else ""
        checkpoint_name = f"checkpoint_{timestamp}{label_suffix}.json"
        checkpoint_path = self.checkpoint_dir / checkpoint_name

        # 保存快照
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(self._state.to_dict(), f, indent=2, ensure_ascii=False)

        # 清理旧快照
        self._cleanup_old_checkpoints()

        return checkpoint_path

    def rollback_to_checkpoint(self, checkpoint_path: Path) -> ExecutionState:
        """回滚到指定快照"""
        self._state = ExecutionState.load(checkpoint_path)
        self.save()  # 更新主状态文件
        return self._state

    def list_checkpoints(self) -> List[Path]:
        """列出所有快照"""
        return sorted(self.checkpoint_dir.glob("checkpoint_*.json"), reverse=True)

    def _cleanup_old_checkpoints(self):
        """保留最新 N 个快照"""
        checkpoints = self.list_checkpoints()
        if len(checkpoints) > self.max_checkpoints:
            for old_checkpoint in checkpoints[self.max_checkpoints:]:
                old_checkpoint.unlink()
```

**集成点**:
- 在每次成功的迭代后创建 checkpoint
- 在遇到错误时自动回滚到最后一个成功的 checkpoint
- 添加 CLI 命令手动回滚

**验收标准**:
- ✅ 每次迭代后自动创建快照
- ✅ 错误时可回滚到之前的状态
- ✅ 保留最近 10 个快照

---

### Phase 1: 核心能力增强 (Core Enhancement) - 2 周

#### Task 1.1: Persona 优化与压缩 (3 天)
**增强文件**: `core/agents/persona.py`

添加动态 Persona 优化:

```python
class PersonaEngine:
    # ... 现有代码 ...

    def __init__(self, persona_config: dict = None, enable_optimization: bool = True):
        self.current_persona = PERSONAS["default"]
        self.switch_history: List[PersonaSwitch] = []
        self.enable_optimization = enable_optimization
        self.context_window = 8000  # Persona最大token数

        if persona_config:
            self._load_config(persona_config)

    async def build_optimized_persona(
        self,
        role: str,
        task_context: dict,
        llm_client = None
    ) -> str:
        """动态构建并优化 Persona"""
        base_persona = PERSONAS.get(role, PERSONAS["default"])
        full_prompt = base_persona.system_prompt

        # 如果禁用优化或没有LLM客户端，直接返回
        if not self.enable_optimization or not llm_client:
            return full_prompt

        # 使用 LLM 压缩 Persona（元提示）
        optimization_prompt = f"""
Given the task: {task_context.get('goal', 'N/A')}

Compress the following persona to ~{self.context_window} tokens, keeping only the most relevant parts for the task:

{full_prompt}

Return ONLY the compressed persona, no explanations.
"""

        try:
            optimized, _ = await llm_client(
                optimization_prompt,
                model="claude-3-haiku-20240307",  # 使用便宜的模型优化
                timeout=30
            )

            # 验证长度（粗略估算）
            if len(optimized) < len(full_prompt) * 0.9:  # 至少压缩10%
                return optimized.strip()
        except Exception as e:
            logger.warning(f"Persona优化失败，使用原始版本: {e}")

        return full_prompt
```

**集成点**:
- 在 `ExecutorAgent` 中调用优化后的 Persona
- 缓存优化后的 Persona (按 role + task hash)

**验收标准**:
- ✅ Persona token 使用减少 > 20%
- ✅ 任务相关性提升（人工评估）

---

#### Task 1.2: Researcher NLI 验证与重排序 (4 天)
**增强文件**: `core/agents/researcher.py`

```python
from sentence_transformers import CrossEncoder  # 重排序模型

class ResearcherAgent:
    # ... 现有代码 ...

    def __init__(self, *args, enable_reranking: bool = True, enable_nli: bool = True, **kwargs):
        # ... 现有初始化 ...
        self.enable_reranking = enable_reranking
        self.enable_nli = enable_nli

        # 加载重排序模型（轻量级）
        if enable_reranking:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

        # NLI 模型（用于幻觉检测）
        if enable_nli:
            from transformers import pipeline
            self.nli_pipeline = pipeline(
                "text-classification",
                model="microsoft/deberta-v3-base-tasksource-nli"
            )

    async def research(self, query: str, use_cache: bool = True) -> Dict:
        """增强版研究流程"""
        # ... 现有缓存检查 ...

        # 1. 执行搜索
        search_result = web_search(query)

        # 2. 重排序（如果启用）
        if self.enable_reranking and isinstance(search_result, list):
            ranked_results = self._rerank_results(query, search_result)
        else:
            ranked_results = search_result

        # 3. LLM 总结
        summary = await self._summarize_results(query, ranked_results)

        # 4. NLI 验证（如果启用）
        if self.enable_nli:
            quality_score = self._verify_consistency(summary, ranked_results)

            if quality_score < 0.6:  # 低质量，标记警告
                logger.warning(f"研究质量评分低: {quality_score:.2f}")
                summary = f"⚠️ 低置信度结果 (score={quality_score:.2f})\n\n{summary}"
        else:
            quality_score = None

        return {
            "summary": summary,
            "sources": ranked_results[:5] if isinstance(ranked_results, list) else [],
            "quality_score": quality_score
        }

    def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """使用 CrossEncoder 重排序"""
        if not results:
            return results

        # 准备查询-文档对
        pairs = [[query, r.get("content", "")] for r in results]

        # 打分
        scores = self.reranker.predict(pairs)

        # 排序
        ranked = sorted(
            zip(results, scores),
            key=lambda x: x[1],
            reverse=True
        )

        return [r for r, _ in ranked]

    def _verify_consistency(self, summary: str, sources: List[Dict]) -> float:
        """NLI 验证：检测幻觉"""
        if not sources:
            return 0.5  # 无法验证

        # 提取源文本
        source_text = " ".join([s.get("content", "")[:500] for s in sources[:3]])

        # NLI 推理
        result = self.nli_pipeline(
            f"{source_text} [SEP] {summary}",
            truncation=True,
            max_length=512
        )

        # 计算一致性分数
        # label: entailment (一致), neutral, contradiction
        label_scores = {r['label']: r['score'] for r in result}
        consistency = label_scores.get('entailment', 0.0)

        return consistency
```

**新增依赖**:
```bash
pip install sentence-transformers transformers torch
```

**可选：轻量级部署方案**
- 使用 ONNX 量化模型减少内存占用
- 或使用 Cohere Rerank API (付费但更快)

**验收标准**:
- ✅ 搜索结果相关性提升 > 30%
- ✅ 幻觉检测准确率 > 70%
- ✅ 低质量结果自动标记

---

#### Task 1.3: Tool Composer (安全版) (5 天)
**新建文件**: `core/tool_composer.py`

**关键决策**: 不实现真正的代码生成，而是安全的函数组合

```python
class ToolComposer:
    """安全的工具组合器 - 不执行任意代码"""

    # 预定义的安全原语
    SAFE_PRIMITIVES = {
        # HTTP 操作
        "http_get": lambda url, **kw: requests.get(url, **kw).json(),
        "http_post": lambda url, data, **kw: requests.post(url, json=data, **kw).json(),

        # 数据转换
        "parse_json": json.loads,
        "parse_xml": lambda x: xmltodict.parse(x),
        "to_json": json.dumps,

        # 列表操作
        "filter_list": lambda lst, condition: [
            x for x in lst if eval(condition, {"x": x, "__builtins__": {}})
        ],
        "map_list": lambda lst, transform: [
            eval(transform, {"x": x, "__builtins__": {}}) for x in lst
        ],
        "sort_list": lambda lst, key: sorted(lst, key=lambda x: x[key]),

        # 字符串操作
        "extract_regex": lambda text, pattern: re.findall(pattern, text),
        "replace_text": lambda text, old, new: text.replace(old, new),
        "split_text": lambda text, sep: text.split(sep),

        # 数学操作
        "sum_values": sum,
        "avg_values": lambda lst: sum(lst) / len(lst) if lst else 0,
        "max_value": max,
        "min_value": min,
    }

    def compose_tool(self, spec: Dict) -> Callable:
        """
        根据 JSON 配置组合工具

        示例配置:
        {
          "name": "fetch_github_stars",
          "description": "获取 GitHub 仓库星数",
          "steps": [
            {
              "primitive": "http_get",
              "args": {"url": "https://api.github.com/repos/{owner}/{repo}"}
            },
            {
              "primitive": "parse_json"
            },
            {
              "primitive": "extract_field",
              "args": {"field": "stargazers_count"}
            }
          ]
        }
        """
        name = spec.get("name", "custom_tool")
        steps = spec.get("steps", [])

        def composed_tool(*args, **kwargs):
            """组合后的工具函数"""
            result = args[0] if args else kwargs

            for step in steps:
                primitive_name = step.get("primitive")
                step_args = step.get("args", {})

                # 获取原语
                primitive = self.SAFE_PRIMITIVES.get(primitive_name)
                if not primitive:
                    raise ValueError(f"Unknown primitive: {primitive_name}")

                # 模板替换（支持 {var} 语法）
                resolved_args = self._resolve_templates(step_args, result, kwargs)

                # 执行原语
                try:
                    if isinstance(result, dict):
                        result = primitive(**result, **resolved_args)
                    else:
                        result = primitive(result, **resolved_args)
                except Exception as e:
                    logger.error(f"工具步骤失败 '{primitive_name}': {e}")
                    raise

            return result

        composed_tool.__name__ = name
        composed_tool.__doc__ = spec.get("description", "Composed tool")

        return composed_tool

    def _resolve_templates(self, args: Dict, result, context: Dict) -> Dict:
        """解析模板变量"""
        resolved = {}
        for key, value in args.items():
            if isinstance(value, str) and "{" in value:
                # 简单模板替换
                resolved[key] = value.format(**context)
            else:
                resolved[key] = value
        return resolved

    def register_from_spec(self, spec: Dict):
        """将组合工具注册到工具注册表"""
        from core.tool_registry import registry, Tool

        composed_func = self.compose_tool(spec)
        tool = Tool(composed_func, name=spec["name"], description=spec["description"])
        registry.register(tool)

        return tool
```

**集成点**:
- 在启动时加载预定义的工具配置（YAML 文件）
- 允许 LLM 建议新的工具组合（但需人工审批）

**示例工具配置**: `configs/composed_tools.yaml`
```yaml
tools:
  - name: "get_weather"
    description: "获取指定城市的天气"
    steps:
      - primitive: "http_get"
        args:
          url: "https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
      - primitive: "parse_json"
      - primitive: "extract_field"
        args:
          field: "main.temp"
```

**验收标准**:
- ✅ 支持 20+ 安全原语
- ✅ 从 YAML 加载工具配置
- ✅ 禁止任意代码执行
- ✅ 完整的错误处理和日志

---

### Phase 2: 多 Agent 协作 (Multi-Agent) - 2 周

#### Task 2.1: Sub-Agent Orchestrator (7 天)
**新建文件**: `core/orchestrator.py`

```python
import asyncio
from typing import List, Dict, Any, Optional
import networkx as nx

class SubTask(BaseModel):
    """子任务定义"""
    id: str
    description: str
    assigned_agent: str
    dependencies: List[str] = []
    timeout_seconds: int = 300
    max_retries: int = 2

class TaskResult(BaseModel):
    """任务结果"""
    task_id: str
    success: bool
    result: Any
    duration: float
    error: Optional[str] = None

class AgentOrchestrator:
    """多 Agent 编排器"""

    def __init__(self, max_concurrent_agents: int = 3):
        self.agents = {}  # agent_name -> agent_instance
        self.max_concurrent = max_concurrent_agents
        self.task_graph = nx.DiGraph()

    def register_agent(self, name: str, agent: Any):
        """注册 Agent"""
        self.agents[name] = agent

    async def execute_swarm(self, subtasks: List[SubTask]) -> Dict[str, TaskResult]:
        """并行执行多个子任务"""
        # 1. 构建依赖图
        self._build_dependency_graph(subtasks)

        # 2. 检测循环依赖
        if not self._is_dag():
            raise ValueError("检测到循环依赖，无法执行")

        # 3. 拓扑排序
        execution_order = list(nx.topological_sort(self.task_graph))

        # 4. 按层级并行执行
        results = {}
        for layer in self._get_execution_layers(execution_order, subtasks):
            layer_results = await self._execute_layer(layer, results)
            results.update(layer_results)

        return results

    def _build_dependency_graph(self, subtasks: List[SubTask]):
        """构建任务依赖图"""
        self.task_graph.clear()

        for task in subtasks:
            self.task_graph.add_node(task.id, task=task)
            for dep in task.dependencies:
                self.task_graph.add_edge(dep, task.id)

    def _is_dag(self) -> bool:
        """检查是否为有向无环图"""
        try:
            list(nx.topological_sort(self.task_graph))
            return True
        except nx.NetworkXError:
            return False

    def _get_execution_layers(self, order: List[str], subtasks: List[SubTask]) -> List[List[SubTask]]:
        """将任务分层（同层可并行执行）"""
        task_map = {t.id: t for t in subtasks}
        layers = []
        completed = set()

        while len(completed) < len(subtasks):
            # 找出所有依赖已完成的任务
            current_layer = []
            for task_id in order:
                if task_id in completed:
                    continue

                task = task_map[task_id]
                if all(dep in completed for dep in task.dependencies):
                    current_layer.append(task)

            if not current_layer:
                raise RuntimeError("无法找到可执行的任务层")

            layers.append(current_layer)
            completed.update(t.id for t in current_layer)

        return layers

    async def _execute_layer(self, layer: List[SubTask], previous_results: Dict) -> Dict[str, TaskResult]:
        """并行执行一层任务"""
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_with_semaphore(task: SubTask):
            async with semaphore:
                return await self._execute_single_task(task, previous_results)

        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in layer],
            return_exceptions=True
        )

        return {
            task.id: result if isinstance(result, TaskResult) else TaskResult(
                task_id=task.id,
                success=False,
                result=None,
                duration=0,
                error=str(result)
            )
            for task, result in zip(layer, results)
        }

    async def _execute_single_task(self, task: SubTask, context: Dict) -> TaskResult:
        """执行单个任务"""
        agent = self.agents.get(task.assigned_agent)
        if not agent:
            raise ValueError(f"Agent 不存在: {task.assigned_agent}")

        start_time = time.time()

        try:
            # 执行任务（根据 agent 类型调用不同方法）
            if hasattr(agent, 'execute_task'):
                result = await asyncio.wait_for(
                    agent.execute_task(task.description),
                    timeout=task.timeout_seconds
                )
            else:
                raise NotImplementedError(f"Agent {task.assigned_agent} 没有 execute_task 方法")

            duration = time.time() - start_time

            return TaskResult(
                task_id=task.id,
                success=True,
                result=result,
                duration=duration
            )

        except asyncio.TimeoutError:
            return TaskResult(
                task_id=task.id,
                success=False,
                result=None,
                duration=task.timeout_seconds,
                error="任务超时"
            )
        except Exception as e:
            return TaskResult(
                task_id=task.id,
                success=False,
                result=None,
                duration=time.time() - start_time,
                error=str(e)
            )
```

**集成点**:
- 在 `main_v3.py` 中创建 Orchestrator
- 注册 Planner, Executor, Researcher 为可调度的 Agent
- 当任务复杂时，使用 LLM 分解为多个子任务

**验收标准**:
- ✅ 支持任务依赖管理
- ✅ 自动检测循环依赖
- ✅ 同层任务并行执行
- ✅ 单个任务失败不影响其他任务

---

### Phase 3: 安全与稳定性 (Safety & Stability) - 1 周

#### Task 3.1: 沙箱执行系统 (可选，仅用于高风险场景) (5 天)

**警告**: 这是高风险功能，建议仅在确实需要时实现

**实现方案**: 使用 Docker 容器隔离

**新建文件**: `core/sandbox.py`

```python
import docker
from pathlib import Path

class DockerSandbox:
    """Docker 沙箱执行器"""

    def __init__(self, image: str = "python:3.11-slim"):
        self.client = docker.from_env()
        self.image = image

    def run_code(
        self,
        code: str,
        timeout: int = 30,
        memory_limit: str = "256m",
        network_disabled: bool = True
    ) -> Dict:
        """在隔离容器中执行代码"""

        # 1. 创建临时工作目录
        work_dir = Path("/tmp/sandbox") / str(uuid.uuid4())
        work_dir.mkdir(parents=True, exist_ok=True)

        # 2. 写入代码
        code_file = work_dir / "main.py"
        code_file.write_text(code)

        try:
            # 3. 运行容器
            container = self.client.containers.run(
                self.image,
                command=f"python /sandbox/main.py",
                volumes={str(work_dir): {"bind": "/sandbox", "mode": "ro"}},
                mem_limit=memory_limit,
                network_disabled=network_disabled,
                detach=True,
                remove=True
            )

            # 4. 等待结果
            result = container.wait(timeout=timeout)
            logs = container.logs().decode()

            return {
                "success": result["StatusCode"] == 0,
                "output": logs,
                "exit_code": result["StatusCode"]
            }

        except docker.errors.ContainerError as e:
            return {
                "success": False,
                "output": str(e),
                "exit_code": -1,
                "error": "容器执行错误"
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "exit_code": -1,
                "error": str(e)
            }
        finally:
            # 清理
            shutil.rmtree(work_dir, ignore_errors=True)
```

**使用场景**:
- ⚠️ 仅在需要执行不可信代码时使用
- ⚠️ 建议优先使用 Tool Composer

**验收标准**:
- ✅ 代码在隔离环境执行
- ✅ 自动清理临时文件
- ✅ 内存/CPU 限制生效

---

## 📊 优先级矩阵

| Phase | 任务 | 工作量 | 价值 | 风险 | 优先级 |
|-------|-----|--------|-----|------|-------|
| **Phase 0** | 预算管理 | 2天 | ⭐⭐⭐⭐⭐ | 🟢 | 🔴 P0 |
| **Phase 0** | OpenTelemetry | 3天 | ⭐⭐⭐⭐ | 🟢 | 🟠 P1 |
| **Phase 0** | Checkpoint/Rollback | 2天 | ⭐⭐⭐⭐ | 🟡 | 🟠 P1 |
| **Phase 1** | Persona 优化 | 3天 | ⭐⭐⭐ | 🟡 | 🟠 P1 |
| **Phase 1** | Researcher NLI | 4天 | ⭐⭐⭐⭐ | 🟡 | 🟠 P1 |
| **Phase 1** | Tool Composer | 5天 | ⭐⭐⭐⭐⭐ | 🟠 | 🟠 P1 |
| **Phase 2** | Sub-Agent Orchestrator | 7天 | ⭐⭐⭐⭐⭐ | 🟠 | 🟡 P2 |
| **Phase 3** | Docker 沙箱 | 5天 | ⭐⭐ | 🔴 | 🟢 P3 (可选) |

---

## 🛠️ 技术栈推荐

### 核心依赖

```bash
# 现有依赖
pydantic>=2.0
pyyaml
anthropic

# Phase 0 新增
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-exporter-jaeger>=1.20.0  # 可选

# Phase 1 新增
sentence-transformers>=2.2.0  # Reranking
transformers>=4.35.0          # NLI
torch>=2.0.0                  # 模型推理

# Phase 2 新增
networkx>=3.0                 # 依赖图
aiohttp>=3.9.0                # 异步 HTTP

# Phase 3 新增 (可选)
docker>=6.0.0                 # 沙箱
```

### 可选服务

- **Jaeger** (分布式追踪可视化): `docker run -d -p 6831:6831/udp -p 16686:16686 jaegertracing/all-in-one:latest`
- **Cohere API** (重排序服务): 替代本地模型，更快但付费

---

## 📈 渐进式部署策略

### 第 1-2 周：基础设施 (Phase 0)
- ✅ 预算管理 (防止成本失控)
- ✅ OpenTelemetry (提升调试能力)
- ✅ Checkpoint (错误恢复)

**产出**: V3.1-alpha (内部测试版)

### 第 3-4 周：核心增强 (Phase 1)
- ✅ Persona 优化 (降低成本)
- ✅ Researcher 增强 (提升质量)
- ✅ Tool Composer (扩展能力)

**产出**: V3.1-beta (功能完整版)

### 第 5-6 周：多 Agent (Phase 2)
- ✅ Sub-Agent Orchestrator (复杂任务分解)

**产出**: V3.1-rc (候选发布版)

### 第 7 周：测试与优化
- 🧪 集成测试
- 📊 性能基准测试
- 📝 文档完善

**产出**: V3.1 (生产版本)

---

## 🎯 成功指标 (KPIs)

| 指标 | 当前 V3.0 | 目标 V3.1 | 测量方法 |
|-----|----------|----------|---------|
| **平均成本/任务** | 未知 | < $0.50 | Cost Tracker |
| **任务成功率** | ~60% | > 85% | Success Rate |
| **平均响应时间** | ~120s | < 90s | OpenTelemetry |
| **研究质量** | 未评估 | > 0.75 | NLI Score |
| **错误恢复率** | 0% | > 90% | Checkpoint 使用率 |

---

## 🚨 风险与缓解

| 风险 | 严重性 | 缓解措施 |
|-----|--------|---------|
| **预算超支** | 🔴 极高 | Phase 0 优先实现预算管理 |
| **依赖安装失败** | 🟠 高 | 提供 Docker 镜像 |
| **NLI 模型内存占用** | 🟡 中 | 使用 ONNX 量化 / Cohere API |
| **沙箱逃逸** | 🔴 极高 | Phase 3 可选，需严格审计 |
| **多 Agent 死锁** | 🟠 高 | 依赖图检测 + 超时机制 |

---

## 📚 参考资源

### 技术文档
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/instrumentation/python/)
- [Sentence Transformers (Reranking)](https://www.sbert.net/examples/applications/cross-encoder/README.html)
- [NetworkX (图论)](https://networkx.org/documentation/stable/)

### 论文
- DSPy: Compiling Declarative Language Model Calls (Stanford, 2023)
- Self-Refine: Iterative Refinement with Self-Feedback (2024)

### 竞品分析
- **AutoGen** (Microsoft): 多 Agent 协作参考
- **LangGraph** (LangChain): 状态机式编排参考
- **CrewAI**: Persona 切换参考

---

## ✅ 验收清单

### Phase 0 完成标准
- [ ] 预算管理系统可运行，测试覆盖率 > 80%
- [ ] OpenTelemetry 集成，Jaeger UI 可查看链路
- [ ] Checkpoint 机制验证，可手动回滚

### Phase 1 完成标准
- [ ] Persona 优化后 token 减少 > 20%
- [ ] Researcher NLI 验证准确率 > 70%
- [ ] Tool Composer 支持 20+ 原语

### Phase 2 完成标准
- [ ] Orchestrator 支持任务依赖管理
- [ ] 并行执行 3+ 任务无死锁

### Phase 3 完成标准
- [ ] 沙箱隔离验证（如实现）

---

## 🎓 下一步行动

1. **立即开始**: Phase 0 Task 0.1 预算管理系统
2. **并行研究**: 评估 Cohere Rerank vs. 本地模型
3. **创建分支**: `feature/v3.1-production`
4. **设置里程碑**: GitHub Issues 跟踪每个 Task

---

**文档版本**: 1.0
**最后更新**: 2025-11-21
**作者**: Claude + Human Collaboration
**状态**: 待执行
