# Leader Mode Guide (v4.0)

**版本**: v4.0
**状态**: ✅ Production Ready
**创建日期**: 2025-01-22

---

## 📋 概述

Leader Mode是v4.0引入的全新智能编排系统,代表了从"静态流水线"到"动态智能编排"的范式转变。

### v3.1 vs v4.0

| 特性 | v3.1 Team Mode | v4.0 Leader Mode |
|------|---------------|------------------|
| 角色选择 | 一次性LLM调用 | 动态任务分解+智能选择 |
| 工具分配 | YAML静态配置 | 运行时资源注入 |
| 监控能力 | 无 | 实时监控+智能干预 |
| 失败处理 | 快速失败 | 多策略恢复 |
| 状态管理 | 无状态 | 全程状态追踪 |
| 输出整合 | 分散文件 | 统一交付物 |

---

## 🚀 快速开始

### 1. 启用Leader Mode

编辑`config.yaml`:

```yaml
# Leader Agent (v4.0) - Dynamic orchestration
leader:
  enabled: true  # 改为true
  max_mission_retries: 3
  quality_threshold: 70.0
  enable_intervention: true
  resource_config_dir: "resources"
```

### 2. 配置任务目标

```yaml
task:
  goal: "创建一个矿井工作App的完整开发文档"
  initial_prompt: ""  # Leader mode不需要initial_prompt
```

### 3. 运行

```bash
python src/main.py
```

### 4. 观察日志

Leader mode启动后,你会看到:

```
🎯 Leader Mode Activated (v4.0)
Goal: 创建一个矿井工作App的完整开发文档

======================================================================
📋 Step 1: Mission Decomposition
======================================================================
✅ Created 3 missions
   1. [market_research] 完成深度市场调研...
   2. [documentation] 生成AI-Native开发文档...
   3. [seo_strategy] 制定SEO优化策略...

======================================================================
🚀 Step 2.1: Execute Mission 'mission_1'
======================================================================
Type: market_research
Goal: 完成深度市场调研...
🔄 Iteration 1/3
   👤 Selected role: Market-Researcher
   🏃 Executing...
   🧠 Intervention: continue
      Reason: Mission completed successfully
✅ Mission 'mission_1' completed

...

======================================================================
📦 Step 3: Output Integration
======================================================================
📦 Deliverable saved: demo_act/session_xyz_deliverable.json

🎉 LEADER AGENT - Execution Complete
Total missions: 3
Completed: 3
Interventions: 5
Cost: $2.35
Duration: 345.2s
```

---

## 🎯 核心特性

### 1. 动态任务分解

Leader自动将复杂目标分解为可执行的子任务:

```python
Goal: "创建矿井App的完整文档"

↓ Leader分解 ↓

Mission 1: [market_research]
  - 目标: 分析矿井工作市场
  - 成功标准: 识别3+用户群体,分析5+竞争对手

Mission 2: [documentation]
  - 目标: 生成8份AI-Native文档
  - 依赖: Mission 1
  - 成功标准: 所有8个文件存在且完整

Mission 3: [seo_strategy]
  - 目标: 制定SEO优化方案
  - 依赖: Mission 1, Mission 2
  - 成功标准: 包含关键词研究和技术SEO建议
```

### 2. 智能资源注入

根据任务类型动态分配资源:

```python
# Mission: market_research
注入资源:
  - MCP: brave_search (web搜索)
  - MCP: filesystem (文件操作)
  - Tools: [web_search, deep_research, write_file]
  - Skill: market_analyst (专业提示词)

# Mission: code_generation
注入资源:
  - MCP: filesystem
  - MCP: git (版本控制)
  - Tools: [write_file, read_file]
  - Skill: python_expert
```

### 3. 监控和干预

Leader实时监控执行并智能决策:

```python
执行结果 → Leader评估 → 干预决策

✅ 质量优秀 (>80分)
   → CONTINUE: 继续下一个任务

🟡 质量可接受 (60-80分)
   → ENHANCE: 添加增强提示词重试

🟠 验证失败但可恢复
   → RETRY: 调整后重新执行

🔴 无法恢复
   → ESCALATE: 添加辅助角色

⛔ 超过重试次数
   → TERMINATE: 终止并报告
```

**实际案例**:

