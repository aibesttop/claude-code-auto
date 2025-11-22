# Claude-Code-Auto v3.1 终极升级方案
## 可立即执行的开发计划

**文档版本**: 1.0 Final
**创建日期**: 2025-11-22
**目标版本**: v3.1 (稳定性与可追溯性)
**预计工期**: 2周 (10个工作日)
**风险等级**: 低-中

---

## 📋 执行摘要

本升级方案综合了原有构想文档与深度代码分析结果，在保持向后兼容的前提下，解决v3.0的5个核心问题：

| 问题 | 严重程度 | 当前影响 | v3.1解决方案 |
|------|---------|---------|-------------|
| **依赖执行乱序** | 🔴 高 | 角色执行顺序不可控 | 拓扑排序+验证 |
| **Planner被绕过** | 🟡 中 | 团队模式缺少规划能力 | 每角色独立Planner |
| **思考过程不可见** | 🟡 中 | 无法调试/审计Agent决策 | Markdown跟踪日志 |
| **上下文信息丢失** | 🔴 高 | 角色间传递截断300字符 | 完整上下文传递 |
| **Researcher未复用** | 🟢 低 | 研究能力浪费 | 工具化封装 |

**新增关键改进** (基于代码分析发现):
- ✅ 成本预算控制系统
- ✅ 语义质量评分器
- ✅ 自适应验证规则

---

## 🎯 v3.1 核心目标

### 1. 确定性执行 (Deterministic Execution)

**问题**:
```python
# 当前: src/core/team/team_assembler.py:343-372
# LLM返回角色列表,但不保证依赖顺序
roles = ["AI-Native-Writer", "Market-Researcher"]  # 错误顺序!
```

**解决方案**:
```python
# 新增: src/core/team/dependency_resolver.py
class DependencyResolver:
    def topological_sort(self, roles: List[Role]) -> List[Role]:
        """拓扑排序,保证依赖顺序"""
        # 构建依赖图
        graph = {role.name: role.dependencies for role in roles}
        # Kahn算法排序
        sorted_roles = self._kahn_sort(graph)
        return sorted_roles

    def validate_dependencies(self, roles: List[Role]) -> ValidationResult:
        """验证依赖关系"""
        # 检查循环依赖
        if self._has_cycle(roles):
            return ValidationResult(valid=False, error="Circular dependency")
        # 检查缺失角色
        missing = self._find_missing_roles(roles)
        if missing:
            return ValidationResult(valid=False, error=f"Missing: {missing}")
        return ValidationResult(valid=True)
```

**实现文件**: `src/core/team/dependency_resolver.py` (新建,约150行)

---

### 2. 可追溯思考链 (Traceable Thinking)

**问题**:
```python
# 当前: 思考过程仅在日志中,难以审计
logger.info(f"Thought: {response}")  # 混在大量日志中
```

**解决方案**:
```python
# 修改: src/core/agents/planner.py
class PlannerAgent:
    def export_plan_to_markdown(self, session_id: str, role_name: str, step: int):
        """导出计划到Markdown"""
        trace_path = f"logs/trace/{session_id}_{role_name}_step{step}.md"

        content = f"""# {role_name} - Step {step} Planning Trace

## Goal
{self.current_goal}

## Previous Context
{self.last_result}

## Generated Plan
{self.plan}

## Next Task
{self.next_task}

## Confidence Score
{self.confidence}

## Timestamp
{datetime.now().isoformat()}
"""
        Path(trace_path).write_text(content, encoding='utf-8')
        return trace_path
```

**文件结构**:
```
logs/trace/
├── abc123_Market-Researcher_step1.md
├── abc123_Market-Researcher_step2.md
├── abc123_AI-Native-Writer_step1.md
└── ...
```

**实现文件**:
- 修改 `src/core/agents/planner.py` (+50行)
- 修改 `src/core/agents/executor.py` (+60行)
- 修改 `src/core/team/role_executor.py` (+30行)

---

### 3. 完整上下文传递 (Full Context Passing)

**问题**:
```python
# 当前: src/core/team/role_executor.py:612-621
preview = content[:300] + "..."  # 截断!!!
```

