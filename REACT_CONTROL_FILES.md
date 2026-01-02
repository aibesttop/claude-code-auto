# ReAct 模式控制文件完整清单

## 🎯 核心控制文件 (4个)

### 1. **executor.py** - ReAct 引擎 ⭐⭐⭐
**路径**: `src/core/agents/executor.py`
**作用**: ReAct 模式的核心实现

**关键配置点**:

#### A. ReAct Prompt 模板 (line 20-35)
```python
REACT_SYSTEM_PROMPT = """
You are a task executor. Use the ReAct format:
Thought: [what you want to do]
Action: [tool name]
Action Input: [JSON input]
...
"""
```
**控制内容**:
- ✅ 定义 ReAct 格式规范
- ✅ 告诉 AI 如何输出 Thought/Action/Action Input
- ✅ 列出可用工具

#### B. 最大步数限制 (line 68)
```python
self.max_steps = 30  # 最多30个 ReAct 步骤
```
**控制内容**:
- ✅ 防止无限循环
- ✅ 30步足够完成复杂任务

#### C. 主循环 (line 203-309)
```python
while step < self.max_steps:
    # 1. 调用 LLM
    response_text, _ = await run_claude_prompt(...)

    # 2. 解析 Action
    action, args = self._parse_action(response_text)

    # 3. 执行工具
    result = registry.execute(action, args)

    # 4. 继续下一步
    step += 1
```
**控制内容**:
- ✅ ReAct 循环逻辑
- ✅ 工具调用
- ✅ 错误处理

#### D. Action 解析器 (line 96-126)
```python
def _parse_action(self, text: str):
    # 查找 "Action: xxx"
    action_match = re.search(r"Action:\s*(.+)", text)

    # 查找 "Action Input: xxx"
    input_match = re.search(r"Action Input:\s*(.+)", text, re.DOTALL)

    # 解析 JSON
    args = extract_json(input_str)

    return action, args
```
**控制内容**:
- ✅ 从 LLM 响应中提取 Action
- ✅ 从 LLM 响应中提取 Action Input
- ✅ 验证 JSON 格式

#### E. Final Answer 解析器 (line 128-133)
```python
FINAL_ANSWER_PATTERN = re.compile(r"(?im)^\s*(?:#+\s*)?Final Answer\s*:?\s*")

def _extract_final_answer(self, text: str):
    match = FINAL_ANSWER_PATTERN.search(text)
    return text[match.end():].strip()
```
**控制内容**:
- ✅ 识别任务完成信号
- ✅ 提取最终答案

---

### 2. **role_executor.py** - 角色执行器 ⭐⭐
**路径**: `src/core/team/role_executor.py`
**作用**: 将角色任务传递给 ExecutorAgent

**关键配置点**:

#### A. 直接执行模式 (line 110-196)
```python
async def _execute_direct(self, context):
    mission = self.role.mission
    task = self._build_task(mission, context)

    # 调用 ExecutorAgent 的 ReAct 循环
    result = await self.executor.execute_task(task)
```
**控制内容**:
- ✅ 不使用 Planner,直接 ReAct
- ✅ 适合简单任务

#### B. 规划执行模式 (line 198+)
```python
async def _execute_with_planner(self, context):
    # 先用 Planner 分解任务
    next_task = await self.planner.get_next_step(last_result)

    # 再用 ExecutorAgent 执行每个子任务
    result = await self.executor.execute_task(next_task)
```
**控制内容**:
- ✅ Planner + Executor 组合
- ✅ 适合复杂任务

#### C. 反射循环 (line 786-872) ⭐ Tier-3 功能
```python
async def _execute_reflection_loop(self, outputs, context):
    # 任务完成后,启动反思循环
    for iteration in range(1, max_retries + 1):
        # 1. 切换到 Critic 角色
        review_result, _ = await run_claude_prompt(critic_prompt, ...)

        # 2. 检查是否有问题
        issues_found = self._parse_review_for_issues(review_result)

        # 3. 如果有问题,改进输出
        if issues_found:
            refinement_task = self._build_refinement_task(outputs, issues_found)
            refined_result = await self.executor.execute_task(refinement_task)
```
**控制内容**:
- ✅ 任务完成后的自我审查
- ✅ 多次改进直到满意

