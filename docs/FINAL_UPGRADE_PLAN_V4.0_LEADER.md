# Claude-Code-Auto v4.0 (Leader) 终极升级方案
## 从Team Mode到Leader模式的范式转变

**文档版本**: 1.0 Final
**创建日期**: 2025-01-22
**目标版本**: v4.0 (Leader - Dynamic Orchestration)
**前置要求**: v3.1 (已完成并修复所有bug)
**预计工期**: 3-4周
**风险等级**: 中

---

## 📋 执行摘要

### v3.1回顾 - 稳定的基础

✅ **已完成的核心能力**:
- 依赖拓扑排序 (`src/core/team/dependency_resolver.py`)
- Markdown跟踪日志 (`logs/trace/*.md`)
- 完整上下文传递 (智能摘要 + 文件保存)
- 每角色独立Planner (动态任务分解)
- 研究工具化 (`deep_research`, `quick_research`)
- 成本预算控制 (`CostTracker` with limits)
- 语义质量验证 (`SemanticQualityValidator`)
- 自适应验证规则 (基于任务复杂度)

✅ **已修复的Critical Bug** (2025-01-22):
- Bug #1: 循环导入错误
- Bug #2: ReAct步骤限制 + 工作目录不匹配
- Bug #3: Windows SDK启动失败
- Bug #4: 事件循环冲突

**v3.1状态**: 🟢 稳定,可投入生产

---

### v4.0目标 - 范式转变

**核心思想**: 从"静态角色流水线"进化到"智能领导者动态编排"

```
v3.1: User → TeamAssembler (一次性) → [Role1 → Role2 → Role3] → Done
                ↑ LLM选择角色,YAML定义工具

v4.0: User → Leader Agent (持续监控) → Dynamic Team
                ↑ 状态化编排,运行时资源注入

Leader Agent:
  ├─ 动态团队组建: 根据进度添加/移除角色
  ├─ 资源智能分配: 按需注入MCP服务器和技能提示词
  ├─ 实时监控干预: 失败时重规划,质量低时加强验证
  └─ 最终整合输出: 将所有角色成果整合为交付物
```

**类比现实团队**:
- v3.1 = 项目经理制定计划后离场
- v4.0 = 敏捷教练全程跟进并调整

---

## 🎯 v4.0 核心特性

### Feature 1: Leader Agent (领导者代理)

**职责**:
```python
class LeaderAgent:
    """
    Meta-level orchestration agent.
    Replaces static TeamAssembler with dynamic,stateful coordination.
    """

    def decompose_mission(self, goal: str) -> List[SubMission]:
        """分解用户目标为子任务"""

    def assemble_team(self, missions: List[SubMission]) -> List[Role]:
        """动态选择角色(可随进度调整)"""

    def inject_resources(self, role: Role, mission: SubMission) -> Role:
        """运行时注入工具和技能"""

    def monitor_execution(self, role: Role, result: Dict) -> Decision:
        """监控执行,决定:继续/重试/加强/终止"""

    def integrate_outputs(self, results: Dict[str, Any]) -> FinalDeliverable:
        """整合所有角色输出为最终交付物"""
```

**关键区别**:

| 能力 | v3.1 TeamAssembler | v4.0 Leader Agent |
|------|-------------------|-------------------|
| 角色选择 | 一次性LLM调用 | 动态调整(可中途增删) |
| 工具分配 | YAML静态定义 | 运行时智能注入 |
| 监控能力 | 无 | 实时监控+干预 |
| 失败处理 | 快速失败 | 重规划或加强 |
| 状态管理 | 无状态 | 状态化跟踪 |

---

### Feature 2: Resource Registry (资源注册表)

**作用**: 管理所有可用的工具、MCP服务器和技能提示词

```python
# src/core/resources/resource_registry.py
class ResourceRegistry:
    """
    Centralized registry for all available resources.
    """

    def __init__(self):
        self.mcp_servers: Dict[str, MCPServerConfig] = {}
        self.skill_prompts: Dict[str, SkillPrompt] = {}
        self.tools: Dict[str, Tool] = {}

    def register_mcp_server(self, name: str, config: MCPServerConfig):
        """注册MCP服务器(如Filesystem, Brave Search, Postgres等)"""

    def register_skill(self, name: str, prompt: SkillPrompt):
        """注册技能提示词(如'python_expert', 'market_analyst'等)"""

    def get_tools_for_mission(self, mission_type: str) -> List[Tool]:
        """根据任务类型返回推荐工具"""

    def get_skills_for_role(self, role_category: str) -> List[SkillPrompt]:
        """根据角色类别返回推荐技能"""


# 配置文件: resources/mcp_servers.yaml
mcp_servers:
  filesystem:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
    capabilities: [read_file, write_file, list_directory]

  brave_search:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-brave-search"]
    env:
      BRAVE_API_KEY: ${BRAVE_API_KEY}
    capabilities: [web_search, news_search]

  postgres:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-postgres", "postgresql://..."]
    capabilities: [query_database, execute_sql]


# 配置文件: resources/skill_prompts.yaml
skills:
  market_analyst:
    category: research
    prompt: |
      You are an expert market analyst with 10+ years experience in competitive
      intelligence and TAM analysis. Focus on data-driven insights and actionable
      recommendations.

  python_expert:
    category: engineering
    prompt: |
      You are a senior Python developer with expertise in clean architecture,
      type hints, pytest, and production best practices.

  seo_specialist:
    category: marketing
    prompt: |
      You are a technical SEO expert specializing in keyword research, on-page
      optimization, and Core Web Vitals.
```