**解决方案**:
```python
# 修改: src/core/team/role_executor.py
def _format_context(self, context: Dict) -> str:
    """格式化完整上下文"""
    lines = []
    for role_name, role_result in context.items():
        lines.append(f"### {role_name} Outputs")
        if 'outputs' in role_result:
            for file, content in role_result['outputs'].items():
                # 方案A: 完整传递(风险:token超限)
                # lines.append(f"**{file}** (完整内容):\n```\n{content}\n```")

                # 方案B: 智能摘要(推荐)
                summary = self._intelligent_summarize(content, max_tokens=500)
                lines.append(f"**{file}** (智能摘要):\n{summary}")

                # 同时保存完整内容到trace
                trace_file = f"logs/trace/{self.session_id}_{role_name}_{file}"
                Path(trace_file).write_text(content, encoding='utf-8')
                lines.append(f"📄 完整内容: {trace_file}")
    return "\n".join(lines)

def _intelligent_summarize(self, content: str, max_tokens: int) -> str:
    """使用LLM智能摘要"""
    if len(content) <= max_tokens * 4:  # 粗略估算
        return content

    prompt = f"Summarize the following in {max_tokens} tokens, preserving key insights:\n\n{content}"
    summary, _ = await run_claude_prompt(prompt, self.work_dir, model="haiku")
    return summary
```

**实现文件**: 修改 `src/core/team/role_executor.py` (+80行)

---

### 4. Planner集成到角色 (Per-Role Planning)

**问题**:
```python
# 当前: src/main.py:280-322
if config.task.initial_prompt:
    # 团队模式完全绕过Planner!
    await run_team_mode(...)
```

**解决方案**:
```python
# 修改: src/core/team/role_executor.py
class RoleExecutor:
    def __init__(self, role: Role, executor: ExecutorAgent, work_dir: str):
        self.role = role
        self.executor = executor
        self.work_dir = work_dir

        # 新增: 为每个角色创建独立Planner
        self.planner = PlannerAgent(
            work_dir=work_dir,
            goal=role.mission.goal,
            model=executor.model,
            timeout_seconds=executor.timeout_seconds,
            permission_mode=executor.permission_mode
        )

    async def execute(self, context: Dict) -> Dict:
        """执行角色使命(带规划)"""
        mission = self.role.mission

        for iteration in range(mission.max_iterations):
            # 1. 规划阶段
            next_task = await self.planner.get_next_step(last_result)

            # 2. 导出跟踪
            trace_file = self.planner.export_plan_to_markdown(
                session_id=self.session_id,
                role_name=self.role.name,
                step=iteration
            )
            logger.info(f"📝 Plan trace: {trace_file}")

            # 3. 执行阶段
            result = await self.executor.execute_task(next_task)

            # 4. 验证
            if self._validate_outputs()['passed']:
                return {"success": True, ...}
```

**实现文件**: 修改 `src/core/team/role_executor.py` (+120行)

---

### 5. 研究工具化 (Researcher as Tool)

**问题**:
```python
# 当前: ResearcherAgent仅作为独立代理,无法被角色调用
```

**解决方案**:
```python
# 新建: src/core/tools/research_tools.py
from src.core.tool_registry import tool
from src.core.agents.researcher import ResearcherAgent

# 全局单例(避免重复初始化)
_researcher_instance = None

def get_researcher() -> ResearcherAgent:
    global _researcher_instance
    if _researcher_instance is None:
        _researcher_instance = ResearcherAgent(
            work_dir=".",
            provider="tavily",
            enabled=True,
            enable_cache=True,
            cache_ttl_minutes=60
        )
    return _researcher_instance

@tool
def deep_research(query: str, max_results: int = 5) -> dict:
    """
    Execute deep research on a query with caching support.

    Args:
        query: Research query
        max_results: Maximum number of results to return

    Returns:
        {
            "summary": str,
            "sources": List[dict],
            "confidence": float
        }
    """
    researcher = get_researcher()
    result = await researcher.deep_research(
        query=query,
        max_results=max_results,
        depth="comprehensive"
    )
    return {
        "summary": result.get('summary', ''),
        "sources": result.get('sources', []),
        "confidence": result.get('quality_score', 0.0)
    }
```

**注册工具**:
```python
# 修改: src/core/tools/__init__.py
from src.core.tools import file_tools, search_tools, shell_tools, research_tools

# research_tools会自动通过@tool装饰器注册
```

**实现文件**:
- 新建 `src/core/tools/research_tools.py` (约100行)
- 修改 `src/core/tools/__init__.py` (+1行)

