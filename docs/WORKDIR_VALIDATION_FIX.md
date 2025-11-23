# 工作目录验证问题 - 完整分析与修复方案

## 🐛 问题描述

系统在验证 AI Agent 生成的文件时，报告"文件不存在"错误，导致无限循环并触发熔断机制：

```
❌ Failed to find '## Concept Expansion' in creative_exploration_report.md
❌ Breaking infinite loop: Same errors repeated 2 times.
   Errors: ['Missing required file: market-research.md']...
```

## 🔍 根本原因分析

### 问题流程

1. **文件创建阶段** ✅
   - `ExecutorAgent` 切换到 `work_dir` (例如: `demo_act`)
   - AI Agent 在 `demo_act/` 下创建文件
   - 文件实际位置: `demo_act/market-research.md`

2. **验证阶段** ❌
   - `RoleExecutor` 使用 `self.work_dir / rule.file` 查找文件
   - 理论上应该查找: `demo_act/market-research.md`
   - **但实际可能在错误的目录查找**

3. **无限循环触发**
   - 相同错误连续出现 2 次
   - 系统判定为无法修复的错误
   - 触发熔断机制退出

### 可能的具体原因

#### 原因1: 工作目录在 Windows 上配置为绝对路径

```yaml
# config.yaml (Windows 系统)
directories:
  work_dir: "D:\\AI-agnet\\claude-code-auto-v4\\claude-code-auto\\demo_act"  # 绝对路径
```

如果配置为绝对路径，不同组件可能解析不一致。

#### 原因2: work_dir 类型不一致

```python
# RoleExecutor 初始化
self.work_dir = Path(work_dir)  # 可能是 str

# 验证时
file_path = self.work_dir / rule.file  # 如果 self.work_dir 是 str，会出问题
```

#### 原因3: CWD 恢复时机问题

```python
# executor.py:224-227
finally:
    os.chdir(original_cwd)  # 恢复到项目根目录
    logger.info(f"📂 Restored CWD to {original_cwd}")
```

如果验证发生在 CWD 恢复**之后**，而代码依赖相对路径，则会失败。

## 🛠️ 修复方案

### 方案1: 确保 work_dir 统一为 Path 对象（推荐）

**修改位置**: `src/core/team/role_executor.py:56-57`

```python
# 修改前
self.work_dir = Path(work_dir)

# 修改后
self.work_dir = Path(work_dir).resolve()  # 转换为绝对路径，消除歧义
logger.info(f"📁 RoleExecutor work_dir (absolute): {self.work_dir}")
```

**优点**:
- 绝对路径消除所有相对路径歧义
- 不受 CWD 变化影响
- 跨平台兼容（Windows/Linux）

### 方案2: 添加详细的验证日志

**修改位置**: `src/core/team/role_executor.py:432-435`

```python
if rule_type == "file_exists":
    file_path = self.work_dir / rule.file

    # 添加调试信息
    logger.debug(f"🔍 Checking file existence:")
    logger.debug(f"   work_dir: {self.work_dir}")
    logger.debug(f"   rule.file: {rule.file}")
    logger.debug(f"   combined path: {file_path}")
    logger.debug(f"   absolute path: {file_path.resolve()}")
    logger.debug(f"   exists: {file_path.exists()}")
    logger.debug(f"   current CWD: {os.getcwd()}")

    if file_path.exists():
        logger.debug(f"   ✅ File found")
    else:
        # 尝试在当前 CWD 查找
        alt_path = Path(os.getcwd()) / rule.file
        if alt_path.exists():
            logger.warning(f"   ⚠️ File found in CWD instead: {alt_path}")
            logger.warning(f"   This indicates a work_dir mismatch issue!")

        errors.append(f"Missing required file: {rule.file}")
```

### 方案3: 强制验证时切换到 work_dir

**修改位置**: `src/core/team/role_executor.py:407`

```python
async def _validate_outputs(self) -> Dict[str, Any]:
    """Validate outputs against validation rules (format + optional quality)"""

    # 保存当前 CWD
    original_cwd = os.getcwd()

    # 切换到 work_dir 确保相对路径正确
    os.chdir(self.work_dir)
    logger.debug(f"📂 Switched to work_dir for validation: {self.work_dir}")

    try:
        errors = []

        # 1. Format validation (original rules)
        format_errors = self._validate_format()
        errors.extend(format_errors)

        # 2. Semantic quality validation (optional, costs tokens)
        if self.role.enable_quality_check:
            quality_errors = await self._validate_quality()
            errors.extend(quality_errors)

        return {
            "passed": len(errors) == 0,
            "errors": errors
        }
    finally:
        # 恢复原始 CWD
        os.chdir(original_cwd)
        logger.debug(f"📂 Restored CWD after validation: {original_cwd}")
```

## 🧪 诊断步骤

### 步骤1: 运行诊断脚本

```bash
python diagnose_workdir.py
```

这将显示:
- 配置文件中的 work_dir 设置
- 实际文件创建位置
- 可能的路径不一致

### 步骤2: 启用调试日志

修改 `config.yaml`:

```yaml
logging:
  level: "DEBUG"  # 从 INFO 改为 DEBUG
```

### 步骤3: 运行任务并检查日志

重新运行你的任务，查找以下关键日志：

```
📁 Work directory: /path/to/work_dir
📂 Changed CWD from X to Y
📂 Restored CWD to Z
🔍 Checking file existence:
   work_dir: ...
   file_path: ...
```

对比这些路径，找出不一致的地方。

## ✅ 推荐实施顺序

1. **立即修复** (方案1): 使用绝对路径
2. **短期改进** (方案2): 添加详细日志
3. **长期优化** (方案3): 重构验证流程

## 🧪 测试验证

修复后运行:

```bash
# 运行测试
pytest tests/test_role_executor.py::test_validation_file_exists -v

# 运行完整集成测试
python -m pytest tests/test_integration_team.py -v
```

## 📝 相关文件

- 配置: `config.yaml`
- 核心逻辑: `src/core/team/role_executor.py`
- 执行器: `src/core/agents/executor.py`
- 诊断脚本: `diagnose_workdir.py`

## 🔗 相关问题

- #11 - Team Mode 架构分析
- COMPLETE_FIX_SUMMARY.md - CWD 位置锁定修复

---

**创建日期**: 2025-11-23
**状态**: 🔍 诊断中
**优先级**: 🔴 高