**动态注入示例**:
```python
# Leader决策过程
mission = SubMission(type="market_research", goal="分析矿井工作App市场")
role = Role(name="Market-Researcher", category="research")

# Leader动态注入资源
resources = registry.get_tools_for_mission("market_research")
# → [web_search (from Brave), deep_research, web_fetch]

skills = registry.get_skills_for_role("research")
# → [market_analyst skill prompt]

# 注入到Executor
executor = ExecutorAgent(
    tools=resources,  # 动态工具列表
    persona_prompt=skills['market_analyst'].prompt,  # 动态技能
    work_dir=...
)
```

---

### Feature 3: Dynamic Resource Injection (动态资源注入)

**问题**: v3.1中工具是YAML静态配置,无法根据任务灵活调整

```yaml
# v3.1: roles/market_researcher.yaml
tools:
  - web_search
  - write_file
  - read_file
# 问题: 所有Market-Researcher任务都用相同工具,即使不需要
```

**v4.0解决方案**: Leader根据子任务动态分配

```python
# src/core/leader/leader_agent.py
class LeaderAgent:
    def inject_resources(
        self,
        role: Role,
        mission: SubMission,
        context: Dict[str, Any]
    ) -> ExecutorAgent:
        """
        根据任务类型和上下文动态注入资源
        """
        # 1. 分析任务需求
        task_analysis = self._analyze_task_requirements(mission)

        # 2. 选择MCP服务器
        mcp_servers = []
        if task_analysis.needs_web_research:
            mcp_servers.append(self.registry.get_mcp("brave_search"))
        if task_analysis.needs_file_ops:
            mcp_servers.append(self.registry.get_mcp("filesystem"))
        if task_analysis.needs_database:
            mcp_servers.append(self.registry.get_mcp("postgres"))

        # 3. 选择工具
        tools = self.registry.get_tools_for_mission(mission.type)

        # 4. 选择技能提示词
        skill_prompt = self.registry.get_skill_for_role(role.category)

        # 5. 创建定制化Executor
        executor = ExecutorAgent(
            mcp_servers=mcp_servers,  # 动态MCP
            tools=tools,              # 动态工具
            persona_prompt=skill_prompt.prompt,  # 动态技能
            work_dir=self.work_dir,
            model=self.model
        )

        logger.info(f"💉 Injected resources for {role.name}:")
        logger.info(f"   MCP Servers: {[s.name for s in mcp_servers]}")
        logger.info(f"   Tools: {[t.name for t in tools]}")
        logger.info(f"   Skill: {skill_prompt.name}")

        return executor


# 使用示例
mission1 = SubMission(
    type="market_research",
    goal="分析矿井App市场",
    requirements=["web_research", "competitor_analysis"]
)
# Leader注入: Brave Search MCP + deep_research tool + market_analyst skill

mission2 = SubMission(
    type="code_generation",
    goal="实现用户认证模块",
    requirements=["database_access", "file_writing"]
)
# Leader注入: Postgres MCP + Filesystem MCP + python_expert skill
```

**优势**:
- 🎯 **精准**: 只给需要的资源,避免工具过载
- 💰 **节省成本**: 减少不必要的MCP调用
- 🔒 **安全**: 限制Sandbox角色的资源访问
- 🧩 **灵活**: 同一角色在不同任务下用不同工具

---

### Feature 4: Monitoring & Intervention (监控与干预)

**问题**: v3.1执行后无法调整,失败就终止

**v4.0解决方案**: Leader实时监控并干预

```python
# src/core/leader/leader_agent.py
class LeaderAgent:
    def monitor_execution(
        self,
        role: Role,
        result: Dict[str, Any],
        iteration: int
    ) -> InterventionDecision:
        """
        监控角色执行,决定如何干预
        """
        # 1. 质量检查
        if result['validation_passed']:
            quality_score = self._assess_quality(result['outputs'])

            if quality_score >= 80:
                return InterventionDecision(
                    action="CONTINUE",
                    reason="High quality output"
                )
            elif quality_score >= 60:
                return InterventionDecision(
                    action="ENHANCE",
                    reason="Quality acceptable but can improve",
                    enhancements=[
                        "Add more specific examples",
                        "Include quantitative data"
                    ]
                )
            else:
                return InterventionDecision(
                    action="RETRY",
                    reason="Quality below threshold",
                    adjustments={
                        "加强提示词": self._get_enhancement_prompt(),
                        "增加研究轮数": 5,
                        "提高验证标准": True
                    }
                )

        # 2. 失败处理
        else:
            if iteration < self.max_retries:
                # 分析失败原因
                failure_analysis = self._analyze_failure(result['errors'])

                if failure_analysis.is_recoverable:
                    return InterventionDecision(
                        action="RETRY_WITH_ADJUSTMENT",
                        reason=f"Recoverable failure: {failure_analysis.root_cause}",
                        adjustments=failure_analysis.recommended_fixes
                    )
                else:
                    return InterventionDecision(
                        action="ESCALATE",
                        reason=f"Non-recoverable: {failure_analysis.root_cause}",
                        fallback_strategy="add_helper_role"
                    )
            else:
                return InterventionDecision(
                    action="TERMINATE",
                    reason="Max retries exceeded"
                )

    def _assess_quality(self, outputs: Dict[str, str]) -> float:
        """使用LLM评估输出质量"""
        # 调用SemanticQualityValidator (v3.1已有)
        validator = SemanticQualityValidator()
        scores = []

        for file, content in outputs.items():
            score = await validator.score_output(
                content=content,
                success_criteria=self.current_mission.success_criteria,
                file_type="markdown"
            )
            scores.append(score.overall_score)

        return sum(scores) / len(scores) if scores else 0.0


# 干预场景示例

# 场景1: 质量不足,加强重试
"""
Market-Researcher 第1次输出:
- 竞争对手分析: 只列了3个App,缺少详细对比
- 质量评分: 65/100

Leader决策:
→ ENHANCE: 添加提示词"请对每个竞争对手进行SWOT分析,并制作对比表格"
→ 增加deep_research轮数: 3 → 5
"""

# 场景2: 验证失败但可恢复
"""
AI-Native-Writer 第2次输出:
- 错误: Missing required file: docs/02-architecture.md

Leader分析:
→ 原因: 文件路径错误(写成了02-arch.md)
→ 可恢复: True
→ 决策: RETRY_WITH_ADJUSTMENT
→ 调整: 在提示词中明确列出8个必需文件的完整路径
"""

# 场景3: 无法恢复,启用帮助角色
"""
Architect 第5次输出:
- 错误: 缺少数据库设计经验

Leader决策:
→ ESCALATE: 添加Database-Expert辅助角色
→ 新流程: Architect (系统设计) → Database-Expert (数据库设计) → Architect (整合)
"""
```