---

### 3. **leader_agent.py** - 任务协调器 ⭐
**路径**: `src/core/leader/leader_agent.py`
**作用**: 分解任务并调用 RoleExecutor

**关键配置点**:

#### A. 任务执行 (line 280-350)
```python
async def _execute_mission(self, mission, role_name):
    # 1. 获取角色定义
    role = self.role_registry.get_role(role_name)

    # 2. 创建 RoleExecutor
    role_executor = RoleExecutor(
        role=role,
        executor_agent=executor,  # ← 传入 ExecutorAgent
        ...
    )

    # 3. 执行任务 (内部会调用 ReAct)
    result = await role_executor.execute(context)
```
**控制内容**:
- ✅ 选择合适的角色
- ✅ 配置执行参数
- ✅ 处理执行结果

#### B. 工作流转换 (line 935-1052) ⭐ Tier-3 功能
```python
async def _determine_next_workflow_state(self, role, result, current_mission):
    if role.workflow.strategy == "conditional":
        # 检查输出内容
        for keyword, target_state in workflow.transition_rules.items():
            if keyword in content:
                return target_state
```
**控制内容**:
- ✅ 根据任务结果动态选择下一个角色
- ✅ 实现条件跳转逻辑

---

### 4. **main.py** - 程序入口
**路径**: `src/main.py`
**作用**: 启动整个系统

**关键配置点**:

#### A. Leader 模式启动 (line 104)
```python
result = await leader.execute(
    goal=config.task.goal,
    session_id=session_id,
    context=config.task.initial_prompt
)
```
**控制内容**:
- ✅ 传入用户目标
- ✅ 启动 Leader 流程

---

## 🔧 辅助控制文件 (3个)

### 5. **tool_registry.py** - 工具注册表 ⭐
**路径**: `src/core/tool_registry.py`
**作用**: 管理所有可用工具

**关键配置点**:
```python
# 工具装饰器 (自动注册)
@tool
def web_search(query: str) -> str:
    ...

# 工具执行
result = registry.execute(action, args)
```
**控制内容**:
- ✅ 哪些工具可用
- ✅ 工具的参数 schema
- ✅ 工具执行逻辑

---

### 6. **research_tools.py** - 研究工具 (已禁用) ⚠️
**路径**: `src/core/tools/research_tools.py`
**作用**: 提供研究功能

**状态**: ❌ 已禁用 (line 4 of `__init__.py`)
```python
# from .research_tools import quick_research, deep_research
```
**原因**: 造成嵌套 LLM 调用,导致 ReAct 格式冲突

---

### 7. **search_tools.py** - 搜索工具 ✅
**路径**: `src/core/tools/search_tools.py`
**作用**: 提供网页搜索功能

**关键实现**:
```python
@tool
def web_search(query: str, max_results: int = 10) -> str:
    from src.utils.tavily_client import TavilyClient
    client = TavilyClient()
    return client.search(query)  # ← 直接 API,无嵌套 LLM
```
**优势**:
- ✅ 不会造成嵌套 LLM 调用
- ✅ 与 ReAct 完美兼容

---

## 🎛️ 配置文件 (1个)

### 8. **config.yaml** - 全局配置 ⭐
**路径**: `config.yaml`
**作用**: 控制整个系统行为

**ReAct 相关配置**:

```yaml
claude:
  model: "claude-sonnet-4-5"
  timeout_seconds: 300  # ← 每个 ReAct 步的超时

safety:
  max_iterations: 30  # ← Leader 层面的最大迭代
  iteration_timeout_minutes: 10

error_handling:
  max_retries: 2
  retry_delay_seconds: 2.0
```

---

## 📊 完整调用链路

