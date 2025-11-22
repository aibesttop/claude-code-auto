# OutputIntegrator 使用指南

**版本**: v1.0
**创建日期**: 2025-11-22

---

## 📖 简介

**OutputIntegrator** 是 Claude Code Auto v4.0 的核心输出集成系统，提供专业的多格式报告生成和交付物组织功能。

### 核心功能

1. ✅ **智能集成** - 自动收集并整合所有任务输出
2. ✅ **多格式报告** - 支持 Markdown、JSON、HTML、Text 4种格式
3. ✅ **自动组织** - 创建结构化的交付物目录
4. ✅ **数据分析** - 自动计算成功率、质量分数、成本等指标
5. ✅ **智能建议** - 根据执行结果生成改进建议

---

## 🚀 快速开始

### 基础用法

```python
from src.core.output import OutputIntegrator, OutputFormat

# 1. 创建集成器
integrator = OutputIntegrator(work_dir="./output")

# 2. 集成任务输出
integrated = integrator.integrate(
    session_id="my-session-001",
    goal="完成市场调研和需求文档",
    mission_results={
        "mission_1": {
            "mission_type": "market_research",
            "goal": "市场调研",
            "role": "Market-Researcher",
            "outputs": {
                "report.md": "# 市场分析...",
            },
            "iterations": 2,
            "quality_score": 85.0,
            "cost_usd": 0.25,
            "success": True
        }
    }
)

# 3. 生成报告
reports = integrator.generate_reports(
    integrated,
    formats=[OutputFormat.MARKDOWN, OutputFormat.JSON]
)

# 4. 组织交付物
integrator.organize_deliverables(integrated)

print(f"报告生成完成:")
for fmt, path in reports.items():
    print(f"  {fmt.value}: {path}")
```

---

## 📊 报告模板

### 1. COMPREHENSIVE (综合报告) - 默认

**适用场景**: 完整的项目报告，包含所有细节

**包含内容**:
- 📊 执行摘要（目标、状态、统计）
- 📈 关键指标（完成率、资源消耗）
- 📋 任务详情（每个任务的执行指标）
- 🎯 质量分析（质量分布、趋势）
- 💰 成本分析（按任务分解）
- ⏱️ 执行时间线
- 📦 交付物清单
- 💡 建议和下一步

**示例**:
```python
from src.core.output.report_generator import ReportTemplate

content = generator.generate(integrated, ReportTemplate.COMPREHENSIVE)
```

### 2. EXECUTIVE (执行摘要)

**适用场景**: 高层汇报，快速了解整体情况

**包含内容**:
- 执行摘要
- 关键指标
- 交付物清单

**示例**:
```python
content = generator.generate(integrated, ReportTemplate.EXECUTIVE)
```

### 3. TECHNICAL (技术报告)

**适用场景**: 开发者视角，关注技术细节

**包含内容**:
- 任务详情（含技术参数）
- 质量分析
- 成本分析
- 时间线

**示例**:
```python
content = generator.generate(integrated, ReportTemplate.TECHNICAL)
```

### 4. SIMPLE (简单报告)

**适用场景**: 快速浏览，只看基本信息

**包含内容**:
- 基本信息
- 关键指标
- 任务列表

---

## 🎨 报告特性

### 可视化元素

#### 1. 进度条
```markdown
[████████░░] 80.0%
```

#### 2. 状态徽章
- 🟢 **优秀** (成功率 ≥ 90%)
- 🟡 **良好** (成功率 ≥ 70%)
- 🟠 **一般** (成功率 ≥ 50%)
- 🔴 **需改进** (成功率 < 50%)

#### 3. 质量等级
- **优秀** (90-100)
- **良好** (70-89)
- **一般** (50-69)
- **较差** (<50)

### 自动分析

#### 质量分析
```markdown
### 质量分布
| 等级 | 数量 |
|------|------|
| 优秀 (90-100) | 2 |
| 良好 (70-89) | 3 |
| 一般 (50-69) | 1 |
| 较差 (<50) | 0 |

### 质量趋势
1. mission_1: [████████░░] 85.5
2. mission_2: [█████████░] 92.0
3. mission_3: [███████░░░] 78.0
```

#### 成本分析
```markdown
| 任务 | 成本 | 占比 |
|------|------|------|
| mission_1 | $0.2500 | 31.2% |
| mission_2 | $0.3500 | 43.7% |
| mission_3 | $0.2000 | 25.0% |
```

### 智能建议

系统会根据执行结果自动生成建议：

**成功率低 (<70%):**
```markdown
### ⚠️ 需要关注
1. 检查失败任务的验证错误
2. 调整质量阈值或增加重试次数
3. 优化任务分解策略
```

**质量分数低 (<70):**
```markdown
### 📈 质量改进
1. 明确化成功标准
2. 增强角色prompt指导
3. 加入更多验证规则
```

**成本高 (>$5):**
```markdown
### 💰 成本优化
1. 使用更便宜的模型（如Haiku）
2. 减少不必要的迭代
3. 优化prompt长度
```

**成功率高 (≥90%):**
```markdown
### ✅ 执行优秀
继续保持当前策略！
```

---

## 📁 文件组织

### 自动生成的目录结构

```
work_dir/
├── deliverables/           # 交付物目录
│   └── {session_id}/
│       ├── mission_1/      # 每个任务独立目录
│       │   ├── file1.md
│       │   └── file2.md
│       ├── mission_2/
│       │   └── file3.md
│       └── README.md       # 项目说明（自动生成）
│
└── reports/                # 报告目录
    ├── {session_id}_report.md
    ├── {session_id}_report.json
    ├── {session_id}_report.html
    └── {session_id}_report.txt
```

### Deliverables README