**监控指标**:
```python
class ExecutionMetrics:
    role_name: str
    iteration: int
    quality_score: float
    validation_passed: bool
    execution_time_seconds: float
    token_usage: int
    cost_usd: float
    errors: List[str]
    warnings: List[str]

# 存储到: logs/metrics/{session_id}_metrics.json
```

---

### Feature 5: Final Integration (最终整合)

**作用**: Leader整合所有角色输出为统一交付物

```python
class LeaderAgent:
    async def integrate_outputs(
        self,
        results: Dict[str, RoleResult]
    ) -> FinalDeliverable:
        """
        整合所有角色成果为最终交付物
        """
        # 1. 收集所有输出文件
        all_files = {}
        for role_name, result in results.items():
            all_files.update(result['outputs'])

        # 2. 生成整合报告
        integration_report = await self._generate_integration_report(results)

        # 3. 质量检查
        final_quality = await self._assess_final_quality(all_files)

        # 4. 生成README和索引
        readme = self._generate_project_readme(all_files, integration_report)

        # 5. 打包交付物
        deliverable = FinalDeliverable(
            files=all_files,
            readme=readme,
            integration_report=integration_report,
            quality_score=final_quality,
            metadata={
                "session_id": self.session_id,
                "goal": self.goal,
                "roles_executed": list(results.keys()),
                "total_cost_usd": self.cost_tracker.get_session_cost(self.session_id),
                "execution_time_seconds": time.time() - self.start_time,
                "leader_interventions": len(self.intervention_history)
            }
        )

        # 6. 保存到work_dir
        deliverable.save_to(self.work_dir)

        logger.info(f"📦 Final deliverable created:")
        logger.info(f"   Total files: {len(all_files)}")
        logger.info(f"   Quality score: {final_quality:.1f}/100")
        logger.info(f"   Location: {self.work_dir}")

        return deliverable


# 生成的README.md示例
"""
# 矿井工作App开发完整文档

**生成时间**: 2025-01-22 17:30:45
**总体质量**: 87.5/100
**Leader干预次数**: 3
**总成本**: $2.35

## 📁 交付物清单

### 市场研究 (Market-Researcher)
- [market-research.md](./market-research.md) - 深度市场调研报告

### 产品文档 (AI-Native-Writer)
- [docs/00-project-context.md](./docs/00-project-context.md) - 项目背景
- [docs/01-requirements.md](./docs/01-requirements.md) - 需求规格
- [docs/02-architecture.md](./docs/02-architecture.md) - 系统架构
- [docs/03-implementation-guide.md](./docs/03-implementation-guide.md) - 实现指南
- [docs/04-quality-gates.md](./docs/04-quality-gates.md) - 质量门禁
- [docs/05-ai-prompt-template.md](./docs/05-ai-prompt-template.md) - AI提示词模板
- [docs/06-testing-strategy.md](./docs/06-testing-strategy.md) - 测试策略
- [docs/07-deployment-guide.md](./docs/07-deployment-guide.md) - 部署指南

### SEO策略 (SEO-Specialist)
- [seo-strategy.md](./seo-strategy.md) - SEO优化方案

## 🎯 执行摘要

本次任务由Leader Agent协调3个专业角色完成,历时45分钟,进行了3次质量干预:

1. **第1次干预** (Market-Researcher, 迭代2):
   - 原因: 竞争对手分析深度不足
   - 措施: 增加deep_research轮数,添加SWOT分析要求
   - 效果: 质量从65分提升到88分

2. **第2次干预** (AI-Native-Writer, 迭代3):
   - 原因: 遗漏docs/06-testing-strategy.md
   - 措施: 重新生成并强化文件清单验证
   - 效果: 完整性从87.5%提升到100%

3. **第3次干预** (SEO-Specialist, 迭代1):
   - 原因: 关键词研究数据缺乏
   - 措施: 注入Brave Search MCP,增加web_search调用
   - 效果: 质量从72分提升到85分

## 📊 质量指标

| 维度 | 得分 |
|------|------|
| 完整性 | 95/100 |
| 准确性 | 88/100 |
| 专业性 | 90/100 |
| 可执行性 | 82/100 |
| **总分** | **87.5/100** |

## 💰 成本分析

| 角色 | Token使用 | 成本 |
|------|----------|------|
| Market-Researcher | 45,230 | $0.68 |
| AI-Native-Writer | 89,450 | $1.34 |
| SEO-Specialist | 22,100 | $0.33 |
| **Total** | **156,780** | **$2.35** |

## 🚀 下一步建议

基于Leader分析,建议您:
1. 审阅market-research.md中的目标用户画像
2. 根据docs/01-requirements.md开始原型设计
3. 参考seo-strategy.md制定内容营销计划
"""
```