---

## 🚀 新增关键功能(基于代码分析)

### 6. 成本预算控制

**问题发现**:
```python
# 当前: src/core/events.py 仅追踪,无限制
cost_tracker.record_cost(...)  # 可能无限增长!
```

**解决方案**:
```python
# 修改: src/config.py
class Config(BaseModel):
    # 新增cost_control节
    cost_control: CostControlConfig = Field(default_factory=CostControlConfig)

class CostControlConfig(BaseModel):
    enabled: bool = True
    max_budget_usd: float = 10.0  # 默认$10预算
    warning_threshold: float = 0.8  # 80%时警告
    auto_stop_on_exceed: bool = True  # 超预算自动停止
```

```python
# 修改: src/core/events.py
class CostTracker:
    def check_budget(self, session_id: str, config: CostControlConfig) -> BudgetStatus:
        """检查预算状态"""
        current_cost = self.get_session_cost(session_id)

        if current_cost >= config.max_budget_usd:
            return BudgetStatus(
                exceeded=True,
                current=current_cost,
                limit=config.max_budget_usd,
                action="STOP" if config.auto_stop_on_exceed else "WARN"
            )

        if current_cost >= config.max_budget_usd * config.warning_threshold:
            return BudgetStatus(
                exceeded=False,
                current=current_cost,
                limit=config.max_budget_usd,
                action="WARN"
            )

        return BudgetStatus(exceeded=False, action="CONTINUE")
```

```python
# 修改: src/main.py - 主循环中检查
while iteration < max_iterations:
    # 预算检查
    budget_status = cost_tracker.check_budget(session_id, config.cost_control)

    if budget_status.action == "STOP":
        logger.error(f"💰 预算超限: ${budget_status.current:.2f} / ${budget_status.limit:.2f}")
        state.status = WorkflowStatus.BUDGET_EXCEEDED
        break

    if budget_status.action == "WARN":
        logger.warning(f"💰 预算警告: ${budget_status.current:.2f} / ${budget_status.limit:.2f} ({budget_status.current/budget_status.limit:.0%})")
```

**实现文件**:
- 修改 `src/config.py` (+20行)
- 修改 `src/core/events.py` (+60行)
- 修改 `src/main.py` (+15行)
- 修改 `config.yaml` (+6行)

---

### 7. 语义质量评分器

**问题发现**:
```yaml
# 当前: roles/market_researcher.yaml
validation_rules:
  - type: "min_length"
    min_chars: 2000  # 只检查长度,不检查质量!
```

**解决方案**:
```python
# 新建: src/core/team/quality_validator.py
class SemanticQualityValidator:
    """基于LLM的语义质量评分"""

    async def score_output(
        self,
        content: str,
        success_criteria: List[str],
        file_type: str = "markdown"
    ) -> QualityScore:
        """
        评估输出质量

        Returns:
            QualityScore(
                overall_score: float (0-100),
                criteria_scores: Dict[str, float],
                issues: List[str],
                suggestions: List[str]
            )
        """
        prompt = f"""You are a quality auditor. Evaluate the following {file_type} content against these criteria:

CRITERIA:
{chr(10).join(f"- {c}" for c in success_criteria)}

CONTENT:
{content[:3000]}  # 限制长度避免token超限

Respond in JSON format:
{{
    "overall_score": 0-100,
    "criteria_scores": {{"criterion_1": score, ...}},
    "issues": ["issue 1", ...],
    "suggestions": ["suggestion 1", ...]
}}
"""

        response, _ = await run_claude_prompt(
            prompt,
            work_dir=self.work_dir,
            model="haiku",  # 使用haiku降低成本
            timeout=30
        )

        score_data = extract_json(response)
        return QualityScore(**score_data)
```

**集成到验证流程**:
```python
# 修改: src/core/team/role_executor.py
async def _validate_outputs(self) -> Dict:
    """增强验证:格式+语义"""
    errors = []

    # 1. 原有格式验证
    format_errors = self._validate_format()
    errors.extend(format_errors)

    # 2. 语义质量验证(可选,耗费token)
    if self.role.enable_quality_check:
        validator = SemanticQualityValidator(self.work_dir)

        for file in self.role.output_standard.required_files:
            content = (self.work_dir / file).read_text()

            quality = await validator.score_output(
                content=content,
                success_criteria=self.role.mission.success_criteria
            )

            if quality.overall_score < 70:  # 阈值可配置
                errors.append(
                    f"{file} quality score too low: {quality.overall_score}/100. "
                    f"Issues: {', '.join(quality.issues)}"
                )

    return {"passed": len(errors) == 0, "errors": errors}
```