自动生成的 `README.md` 包含:
- 项目信息（会话ID、目标、时间）
- 执行汇总
- 目录结构
- 任务清单（含状态、质量分数）

---

## 🔧 高级用法

### 自定义元数据

```python
metadata = {
    "intervention_count": 5,
    "model": "claude-sonnet-4-5",
    "custom_field": "custom_value"
}

integrated = integrator.integrate(
    session_id=session_id,
    goal=goal,
    mission_results=results,
    metadata=metadata  # 自定义元数据
)
```

### 选择性格式输出

```python
# 只生成Markdown和JSON
reports = integrator.generate_reports(
    integrated,
    formats=[OutputFormat.MARKDOWN, OutputFormat.JSON]
)

# 生成所有格式
reports = integrator.generate_reports(
    integrated,
    formats=[
        OutputFormat.MARKDOWN,
        OutputFormat.JSON,
        OutputFormat.HTML,
        OutputFormat.TEXT
    ]
)
```

### 单独使用ReportGenerator

```python
from src.core.output.report_generator import (
    ReportGenerator,
    ReportTemplate
)

generator = ReportGenerator()

# 生成执行摘要
executive_content = generator.generate(
    integrated,
    ReportTemplate.EXECUTIVE
)

# 保存到自定义位置
Path("custom_report.md").write_text(executive_content)
```

---

## 📈 数据结构

### IntegratedOutput

```python
@dataclass
class IntegratedOutput:
    session_id: str
    goal: str
    mission_outputs: List[MissionOutput]
    summary: Dict[str, Any]
    start_time: float
    end_time: Optional[float]
    reports: Dict[OutputFormat, Path]
```

### MissionOutput

```python
@dataclass
class MissionOutput:
    mission_id: str
    mission_type: str
    goal: str
    role: str
    files: Dict[str, str]        # filename -> content
    iterations: int
    quality_score: float
    cost_usd: float
    duration_seconds: float
    success: bool
    validation_passed: bool
    validation_errors: List[str]
```

### Summary 字段

```python
summary = {
    "total_missions": 3,
    "successful_missions": 3,
    "failed_missions": 0,
    "success_rate": 1.0,
    "total_files_generated": 5,
    "average_quality_score": 85.2,
    "total_cost_usd": 0.8000,
    "total_duration_seconds": 165.2,
    "timestamp": "2025-11-22T18:46:22.791803Z"
}
```

---

## 🧪 测试

### 运行测试脚本

```bash
# 运行完整测试
python test_output_integrator.py

# 查看生成的报告
ls test_output/reports/
cat test_output/reports/*_report.md

# 查看交付物
ls -R test_output/deliverables/
```

### 测试输出示例

```
✅ Generated 4 reports:
   markdown  : test_output/reports/test-session-001_report.md
   json      : test_output/reports/test-session-001_report.json
   html      : test_output/reports/test-session-001_report.html
   text      : test_output/reports/test-session-001_report.txt

📊 SUMMARY
Total Missions:     3
Successful:         3
Success Rate:       100.0%
Files Generated:    5
Average Quality:    85.2/100
Total Cost:         $0.8000
```

---

## 🔗 集成到 Leader Agent

OutputIntegrator 已自动集成到 LeaderAgent：

```python
# LeaderAgent 会自动调用
async def _integrate_outputs(self):
    integrator = OutputIntegrator(self.work_dir)

    integrated = integrator.integrate(
        session_id=self.context.session_id,
        goal=self.context.goal,
        mission_results=self.context.completed_missions
    )

    reports = integrator.generate_reports(integrated)
    integrator.organize_deliverables(integrated)

    return deliverable
```

### 启用 Leader Mode

```yaml
# config.yaml
leader:
  enabled: true  # 启用后自动使用OutputIntegrator
```

---

## 📝 最佳实践

### 1. 提供完整的任务信息

```python
mission_result = {
    "mission_type": "market_research",  # ✅ 明确类型
    "goal": "完整的目标描述",            # ✅ 清晰目标
    "role": "具体的角色名称",            # ✅ 角色信息
    "quality_score": 85.0,              # ✅ 质量分数
    "validation_errors": []             # ✅ 验证信息
}
```

### 2. 合理使用报告模板

- **日常使用**: COMPREHENSIVE (完整信息)
- **向上汇报**: EXECUTIVE (高层摘要)
- **技术讨论**: TECHNICAL (技术细节)
- **快速查看**: SIMPLE (基本信息)

### 3. 定期清理输出

```bash
# 定期清理旧的测试输出
rm -rf test_output/

# 保留重要的交付物
cp -r work_dir/deliverables/ archive/
```

---

## ❓ 常见问题

### Q: 报告中文乱码？
**A**: 确保使用 UTF-8 编码保存和读取文件。

### Q: 如何自定义报告样式？
**A**: 修改 `ReportGenerator` 中的模板方法，或创建新的报告模板。

### Q: 能否支持PDF格式？
**A**: 当前支持 MD/JSON/HTML/TEXT，HTML可转换为PDF。

### Q: 报告太大怎么办？
**A**: 使用 EXECUTIVE 或 SIMPLE 模板，或过滤部分内容。

---

## 🔮 未来计划

- [ ] PDF 导出支持
- [ ] 图表可视化（使用matplotlib/plotly）
- [ ] 报告模板自定义系统
- [ ] 多语言支持（i18n）
- [ ] 实时预览功能

---

## 📚 相关文档

- [Architecture Status Report](../ARCHITECTURE_STATUS.md)
- [Leader Agent Guide](./LeaderAgent-Guide.md)
- [Team Mode Workflow](../AI-Native-Team-Workflow.md)

---

**最后更新**: 2025-11-22
**维护者**: Claude Code Team
**版本**: v1.0