---

## 🏗️ 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         User Goal                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      Leader Agent                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Mission    │  │   Resource   │  │   Monitoring &   │  │
│  │ Decomposer   │  │   Injector   │  │  Intervention    │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Final Output Integrator                    │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────────────┘
                        │ (动态编排)
            ┌───────────┼───────────┐
            ▼           ▼           ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Role 1  │  │  Role 2  │  │  Role N  │
    │ Executor │  │ Executor │  │ Executor │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │              │
         │ (注入资源)   │              │
         ▼             ▼              ▼
┌────────────────────────────────────────────────────┐
│              Resource Registry                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │   MCP    │  │  Skills  │  │  Tool Registry   │ │
│  │ Servers  │  │ Prompts  │  │                  │ │
│  └──────────┘  └──────────┘  └──────────────────┘ │
└────────────────────────────────────────────────────┘
```

### 数据流

```
1. User提交Goal
   ↓
2. Leader.decompose_mission(goal) → [Mission1, Mission2, Mission3]
   ↓
3. Leader.assemble_team(missions) → [Role1, Role2, Role3]
   ↓
4. For each Role:
   ├─ Leader.inject_resources(role, mission) → ExecutorAgent (定制化)
   ├─ ExecutorAgent.execute_task(mission.goal) → Result
   ├─ Leader.monitor_execution(role, result) → Decision
   │  ├─ CONTINUE: 下一个角色
   │  ├─ RETRY: 重新执行
   │  ├─ ENHANCE: 加强后重试
   │  └─ ESCALATE: 添加辅助角色
   └─ Save result to context
   ↓
5. Leader.integrate_outputs(all_results) → FinalDeliverable
   ↓
6. Save to work_dir + Generate README
```

---

## 📁 文件结构

### 新增文件

```
src/
├── core/
│   ├── leader/                        # NEW v4.0
│   │   ├── __init__.py
│   │   ├── leader_agent.py           # Leader Agent主类(约400行)
│   │   ├── mission_decomposer.py     # 任务分解器(约150行)
│   │   ├── intervention_engine.py    # 干预决策引擎(约200行)
│   │   └── output_integrator.py      # 输出整合器(约150行)
│   │
│   ├── resources/                     # NEW v4.0
│   │   ├── __init__.py
│   │   ├── resource_registry.py      # 资源注册表(约250行)
│   │   ├── mcp_manager.py            # MCP服务器管理(约180行)
│   │   └── skill_manager.py          # 技能提示词管理(约120行)
│   │
│   └── team/                          # MODIFIED
│       ├── team_orchestrator.py      # 重构:委托给LeaderAgent
│       └── role_executor.py          # 修改:支持动态资源注入
│
├── resources/                         # NEW v4.0 配置
│   ├── mcp_servers.yaml              # MCP服务器定义
│   ├── skill_prompts.yaml            # 技能提示词库
│   └── tool_mappings.yaml            # 任务类型→工具映射
│
└── logs/
    ├── trace/                         # v3.1已有
    ├── metrics/                       # NEW v4.0
    │   └── {session_id}_metrics.json
    └── interventions/                 # NEW v4.0
        └── {session_id}_interventions.md
