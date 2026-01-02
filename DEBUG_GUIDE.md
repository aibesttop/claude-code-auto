# 🔍 调试监控指南 - Debug & Monitoring Guide

## 目录
1. [执行流程图](#执行流程图)
2. [日志系统](#日志系统)
3. [VS Code调试](#vs-code调试)
4. [代码追踪](#代码追踪)
5. [性能监控](#性能监控)

---

## 执行流程图

### Leader Mode (v4.0) 执行路径

```
main.py
 └─> run_leader_mode() [line 58]
      ├─> 初始化 LeaderAgent [line 93]
      │   ├─> MissionDecomposer (任务分解)
      │   ├─> RoleRegistry (角色注册表)
      │   ├─> TeamAssembler (团队组装)
      │   └─> HelperGovernor (助手管理)
      │
      └─> leader.execute() [line 104]
           ├─> 1. 分解任务 [line ~170]
           │    └─> mission_decomposer.decompose()
           │         └─> LLM调用: 生成SubMissions
           │
           ├─> 2. 组装团队 [line ~180]
           │    └─> team_assembler.assemble_team()
           │         ├─> LLM调用: 选择角色
           │         └─> dependency_resolver.topological_sort()
           │
           ├─> 3. 执行任务循环 [line ~220]
           │    └─> for each mission:
           │         └─> _execute_mission() [line 280]
           │              ├─> RoleExecutor初始化
           │              └─> role_executor.execute() [role_executor.py:90]
           │                   ├─> _execute_direct() [line 110]
           │                   │    └─> ReAct循环 [line 129-196]
           │                   │         ├─> executor.execute_task() [executor.py]
           │                   │         ├─> _validate_outputs()
           │                   │         └─> _execute_reflection_loop() ← Tier-3
           │                   │
           │                   └─> _execute_with_planner() [line 198]
           │                        └─> planner.get_next_step()
           │
           ├─> 4. 工作流转换 [line 248] ← Tier-3
           │    └─> _determine_next_workflow_state() [line 935]
           │         ├─> FIXED: 固定跳转
           │         ├─> CONDITIONAL: 关键词匹配
           │         └─> LLM_DECIDE: LLM动态决策
           │
           └─> 5. 整合输出 [line 260]
                └─> _integrate_outputs()
```

### 关键文件和行号

| 组件 | 文件 | 关键方法 | 行号 |
|------|------|---------|------|
| **入口** | main.py | run_leader_mode() | 58 |
| **Leader** | leader_agent.py | execute() | 140 |
| **任务分解** | mission_decomposer.py | decompose() | ~50 |
| **团队组装** | team_assembler.py | assemble_team() | 37 |
| **角色执行** | role_executor.py | execute() | 90 |
| **直接执行** | role_executor.py | _execute_direct() | 110 |
| **规划执行** | role_executor.py | _execute_with_planner() | 198 |
| **反思循环** | role_executor.py | _execute_reflection_loop() | 786 |
| **工作流转换** | leader_agent.py | _determine_next_workflow_state() | 935 |
| **ReAct循环** | executor.py | execute_task() | ~100 |

---

## 日志系统

### 日志级别

```python
import logging
from src.utils.logger import setup_logger

# 配置日志级别
logger = setup_logger(
    name="debug_session",
    log_dir="logs/debug",
    level=logging.DEBUG,  # DEBUG, INFO, WARNING, ERROR
    console_output=True
)
```

### 日志文件位置

```
logs/
├── workflow.log           # 主工作流日志
├── events/                # 事件存储
│   └── <session_id>.json
└── trace/                 # 执行追踪
    └── <role>_<step>.md   # Planner追踪
```

### 查看实时日志

**Windows PowerShell:**
```powershell
Get-Content logs\workflow.log -Wait -Tail 50
```

**Git Bash / Linux:**
```bash
tail -f logs/workflow.log
```

### 关键日志标记

搜索这些关键词来追踪执行:

```
🎯 Leader Agent
🔄 ReAct Step
🎭 Role Executor
🔍 Reflection Loop
🔄 Workflow Transition
✅ SUCCESS
❌ ERROR
⚠️ WARNING
```

---

## VS Code调试

### 1. 使用提供的launch.json

已创建 `.vscode/launch.json` 配置文件。

### 2. 设置断点

在关键位置设置断点:

- **main.py:104** - Leader开始执行
- **leader_agent.py:140** - execute()入口
- **leader_agent.py:220** - 任务循环
- **role_executor.py:90** - 角色执行
- **role_executor.py:129** - ReAct循环

### 3. 启动调试

1. 打开VS Code
2. 按 `F5` 或点击 "Run and Debug"
3. 选择 "Python: Debug Main (Leader Mode)"
4. 使用调试工具栏:
   - Continue (F5) - 继续执行
   - Step Over (F10) - 单步跳过
   - Step Into (F11) - 单步进入
   - Step Out (Shift+F11) - 跳出函数

### 4. 查看变量

在调试时查看关键变量:

```
# LeaderAgent执行上下文
- leader.context              # ExecutionContext
- leader.context.missions     # List[SubMission]
- leader.context.completed_missions  # Dict

# RoleExecutor
- executor.role               # 当前角色
- executor.work_dir           # 工作目录
- executor.use_planner        # 是否使用Planner

# ExecutorAgent (ReAct循环)
- executor.thoughts           # 思考过程
- executor.observations       # 观察结果
```

### 5. 调试配置文件

使用 `config_debug.yaml` 进行调试:

```bash
python src/main.py --config config_debug.yaml
```

调试模式特点:
- ✅ 更详细的日志 (DEBUG级别)
- ✅ 更少的重试次数
- ✅ 更低的预算限制 ($5)
- ✅ 禁用研究功能 (节省成本)

---

## 代码追踪

### 使用debug_tracer追踪执行

#### 1. 启用追踪

在代码开头添加:

```python
from src.utils.debug_tracer import enable_tracing, trace_function

# 启用全局追踪
enable_tracing(enabled=True, output_dir="logs/traces")

# 追踪特定函数
@trace_function()
async def my_function():
    ...
```

#### 2. 查看追踪结果

追踪会保存到 `logs/traces/trace_YYYYMMDD_HHMMSS.json`

使用可视化工具:

```python
from src.utils.debug_tracer import CallStackVisualizer

visualizer = CallStackVisualizer()
trace_text = visualizer.visualize_trace("logs/traces/trace_20260102_143026.json")
print(trace_text)
```

输出示例:

```
================================================================================
EXECUTION TRACE VISUALIZATION
================================================================================

🚀 Session: Leader Agent Execution
   Started: 2026-01-02T14:30:26

└─→ execute()
  └─→ decompose()
    └─← decompose (1234.5ms) → SubMissions[...]
  └─→ assemble_team()
    └─← assemble_team (567.8ms) → [Role1, Role2, Role3]
  └─→ execute_mission()
    └─→ role_executor.execute()
      └─→ _execute_direct()
        └─→ executor.execute_task()
          └─← execute_task (5000.2ms) → "Task completed"
        └─← _execute_direct (6500.3ms) → {"success": true}
      └─→ _execute_reflection_loop()
        └─← _execute_reflection_loop (1200.1ms) → {"refined": true}
      └─← role_executor.execute (8500.4ms) → {"success": true}
    └─← execute_mission (9500.5ms) → {"success": true}
  └─← execute (15000.0ms) → {"success": true}

✅ Completed in 15.00s
================================================================================
```

---

## 性能监控

### 1. Event Store系统

系统自动记录事件:

```python
from src.core.events import EventStore, EventType

event_store = EventStore(storage_dir="logs/events")

# 查看事件统计
stats = event_store.get_event_statistics(session_id)
print(f"Total Events: {stats['total_events']}")
print(f"API Calls: {stats['api_calls']}")
print(f"Errors: {stats['errors']}")
```

### 2. Cost Tracker

追踪API调用成本:

```python
from src.core.events import CostTracker

cost_tracker = CostTracker(max_budget_usd=10.0)

# 记录成本
cost_record = cost_tracker.record_cost(
    session_id="abc123",
    agent_type="executor",
    model="claude-sonnet-4-5",
    token_usage=TokenUsage(input_tokens=1000, output_tokens=500),
    duration_seconds=5.0
)

# 检查预算
budget_status = cost_tracker.check_budget("abc123")
print(f"Budget Status: {budget_status}")
```

### 3. 查看执行报告

每次运行结束会生成报告:

```
============================================================
📊 Final Reports
============================================================
💰 Total Cost: $1.2345
📈 Total Tokens: 15,234
🔧 Total API Calls: 12
📋 Total Events: 45
🎭 Persona Switches: 2
============================================================
```

### 4. 导出事件数据

```python
# 保存事件到JSON
event_file = event_store.save_to_file(session_id)
print(f"Events saved to: {event_file}")

# 读取并分析
import json
with open(event_file) as f:
    events = json.load(f)

for event in events:
    print(f"{event['timestamp']}: {event['type']}")
```

---

## 常见调试场景

### 场景1: 任务卡在ReAct循环

**症状**: 日志显示 "ReAct Step 1/30" 但无进展

**调试步骤**:
1. 检查 `executor.py` 的 `execute_task()` 方法
2. 在循环处设置断点: [executor.py:~150]
3. 查看 `thoughts`, `observations` 变量
4. 检查LLM返回格式是否正确

**关键代码位置**:
```
executor.py:
  line 100: async def execute_task()
  line 150: while iteration < max_iterations:
  line 180: thought, action = self._parse_response(response)
```

### 场景2: Leader任务分解失败

**症状**: "Failed to decompose goal"

**调试步骤**:
1. 检查 `mission_decomposer.py` 的 `decompose()` 方法
2. 查看 LLM prompt是否正确构建
3. 检查返回的JSON解析
4. 查看文件: `logs/trace/<mission_id>_decompose.md`

**关键代码位置**:
```
mission_decomposer.py:
  line 50: async def decompose()
  line 80: response, _ = await run_claude_prompt(...)
  line 90: missions_data = extract_json(response)
```

### 场景3: Role Executor验证失败

**症状**: "Validation failed" 但文件已存在

**调试步骤**:
1. 检查 `role_executor.py` 的 `_validate_outputs()` 方法
2. 查看验证规则配置
3. 检查文件路径是否正确 (绝对路径 vs 相对路径)
4. 设置断点: [role_executor.py:~350]

**关键代码位置**:
```
role_executor.py:
  line 330: async def _validate_outputs()
  line 350: for rule in self.role.output_standard.validation_rules:
  line 400: return {"passed": passed, "errors": errors}
```

### 场景4: Reflection Loop无限循环

**症状**: 反射循环达到 max_retries

**调试步骤**:
1. 检查 `_execute_reflection_loop()` 方法
2. 查看 critic prompt 是否合理
3. 检查 LLM 返回的issues是否有效
4. 设置断点: [role_executor.py:822]

**关键代码位置**:
```
role_executor.py:
  line 786: async def _execute_reflection_loop()
  line 822: for iteration in range(1, max_retries + 1):
  line 840: issues_found = self._parse_review_for_issues(review_result)
```

---

## 监控仪表板 (TODO)

可以创建一个实时监控面板:

```python
# 监控日志文件并实时显示
import asyncio
from pathlib import Path

async def monitor_log_file(log_path: str):
    """实时监控日志文件"""
    with open(log_path, 'r') as f:
        while True:
            line = f.readline()
            if line:
                # 解析并显示关键指标
                print(line.strip())
            else:
                await asyncio.sleep(0.1)

# 运行监控
asyncio.run(monitor_log_file("logs/workflow.log"))
```

---

## 快速调试命令

```bash
# 1. 运行调试模式
python src/main.py

# 2. 查看最近日志
tail -n 100 logs/workflow.log

# 3. 搜索错误
grep "ERROR" logs/workflow.log

# 4. 查看特定会话
cat logs/workflow.log | grep "SESSION_ID"

# 5. 统计API调用
grep "API_CALL" logs/workflow.log | wc -l

# 6. 查看Planner追踪
ls -lh logs/trace/

# 7. 清除调试数据
rm -rf debug_workspace logs/debug state/debug
```

---

## 总结

### 最有效的调试方法:

1. **使用DEBUG日志级别** - 看到所有执行细节
2. **在关键位置设置断点** - 暂停执行查看变量
3. **查看trace文件** - 理解执行路径
4. **监控日志实时输出** - 发现问题第一时间知道
5. **使用config_debug.yaml** - 降低成本和复杂度

### 调试流程:

```
发现问题 → 查看日志 → 设置断点 → 单步执行 → 找到原因 → 修复 → 验证
```

### 关键监控指标:

- ✅ 任务完成率
- ✅ API调用次数
- ✅ 执行时间
- ✅ 成本消耗
- ✅ 错误频率

---

*文档生成时间: 2026-01-02*
*适用于: Claude Code Auto v4.0*
