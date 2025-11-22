# 系统流程图与日志输出标准

**版本**: v3.1 (包含验证修复和路径修复)
**日期**: 2025-11-22
**状态**: ✅ 生产标准

---

## 📊 完整系统流程图

### 1. 主流程 (main.py)

```
┌─────────────────────────────────────────────────────────────────┐
│                    启动 Claude Code Auto                         │
│                                                                  │
│  1. 加载配置 (config.yaml)                                       │
│  2. 初始化日志系统                                              │
│  3. 创建工作目录 (demo_act)                                      │
│  4. 初始化事件存储 & 成本追踪器                                 │
│  5. SDK健康检查                                                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
         ┌─────────────────────────────────┐
         │  检测执行模式                    │
         │  1. Leader Mode (v4.0)?         │
         │  2. Team Mode (v3.1)?           │
         │  3. Original Mode (v2.0)?       │
         └────┬────────────────┬───────────┘
              │                │
    ┌─────────┘                └──────────┐
    │                                     │
    ▼                                     ▼
┌──────────────────┐              ┌──────────────────┐
│  Leader Mode     │              │  Team Mode       │
│  (v4.0)          │              │  (v3.1)          │
│  Disabled        │              │  ✅ Active       │
└──────────────────┘              └─────────┬────────┘
                                            │
                                            ▼
                    ┌────────────────────────────────────────┐
                    │         Team Mode 工作流                │
                    └────────────────────────────────────────┘
```

