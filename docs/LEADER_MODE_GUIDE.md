# Leader Mode 使用指南

> Claude Code Auto v4.0 - 智能团队编排系统

## 📖 目录

1. [简介](#简介)
2. [快速开始](#快速开始)
3. [核心特性](#核心特性)
4. [配置说明](#配置说明)
5. [干预策略](#干预策略)
6. [资源注入](#资源注入)
7. [报告系统](#报告系统)
8. [常见问题](#常见问题)

---

## 简介

Leader Mode是Claude Code Auto v4.0的核心特性，提供智能的团队编排和任务管理能力。

### 核心优势

- 🤖 **智能任务分解**：自动将复杂目标分解为可执行的子任务
- 👥 **动态团队组装**：根据任务类型自动选择和组织角色
- 🧠 **实时监控干预**：基于质量阈值的智能决策系统
- 🔧 **资源智能注入**：根据任务类型动态分配工具和技能
- 📊 **多格式报告**：生成Markdown、JSON、HTML格式的执行报告

---

## 快速开始

### 1. 启用Leader Mode

编辑 `config.yaml`:

```yaml
leader:
  enabled: true                      # 启用Leader模式
  max_mission_retries: 3            # 每个任务最多重试3次
  quality_threshold: 70.0           # 质量阈值70分（0-100）
  enable_intervention: true         # 启用监控干预
  resource_config_dir: "resources"  # 资源配置目录
```

### 2. 设置项目目标

```yaml
task:
  goal: "开发一个Web应用的MVP版本"
  initial_prompt: |
    你们是一个专业的开发团队。
    目标：创建一个用户管理系统的MVP。
    要求：包括用户注册、登录、个人资料管理功能。
```

### 3. 运行

```bash
python src/main.py
```

### 4. 查看结果

执行完成后，检查以下目录：

```
demo_act/
├── deliverables/           # 交付物
│   └── [session_id]/
│       ├── README.md      # 项目总结
│       └── mission_*/     # 各任务输出
└── reports/               # 执行报告
    ├── [session_id]_report.md      # Markdown报告
    ├── [session_id]_report.json    # JSON报告
    └── [session_id]_report.html    # HTML报告

logs/
└── interventions/         # 干预决策日志
    └── [session_id]_interventions.md
```

---

## 核心特性

### 1. 任务分解 (Mission Decomposition)

Leader Agent使用LLM自动将高层目标分解为具体的子任务（SubMissions）。

**SubMission结构**:
```python
{
    "id": "mission_1",
    "type": "market_research",      # 任务类型
    "goal": "进行市场调研",           # 具体目标
    "requirements": [...],           # 详细需求
    "success_criteria": [...],       # 成功标准
    "dependencies": [],              # 依赖关系
    "priority": 1,                   # 优先级(1-5)
    "estimated_cost_usd": 0.5        # 成本估算
}
```

### 2. 团队组装 (Team Assembly)

根据SubMissions自动选择合适的角色。

**预定义角色** (8个):
- `Market-Researcher` - 市场研究
- `Architect` - 系统架构
- `AI-Native-Developer` - 开发
- `AI-Native-Writer` - 文档
- `SEO-Specialist` - SEO优化
- `Creative-Explorer` - 创意探索
- `Multidimensional-Observer` - 多维观察
- `Role-Definition-Expert` - 角色定义

### 3. 依赖解析 (Dependency Resolution)

使用Kahn算法进行拓扑排序，确保任务按正确的依赖顺序执行。

**特性**:
- ✅ 自动检测循环依赖
- ✅ 支持复杂的DAG结构
- ✅ 清晰的错误信息

---

## 配置说明

### 完整配置示例

```yaml
# Leader Agent配置
leader:
  enabled: true
  max_mission_retries: 3
  quality_threshold: 70.0
  enable_intervention: true
  resource_config_dir: "resources"

# 成本控制
cost_control:
  enabled: true
  max_budget_usd: 10.0
  warning_threshold: 0.8     # 80%时预警

# 安全限制
safety:
  max_iterations: 50
  max_duration_hours: 8
  emergency_stop_file: ".emergency_stop"

# Claude配置
claude:
  model: "claude-sonnet-4-5"
  permission_mode: "bypassPermissions"
  timeout_seconds: 300
```

### 配置参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `leader.enabled` | `false` | 是否启用Leader模式 |
| `leader.max_mission_retries` | `3` | 单个任务最大重试次数 |
| `leader.quality_threshold` | `70.0` | 质量阈值(0-100) |
| `leader.enable_intervention` | `true` | 是否启用监控干预 |
| `cost_control.max_budget_usd` | `10.0` | 最大预算（美元） |
| `safety.max_iterations` | `50` | 全局最大迭代次数 |

---

## 干预策略

Leader Agent支持5种干预策略：

### 1. CONTINUE（继续）

**触发条件**: 质量分数 ≥ 阈值

**行为**: 标记任务完成，继续下一个任务

```python
if quality_score >= quality_threshold:
    return InterventionDecision(action=CONTINUE)
```

### 2. RETRY（重试）

**触发条件**:
- 质量分数 < 阈值
- 重试次数 < max_retries
- 临时性失败（如网络错误）

**行为**: 使用相同配置重新执行任务

### 3. ENHANCE（增强）⭐ **P0新增**

**触发条件**:
- 任务需求不够清晰
- 质量问题反复出现

**行为**:
- 使用LLM分析质量问题
- 重新细化任务描述
- 优化requirements和success_criteria

**实现**:
```python
async def _enhance_mission(mission, quality_issues):
    # LLM驱动的任务细化
    enhanced_mission = await llm.refine_task(
        original=mission,
        issues=quality_issues
    )
    return enhanced_mission
```

### 4. ESCALATE（升级）⭐ **P1新增**

**触发条件**:
- 主角色能力不足
- 需要专家协助

**行为**:
- 动态创建Helper角色（Debugger/Reviewer/SecurityExpert/PerfAnalyzer）
- Helper独立执行修复任务
- 合并Helper输出到主任务

**Helper选择逻辑**:
```python
def _select_helper_role(validation_errors):
    if "security" in errors:
        return "SecurityExpert"
    elif "performance" in errors:
        return "PerfAnalyzer"
    elif "review" in errors:
        return "Reviewer"
    else:
        return "Debugger"  # 默认
```

### 5. TERMINATE（终止）

**触发条件**:
- 达到最大重试次数
- 预算超限
- 无法修复的错误

**行为**: 记录失败原因，终止执行

---

## 资源注入 ⭐ **P0新增**

Leader Agent根据任务类型动态注入资源。

### 资源类型

1. **MCP Servers** - 外部服务集成
2. **Skill Prompts** - 角色技能增强
3. **Tool Mappings** - 任务工具映射

### 配置文件

#### `resources/tool_mappings.yaml`

```yaml
mappings:
  market_research:
    required_tools:
      - web_search
      - write_file
    optional_tools:
      - deep_research
    mcp_servers:
      - filesystem

  documentation:
    required_tools:
      - write_file
      - read_file
    mcp_servers:
      - filesystem

  development:
    required_tools:
      - write_file
      - read_file
      - run_command
    mcp_servers:
      - filesystem
      - git
```

#### `resources/skill_prompts.yaml`

```yaml
skills:
  market_analyst:
    category: "research"
    prompt: "You are an expert market analyst with deep experience in competitive intelligence."
    tags: ["research", "market_analysis"]

  python_expert:
    category: "engineering"
    prompt: "You are a senior Python developer with expertise in clean architecture."
    tags: ["engineering", "python"]
```

### 注入流程

```
1. Leader分析任务类型 (mission.type)
   ↓
2. ResourceRegistry查询配置
   ├─ 获取required_tools
   ├─ 获取mcp_servers
   └─ 获取skill_prompt (by role.category)
   ↓
3. RoleExecutor接收资源
   ├─ skill_prompt → 添加到任务描述
   └─ allowed_tools → 工具使用建议
   ↓
4. Agent执行任务（使用注入的资源）
```

---

## 报告系统 ⭐ **P0增强**

### 报告类型

#### 1. Markdown报告 (`_report.md`)

**内容**:
- 📊 执行摘要（成功率、成本、耗时）
- 📈 关键指标（进度条、统计图表）
- 📋 任务详情（每个任务的完整信息）
- 🎯 质量分析（质量分布、趋势）
- 💰 成本分析（按任务分解）
- ⏱️ 执行时间线
- 🧠 Leader干预日志 **（新增）**
- 📦 交付物清单
- 💡 建议和下一步

**示例**:
```markdown
## 🧠 Leader干预决策日志

**总干预次数**: 5

### 干预类型统计
| 干预类型 | 次数 |
|---------|------|
| ✅ 继续 | 2 |
| 🔁 重试 | 2 |
| ⚡ 增强 | 1 |

### 详细干预记录
#### 任务: mission_1

1. **🔁 重试** (迭代 1)
   - **角色**: Market-Researcher
   - **原因**: Quality 65 < 70
   - **时间**: 14:23:15

2. **✅ 继续** (迭代 2)
   - **角色**: Market-Researcher
   - **原因**: Quality 75 > 70
   - **时间**: 14:25:42
```

#### 2. HTML报告 (`_report.html`)

**特性**:
- 🎨 专业的CSS样式
- 📱 响应式设计
- 🖨️ 打印优化
- 📊 表格、图表美化
- 🎯 语义化HTML

**增强功能**:
- Markdown元素完整渲染
- 代码高亮支持
- 表格自动美化
- 链接自动识别

#### 3. JSON报告 (`_report.json`)

**用途**:
- 程序化分析
- 数据导出
- CI/CD集成

**结构**:
```json
{
  "session_id": "...",
  "goal": "...",
  "summary": {
    "total_missions": 3,
    "successful_missions": 3,
    "total_cost_usd": 1.234,
    "average_quality_score": 85.3
  },
  "missions": [...],
  "intervention_history": [...]
}
```

### 交付物README

自动生成 `deliverables/[session_id]/README.md`:

```markdown
# 项目交付物

**会话ID**: session_123
**目标**: 创建Web应用MVP
**生成时间**: 2025-11-22T10:30:00Z

## 📊 执行汇总
- **总任务数**: 3
- **成功任务**: 3
- **成功率**: 100.0%
- **总成本**: $1.234
- **总耗时**: 456.7秒

## 📁 目录结构
```
mission_1/
  ├── market-research.md
mission_2/
  ├── architecture.md
mission_3/
  ├── src/app.py
  ├── README.md
```

## 📋 任务清单
### 1. ✅ mission_1
- **类型**: market_research
- **角色**: Market-Researcher
- **质量分数**: 85.0/100
- **生成文件**: 1个
```

---

## 常见问题

### Q1: 如何自定义质量阈值？

A: 在 `config.yaml` 中调整：

```yaml
leader:
  quality_threshold: 80.0  # 提高到80分
```

### Q2: 如何添加自定义角色？

A: 在 `roles/` 目录创建YAML文件：

```yaml
name: "CustomRole"
description: "My custom role"
category: "engineering"
mission:
  goal: "..."
  success_criteria: [...]
  max_iterations: 10
output_standard:
  required_files: [...]
  validation_rules: [...]
dependencies: []
```

### Q3: 如何禁用某个干预策略？

A: 修改 `_monitor_and_decide` 方法的逻辑，或设置：

```yaml
leader:
  enable_intervention: false  # 禁用所有干预
```

### Q4: 报告生成在哪里？

A: 默认路径：
- Markdown: `demo_act/reports/[session_id]_report.md`
- HTML: `demo_act/reports/[session_id]_report.html`
- JSON: `demo_act/reports/[session_id]_report.json`

### Q5: 如何控制成本？

A: 启用成本控制：

```yaml
cost_control:
  enabled: true
  max_budget_usd: 5.0        # 最多花费$5
  warning_threshold: 0.8     # 80%时警告
```

### Q6: Helper角色什么时候触发？

A: 当主角色反复失败且Leader决定ESCALATE时：
- 检测到安全问题 → SecurityExpert
- 性能问题 → PerfAnalyzer
- 质量问题 → Reviewer
- 一般问题 → Debugger

### Q7: 如何查看干预历史？

A: 查看日志文件：

```bash
cat logs/interventions/[session_id]_interventions.md
```

或者查看HTML报告中的"Leader干预决策日志"部分。

---

## 最佳实践

### 1. 任务目标设定

✅ **好的目标**:
```yaml
goal: "创建一个用户管理系统的MVP，包括注册、登录和个人资料管理功能"
```

❌ **不好的目标**:
```yaml
goal: "做一个网站"  # 太模糊
```

### 2. 质量阈值设置

- **快速原型**: 60-70分
- **生产环境**: 75-85分
- **高质量**: 85-95分

### 3. 预算控制

建议设置合理的预算：
- 小型任务: $1-3
- 中型项目: $5-10
- 大型项目: $10-20

### 4. 监控干预

定期检查干预日志，了解：
- 哪些任务经常失败
- 什么类型的问题最常见
- 是否需要调整质量阈值

---

## 更新日志

### v4.0 - 2025-11-22

**P0改进**:
- ✅ 完整的报告生成系统（Markdown/HTML/JSON）
- ✅ 干预决策日志集成
- ✅ 资源注入系统
- ✅ ENHANCE策略（LLM驱动的任务细化）

**P1改进**:
- ✅ ESCALATE策略（Helper角色支持）
- ✅ HelperGovernor集成

**完成度**: 85% → 95%+

---

## 支持

遇到问题？

1. 查看 `logs/` 目录下的日志
2. 检查 `reports/` 目录下的详细报告
3. 查看 `docs/ARCHITECTURE_EVALUATION.md` 了解架构详情

**项目地址**: https://github.com/aibesttop/claude-code-auto

---

*本文档由 Claude Code Auto v4.0 团队维护*