```

### 修改文件

```
src/main.py                           # 集成Leader模式
src/config.py                         # 添加leader配置
```

---

## 🛠️ 实现细节

### Phase 1: Leader Agent核心 (Week 1-2)

#### 1.1 LeaderAgent类

**文件**: `src/core/leader/leader_agent.py`

```python
"""
Leader Agent - Meta-level orchestration for dynamic team management.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import time

from src.core.leader.mission_decomposer import MissionDecomposer
from src.core.leader.intervention_engine import InterventionEngine, InterventionDecision
from src.core/leader.output_integrator import OutputIntegrator
from src.core.resources.resource_registry import ResourceRegistry
from src.core.team.role_registry import Role, RoleRegistry
from src.core.agents.executor import ExecutorAgent
from src.core.events import EventStore, CostTracker
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class SubMission:
    """子任务定义"""
    id: str
    type: str  # "market_research", "code_generation", "documentation", etc.
    goal: str
    requirements: List[str]
    success_criteria: List[str]
    dependencies: List[str] = None  # 依赖的其他子任务ID
    priority: int = 1
    estimated_cost_usd: float = 0.0


@dataclass
class ExecutionContext:
    """执行上下文"""
    session_id: str
    goal: str
    missions: List[SubMission]
    completed_missions: Dict[str, Any]
    active_roles: List[Role]
    total_cost_usd: float
    start_time: float
    intervention_count: int


class LeaderAgent:
    """
    Leader Agent - Dynamic team orchestrator.

    Responsibilities:
    1. Decompose user goal into sub-missions
    2. Dynamically assemble and adjust team
    3. Inject resources (MCP, tools, skills) per mission
    4. Monitor execution and intervene when needed
    5. Integrate final outputs
    """

    def __init__(
        self,
        work_dir: str,
        model: str = "sonnet",
        max_mission_retries: int = 3,
        quality_threshold: float = 70.0,
        budget_limit_usd: Optional[float] = None
    ):
        self.work_dir = work_dir
        self.model = model
        self.max_mission_retries = max_mission_retries
        self.quality_threshold = quality_threshold
        self.budget_limit_usd = budget_limit_usd

        # 初始化组件
        self.mission_decomposer = MissionDecomposer(model=model)
        self.intervention_engine = InterventionEngine(
            quality_threshold=quality_threshold,
            max_retries=max_mission_retries
        )
        self.output_integrator = OutputIntegrator(work_dir=work_dir)

        # 资源管理
        self.resource_registry = ResourceRegistry()
        self.role_registry = RoleRegistry()

        # 追踪
        self.event_store = EventStore()
        self.cost_tracker = CostTracker(max_budget_usd=budget_limit_usd)

        # 状态
        self.context: Optional[ExecutionContext] = None
        self.intervention_history: List[Dict] = []

    async def execute(self, goal: str, session_id: str) -> Dict[str, Any]:
        """
        主执行流程

        Args:
            goal: 用户目标
            session_id: 会话ID

        Returns:
            {
                "success": bool,
                "deliverable": FinalDeliverable,
                "metadata": {...}
            }
        """
        logger.info(f"🎯 Leader Agent启动")
        logger.info(f"   Goal: {goal}")
        logger.info(f"   Session: {session_id}")

        start_time = time.time()

        # Step 1: 分解任务
        logger.info(f"\n{'='*60}")
        logger.info(f"Step 1: Mission Decomposition")
        logger.info(f"{'='*60}")

        missions = await self.mission_decomposer.decompose(goal)
        logger.info(f"✅ Decomposed into {len(missions)} missions")
        for i, mission in enumerate(missions, 1):
            logger.info(f"   {i}. [{mission.type}] {mission.goal}")

        # 初始化执行上下文
        self.context = ExecutionContext(
            session_id=session_id,
            goal=goal,
            missions=missions,
            completed_missions={},
            active_roles=[],
            total_cost_usd=0.0,
            start_time=start_time,
            intervention_count=0
        )

        # Step 2: 执行各子任务
        for i, mission in enumerate(missions, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Step 2.{i}: Execute Mission - {mission.type}")
            logger.info(f"{'='*60}")

            result = await self._execute_mission(mission)

            if result['success']:
                self.context.completed_missions[mission.id] = result
                logger.info(f"✅ Mission {mission.id} completed")
            else:
                logger.error(f"❌ Mission {mission.id} failed after retries")
                return {
                    "success": False,
                    "failed_mission": mission.id,
                    "error": result.get('error'),
                    "metadata": self._get_metadata()
                }

        # Step 3: 整合输出
        logger.info(f"\n{'='*60}")
        logger.info(f"Step 3: Output Integration")
        logger.info(f"{'='*60}")

        deliverable = await self.output_integrator.integrate(
            results=self.context.completed_missions,
            goal=goal,
            metadata=self._get_metadata()
        )

        logger.info(f"✅ Leader Agent完成")
        logger.info(f"   Total missions: {len(missions)}")
        logger.info(f"   Interventions: {self.context.intervention_count}")
        logger.info(f"   Total cost: ${self.context.total_cost_usd:.2f}")
        logger.info(f"   Duration: {time.time() - start_time:.1f}s")

        return {
            "success": True,
            "deliverable": deliverable,
            "metadata": self._get_metadata()
        }

    async def _execute_mission(self, mission: SubMission) -> Dict[str, Any]:
        """
        执行单个子任务(带重试和干预)
        """
        iteration = 0

        while iteration < self.max_mission_retries:
            iteration += 1
            logger.info(f"🔄 Mission {mission.id} - Iteration {iteration}/{self.max_mission_retries}")

            # 1. 选择角色
            role = await self._select_role_for_mission(mission)
            logger.info(f"   Selected role: {role.name}")

            # 2. 动态注入资源
            executor = await self._inject_resources(role, mission)
            logger.info(f"   Resources injected")

            # 3. 执行
            logger.info(f"   Executing...")
            result = await executor.execute_task(mission.goal)

            # 4. 监控和干预
            decision = await self.intervention_engine.decide(
                mission=mission,
                role=role,
                result=result,
                iteration=iteration,
                context=self.context
            )

            logger.info(f"   Intervention: {decision.action.value}")

            # 记录干预
            self._record_intervention(mission, role, decision)

            # 5. 根据决策行动
            if decision.action == InterventionAction.CONTINUE:
                return {
                    "success": True,
                    "mission_id": mission.id,
                    "role": role.name,
                    "result": result,
                    "iterations": iteration
                }

            elif decision.action == InterventionAction.RETRY:
                logger.info(f"   Reason: {decision.reason}")
                continue

            elif decision.action == InterventionAction.ENHANCE:
                logger.info(f"   Enhancements: {decision.enhancements}")
                # 应用增强后重试
                mission = self._apply_enhancements(mission, decision.enhancements)
                continue

            elif decision.action == InterventionAction.ESCALATE:
                logger.warning(f"   Escalating: {decision.reason}")
                # 添加辅助角色
                helper_result = await self._execute_with_helper(mission, decision)
                if helper_result['success']:
                    return helper_result
                else:
                    continue

            else:  # TERMINATE
                return {
                    "success": False,
                    "error": decision.reason
                }

        # 超过最大重试次数
        return {
            "success": False,
            "error": f"Max retries ({self.max_mission_retries}) exceeded"
        }

    async def _select_role_for_mission(self, mission: SubMission) -> Role:
        """根据任务类型选择角色"""
        # 映射: 任务类型 → 角色名称
        type_to_role = {
            "market_research": "Market-Researcher",
            "documentation": "AI-Native-Writer",
            "code_generation": "AI-Native-Developer",
            "architecture_design": "Architect",
            "seo_strategy": "SEO-Specialist"
        }

        role_name = type_to_role.get(mission.type)
        if not role_name:
            # 使用LLM动态选择
            role_name = await self._llm_select_role(mission)

        role = self.role_registry.get_role(role_name)
        return role

    async def _inject_resources(
        self,
        role: Role,
        mission: SubMission
    ) -> ExecutorAgent:
        """动态注入资源"""
        # 1. 获取MCP服务器
        mcp_servers = self.resource_registry.get_mcp_for_mission(mission.type)

        # 2. 获取工具
        tools = self.resource_registry.get_tools_for_mission(mission.type)

        # 3. 获取技能提示词
        skill_prompt = self.resource_registry.get_skill_for_role(role.category)

        # 4. 创建定制化Executor
        executor = ExecutorAgent(
            work_dir=self.work_dir,
            model=self.model,
            persona_prompt=skill_prompt.prompt if skill_prompt else role.persona,
            timeout_seconds=300,
            permission_mode="bypassPermissions"
        )

        # 注入MCP服务器(如果支持)
        # TODO: 需要ExecutorAgent支持动态MCP注入

        logger.info(f"💉 Resources for {role.name}:")
        logger.info(f"   MCP: {[s.name for s in mcp_servers]}")
        logger.info(f"   Tools: {[t.name for t in tools]}")
        logger.info(f"   Skill: {skill_prompt.name if skill_prompt else 'default'}")

        return executor

    def _record_intervention(
        self,
        mission: SubMission,
        role: Role,
        decision: InterventionDecision
    ):
        """记录干预历史"""
        self.context.intervention_count += 1

        intervention = {
            "id": self.context.intervention_count,
            "mission_id": mission.id,
            "role": role.name,
            "action": decision.action.value,
            "reason": decision.reason,
            "enhancements": decision.enhancements,
            "timestamp": time.time()
        }

        self.intervention_history.append(intervention)

        # 保存到文件
        self._save_intervention_log()

    def _get_metadata(self) -> Dict[str, Any]:
        """获取元数据"""
        return {
            "session_id": self.context.session_id,
            "goal": self.context.goal,
            "total_missions": len(self.context.missions),
            "completed_missions": len(self.context.completed_missions),
            "total_cost_usd": self.context.total_cost_usd,
            "execution_time_seconds": time.time() - self.context.start_time,
            "intervention_count": self.context.intervention_count,
            "model": self.model
        }
```

---

### Phase 2: Resource Registry (Week 2)

#### 2.1 ResourceRegistry类

**文件**: `src/core/resources/resource_registry.py`

```python
"""
Resource Registry - Centralized management of MCP servers, tools, and skills.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class MCPServerConfig:
    """MCP服务器配置"""
    name: str
    command: str
    args: List[str]
    env: Dict[str, str] = None
    capabilities: List[str] = None