### 2. Team Mode 详细流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    Team Mode 激活                                │
│                                                                  │
│  1. 检测到 initial_prompt                                        │
│  2. 加载所有角色定义 (roles/*.yaml)                             │
│  3. 创建 ExecutorAgent, ResearcherAgent                         │
│  4. 初始化 TeamAssembler                                        │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               TeamAssembler.assemble_team()                      │
│                                                                  │
│  Input: initial_prompt + goal                                   │
│  Process:                                                        │
│    1. LLM分析任务需求                                           │
│    2. 选择合适的角色                                            │
│    3. 确定执行顺序                                              │
│  Output: List[Role] with suggested order                        │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│            DependencyResolver.resolve_order()                    │
│                                                                  │
│  Input: List[Role] + suggested order                            │
│  Process:                                                        │
│    1. 构建依赖关系图                                            │
│    2. 拓扑排序                                                  │
│    3. 验证无循环依赖                                            │
│  Output: Dependency-correct order                               │
│                                                                  │
│  ⚠️ If LLM order ≠ Dependency order:                            │
│     Log warning and use dependency-correct order                │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              TeamOrchestrator.execute()                          │
│                                                                  │
│  For each role in order:                                        │
│    ├─ Create RoleExecutor                                       │
│    ├─ Execute role mission                                      │
│    ├─ Validate outputs                                          │
│    ├─ Collect results                                           │
│    └─ Pass context to next role                                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │   RoleExecutor.execute()              │
        │   (详见下方)                          │
        └──────────────────────────────────────┘
```

### 3. RoleExecutor 执行循环 (核心)

```
┌─────────────────────────────────────────────────────────────────┐
│                 RoleExecutor.execute()                           │
│                                                                  │
│  Mode: Direct or Planner                                        │
│  Max Iterations: 10 (from role config)                          │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│               初始化循环保护机制 (v3.1.1)                        │
│                                                                  │
│  previous_errors = []                                           │
│  same_error_count = 0                                           │
│  MAX_SAME_ERROR_RETRIES = 2                                     │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │   Mission Execution Loop              │
        │   (iteration 1 to max_iterations)     │
        └──────┬───────────────────────────────┘
               │
               ▼
    ┌─────────────────────────────────────────────┐
    │  Iteration N                                 │
    │                                              │
    │  1. Build Task Prompt                        │
    │     - Success criteria                       │
    │     - Context from previous roles            │
    │     - Output standards                       │
    │     - Validation rules                       │
    │                                              │
    │  2. ExecutorAgent.execute_task()             │
    │     └─> ReAct Loop (见下方)                 │
    │                                              │
    │  3. Validate Outputs                         │
    │     ├─ Format Validation                     │
    │     │  ├─ file_exists                        │
    │     │  ├─ content_check (3种方法) ✨         │
    │     │  ├─ min_length (自适应)                │
    │     │  └─ no_placeholders                    │
    │     │                                         │
    │     └─ Quality Validation (可选)             │
    │        └─ LLM-based scoring                  │
    │                                              │
    │  4. Check Result                             │
    │     ├─ ✅ Passed → Return Success            │
    │     │                                         │
    │     └─ ❌ Failed                              │
    │        ├─ Compare with previous_errors       │
    │        ├─ If same → same_error_count++       │
    │        ├─ If same_error_count >= 2 → BREAK ✨│
    │        └─ Build retry task with errors       │
    └─────────────┬───────────────────────────────┘
                  │
                  ├─→ Continue to next iteration
                  │
                  └─→ Or Exit with result
```

### 4. ExecutorAgent ReAct Loop

```
┌─────────────────────────────────────────────────────────────────┐
│              ExecutorAgent.execute_task()                        │
│                                                                  │
│  1. Resolve work_dir to absolute path                           │
│  2. Create work directory                                       │
│  3. Build system prompt:                                        │
│     - Persona prompt                                            │
│     - ReAct format instructions                                 │
│     - Tool descriptions                                         │
│     - Work directory instruction ✨ (相对路径)                  │
│  4. Initialize ReAct history                                    │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │   ReAct Step Loop                     │
        │   (step 1 to 30)                      │
        └──────┬───────────────────────────────┘
               │
               ▼
    ┌─────────────────────────────────────────────┐
    │  ReAct Step N                                │
    │                                              │
    │  1. Call Claude SDK                          │
    │     - Pass: prompt + history                 │
    │     - CWD: work_dir ✨                       │
    │     - Permission: bypassPermissions          │
    │                                              │
    │  2. Parse Response                           │
    │     ├─ "Final Answer:" found?                │
    │     │  └─> ✅ Task Complete, Return          │
    │     │                                         │
    │     ├─ Parse Action & Action Input           │
    │     │  ├─ Extract action name                │
    │     │  └─ Extract JSON args ✨                │
    │     │      (处理Windows路径反斜杠)            │
    │     │                                         │
    │     └─ Execute Tool                          │
    │        ├─ Get tool from registry             │
    │        ├─ Execute with args                  │
    │        ├─ Get observation                    │
    │        └─ Append to history                  │
    │                                              │
    │  3. Update History                           │
    │     history.append(response + observation)   │
    │                                              │
    │  4. Continue to next step                    │
    └─────────────┬───────────────────────────────┘
                  │
                  ├─→ Continue loop
                  │
                  └─→ Or return Final Answer
```

### 5. Validation 详细流程 (v3.1.1 改进)

```
┌─────────────────────────────────────────────────────────────────┐
│              RoleExecutor._validate_outputs()                    │
│                                                                  │
│  1. Format Validation                                           │
│  2. Quality Validation (if enabled)                             │
│                                                                  │
│  Return: {"passed": bool, "errors": List[str]}                  │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              _validate_format()                                  │
│                                                                  │
│  For each validation rule:                                      │
│    ├─ file_exists                                               │
│    │  └─ Check: work_dir / file exists                          │
│    │                                                             │
│    ├─ content_check ✨ (3-Method Approach)                      │
│    │  └─ For each required section:                             │
│    │     ├─ Method 1: Exact match                               │
│    │     │  if required in content: ✅                           │
│    │     │                                                       │
│    │     ├─ Method 2: Flexible regex                            │
│    │     │  pattern = re.escape(required)                       │
│    │     │  pattern.replace(r'\ ', r'\s*')  # 0+ spaces         │
│    │     │  if re.search(pattern, content): ✅                  │
│    │     │                                                       │
│    │     ├─ Method 3: Normalized                                │
│    │     │  norm_req = ' '.join(required.split())               │
│    │     │  norm_content = ' '.join(content.split())            │
│    │     │  if norm_req in norm_content: ✅                     │
│    │     │                                                       │
│    │     └─ ❌ Not Found                                         │
│    │        ├─ Log: Failed to find '{required}'                 │
│    │        ├─ Log: Tried pattern                               │
│    │        ├─ Log: File content preview                        │
│    │        └─ Log: All headers in file                         │
│    │                                                             │
│    ├─ min_length (adaptive)                                     │
│    │  └─ Adjust threshold by task complexity                    │
│    │                                                             │
│    └─ no_placeholders                                           │
│       └─ Check for [TODO], [PLACEHOLDER], etc.                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6. 错误处理与循环保护 (v3.1.1 新增)

```
┌─────────────────────────────────────────────────────────────────┐
│           Infinite Loop Detection & Breaking                     │
│                                                                  │
│  Track: previous_errors, same_error_count                       │
│  Threshold: MAX_SAME_ERROR_RETRIES = 2                          │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
            After Each Validation Failure:
            
    ┌──────────────────────────────────────────┐
    │  1. Get current_errors (sorted)           │
    │  2. Compare with previous_errors          │
    │                                           │
    │  If SAME:                                 │
    │    same_error_count++                     │
    │    Log: "🔁 Same errors X times"         │
    │                                           │
    │    If same_error_count >= 2:              │
    │      Log: "❌ Breaking infinite loop"     │
    │      Return: {                            │
    │        success: false,                    │
    │        exit_reason: "infinite_loop"       │
    │      }                                    │
    │                                           │
    │  If DIFFERENT:                            │
    │    same_error_count = 0                   │
    │    previous_errors = current_errors       │
    │    Continue with retry                    │
    └──────────────────────────────────────────┘
```

---

## 📝 标准日志输出规范

### 1. 日志级别定义

| 级别 | 用途 | 示例 |
|------|------|------|
| **INFO** | 正常流程进展 | 启动、完成、状态变更 |
| **WARNING** | 潜在问题，不影响继续 | 验证失败、降级、重试 |
| **ERROR** | 严重错误，可能导致失败 | 工具执行失败、解析错误 |
| **DEBUG** | 详细调试信息 | 文件内容、中间结果 |

### 2. 日志格式标准

#### 基础格式
```
YYYY-MM-DD HH:MM:SS | LEVEL | [module:function:line] | message
```

#### 示例
```
2025-11-22 18:04:06 | INFO     | [main_v3:info:129] | 🚀 Starting Claude Code Auto v3.0
2025-11-22 18:04:31 | WARNING  | [workflow:warning:132] | ⚠️ Validation failed: [...]
2025-11-22 18:08:31 | ERROR    | [workflow:error:135] | ❌ Failed to parse JSON args
```

### 3. 关键事件日志模板

#### 3.1 系统启动
```python
logger.info("=" * 70)
logger.info("🚀 Starting Claude Code Auto v3.1")
logger.info(f"Goal: {config.task.goal}")
logger.info(f"Work Directory: {work_dir}")
logger.info(f"Mode: {'Team' if team_mode else 'Original'}")
logger.info("=" * 70)
```

**输出示例**:
```
======================================================================
🚀 Starting Claude Code Auto v3.1
Goal: 挖掘出2个在矿井工作这个利基市场的app机会...
Work Directory: D:\AI-agnet\claude-code-auto\demo_act
Mode: Team
======================================================================
```

#### 3.2 Team Assembly
```python
logger.info("🔍 Assembling team based on initial_prompt...")
logger.info(f"📚 Loaded {len(roles)} roles: {[r.name for r in roles]}")
# ... assembly process ...
logger.info(f"✅ Team assembled: {selected_role_names}")
logger.info(f"📋 Execution order: {execution_order}")
```

**输出示例**:
```
🔍 Assembling team based on initial_prompt...
📚 Loaded 8 roles: ['Market-Researcher', 'Creative-Explorer', ...]
✅ Team assembled: ['Market-Researcher', 'Creative-Explorer', ...]
📋 Execution order: ['Market-Researcher', 'Creative-Explorer', ...]
```

#### 3.3 Role Execution Start
```python
logger.info("=" * 70)
logger.info(f"🎭 Role {idx+1}/{total}: {role.name}")
logger.info("=" * 70)
logger.info(f"📋 Mission: {role.mission.goal}")
logger.info(f"✅ Success Criteria:")
for criterion in role.mission.success_criteria:
    logger.info(f"   - {criterion}")
logger.info(f"📁 Work Directory: {work_dir}")
logger.info("=" * 70)
```

**输出示例**:
```
======================================================================
🎭 Role 1/5: Market-Researcher
======================================================================
📋 Mission: Complete in-depth market research and output comprehensive report
✅ Success Criteria:
   - Identify at least 3 target user segments
   - Analyze at least 5 competitors
   - Provide specific market size data
   - Include user pain points analysis
   - Output market-research.md with all sections
📁 Work Directory: D:\AI-agnet\claude-code-auto\demo_act
======================================================================
```

#### 3.4 ReAct Step Progress
```python
logger.info(f"🔄 ReAct Step {step}/{max_steps}")
logger.info(f"🛠️ Calling Tool: {tool_name}")
logger.info(f"🔧 Executing tool: {tool_name} with args: {args}")
# ... after execution ...
logger.debug(f"📤 Tool Result: {result[:200]}...")
```

**输出示例**:
```
🔄 ReAct Step 3/30
🛠️ Calling Tool: write_file
🔧 Executing tool: write_file with args: {'path': 'market-research.md', ...}
📤 Tool Result: Successfully wrote to market-research.md
```

#### 3.5 Validation Process
```python
# Validation start
logger.info("🔍 Validating outputs...")

# For each check
logger.debug(f"   Checking: {rule.type} for {rule.file}")

# Success
logger.info(f"   ✅ {rule.file}: All checks passed")

# Failure - with details
logger.warning(f"   ❌ Failed to find '{required}' in {rule.file}")
logger.debug(f"      Tried pattern: {pattern}")
logger.debug(f"      File headers found:")
for header in headers[:10]:
    logger.debug(f"         - {header}")
```

**输出示例**:
```
🔍 Validating outputs...
   Checking: file_exists for market-research.md
   ✅ market-research.md: File exists
   Checking: content_check for market-research.md
   ❌ Failed to find '## Target Users' in market-research.md
      Tried pattern: ##\s*Target\s*Users
      File headers found:
         - # Mining Industry Market Research
         - ## Executive Summary
         - ## Target User Segments
         - ## Competitive Landscape
```

#### 3.6 Infinite Loop Detection
```python
if current_errors == previous_errors:
    same_error_count += 1
    logger.warning(f"🔁 Same validation errors detected {same_error_count} times in a row")
    
    if same_error_count >= MAX_SAME_ERROR_RETRIES:
        logger.error("=" * 70)
        logger.error("❌ BREAKING INFINITE LOOP")
        logger.error(f"Same errors repeated {same_error_count} times:")
        for error in current_errors[:5]:
            logger.error(f"   - {error}")
        logger.error("Possible causes:")
        logger.error("   1. Validation logic issue")
        logger.error("   2. File path problem")
        logger.error("   3. Agent unable to fix")
        logger.error("=" * 70)
```

**输出示例**:
```
🔁 Same validation errors detected 1 times in a row
🔁 Same validation errors detected 2 times in a row
======================================================================
❌ BREAKING INFINITE LOOP
Same errors repeated 2 times:
   - market-research.md missing section: ## Target Users
   - market-research.md missing section: ## Competitor Analysis
   - market-research.md missing section: ## Opportunities
Possible causes:
   1. Validation logic issue
   2. File path problem
   3. Agent unable to fix
======================================================================
```

#### 3.7 Role Completion
```python
if success:
    logger.info("=" * 70)
    logger.info(f"✅ {role.name} - Mission Accomplished!")
    logger.info(f"📊 Statistics:")
    logger.info(f"   - Iterations: {iterations}")
    logger.info(f"   - Files generated: {len(outputs)}")
    logger.info(f"   - Validation: Passed")
    logger.info("=" * 70)
else:
    logger.error("=" * 70)
    logger.error(f"❌ {role.name} - Mission Failed")
    logger.error(f"📊 Statistics:")
    logger.error(f"   - Iterations: {iterations}/{max_iterations}")
    logger.error(f"   - Last errors: {validation_errors[:3]}")
    logger.error(f"   - Exit reason: {exit_reason}")
    logger.error("=" * 70)
```

**输出示例** (成功):
```
======================================================================
✅ Market-Researcher - Mission Accomplished!
📊 Statistics:
   - Iterations: 3
   - Files generated: 1
   - Validation: Passed
======================================================================
```

**输出示例** (失败):
```
======================================================================
❌ Market-Researcher - Mission Failed
📊 Statistics:
   - Iterations: 3/10
   - Last errors: ['market-research.md missing section: ## Target Users', ...]
   - Exit reason: infinite_loop_detected
======================================================================
```

#### 3.8 Final Summary
```python
logger.info("=" * 70)
logger.info("🎉 EXECUTION COMPLETE")
logger.info("=" * 70)
logger.info(f"📊 Overall Statistics:")
logger.info(f"   Total Roles: {total_roles}")
logger.info(f"   Successful: {successful_roles}")
logger.info(f"   Failed: {failed_roles}")
logger.info(f"   Total Cost: ${total_cost:.2f}")
logger.info(f"   Duration: {duration:.1f}s")
logger.info(f"📁 Output Directory: {work_dir}")
logger.info(f"📄 Generated Files:")
for file in generated_files:
    logger.info(f"   - {file}")
logger.info("=" * 70)
```

**输出示例**:
```
======================================================================
🎉 EXECUTION COMPLETE
======================================================================
📊 Overall Statistics:
   Total Roles: 5
   Successful: 4
   Failed: 1
   Total Cost: $2.35
   Duration: 345.2s
📁 Output Directory: D:\AI-agnet\claude-code-auto\demo_act
📄 Generated Files:
   - market-research.md
   - app-idea-1.md
   - app-idea-2.md
======================================================================
```

---

## 🎨 日志可视化建议

### 1. 使用Emoji增强可读性

| 阶段 | Emoji | 用途 |
|------|-------|------|
| 启动 | 🚀 | 系统启动、模式激活 |
| 进行中 | 🔄 | 循环、迭代、处理中 |
| 成功 | ✅ | 完成、通过、成功 |
| 失败 | ❌ | 错误、失败、拒绝 |
| 警告 | ⚠️ | 警告、降级、重试 |
| 信息 | 📊📋📁📄🎯 | 统计、任务、目录、文件、目标 |
| 工具 | 🛠️🔧 | 工具调用、执行 |
| 角色 | 🎭👤 | 角色、人员 |
| 搜索 | 🔍 | 查找、验证、检查 |
| 循环 | 🔁 | 重复、循环检测 |
| 庆祝 | 🎉 | 最终成功 |

### 2. 使用分隔线增强结构

```python
# 主要章节
logger.info("=" * 70)

# 次要章节
logger.info("-" * 70)

# 列表项
logger.info(f"   - Item")
logger.info(f"      - Sub-item")
```

### 3. 进度指示

```python
# 当前步骤/总步骤
logger.info(f"🎭 Role {idx+1}/{total}: {role.name}")
logger.info(f"🔄 ReAct Step {step}/{max_steps}")
logger.info(f"Iteration {iteration}/{max_iterations}")

# 百分比
logger.info(f"Progress: {completed}/{total} ({completed/total*100:.1f}%)")
```

---

## 🔧 实现代码示例

### logging_utils.py (建议新增)

```python
"""
Logging utilities for consistent log formatting
"""

def log_section_start(logger, title: str, level: int = 1):
    """Log section start with appropriate separator"""
    sep = "=" if level == 1 else "-"
    logger.info(sep * 70)
    logger.info(title)
    logger.info(sep * 70)

def log_section_end(logger, level: int = 1):
    """Log section end"""
    sep = "=" if level == 1 else "-"
    logger.info(sep * 70)

def log_statistics(logger, stats: dict, prefix: str = ""):
    """Log statistics in consistent format"""
    logger.info(f"{prefix}📊 Statistics:")
    for key, value in stats.items():
        logger.info(f"{prefix}   - {key}: {value}")

def log_file_list(logger, files: list, prefix: str = ""):
    """Log file list"""
    logger.info(f"{prefix}📄 Files:")
    for file in files:
        logger.info(f"{prefix}   - {file}")

def log_role_execution(logger, role_name: str, index: int, total: int):
    """Log role execution start"""
    log_section_start(logger, f"🎭 Role {index+1}/{total}: {role_name}")

def log_validation_result(logger, passed: bool, errors: list = None):
    """Log validation result"""
    if passed:
        logger.info("   ✅ Validation: PASSED")
    else:
        logger.warning("   ❌ Validation: FAILED")
        if errors:
            logger.warning("   Errors:")
            for error in errors[:5]:  # Limit to first 5
                logger.warning(f"      - {error}")
```

### 使用示例

```python
from src.utils.logging_utils import (
    log_section_start,
    log_statistics,
    log_validation_result
)

# In role_executor.py
log_section_start(logger, f"🎭 {self.role.name} - Mission Start")

# ... execution ...

log_statistics(logger, {
    "Iterations": iteration,
    "Files Generated": len(outputs),
    "Cost": f"${cost:.2f}"
})

log_validation_result(logger, validation['passed'], validation.get('errors'))
```

---

## 📊 推荐日志分析工具

### 1. 实时监控

```bash
# Linux/Mac
tail -f logs/claude_code_auto.log | grep -E '(✅|❌|⚠️|🔁)'

# Windows PowerShell
Get-Content -Path logs/claude_code_auto.log -Wait | Select-String -Pattern '(✅|❌|⚠️|🔁)'
```

### 2. 错误统计

```bash
# 统计各类错误
grep '❌' logs/claude_code_auto.log | wc -l
grep '⚠️' logs/claude_code_auto.log | wc -l
grep '🔁 Same validation' logs/claude_code_auto.log | wc -l
```

### 3. 性能分析

```bash
# 提取耗时统计
grep 'Duration:' logs/claude_code_auto.log
grep 'Iterations:' logs/claude_code_auto.log
```

---

## ✅ 结论

这份文档提供了：
1. **完整系统流程图** - 6个层级的详细流程
2. **标准日志格式** - 统一的日志输出规范
3. **关键事件模板** - 8种常见场景的日志模板
4. **可视化建议** - Emoji、分隔线、进度指示
5. **实现工具** - logging_utils.py 示例代码

遵循这个标准将使日志：
- ✅ 更易读
- ✅ 更结构化
- ✅ 更易于调试
- ✅ 更适合生产环境

---

**文档版本**: 1.0  
**作者**: Claude Code Agent  
**日期**: 2025-11-22