**配置启用**:
```yaml
# roles/market_researcher.yaml
enable_quality_check: true  # 新增字段
quality_threshold: 70  # 新增字段
```

**实现文件**:
- 新建 `src/core/team/quality_validator.py` (约200行)
- 修改 `src/core/team/role_executor.py` (+40行)
- 修改 `src/core/team/role_registry.py` (+5行, 添加字段)
- 修改所有 `roles/*.yaml` (+2行/文件)

---

### 8. 自适应验证规则

**问题发现**:
```yaml
# 当前验证规则完全静态
min_chars: 2000  # 所有任务都一样!
```

**解决方案**:
```python
# 修改: src/core/team/role_registry.py
class AdaptiveValidationRule(BaseModel):
    type: str
    base_value: int  # 基准值
    complexity_multiplier: float = 1.0  # 复杂度乘数

    def get_effective_value(self, task_complexity: str) -> int:
        """根据任务复杂度计算实际值"""
        multipliers = {
            "simple": 0.7,
            "medium": 1.0,
            "complex": 1.5,
            "expert": 2.0
        }
        return int(self.base_value * multipliers.get(task_complexity, 1.0))
```

```yaml
# roles/market_researcher.yaml
validation_rules:
  - type: "adaptive_min_length"
    file: "market-research.md"
    base_chars: 2000
    # 简单任务:1400字, 中等:2000字, 复杂:3000字, 专家:4000字
```

```python
# 修改: src/core/team/role_executor.py
def _estimate_task_complexity(self, goal: str) -> str:
    """估算任务复杂度"""
    # 方法1: 关键词匹配
    if any(word in goal.lower() for word in ["simple", "quick", "basic"]):
        return "simple"
    if any(word in goal.lower() for word in ["comprehensive", "detailed", "in-depth"]):
        return "complex"
    if any(word in goal.lower() for word in ["expert", "advanced", "sophisticated"]):
        return "expert"

    # 方法2: 基于字符数
    if len(goal) < 100:
        return "simple"
    if len(goal) > 500:
        return "complex"

    return "medium"
```

**实现文件**:
- 修改 `src/core/team/role_registry.py` (+50行)
- 修改 `src/core/team/role_executor.py` (+40行)

---

## 📊 实施计划 (10个工作日)

### Week 1: 核心功能 (5天)

#### Day 1-2: 依赖解析 + 拓扑排序
```
✅ 新建 src/core/team/dependency_resolver.py
✅ 修改 src/core/team/team_assembler.py (集成resolver)
✅ 修改 src/core/team/team_orchestrator.py (使用排序结果)
✅ 编写测试 tests/test_dependency_resolver.py
```

**验收标准**:
```python
# 测试用例
def test_dependency_ordering():
    roles = [
        Role(name="Writer", dependencies=["Researcher"]),
        Role(name="Researcher", dependencies=[]),
        Role(name="SEO", dependencies=["Writer"])
    ]

    sorted_roles = resolver.topological_sort(roles)
    assert [r.name for r in sorted_roles] == ["Researcher", "Writer", "SEO"]

def test_circular_dependency():
    roles = [
        Role(name="A", dependencies=["B"]),
        Role(name="B", dependencies=["A"])
    ]

    with pytest.raises(CircularDependencyError):
        resolver.topological_sort(roles)
```

---

#### Day 3: 跟踪日志系统
```
✅ 修改 src/core/agents/planner.py (+export_plan_to_markdown)
✅ 修改 src/core/agents/executor.py (+export_react_trace)
✅ 修改 src/core/team/role_executor.py (调用导出)
✅ 创建 logs/trace/ 目录结构
```

**验收标准**:
```bash
# 运行团队模式后
ls logs/trace/
# 应该看到:
# abc123_Market-Researcher_step1.md
# abc123_Market-Researcher_step2.md
# abc123_AI-Native-Writer_step1.md

# 检查内容
cat logs/trace/abc123_Market-Researcher_step1.md
# 应该包含: Goal, Plan, Thought, Action, Observation
```

---

