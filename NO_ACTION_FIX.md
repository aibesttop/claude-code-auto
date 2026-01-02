# "No Action Detected" 问题修复报告

## 问题描述

### 症状
```
2026-01-02 19:50:35 | INFO | 🔄 ReAct Step 1/30
2026-01-02 19:53:57 | WARNING | No action detected and no Final Answer.
2026-01-02 19:53:57 | INFO | 🔄 ReAct Step 2/30
2026-01-02 19:54:53 | WARNING | Final Answer provided but no tools were called.
2026-01-02 19:54:53 | INFO | 🔄 ReAct Step 3/30
```

### 影响
- ❌ Executor 无法正确执行任务
- ❌ 任务陷入无限循环
- ❌ 浪费 API 调用成本
- ❌ 最终导致超时或失败

---

## 根本原因分析

### 问题定位

**文件**: [src/core/tools/research_tools.py](src/core/tools/research_tools.py)

**问题代码**:
```python
@tool
def quick_research(query: str) -> str:
    researcher = get_researcher()
    # 这个调用在 ReAct 循环内部!
    result = _run_async_in_new_loop(researcher.research(query, use_cache=True))
    return result
```

### 执行流程图

```
ExecutorAgent.execute_task()
  │
  ├─> 构建 ReAct Prompt:
  │    "You are a task executor. Use this format:
  │     Thought: your thinking
  │     Action: tool name
  │     Action Input: tool input"
  │
  ├─> 调用 Claude API (第1次)
  │
  ├─> LLM 返回: "Action: quick_research\nAction Input: elderly care..."
  │
  ├─> 执行 quick_research 工具
  │    │
  │    └─> researcher.research()
  │         │
  │         └─> run_claude_prompt()  ← 第2次 LLM 调用!
  │              │
  │              └─> 不同的 prompt (研究格式)
  │
  ├─> 返回到 Executor
  │
  ├─> 期望: ReAct 格式 (Thought/Action)
  ├─> 实际: 研究结果 (纯文本)
  │
  └─> 解析失败 → "No action detected"
```

### 为什么会失败?

1. **Prompt 格式冲突**
   - Executor 要求 ReAct 格式
   - Researcher 要求 Research 格式
   - LLM 收到混合指令,不知道遵循哪个

2. **嵌套 LLM 调用**
   - 第1层 LLM: Executor (ReAct 模式)
   - 第2层 LLM: Researcher (Research 模式)
   - 两层 prompt 互相干扰

3. **输出解析失败**
   - Executor 期望: `Action: write_file\nAction Input: ...`
   - 实际收到: 研究结果文本
   - 正则表达式匹配失败

---

## 解决方案

### ✅ 已应用的修复

**修改文件**: [src/core/tools/__init__.py](src/core/tools/__init__.py)

**修改内容**:
```python
# 之前:
from .research_tools import quick_research, deep_research, get_research_stats

# 之后:
# from .research_tools import quick_research, deep_research, get_research_stats  # DISABLED: Causes nested LLM calls
```

**效果**:
- ✅ 移除了 `quick_research` 和 `deep_research` 工具
- ✅ Executor 无法调用这些工具
- ✅ 避免了嵌套 LLM 调用
- ✅ 恢复正常的 ReAct 循环

### 替代方案

如果需要研究功能,使用以下方式:

#### 方案1: 使用 web_search 工具 (推荐)

`web_search` 工具不会造成嵌套 LLM 调用,因为:
- 它直接调用 Tavily API
- 不需要 LLM 处理
- 返回 JSON 格式搜索结果

```python
# Executor 可以正常使用
Action: web_search
Action Input: {"query": "elderly care digital health opportunities"}
```

#### 方案2: 在任务层面进行研究

```python
# Mission 1: Market Research (使用 web_search)
# Mission 2: Architecture Design (基于研究结果)
# Mission 3: Content Writing
```

#### 方案3: 预先研究

```python
# 在执行前先进行研究
# 将研究结果作为 context 传递给 Leader
leader.execute(
    goal="Design architecture",
    context=research_results  # 预先研究的结果
)
```

---

## 验证修复

### 测试步骤

