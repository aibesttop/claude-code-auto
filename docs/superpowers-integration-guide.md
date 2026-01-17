# Superpowers Skills Integration Guide

## 概述

本项目现已集成 **Superpowers Commands** 与 **Agentic Skills**，实现两者有机融合。

```
用户触发 /command
        ↓
Superpowers Adapter (命令适配器)
        ↓
Agentic Skill (结构化思维模板)
        ↓
增强的 Prompt → LLM 执行
```

## 可用命令列表

### 代码类 (CODE)

| 命令 | 用途 | 对应 Skill |
|------|------|-----------|
| `/commit` | 生成规范的 commit message | `technical_writer` |
| `/review` | PR 代码审查 | `code_analysis_expert` |
| `/test` | 生成测试用例 | `python_expert` |
| `/analyze` | 深度代码分析 | `code_analysis_expert` |

### 规划类 (PLANNING)

| 命令 | 用途 | 对应 Skill |
|------|------|-----------|
| `/plan` | 任务分解与实施计划 | `complex_problem_solver` |
| `/brainstorm` | 创意方案生成 | `creative_innovator` |
| `/architecture` | 系统架构设计 | `system_architect` |

### 研究类 (RESEARCH)

| 命令 | 用途 | 对应 Skill |
|------|------|-----------|
| `/market-research` | 市场研究 | `market_analyst` |
| `/docs` | 技术文档编写 | `technical_writer` |
| `/research` | 综合研究 | `market_analyst` |

### 自动化类 (AUTOMATION)

| 命令 | 用途 | 对应 Skill |
|------|------|-----------|
| `/scrape` | 网页抓取 | `web_automation_specialist` |
| `/automate` | 浏览器自动化 | `web_automation_specialist` |

## 使用方法

### Python API

```python
from src.core.superpowers_adapter import execute_with_skill, list_available_commands

# 1. 查看所有可用命令
commands = list_available_commands()
for cmd in commands:
    print(f"{cmd['name']}: {cmd['purpose']}")

# 2. 执行命令（自动应用 Agentic Skill）
result = execute_with_skill("/commit", {
    "changes": "Added user authentication with OAuth2",
    "branch": "feature/auth",
    "files": ["src/auth/oauth.py", "src/auth/handlers.py"]
})

# 3. 获取增强后的 Prompt
enhanced_prompt = result["enhanced_prompt"]
print(enhanced_prompt)
```

### 命令行执行

```bash
# 创建一个简单的命令行工具
python -m src.core.superpowers_adapter /commit --changes "Added auth" --branch "feature/auth"
```

## 增强效果对比

### 不使用 Agentic Skill
```
User: /commit
> 帮我写一个 commit message
AI: 好的，这是 commit message: "Added auth"
```

### 使用 Agentic Skill 增强
```
User: /commit

# Command: /commit
# Purpose: Generate high-quality commit messages

## Role
Senior Technical Writer (Agentic)

## Task Context
- changes: "Added user authentication with OAuth2"
- branch: "feature/auth"
- files: src/auth/oauth.py, src/auth/handlers.py

## Approach
**Step 1: Audience Analysis**
- Identify target audience (developers, reviewers)
- Determine prior knowledge required

**Step 2: Content Planning**
- Create outline with clear hierarchy
- Plan code examples and diagrams

... (更多结构化思维)

## Constraints
- No [TODO], [FIXME], or [PLACEHOLDER] markers
- Use Flesch Reading Ease score > 60
- Maximum 3 levels of heading depth

## Self-Reflection Questions
- Can a developer immediately use this documentation without confusion?
- Did I explain WHY, not just WHAT and HOW?

## Output Format
Please provide output in: conventional_commit format

AI: feat(auth): implement OAuth2 authentication

- Add OAuth2 provider support (Google, GitHub)
- Implement token refresh mechanism
- Add user profile sync on first login
- Handle OAuth errors and edge cases

Closes #123
```

## 配置说明

配置文件: `resources/superpowers_integration.yaml`

### 启用/禁用集成
```yaml
integration:
  enabled: true  # 设为 false 禁用集成
```

### 自定义命令映射
```yaml
commands:
  /mycommand:
    skill: market_analyst
    purpose: "My custom purpose"
    auto_apply: true
    skill_enhancement:
      include_logic_flow: true
      include_reflection: true
```

### 调整增强策略
```yaml
skill_enhancement:
  include_sections:
    - role
    - logic_flow
    - constraints
    - reflection
  priority: "skill_over_command"  # skill_over_command | command_over_skill
```

## 实际应用示例

### 示例 1: Git Commit
```python
result = execute_with_skill("/commit", {
    "changes": "Fixed race condition in payment processing",
    "branch": "hotfix/payment-race",
    "files": ["src/payment/processor.py"]
})
```

### 示例 2: 实施计划
```python
result = execute_with_skill("/plan", {
    "requirement": "Add real-time notifications using WebSockets",
    "constraints": ["Max 100ms latency", "Support 10k concurrent users"],
    "existing_infrastructure": ["Redis", "Node.js"]
})
```

### 示例 3: 市场研究
```python
result = execute_with_skill("/market-research", {
    "query": "Electric vehicle market in Southeast Asia",
    "market": ["Thailand", "Indonesia", "Vietnam"],
    "focus": ["market_size", "competitors", "charging_infrastructure"]
})
```

## 故障排除

### 问题: Skill 未找到
```
解决方案: 检查 resources/skill_prompts.yaml 中是否定义了对应的 skill
```

### 问题: 命令无响应
```
解决方案: 检查 resources/superpowers_integration.yaml 中 command 是否正确配置
```

### 问题: 增强效果不理想
```
解决方案: 调整 skill_enhancement.include_sections 来控制包含哪些部分
```

## 扩展新命令

1. 在 `resources/superpowers_integration.yaml` 中添加命令配置
2. 在 `resources/skill_prompts.yaml` 中定义对应的 skill（如需要）
3. 使用 `execute_with_skill()` 调用

```yaml
# 在 superpowers_integration.yaml 中添加
commands:
  /my-new-command:
    skill: my_custom_skill
    purpose: "What this command does"
    auto_apply: true
```

## 总结

| 特性 | Superpowers | Agentic Skills | 集成后 |
|------|------------|---------------|--------|
| 用户触发 | ✅ | ❌ | ✅ |
| 结构化思维 | ❌ | ✅ | ✅ |
| 可复用性 | 中 | 高 | 高 |
| 易用性 | 高 | 低 | 高 |
| 输出质量 | 中 | 高 | 高 |
