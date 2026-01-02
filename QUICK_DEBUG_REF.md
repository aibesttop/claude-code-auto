# 🔧 快速调试参考卡

## 立即开始调试

### 方法1: 实时监控 (推荐)

```bash
# 终端1: 启动程序
python src/main.py

# 终端2: 实时监控日志
python monitor.py
```

### 方法2: VS Code调试

1. 打开 `main.py`
2. 在行号左侧点击设置断点
3. 按 `F5` 启动调试
4. 使用 `F10` 单步, `F11` 进入

---

## 关键断点位置

| 文件 | 行号 | 说明 |
|------|------|------|
| main.py | 104 | Leader开始执行 |
| leader_agent.py | 140 | execute()入口 |
| leader_agent.py | 220 | 任务循环 |
| role_executor.py | 90 | 角色执行 |
| role_executor.py | 129 | ReAct循环 |
| executor.py | 100 | ReAct执行 |

---

## 查看日志

```bash
# 实时查看所有日志
python monitor.py

# 只看重要日志
python monitor.py --important

# 查看trace文件
python monitor.py --trace

# 查看事件统计
python monitor.py --events

# 查看所有信息
python monitor.py --all
```

---

## 搜索关键词

```bash
# 错误
grep "ERROR" logs/workflow.log

# 警告
grep "WARNING" logs/workflow.log

# Leader决策
grep "Leader Agent" logs/workflow.log

# ReAct步骤
grep "ReAct Step" logs/workflow.log

# 反射循环
grep "Reflection" logs/workflow.log
```

---

## 常见问题速查

### ❌ 问题: ReAct卡住
**位置**: executor.py:150
**原因**: LLM返回格式错误
**解决**: 检查prompt和parse_response()

### ❌ 问题: 任务分解失败
**位置**: mission_decomposer.py:80
**原因**: JSON解析失败
**解决**: 查看trace文件,检查LLM输出

### ❌ 问题: 验证失败
**位置**: role_executor.py:350
**原因**: 文件不存在或内容不符
**解决**: 检查文件路径和验证规则

### ❌ 问题: 反射循环不收敛
**位置**: role_executor.py:822
**原因**: Critic prompt过于严格
**解决**: 减少aspects数量或降低max_retries

---

## 调试配置文件

```yaml
# config_debug.yaml
logging:
  level: "DEBUG"  # 详细的DEBUG日志

cost_control:
  max_budget_usd: 5.0  # 低限额测试

safety:
  max_iterations: 10  # 少量迭代

research:
  enabled: false  # 禁用节省成本
```

使用:
```bash
python src/main.py --config config_debug.yaml
```

---

## 关键文件位置

```
项目根目录/
├── src/main.py                    # 入口
├── src/core/leader/
│   ├── leader_agent.py           # Leader协调器
│   └── mission_decomposer.py     # 任务分解
├── src/core/team/
│   ├── role_executor.py          # 角色执行器
│   └── team_assembler.py         # 团队组装器
├── src/core/agents/
│   ├── executor.py               # ReAct执行器
│   └── planner.py                # 规划器
├── logs/
│   ├── workflow.log              # 主日志
│   ├── trace/                    # 执行追踪
│   └── events/                   # 事件存储
└── monitor.py                    # 监控脚本
```

---

## 执行流程快速参考

```
main.py
  ↓
run_leader_mode() [line 58]
  ↓
leader.execute() [line 104]
  ├─→ decompose()     # 分解任务
  ├─→ assemble_team() # 组装团队
  ├─→ 执行循环 [line 220]
  │    └─→ execute_mission() [line 280]
  │         └─→ role_executor.execute() [line 90]
  │              ├─→ _execute_direct() [line 110]
  │              │    └─→ ReAct循环 [line 129]
  │              └─→ _execute_reflection_loop() [line 786]
  └─→ _integrate_outputs() [line 260]
```

---

## 性能指标

正常执行参考值:

| 指标 | 正常范围 |
|------|---------|
| 单次API调用 | 2-10秒 |
| 任务分解 | 10-30秒 |
| 单个Mission | 1-5分钟 |
| Reflection迭代 | 1-2分钟 |
| 完整工作流 | 5-30分钟 |

---

## 日志标记含义

| 标记 | 含义 |
|------|------|
| 🎯 | Leader Agent |
| 🔄 | ReAct循环 |
| 🎭 | Role执行 |
| ✅ | 成功 |
| ❌ | 失败 |
| ⚠️ | 警告 |
| 🔍 | 调试/追踪 |

---

## 监控快捷命令

```bash
# 1. 查看最后100行
tail -n 100 logs/workflow.log

# 2. 实时监控
tail -f logs/workflow.log

# 3. 查看trace文件
ls -lh logs/trace/

# 4. 查看事件
cat logs/events/*.json | jq '.type' | sort | uniq -c

# 5. 清除调试数据
rm -rf debug_workspace logs/debug state/debug
```

---

## 实用技巧

### 技巧1: 过滤日志
```bash
# 只看Leader相关日志
grep "Leader Agent" logs/workflow.log | tail -f

# 只看错误和警告
grep -E "(ERROR|WARNING)" logs/workflow.log
```

### 技巧2: 统计API调用
```bash
# 统计API调用次数
grep "Claude API call" logs/workflow.log | wc -l

# 统计每个角色的调用
grep "Role:" logs/workflow.log | cut -d: -f2 | sort | uniq -c
```

### 技巧3: 查看最慢的步骤
```bash
# 查看执行时间(如果日志包含)
grep "duration" logs/workflow.log | sort -t: -k3 -n
```

### 技巧4: 对比两次运行
```bash
# 比较两个日志文件
diff <(grep "STEP" logs/run1.log) <(grep "STEP" logs/run2.log)
```

---

## 紧急修复

### 修复1: 降低迭代次数
```yaml
# config.yaml
safety:
  max_iterations: 5  # 从30降到5
```

### 修复2: 禁用反思
```yaml
# roles/*.yaml
reflection:
  enabled: false  # 禁用reflection
```

### 修复3: 禁用工作流
```yaml
# roles/*.yaml
workflow:
  next_state: null  # 禁用自动跳转
```

---

## 获取帮助

```bash
# 查看监控帮助
python monitor.py --help

# 查看配置
python src/main.py --help

# 运行测试
python -m pytest tests/
```

---

*最后更新: 2026-01-02*
*版本: v4.0*