```
用户运行: python src/main.py
    ↓
main.py:104
  → leader.execute(goal)
    ↓
leader_agent.py:314 (execute 方法)
  → leader._execute_mission(mission, role)
    ↓
leader_agent.py:280 (_execute_mission 方法)
  → 创建 RoleExecutor(role, executor_agent)
    ↓
role_executor.py:90 (execute 方法)
  → role_executor._execute_direct(context) 或 _execute_with_planner(context)
    ↓
role_executor.py:141 (_execute_direct 内)
  → self.executor.execute_task(task)
    ↓
executor.py:159 (execute_task 方法)
  → ReAct Loop 开始 (line 203-309)
    │
    ├─> 构建提示词 (line 183-190)
    │   └─> REACT_SYSTEM_PROMPT + tool_descriptions + task
    │
    ├─> 调用 LLM (line 208-217)
    │   └─> response_text, _ = await run_claude_prompt(current_prompt, ...)
    │
    ├─> 解析响应 (line 228, 271)
    │   ├─> 提取 Final Answer (line 239)
    │   └─> 解析 Action (line 282)
    │       └─> action, args = self._parse_action(response_text)
    │
    ├─> 执行工具 (line 292-308)
    │   ├─> if action and args is not None:
    │   │   └─> result = registry.execute(action, args)
    │   └─> else:
    │       └─> 记录错误
    │
    └─> 继续循环 (line 203)
```

---

## 🎯 如何修改 ReAct 行为

### 修改 1: 改变 ReAct 格式
**文件**: `src/core/agents/executor.py:20-35`

```python
# 修改 Prompt 模板
REACT_SYSTEM_PROMPT = """
Use this format:
Thinking: [your thought]
Tool: [tool name]
Parameters: [JSON]
Final: [answer]
"""
```

### 修改 2: 改变最大步数
**文件**: `src/core/agents/executor.py:68`

```python
self.max_steps = 50  # 从 30 改为 50
```

### 修改 3: 添加新工具到 ReAct
**文件**: `src/core/tools/*.py`

```python
# 在任何工具文件中添加
@tool
def my_new_tool(param: str) -> str:
    """Tool description"""
    return f"Result: {param}"

# 会自动注册到 ReAct 系统中
```

### 修改 4: 禁用 ReAct 使用 Planner
**文件**: `src/core/team/role_executor.py`

```python
# 在创建 RoleExecutor 时
role_executor = RoleExecutor(
    role=role,
    executor_agent=executor,
    use_planner=False,  # ← 禁用 Planner,只用 ReAct
    ...
)
```

### 修改 5: 调整超时时间
**文件**: `config.yaml`

```yaml
claude:
  timeout_seconds: 600  # 从 300 改为 600 (10分钟)
```

---

## 🔍 诊断 ReAct 问题的文件

当出现 "No Action Detected" 时,检查这些文件:

1. **executor.py:20-35** - Prompt 是否太复杂?
2. **executor.py:96-126** - Action 解析逻辑是否正确?
3. **executor.py:208-217** - LLM 调用是否成功?
4. **role_executor.py:141** - 是否正确调用 executor?
5. **tools/__init__.py** - 是否禁用了嵌套 LLM 工具?

---

## 📚 总结

### 核心 ReAct 控制文件

| 优先级 | 文件 | 作用 |
|--------|------|------|
| ⭐⭐⭐ | executor.py | ReAct 引擎,定义格式和循环 |
| ⭐⭐ | role_executor.py | 调用 executor,处理角色逻辑 |
| ⭐ | leader_agent.py | 协调任务执行 |
| ⭐ | main.py | 程序入口 |

### 修改 ReAct 行为的优先级

1. **Prompt 格式** (executor.py:20-35) - 最直接的影响
2. **工具列表** (tools/*.py) - 决定 AI 能做什么
3. **最大步数** (executor.py:68) - 控制循环长度
4. **超时时间** (config.yaml) - 防止卡住
5. **错误处理** (executor.py:290-308) - 决定如何应对失败

---

**当前状态**:
- ✅ 已简化 Prompt (executor.py:20-35)
- ✅ 已禁用嵌套 LLM 工具 (tools/__init__.py:4)
- ✅ 已添加调试日志 (executor.py:228-237, 285-287)
- ⏳ 等待测试验证