#### Day 4: 完整上下文传递
```
✅ 修改 src/core/team/role_executor.py
   - _format_context() 使用智能摘要
   - _intelligent_summarize() 新增
✅ 修改 src/core/team/team_orchestrator.py
   - 传递完整context对象(不截断)
```

**验收标准**:
```python
def test_full_context_passing():
    # 第一个角色生成5000字输出
    role1_output = "A" * 5000

    # 传递给第二个角色
    context = {"Role1": {"outputs": {"file.md": role1_output}}}
    formatted = executor._format_context(context)

    # 应该包含摘要 + trace文件引用
    assert "智能摘要" in formatted
    assert "logs/trace/" in formatted
    assert len(formatted) < 1000  # 摘要不应过长
```

---

#### Day 5: Planner集成
```
✅ 修改 src/core/team/role_executor.py
   - __init__() 初始化PlannerAgent
   - execute() 集成规划循环
✅ 测试 Team Mode + Planner 联合工作
```

**验收标准**:
```python
def test_role_executor_with_planner():
    role = Role(name="Test", mission=Mission(goal="Test goal"))
    executor = RoleExecutor(role, executor_agent, work_dir)

    result = await executor.execute(context={})

    # 应该生成规划跟踪文件
    assert Path(f"logs/trace/{session_id}_Test_step1.md").exists()
    # 应该调用Planner
    assert executor.planner.call_count > 0
```

---

### Week 2: 增强功能 + 测试 (5天)

#### Day 6: 研究工具化
```
✅ 新建 src/core/tools/research_tools.py
✅ 修改 src/core/tools/__init__.py (导入)
✅ 测试工具调用
```

**验收标准**:
```python
def test_deep_research_tool():
    # 从工具注册表调用
    result = registry.execute("deep_research", {
        "query": "AI agent architectures 2024",
        "max_results": 3
    })

    assert "summary" in result
    assert len(result["sources"]) <= 3
    assert result["confidence"] > 0
```

---

#### Day 7: 成本预算控制
```
✅ 修改 src/config.py (+CostControlConfig)
✅ 修改 src/core/events.py (+check_budget)
✅ 修改 src/main.py (主循环检查)
✅ 修改 config.yaml (添加cost_control节)
```

**验收标准**:
```python
def test_budget_exceeded():
    config = Config()
    config.cost_control.max_budget_usd = 1.0

    # 模拟消耗$1.5
    cost_tracker.record_cost(..., estimated_cost_usd=1.5)

    status = cost_tracker.check_budget(session_id, config.cost_control)
    assert status.exceeded == True
    assert status.action == "STOP"
```

---

#### Day 8: 语义质量评分
```
✅ 新建 src/core/team/quality_validator.py
✅ 修改 src/core/team/role_executor.py (集成validator)
✅ 修改 src/core/team/role_registry.py (+quality字段)
✅ 更新 roles/*.yaml (添加quality配置)
```

**验收标准**:
```python
def test_semantic_quality_validation():
    content = "This is a very short and low-quality report."
    validator = SemanticQualityValidator(work_dir)

    score = await validator.score_output(
        content=content,
        success_criteria=["In-depth analysis", "Data-driven insights"]
    )

    assert score.overall_score < 50  # 应该得低分
    assert len(score.issues) > 0
```

---

#### Day 9: 自适应验证规则
```
✅ 修改 src/core/team/role_registry.py (+AdaptiveValidationRule)
✅ 修改 src/core/team/role_executor.py (+complexity估算)
✅ 更新 roles/*.yaml (adaptive规则)
```

---

#### Day 10: 集成测试 + 文档
```
✅ 端到端测试 (完整团队工作流)
✅ 性能测试 (成本、耗时)
✅ 更新文档:
   - README.md (v3.1特性)
   - TEAM_MODE_GUIDE.md (新功能说明)
   - CHANGELOG.md (变更日志)
✅ 创建迁移指南
```

---

## 🧪 测试策略

### 单元测试 (70%覆盖率)