@dataclass
class SkillPrompt:
    """技能提示词"""
    name: str
    category: str
    prompt: str
    tags: List[str] = None


@dataclass
class ToolMapping:
    """任务类型→工具映射"""
    mission_type: str
    required_tools: List[str]
    optional_tools: List[str]
    mcp_servers: List[str]


class ResourceRegistry:
    """
    资源注册表 - 管理所有可用资源
    """

    def __init__(self, config_dir: str = "resources"):
        self.config_dir = Path(config_dir)

        # 资源存储
        self.mcp_servers: Dict[str, MCPServerConfig] = {}
        self.skills: Dict[str, SkillPrompt] = {}
        self.tool_mappings: Dict[str, ToolMapping] = {}

        # 加载配置
        self._load_mcp_servers()
        self._load_skills()
        self._load_tool_mappings()

    def _load_mcp_servers(self):
        """加载MCP服务器配置"""
        config_file = self.config_dir / "mcp_servers.yaml"
        if not config_file.exists():
            logger.warning(f"MCP config not found: {config_file}")
            return

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for name, config in data.get('mcp_servers', {}).items():
            self.mcp_servers[name] = MCPServerConfig(
                name=name,
                command=config['command'],
                args=config['args'],
                env=config.get('env', {}),
                capabilities=config.get('capabilities', [])
            )

        logger.info(f"✅ Loaded {len(self.mcp_servers)} MCP servers")

    def _load_skills(self):
        """加载技能提示词"""
        config_file = self.config_dir / "skill_prompts.yaml"
        if not config_file.exists():
            logger.warning(f"Skills config not found: {config_file}")
            return

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for name, config in data.get('skills', {}).items():
            self.skills[name] = SkillPrompt(
                name=name,
                category=config['category'],
                prompt=config['prompt'],
                tags=config.get('tags', [])
            )

        logger.info(f"✅ Loaded {len(self.skills)} skill prompts")

    def _load_tool_mappings(self):
        """加载工具映射"""
        config_file = self.config_dir / "tool_mappings.yaml"
        if not config_file.exists():
            logger.warning(f"Tool mappings not found: {config_file}")
            return

        with open(config_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for mission_type, config in data.get('mappings', {}).items():
            self.tool_mappings[mission_type] = ToolMapping(
                mission_type=mission_type,
                required_tools=config.get('required_tools', []),
                optional_tools=config.get('optional_tools', []),
                mcp_servers=config.get('mcp_servers', [])
            )

        logger.info(f"✅ Loaded {len(self.tool_mappings)} tool mappings")

    def get_mcp_for_mission(self, mission_type: str) -> List[MCPServerConfig]:
        """获取任务所需的MCP服务器"""
        mapping = self.tool_mappings.get(mission_type)
        if not mapping:
            return []

        servers = []
        for server_name in mapping.mcp_servers:
            if server_name in self.mcp_servers:
                servers.append(self.mcp_servers[server_name])

        return servers

    def get_tools_for_mission(self, mission_type: str) -> List[str]:
        """获取任务所需的工具"""
        mapping = self.tool_mappings.get(mission_type)
        if not mapping:
            return []

        return mapping.required_tools + mapping.optional_tools

    def get_skill_for_role(self, role_category: str) -> Optional[SkillPrompt]:
        """获取角色对应的技能提示词"""
        for skill in self.skills.values():
            if skill.category == role_category:
                return skill
        return None
```

---

### Phase 3: Configuration Files (Week 2)

#### 3.1 MCP Servers配置

**文件**: `resources/mcp_servers.yaml`

```yaml
# MCP服务器配置
# 定义所有可用的MCP服务器及其启动参数

mcp_servers:
  # 文件系统访问
  filesystem:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "./workspace"
    capabilities:
      - read_file
      - write_file
      - list_directory
      - create_directory
      - delete_file
    description: "本地文件系统访问"

  # Brave搜索引擎
  brave_search:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-brave-search"
    env:
      BRAVE_API_KEY: ${BRAVE_API_KEY}
    capabilities:
      - web_search
      - news_search
      - local_search
    description: "Brave搜索引擎API"

  # PostgreSQL数据库
  postgres:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-postgres"
      - "postgresql://localhost/mydb"
    env:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    capabilities:
      - query_database
      - execute_sql
      - list_tables
      - describe_table
    description: "PostgreSQL数据库访问"

  # Git版本控制
  git:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-git"
    capabilities:
      - git_status
      - git_commit
      - git_log
      - git_diff
    description: "Git版本控制操作"

  # Slack通知
  slack:
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-slack"
    env:
      SLACK_BOT_TOKEN: ${SLACK_BOT_TOKEN}
    capabilities:
      - send_message
      - list_channels
      - read_messages
    description: "Slack消息发送"
```

#### 3.2 Skill Prompts配置

**文件**: `resources/skill_prompts.yaml`

```yaml
# 技能提示词库
# 为不同角色类别提供专业化的提示词

skills:
  # 市场分析专家
  market_analyst:
    category: research
    prompt: |
      You are an expert market analyst with 10+ years of experience in:
      - Competitive intelligence and SWOT analysis
      - TAM/SAM/SOM market sizing methodology
      - User persona development and segmentation
      - Product-market fit validation

      Your analysis is always:
      - Data-driven with quantitative metrics
      - Structured with clear frameworks (Porter's Five Forces, PESTEL, etc.)
      - Actionable with specific recommendations
      - Comprehensive covering market trends, competitors, and opportunities
    tags:
      - research
      - market_analysis
      - competitive_intelligence

  # Python专家
  python_expert:
    category: engineering
    prompt: |
      You are a senior Python developer with expertise in:
      - Clean architecture and design patterns (SOLID, DDD, Hexagonal)
      - Type hints and static type checking (mypy, pyright)
      - Testing (pytest, unittest, mocking, fixtures, 80%+ coverage)
      - Production best practices (logging, error handling, configuration management)

      Your code always:
      - Follows PEP 8 style guide
      - Includes comprehensive docstrings (Google style)
      - Has type annotations for all function signatures
      - Is tested with unit and integration tests
      - Handles errors gracefully with proper logging
    tags:
      - engineering
      - python
      - backend

  # SEO专家
  seo_specialist:
    category: marketing
    prompt: |
      You are a technical SEO expert with expertise in:
      - Keyword research (search volume, competition, intent analysis)
      - On-page optimization (title tags, meta descriptions, headers, schema markup)
      - Technical SEO (site speed, Core Web Vitals, crawlability, mobile-first)
      - Content strategy and topic clusters
      - Link building and backlink analysis

      Your recommendations are:
      - Based on current SEO best practices (2024+)
      - Measurable with clear KPIs (CTR, impressions, rankings)
      - Prioritized by impact and effort (quick wins vs long-term)
      - Tool-specific when relevant (Google Search Console, Ahrefs, Semrush)
    tags:
      - marketing
      - seo
      - content_strategy

  # 架构师
  system_architect:
    category: engineering
    prompt: |
      You are a senior software architect with expertise in:
      - System design and scalability patterns (microservices, event-driven, CQRS)
      - Database design (SQL vs NoSQL, normalization, indexing, sharding)
      - API design (RESTful, GraphQL, gRPC, versioning, authentication)
      - Cloud architecture (AWS, GCP, Azure, serverless, containers)
      - Security best practices (OWASP Top 10, OAuth2, encryption)

      Your architecture designs:
      - Start with requirements and constraints
      - Use industry-standard diagrams (C4 model, UML, sequence diagrams)
      - Address non-functional requirements (performance, security, scalability)
      - Include trade-off analysis for major decisions
      - Provide implementation roadmap
    tags:
      - engineering
      - architecture
      - system_design

  # 文档撰写专家
  technical_writer:
    category: documentation
    prompt: |
      You are an expert technical writer specializing in:
      - Developer documentation (API references, guides, tutorials)
      - AI-Native documentation format (context, requirements, architecture, implementation)
      - Clear, concise writing with examples
      - Markdown formatting and structure

      Your documentation:
      - Follows a clear hierarchy (H1→H2→H3)
      - Includes code examples with syntax highlighting
      - Uses tables for comparison and specifications
      - Has diagrams where helpful (mermaid, ASCII art)
      - Is complete with no [TODO] or [PLACEHOLDER] markers
    tags:
      - documentation
      - technical_writing
      - ai_native
```

#### 3.3 Tool Mappings配置

**文件**: `resources/tool_mappings.yaml`

```yaml
# 任务类型→工具/MCP映射
# 定义每种任务需要哪些资源

mappings:
  # 市场调研任务
  market_research:
    required_tools:
      - web_search
      - deep_research
      - write_file
    optional_tools:
      - web_fetch
      - quick_research
    mcp_servers:
      - brave_search
      - filesystem

  # 文档编写任务
  documentation:
    required_tools:
      - write_file
      - read_file
      - list_dir
    optional_tools:
      - web_search
    mcp_servers:
      - filesystem

  # 代码生成任务
  code_generation:
    required_tools:
      - write_file
      - read_file
      - run_tests
    optional_tools:
      - git_commit
      - lint_code
    mcp_servers:
      - filesystem
      - git

  # 架构设计任务
  architecture_design:
    required_tools:
      - write_file
      - read_file
    optional_tools:
      - web_search
      - diagram_generator
    mcp_servers:
      - filesystem

  # SEO策略任务
  seo_strategy:
    required_tools:
      - web_search
      - write_file
    optional_tools:
      - web_fetch
      - keyword_analyzer
    mcp_servers:
      - brave_search
      - filesystem

  # 数据库设计任务
  database_design:
    required_tools:
      - query_database
      - write_file
    optional_tools:
      - execute_sql
      - generate_erd
    mcp_servers:
      - postgres
      - filesystem
```

---

## 📊 实施计划

### Week 1: Leader核心 + Resource Registry

**Day 1-2**: Leader Agent框架
- [ ] `leader_agent.py`: 主类和执行流程
- [ ] `mission_decomposer.py`: 任务分解器
- [ ] 单元测试

**Day 3-4**: Resource Registry
- [ ] `resource_registry.py`: 资源注册表
- [ ] `mcp_servers.yaml`: MCP配置
- [ ] `skill_prompts.yaml`: 技能配置
- [ ] `tool_mappings.yaml`: 工具映射

**Day 5**: 集成测试
- [ ] Leader + Registry集成
- [ ] 动态资源注入测试

---

### Week 2: Intervention Engine + Integration

**Day 1-2**: Intervention Engine
- [ ] `intervention_engine.py`: 干预决策引擎
- [ ] 质量评估逻辑
- [ ] 失败分析和恢复策略

**Day 3-4**: Output Integrator
- [ ] `output_integrator.py`: 输出整合器
- [ ] README生成
- [ ] 质量报告生成

**Day 5**: 端到端测试
- [ ] 完整流程测试
- [ ] Bug修复

---

### Week 3: 主流程集成 + 文档

**Day 1-2**: main.py集成
- [ ] 修改`src/main.py`支持Leader模式
- [ ] config.yaml添加leader配置
- [ ] 向后兼容性测试

**Day 3-4**: 文档
- [ ] 更新TEAM_MODE_GUIDE.md
- [ ] 创建LEADER_MODE_GUIDE.md
- [ ] API文档

**Day 5**: 发布准备
- [ ] 性能测试
- [ ] 安全审计
- [ ] 发布notes

---

### Week 4: 生产验证 + 优化

**Day 1-3**: 生产测试
- [ ] 真实场景测试(矿井App, 其他)
- [ ] Bug修复
- [ ] 性能优化

**Day 4-5**: 最终准备
- [ ] 代码审查
- [ ] 文档完善
- [ ] 发布v4.0

---

## ✅ 验收标准

### Functional Requirements

- [ ] **FR1**: Leader能分解复杂目标为子任务
- [ ] **FR2**: 动态资源注入功能正常
- [ ] **FR3**: 监控和干预机制工作
- [ ] **FR4**: 最终输出整合完整
- [ ] **FR5**: 成本追踪准确
- [ ] **FR6**: 向后兼容v3.1

### Quality Gates

- [ ] **QG1**: 单元测试覆盖率 ≥ 80%
- [ ] **QG2**: 所有Critical bug已修复
- [ ] **QG3**: 性能测试通过(不慢于v3.1)
- [ ] **QG4**: 文档完整且准确
- [ ] **QG5**: 生产环境测试成功

### Success Metrics

- [ ] **SM1**: 干预成功率 ≥ 70%
- [ ] **SM2**: 任务完成质量 ≥ 75分
- [ ] **SM3**: 成本预测准确度 ± 20%
- [ ] **SM4**: 用户满意度 ≥ 4/5

---

## 🚀 后续路线图

### v4.1 (Sandbox Security) - Q2 2025

- Docker隔离环境
- 网络隔离和资源限制
- 输入/输出验证

### v4.2 (Parallel Execution) - Q3 2025

- 并行角色执行
- 依赖图并行调度
- 资源竞争解决

### v4.3 (Learning & Optimization) - Q4 2025

- 历史数据分析
- 自动策略优化
- 知识库积累

---

## 📝 总结

v4.0(Leader)代表了从"静态流水线"到"智能编排"的范式转变:

**v3.1**: "配置好就运行,成功或失败"
**v4.0**: "持续监控,动态调整,确保成功"

这个升级方案:
- ✅ 基于稳定的v3.1基础
- ✅ 清晰的实施路径(3-4周)
- ✅ 可立即执行的详细设计
- ✅ 完整的验收标准
- ✅ 未来扩展性强

**立即开始**: 从Week 1 Day 1的Leader Agent框架开始! 🎯