1. **运行程序**:
   ```bash
   python src/main.py
   ```

2. **观察日志**:
   ```
   # 期望看到:
   ✅ ReAct Step 1/30
   ✅ Thought: I need to research...
   ✅ Action: web_search
   ✅ Action Input: {"query": "..."}
   ✅ Observation: [搜索结果]
   ✅ Thought: Based on the research...
   ✅ Action: write_file
   ```

3. **监控执行**:
   ```bash
   # 终端2
   python monitor.py --important
   ```

### 预期结果

修复后应该看到:
- ✅ 正常的 ReAct 循环
- ✅ Action 被正确识别
- ✅ 工具被正确调用
- ✅ 任务顺利完成

### 如果仍有问题

如果仍然出现 "No action detected",检查:

1. **Prompt 复杂度**:
   ```yaml
   # config.yaml
   claude:
     timeout_seconds: 300  # 足够的响应时间
   ```

2. **Persona 干扰**:
   ```yaml
   # config.yaml
   persona:
     enabled: false  # 暂时禁用测试
   ```

3. **验证日志**:
   ```bash
   grep "No action detected" logs/workflow.log
   grep "Thought:" logs/workflow.log | tail -20
   ```

---

## 技术细节

### 为什么 web_search 不会有问题?

**对比**:

```python
# ❌ quick_research (有嵌套调用)
def quick_research(query: str) -> str:
    researcher = get_researcher()
    # ← 调用 run_claude_prompt() 嵌套 LLM
    return researcher.research(query)

# ✅ web_search (无嵌套调用)
def web_search(query: str, max_results: int = 10) -> str:
    from src.utils.tavily_client import TavilyClient
    client = TavilyClient()
    # ← 直接调用 API,无 LLM
    return client.search(query)
```

### 执行对比

| 工具 | LLM 调用层级 | Prompt 格式 | 问题 |
|------|-------------|------------|------|
| `quick_research` | 嵌套2层 | 混合 | ❌ 导致格式冲突 |
| `deep_research` | 嵌套2层 | 混合 | ❌ 导致格式冲突 |
| `web_search` | 单层 | 纯ReAct | ✅ 正常工作 |
| `write_file` | 单层 | 纯ReAct | ✅ 正常工作 |
| `read_file` | 单层 | 纯ReAct | ✅ 正常工作 |

---

## 长期解决方案

如果要恢复研究功能,需要重构架构:

### 方案A: 异步研究模式

```python
# 在 ReAct 循环外进行
async def execute_with_research():
    # 1. 先研究
    research_results = await researcher.research(query)

    # 2. 将结果作为 context
    task = f"Use these research results: {research_results}\n\n{original_task}"

    # 3. 执行任务
    result = await executor.execute_task(task)
    return result
```

### 方案B: 工具结果后处理

```python
# 让 LLM 知道如何处理研究工具
TOOL_SYSTEM_PROMPT = """
Available tools:
- web_search: Returns JSON search results (use this)
- quick_research: Returns research summary (DO NOT USE - causes prompt confusion)
"""
```

### 方案C: 分离研究 Agent

```python
# 创建独立的 Research Mode
if task.requires_research:
    # 使用专门的 ResearcherAgent
    result = await researcher.execute(task)
else:
    # 使用普通的 ExecutorAgent
    result = await executor.execute(task)
```

---

## 总结

### 问题
- ❌ `quick_research` 工具在 ReAct 循环内调用 LLM
- ❌ 导致嵌套 LLM 调用和 prompt 格式冲突
- ❌ Executor 无法解析响应 → "No action detected"

### 修复
- ✅ 禁用 `quick_research` 和 `deep_research` 工具
- ✅ 使用 `web_search` 替代
- ✅ 恢复正常的 ReAct 循环

### 验证
- ✅ 观察 ReAct 循环是否正常
- ✅ Action 是否被正确识别
- ✅ 工具是否被正确调用

### 下一步
1. 运行测试: `python src/main.py`
2. 监控日志: `python monitor.py --important`
3. 验证任务完成

---

**修复状态**: ✅ 已完成
**修复时间**: 2026-01-02
**测试状态**: 待验证