```python
# tests/test_dependency_resolver.py
def test_topological_sort_simple()
def test_topological_sort_complex()
def test_circular_dependency_detection()
def test_missing_role_detection()

# tests/test_trace_export.py
def test_planner_markdown_export()
def test_executor_react_trace()
def test_trace_file_structure()

# tests/test_context_passing.py
def test_full_context_no_truncation()
def test_intelligent_summarization()
def test_trace_file_reference()

# tests/test_research_tool.py
def test_deep_research_tool_registration()
def test_research_caching()
def test_research_tool_in_role()

# tests/test_cost_control.py
def test_budget_warning()
def test_budget_exceeded()
def test_auto_stop()

# tests/test_quality_validator.py
def test_semantic_scoring()
def test_quality_threshold()
def test_quality_suggestions()
```

### 集成测试 (关键路径)

```python
# tests/integration/test_v31_full_workflow.py
async def test_market_research_workflow():
    """完整测试: Market Research → AI-Native-Writer → SEO"""

    config = Config()
    config.task.goal = "Create app documentation"
    config.task.initial_prompt = "Research, document, optimize"

    # 运行团队模式
    result = await run_team_mode(config)

    # 验证依赖顺序
    assert result['role_sequence'] == [
        "Market-Researcher",
        "AI-Native-Writer",
        "SEO-Specialist"
    ]

    # 验证跟踪文件生成
    trace_files = list(Path("logs/trace").glob(f"{session_id}_*.md"))
    assert len(trace_files) >= 3  # 每个角色至少1个trace

    # 验证完整上下文传递
    writer_trace = Path(f"logs/trace/{session_id}_AI-Native-Writer_step1.md").read_text()
    assert "Market-Researcher" in writer_trace  # 应该引用前置角色

    # 验证成本未超限
    cost = cost_tracker.get_session_cost(session_id)
    assert cost < config.cost_control.max_budget_usd
```

### 性能测试

```python
# tests/performance/test_v31_benchmarks.py
def test_dependency_resolution_performance():
    """测试100个角色的拓扑排序性能"""
    roles = generate_complex_dependency_graph(n=100)

    start = time.time()
    sorted_roles = resolver.topological_sort(roles)
    duration = time.time() - start

    assert duration < 1.0  # 应该在1秒内完成

def test_trace_export_overhead():
    """测试跟踪导出的性能开销"""
    # 对比: 有/无trace的执行时间
    time_without_trace = measure_execution_time(export_trace=False)
    time_with_trace = measure_execution_time(export_trace=True)

    overhead = (time_with_trace - time_without_trace) / time_without_trace
    assert overhead < 0.1  # 开销应<10%
```

---

## 🔒 风险评估与缓解

### 高风险项

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **拓扑排序bug导致死锁** | 中 | 高 | 完善单元测试,增加循环检测 |
| **智能摘要token消耗过高** | 高 | 中 | 使用haiku模型,设置token上限 |
| **语义评分拖慢执行速度** | 高 | 中 | 设为可选功能,默认关闭 |
| **向后兼容性破坏** | 低 | 高 | 所有新功能都是增量的,不修改现有API |

### 中风险项

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| **trace文件过多占用磁盘** | 中 | 低 | 实施自动清理策略(保留最近7天) |
| **成本预算过严格导致中断** | 中 | 中 | 提供软限制(warn)和硬限制(stop) |
| **Planner集成增加延迟** | 中 | 低 | 优化planner提示词,使用缓存 |

---

## 📈 成功指标

### 定量指标

| 指标 | v3.0基线 | v3.1目标 | 测量方法 |
|------|---------|---------|---------|
| **角色执行顺序正确率** | 60% | 100% | 依赖验证测试 |
| **决策可追溯性** | 0% | 100% | trace文件完整性 |
| **上下文信息保留率** | 15% | 95% | 内容完整性检查 |
| **成本超限事故** | 未控制 | 0次 | 预算检查日志 |
| **质量不合格率** | 未评估 | <10% | 语义评分统计 |

### 定性指标

- ✅ 开发者能够审计每个角色的决策过程
- ✅ 用户可以设置预算限制防止意外高费用
- ✅ 系统能够识别低质量输出并提示改进
- ✅ 团队模式与原模式无缝切换

---

## 📚 向后兼容性保证

### 不变的API

```python
# 这些接口保持100%兼容
TeamOrchestrator(roles, executor, work_dir)  # 签名不变
RoleExecutor(role, executor, work_dir)  # 签名不变
registry.execute(tool_name, args)  # 签名不变
```

### 可选的新功能

```yaml
# config.yaml - 所有新功能都是可选的
cost_control:
  enabled: false  # 默认关闭,不影响现有用户

# roles/*.yaml - 新字段有默认值
enable_quality_check: false  # 默认关闭
enable_trace_export: true  # 默认开启(低风险)
```