```
Mission: Market Research
Iteration 1:
  - 输出: 竞争对手分析(只有3个)
  - 质量评分: 65/100
  - Leader决策: ENHANCE
  - 调整: 添加"请对每个竞争对手进行SWOT分析"

Iteration 2:
  - 输出: 竞争对手分析(5个,含SWOT)
  - 质量评分: 88/100
  - Leader决策: CONTINUE ✅
```

### 4. 输出整合

所有任务完成后,Leader生成统一交付物:

```
demo_act/
├── session_xyz_deliverable.json  # 完整交付物
├── market-research.md             # Mission 1输出
├── docs/                          # Mission 2输出
│   ├── 00-project-context.md
│   ├── 01-requirements.md
│   └── ...
└── seo-strategy.md                # Mission 3输出

logs/
└── interventions/
    └── session_xyz_interventions.md  # 干预历史
```

**deliverable.json结构**:

```json
{
  "goal": "创建矿井App的完整文档",
  "session_id": "xyz",
  "missions": {
    "mission_1": {
      "type": "market_research",
      "role": "Market-Researcher",
      "outputs": {
        "market-research.md": "..."
      },
      "iterations": 2
    },
    ...
  },
  "summary": {
    "total_missions": 3,
    "completed_missions": 3,
    "total_cost_usd": 2.35,
    "total_interventions": 5,
    "duration_seconds": 345.2
  }
}
```

---

## 🛠️ 配置详解

### leader配置

```yaml
leader:
  # 启用Leader模式
  enabled: true

  # 每个任务最大重试次数 (1-10)
  max_mission_retries: 3

  # 最低质量分数 (0-100)
  # 低于此分数会触发干预
  quality_threshold: 70.0

  # 启用智能干预
  # false: 只记录不干预
  enable_intervention: true

  # 资源配置目录
  resource_config_dir: "resources"
```

### 资源配置 (resources/)

#### mcp_servers.yaml - MCP服务器定义

```yaml
mcp_servers:
  brave_search:  # 搜索引擎
    command: npx
    args: ["-y", "@modelcontextprotocol/server-brave-search"]
    env:
      BRAVE_API_KEY: "${BRAVE_API_KEY}"
    capabilities: [web_search, news_search]

  filesystem:  # 文件系统
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
    capabilities: [read_file, write_file, list_directory]
```

#### skill_prompts.yaml - 专业技能提示词

```yaml
skills:
  market_analyst:  # 市场分析师
    category: research
    prompt: |
      You are an expert market analyst with 10+ years experience...
      Your analysis is data-driven, structured, and actionable.
    tags: [research, market_analysis]

  python_expert:  # Python专家
    category: engineering
    prompt: |
      You are a senior Python developer...
      Your code follows PEP 8 and includes comprehensive tests.
    tags: [engineering, python]
```

#### tool_mappings.yaml - 任务→工具映射

```yaml
mappings:
  market_research:  # 市场调研任务
    required_tools:
      - web_search
      - deep_research
      - write_file
    optional_tools:
      - web_fetch
    mcp_servers:
      - brave_search
      - filesystem

  documentation:  # 文档编写任务
    required_tools:
      - write_file
      - read_file
    mcp_servers:
      - filesystem
```

---

## 📊 监控和日志

### 干预历史

Leader记录所有干预决策:

```markdown
# Leader Interventions - Session abc123

**Goal**: 创建矿井App文档
**Total Interventions**: 5

---

## Intervention #1

- **Mission**: mission_1 (market_research)
- **Role**: Market-Researcher
- **Iteration**: 2
- **Action**: enhance
- **Reason**: Quality below threshold (65/100)
- **Time**: 2025-01-22 16:30:15

---

## Intervention #2

- **Mission**: mission_2 (documentation)
- **Role**: AI-Native-Writer
- **Iteration**: 3
- **Action**: retry
- **Reason**: Validation failed: Missing file: docs/06-testing-strategy.md
- **Time**: 2025-01-22 16:35:42

...
```

### 成本追踪

```
💰 Total Cost: $2.35
   Mission 1 (market_research): $0.68
   Mission 2 (documentation): $1.34
   Mission 3 (seo_strategy): $0.33
```

---

## 🎓 最佳实践

### 1. 清晰的目标描述

**❌ 不好**:
```yaml
goal: "做个App"
```

**✅ 好**:
```yaml
goal: "为矿井工作场景创建App的完整开发文档,包括市场调研、需求分析、架构设计和SEO策略"
```