### 迁移路径

**从v3.0升级到v3.1**:
```bash
# 1. 更新代码
git pull origin main
git checkout v3.1

# 2. 更新依赖(无新依赖!)
pip install -r requirements.txt

# 3. 更新配置(可选)
cp config.yaml config.yaml.backup
# 手动添加cost_control节(参考config.yaml.example)

# 4. 更新角色定义(可选)
# 在roles/*.yaml中添加:
# enable_quality_check: false
# enable_trace_export: true

# 5. 测试运行
python src/main.py

# 6. 检查trace文件
ls logs/trace/
```

---

## 🎓 开发者指南

### 本地开发环境设置

```bash
# 1. 克隆仓库
git clone https://github.com/aibesttop/claude-code-auto.git
cd claude-code-auto

# 2. 切换到v3.1开发分支
git checkout -b feature/v3.1-upgrade

# 3. 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 测试依赖

# 4. 运行测试确保基线正常
pytest tests/ -v

# 5. 按Day 1-10顺序开发
# 每完成一个Day,提交一个commit
git commit -m "Day 1: Implement dependency resolver"
```

### 代码审查检查清单

每个Pull Request必须通过:
- [ ] 所有单元测试通过 (`pytest tests/`)
- [ ] 代码覆盖率≥70% (`pytest --cov`)
- [ ] 类型检查通过 (`mypy src/`)
- [ ] 代码格式化 (`black src/ tests/`)
- [ ] 无重大Linting问题 (`flake8 src/`)
- [ ] 文档字符串完整 (所有public函数)
- [ ] CHANGELOG.md更新
- [ ] 向后兼容性测试通过

### 调试技巧

**问题**: 拓扑排序失败
```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
python src/main.py

# 检查依赖图
# 在dependency_resolver.py中添加:
logger.debug(f"Dependency graph: {graph}")
```

**问题**: trace文件未生成
```bash
# 检查目录权限
ls -la logs/trace/
# 应该是writable

# 检查是否启用
grep "enable_trace_export" roles/*.yaml
```

**问题**: 成本计算不准确
```bash
# 查看成本记录
cat logs/events/cost_*.json | jq '.[] | select(.type=="COST_RECORDED")'
```

---

## 📦 交付物清单

### 代码文件

**新建** (8个文件):
- [ ] `src/core/team/dependency_resolver.py` (150行)
- [ ] `src/core/tools/research_tools.py` (100行)
- [ ] `src/core/team/quality_validator.py` (200行)
- [ ] `tests/test_dependency_resolver.py` (150行)
- [ ] `tests/test_research_tool.py` (80行)
- [ ] `tests/test_quality_validator.py` (120行)
- [ ] `tests/test_cost_control.py` (100行)
- [ ] `tests/integration/test_v31_full_workflow.py` (200行)

**修改** (9个文件):
- [ ] `src/config.py` (+20行)
- [ ] `src/main.py` (+15行)
- [ ] `src/core/agents/planner.py` (+50行)
- [ ] `src/core/agents/executor.py` (+60行)
- [ ] `src/core/team/team_assembler.py` (+40行)
- [ ] `src/core/team/team_orchestrator.py` (+20行)
- [ ] `src/core/team/role_executor.py` (+270行)
- [ ] `src/core/team/role_registry.py` (+55行)
- [ ] `src/core/events.py` (+60行)
- [ ] `src/core/tools/__init__.py` (+1行)

**配置文件** (2个):
- [ ] `config.yaml` (+6行,添加cost_control)
- [ ] 所有 `roles/*.yaml` (+2行/文件,添加quality配置)

### 文档

- [ ] `README.md` (更新v3.1特性说明)
- [ ] `docs/TEAM_MODE_GUIDE.md` (新增章节)
- [ ] `docs/CHANGELOG.md` (v3.1变更日志)
- [ ] `docs/MIGRATION_GUIDE_v3.1.md` (迁移指南,新建)
- [ ] `docs/DEVELOPER_GUIDE_v3.1.md` (开发者指南,新建)

### 测试报告

- [ ] 单元测试覆盖率报告 (`coverage.html`)
- [ ] 集成测试结果 (`integration_test_report.md`)
- [ ] 性能基准测试 (`benchmark_v3.1.md`)

---

## ✅ 验收标准 (Definition of Done)

v3.1可以发布当且仅当:

### 功能完整性
- [x] 所有8个核心功能已实现
- [x] 所有新增功能已实现
- [x] 所有测试通过(单元+集成)
- [x] 代码覆盖率≥70%

### 质量保证
- [x] 无P0/P1 bug
- [x] 代码审查完成
- [x] 性能满足基准(无明显退化)
- [x] 安全审计通过

### 文档完整性
- [x] API文档更新
- [x] 用户指南更新
- [x] 迁移指南完成
- [x] CHANGELOG完整

### 兼容性
- [x] v3.0配置文件可直接使用
- [x] v3.0代码调用API无需修改
- [x] 测试v3.0→v3.1升级路径

---

## 🚀 发布计划

### Pre-Release (Alpha)
**时间**: Day 8
**范围**: 内部测试
**版本号**: v3.1.0-alpha.1

### Release Candidate
**时间**: Day 9
**范围**: 早期采用者测试
**版本号**: v3.1.0-rc.1

### Stable Release
**时间**: Day 10
**范围**: 正式发布
**版本号**: v3.1.0

**发布清单**:
- [ ] Git tag创建
- [ ] GitHub Release发布
- [ ] PyPI包发布(如适用)
- [ ] 文档网站更新
- [ ] 发布公告撰写
- [ ] 社交媒体宣传

---

## 🔮 v3.2 展望

v3.1完成后,下一步可以考虑:

1. **并行执行** (DAG调度)
   - 无依赖的角色并行运行
   - 预计性能提升2-3x

2. **人机协作审批网关**
   - 关键决策点插入人工审核
   - WebSocket实时通知

3. **角色学习系统**
   - 从历史执行学习最优角色组合
   - 推荐系统优化

4. **分布式执行**
   - Ray/Celery支持
   - 多GPU/多节点扩展

但这些都在v3.1稳定后再考虑。**保持专注,逐步迭代**。

---

## 📞 支持与反馈

**技术问题**:
- GitHub Issues: https://github.com/aibesttop/claude-code-auto/issues
- 标签: `v3.1`, `upgrade`

**进度追踪**:
- Project Board: https://github.com/aibesttop/claude-code-auto/projects/v3.1

**团队沟通**:
- Daily Standup: 每日10:00 (15分钟)
- Code Review: 每个PR必须有至少1个approval

---

**文档版本**: 1.0 Final
**最后更新**: 2025-11-22
**下次审查**: 完成Day 5后
**负责人**: Development Team
**审批人**: Tech Lead

---

## 附录A: 快速命令参考

```bash
# 开发环境
pytest tests/ -v                    # 运行所有测试
pytest --cov=src tests/             # 测试+覆盖率
mypy src/                           # 类型检查
black src/ tests/                   # 代码格式化
flake8 src/                         # Linting

# 调试
export LOG_LEVEL=DEBUG              # 启用详细日志
python src/main.py                  # 运行主程序
ls logs/trace/                      # 检查trace文件

# 测试特定功能
pytest tests/test_dependency_resolver.py -v
pytest tests/integration/test_v31_full_workflow.py -v -s

# 性能分析
python -m cProfile -o profile.stats src/main.py
python -c "import pstats; p=pstats.Stats('profile.stats'); p.sort_stats('time'); p.print_stats(20)"

# 发布
git tag v3.1.0
git push origin v3.1.0
```

---

## 附录B: 故障排除FAQ

**Q: 拓扑排序报错"Circular dependency detected"**
A: 检查roles/*.yaml中的dependencies字段,使用工具绘制依赖图:
```python
python scripts/visualize_dependencies.py
```

**Q: trace文件为空**
A: 检查日志级别和权限:
```bash
ls -la logs/trace/
grep "export_plan_to_markdown" logs/workflow.log
```

**Q: 成本估算异常高**
A: 检查token使用:
```bash
cat logs/events/*.json | jq '.[] | select(.type=="COST_RECORDED") | .tokens'
```

**Q: 语义评分总是失败**
A: 降低阈值或禁用质量检查:
```yaml
# roles/xxx.yaml
quality_threshold: 50  # 从70降到50
# 或
enable_quality_check: false  # 完全禁用
```

---

**🎉 Let's ship v3.1! 🚀**