### 2. 合理的重试次数

- **简单任务** (文档生成): `max_mission_retries: 2`
- **中等复杂** (市场调研): `max_mission_retries: 3`
- **复杂任务** (代码生成): `max_mission_retries: 5`

### 3. 质量阈值设置

- **宽松** (快速迭代): `quality_threshold: 60.0`
- **标准** (平衡质量和速度): `quality_threshold: 70.0`
- **严格** (高质量要求): `quality_threshold: 85.0`

### 4. 成本控制

```yaml
cost_control:
  enabled: true
  max_budget_usd: 5.0
  warning_threshold: 0.8
```

### 5. 自定义资源

添加新的MCP服务器:

```yaml
# resources/mcp_servers.yaml
mcp_servers:
  my_custom_server:
    command: node
    args: ["./my-server.js"]
    capabilities: [custom_tool]
```

添加新的技能:

```yaml
# resources/skill_prompts.yaml
skills:
  data_scientist:
    category: analytics
    prompt: |
      You are an expert data scientist...
```

添加新的任务类型:

```yaml
# resources/tool_mappings.yaml
mappings:
  data_analysis:
    required_tools: [query_database, write_file]
    mcp_servers: [postgres, filesystem]
```

---

## 🔧 故障排除

### Q: Leader mode不启动

**A**: 检查配置

```bash
# 确认leader.enabled = true
grep -A 5 "leader:" config.yaml

# 检查导入
python -c "from src.core.leader.leader_agent import LeaderAgent; print('OK')"
```

### Q: Mission分解失败

**A**: 查看日志

```bash
# 检查decomposition日志
tail -n 100 logs/claude-code-auto.log | grep "decompose"
```

可能原因:
- Claude API超时 → 增加`claude.timeout_seconds`
- 目标过于复杂 → 简化goal描述

### Q: 所有mission都失败

**A**: 检查role配置

```bash
# 确认roles/目录存在
ls -la roles/

# 检查是否有role定义
ls roles/*.yaml
```

### Q: 成本超支

**A**: 启用成本控制

```yaml
cost_control:
  enabled: true
  max_budget_usd: 3.0
  auto_stop_on_exceed: true
```

---

## 📖 示例场景

### 场景1: App产品文档生成

```yaml
task:
  goal: "创建矿井安全监控App的完整产品文档"

leader:
  enabled: true
  max_mission_retries: 3
  quality_threshold: 75.0
```

**预期输出**:
- market-research.md (市场分析)
- docs/01-requirements.md (需求文档)
- docs/02-architecture.md (架构设计)
- seo-strategy.md (SEO方案)

### 场景2: 代码生成

```yaml
task:
  goal: "实现一个Python用户认证模块,包含单元测试"

leader:
  enabled: true
  max_mission_retries: 5  # 代码生成可能需要更多重试
```

**预期输出**:
- src/auth.py (认证模块)
- tests/test_auth.py (单元测试)
- README.md (使用文档)

### 场景3: 研究报告

```yaml
task:
  goal: "分析AI Agent市场的最新趋势和竞争格局"

leader:
  enabled: true
  quality_threshold: 80.0  # 研究报告要求更高质量
```

**预期输出**:
- market-trends-analysis.md (趋势分析)
- competitive-landscape.md (竞争格局)
- recommendations.md (战略建议)

---

## 🚀 下一步

### 立即尝试

1. 启用Leader mode
2. 设置一个简单目标
3. 观察执行过程
4. 查看干预历史
5. 分析交付物

### 高级用法

- [自定义MCP服务器](./MCP_SERVER_GUIDE.md)
- [编写技能提示词](./SKILL_PROMPT_GUIDE.md)
- [任务类型扩展](./MISSION_TYPE_GUIDE.md)

### 深入学习

- [Leader Agent架构](./FINAL_UPGRADE_PLAN_V4.0_LEADER.md)
- [干预策略详解](./INTERVENTION_STRATEGIES.md)
- [质量评估机制](./QUALITY_ASSESSMENT.md)

---

**版本历史**:
- v4.0 (2025-01-22): Leader Mode首次发布
- v3.1 (2025-01-22): Team Mode + 全部Bug修复
- v3.0 (2025-01-21): Team Mode + ReAct Engine

**反馈**: 请在GitHub Issues报告问题或建议
