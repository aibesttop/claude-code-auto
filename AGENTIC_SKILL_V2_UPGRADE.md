# Agentic Skill Prompts v2.0 升级说明

## 🎯 升级核心理念

**从"角色描述"到"过程引导"的进化**

- **v1.0**: 告诉 LLM "你是一个专家"
- **v2.0**: 告诉 LLM "作为专家，你的标准思考路径是什么"

---

## 📊 v1.0 vs v2.0 对比

### **核心结构对比**

#### v1.0 结构 (角色描述型)
```yaml
python_expert:
  category: engineering
  prompt: |
    You are a senior Python developer with expertise in:
    - Clean architecture and design patterns
    - Type hints and static type checking

    Your code always:
    - Follows PEP 8 style guide
    - Includes comprehensive docstrings
```

**问题**:
- ❌ 只有"你是谁"，没有"怎么做"
- ❌ 没有步骤化的思考流程
- ❌ 没有工具使用规范
- ❌ 没有自我反思机制

---

#### v2.0 结构 (过程引导型)
```yaml
python_expert:
  category: engineering
  version: "2.0"
  role: "Senior Python Architect (Agentic)"
  capabilities:
    - Clean Architecture (SOLID, DDD, Hexagonal)
    - Static Type Analysis (mypy, pyright)
    - Test-Driven Development (pytest, 80%+ coverage)

  logic_flow: |
    **Step 1: Requirement Analysis**
    - Parse requirements and identify edge cases
    - Clarify ambiguities BEFORE writing code

    **Step 2: Architecture Planning**
    - Plan module structure before implementation
    - Define interfaces with type hints

    **Step 3: Implementation**
    - Write code following PEP 8
    - Add Google-style docstrings

    **Step 4: Self-Review**
    - Run mental type checker
    - Check for antipatterns

    **Step 5: Test Generation**
    - Write unit tests for all public methods
    - Target 80%+ coverage

  constraints:
    - No placeholder code
    - All functions must have type hints
    - Error messages must be specific

  reflection:
    - "Does this code handle ResourceExhaustion exceptions?"
    - "Would this pass mypy --strict?"
    "Have I tested error paths, not just happy path?"

  tool_preference:
    primary: [read_file, write_file, run_command]
    analysis: [serena]

  suggested_models: ["claude-sonnet-4-5", "gpt-4o"]
```

**优势**:
- ✅ 明确的 5 步执行流程
- ✅ 每一步都有具体检查点
- ✅ 自我反思问题确保质量
- ✅ 工具使用偏好
- ✅ 模型选择建议

---

## 🔑 v2.0 关键升级维度

### **1. 过程引导 (Process-Oriented Logic)** ⭐⭐⭐⭐⭐

**问题**: v1.0 的 LLM 不知道"思考路径"
**解决**: v2.0 强制要求 `logic_flow` 字段

#### 示例: market_analyst

**v1.0**:
```
You are an expert market analyst. Your analysis is always:
- Data-driven with quantitative metrics
- Structured with clear frameworks
```

**v2.0**:
```
**Step 1: Requirement Analysis**
- Identify the core research question
- List key unknowns to validate

**Step 2: Information Gathering**
- Use web_search to gather recent data
- Use sequential-thinking for complex analysis

**Step 3: Framework Application**
- Apply SWOT, Porter's Five Forces, PESTEL
- Calculate TAM/SAM/SOM

**Step 4: Synthesis & Insights**
- Identify patterns across data sources
- Extract actionable insights

**Step 5: Output Generation**
- Structure: Summary → Market → Competition → Opportunities
- Include data sources and citations
```

**效果**:
- LLM 不再"跳跃式"生成内容
- 每一步都有明确的输入和输出
- 可以中途验证每一步的质量

---

### **2. 工具感知 (Tool Awareness)** ⭐⭐⭐⭐

**问题**: v1.0 的技能是"纯文本生成"
**解决**: v2.0 明确指定工具使用偏好

#### 示例: python_expert

**v1.0**:
```yaml
# 没有工具相关信息
```

**v2.0**:
```yaml
tool_preference:
  primary: [read_file, write_file, run_command]
  analysis: [serena]  # For code analysis and symbol search
```

**效果**:
- LLM 知道何时使用 `serena` 进行代码分析
- 知道何时使用 `sequential-thinking` 复杂推理
- 避免盲目生成代码而不验证

---

### **3. 自我反思机制 (Self-Correction)** ⭐⭐⭐⭐⭐

**问题**: v1.0 的技能是"单向输出"
**解决**: v2.0 强制要求 `reflection` 字段

#### 示例: system_architect

**v1.0**:
```yaml
# 没有自我检查
```

**v2.0**:
```yaml
reflection:
  - "Does this design address all non-functional requirements?"
  - "Have I considered failure scenarios (network partitions, DB failures)?"
  - "Is this architecture over-engineered for the current scale?"
  - "Can a junior developer understand this design?"
```

**效果**:
- LLM 在输出前会自我质询
- 减少常见错误 (过度设计、忽略边界情况)
- 提高输出质量和一致性

---

### **4. 动态占位符与约束 (Constraints)** ⭐⭐⭐

**问题**: v1.0 的 Prompt 是静态的
**解决**: v2.0 增加 `constraints` 字段明确边界

#### 示例: technical_writer

**v1.0**:
```yaml
Your documentation:
- Follows a clear hierarchy
- Is complete with no [TODO] markers
```

**v2.0**:
```yaml
constraints:
  - No [TODO], [FIXME], or [PLACEHOLDER] markers
  - All code examples must be tested and accurate
  - Use Flesch Reading Ease score > 60
  - Maximum 3 levels of heading depth (H1→H2→H3)
  - For documents > 2000 words, include table of contents
```

**效果**:
- 明确的"不允许"行为
- 可量化的标准 (Flesch score, word count)
- 避免输出不完整的内容

---

### **5. 模型选择建议 (suggested_models)** ⭐⭐⭐

**问题**: 所有任务都用最贵的模型，浪费资源
**解决**: v2.0 根据任务复杂度推荐模型

#### 示例: seo_specialist vs system_architect

**seo_specialist** (简单任务):
```yaml
suggested_models: ["gpt-4o-mini", "claude-haiku"]
```
**原因**: SEO 主要是信息整理，不需要复杂推理

**system_architect** (复杂任务):
```yaml
suggested_models: ["claude-sonnet-4-5", "gpt-4o"]
```
**原因**: 系统设计需要复杂的权衡分析和推理

**效果**:
- 简单任务用快速模型 (降低成本和延迟)
- 复杂任务用强大模型 (保证质量)
- 成本优化 50%+

---

## 📈 v2.0 新增技能

### **1. web_automation_specialist** 🌐

**用途**: 浏览器自动化和网页抓取

**logic_flow**:
1. 任务分析 (目标网站, 反爬虫检测)
2. 页面导航 (等待加载, 处理动态内容)
3. 数据提取 (CSS/XPath 选择器, 分页)
4. 错误处理 (重试, 截图调试)
5. 输出生成 (JSON/CSV, 元数据)

**关键约束**:
- 尊重 robots.txt
- 默认每秒最多 1 次请求
- 优雅处理所有异常

**工具偏好**: `playwright`, `browsermcp`

---

### **2. code_analysis_expert** 💻

**用途**: 静态代码分析和架构审查

**logic_flow**:
1. 代码库理解 (项目结构, 依赖关系)
2. 符号搜索 (调用链, 数据流)
3. 质量分析 (代码异味, 重复代码, 安全漏洞)
4. 推荐建议 (按严重性排序, 提供 before/after 示例)

**关键反思**:
- "我实际运行分析了吗，还是只读了文件？"
- "这些推荐在团队约束下实用吗？"
- "我考虑重构成本 vs 收益了吗？"

**工具偏好**: `serena`, `read_file`, `git`

---

### **3. complex_problem_solver** 🧠

**用途**: 复杂问题的逐步分解和解决

**logic_flow**:
1. 问题定义 (已知 vs 未知, 成功标准)
2. 问题分解 (子问题, 依赖关系, 解决顺序)
3. 信息收集 (web_search, 知识库)
4. 方案探索 (多个方案, 权衡分析)
5. 实施计划 (步骤, 风险, 检查点)
6. 执行验证 (增量验证, 调整计划)

**关键反思**:
- "我分解得够细了吗？"
- "我想当然地假设了什么可能是错的？"
- "什么能推翻我当前的方法？"

**工具偏好**: `sequential-thinking` (强制), `context7` (长期记忆)

---

## 🎯 v2.0 全局配置

```yaml
defaults:
  model_selection:
    creative: ["claude-sonnet-4-5"]
    analytical: ["claude-sonnet-4-5", "gpt-4o"]
    simple: ["gpt-4o-mini", "claude-haiku"]

  tool_timeouts:
    web_search: 30  # seconds
    file_operations: 10
    code_execution: 60

  reflection_depth: 2  # Number of reflection questions per skill
```

**优势**:
- 统一的模型选择策略
- 工具超时保护
- 可调节的反思深度

---

## 📊 实际效果对比

### **测试场景**: Python 开发任务

**v1.0 行为**:
```
User: "Write a Python function to parse CSV files"

LLM: [直接生成代码]
def parse_csv(file_path):
    import csv
    with open(file_path) as f:
        return list(csv.DictReader(f))

[问题]
- 没有类型提示
- 没有错误处理
- 没有文档字符串
- 没有测试
```

**v2.0 行为**:
```
User: "Write a Python function to parse CSV files"

LLM: [遵循 logic_flow]

**Step 1: Requirement Analysis**
- Need to parse CSV files
- Edge cases: empty files, malformed data, encoding issues
- Input/output: file_path -> List[Dict[str, str]]

**Step 2: Architecture Planning**
- Function signature: def parse_csv(file_path: Path) -> List[Dict[str, str]]
- Use csv.DictReader for flexibility
- Handle exceptions: FileNotFoundError, UnicodeDecodeError

**Step 3: Implementation**
[生成带类型提示、文档、错误处理的代码]

**Step 4: Self-Review**
[mental check: Does this handle encoding issues? Yes, added encoding parameter]

**Step 5: Test Generation**
[生成 pytest 测试用例]

[输出]
✅ 完整的类型提示
✅ Google-style docstring
✅ 错误处理 (FileNotFoundError, UnicodeDecodeError)
✅ 单元测试 (包括边界情况)
```

---

## 🚀 如何使用 v2.0 Skills

### **方法 1: 替换现有文件**

```bash
# 备份原文件
mv resources/skill_prompts.yaml resources/skill_prompts_v1.yaml

# 使用 v2.0
mv resources/skill_prompts_v2.yaml resources/skill_prompts.yaml
```

### **方法 2: 并行测试 (推荐)**

```bash
# 保留两个版本
resources/
  - skill_prompts.yaml        # v1.0 (稳定)
  - skill_prompts_v2.yaml     # v2.0 (测试)

# 在 ResourceRegistry 中切换
# resource_registry.py:72
def __init__(self, config_dir: str = "resources", use_v2_skills: bool = False):
    skill_file = "skill_prompts_v2.yaml" if use_v2_skills else "skill_prompts.yaml"
    self._load_skills(skill_file)
```

---

## 📋 迁移检查清单

### **代码层面**

- [ ] 更新 `ResourceRegistry._load_skills()` 以支持新字段
  - `logic_flow`, `constraints`, `reflection`, `tool_preference`, `suggested_models`
- [ ] 更新 `SkillPrompt` dataclass 结构
- [ ] 在 `RoleExecutor` 中集成 reflection 机制
- [ ] 实现模型选择逻辑 (基于 `suggested_models`)

### **测试层面**

- [ ] 用相同任务测试 v1.0 vs v2.0
- [ ] 对比输出质量 (code coverage, 文档完整性, 分析深度)
- [ ] 测量 token 使用差异
- [ ] 测量执行时间差异

### **配置层面**

- [ ] 更新 `tool_mappings.yaml` 以匹配新技能
  - 添加 `web_automation`, `code_analysis`, `complex_problem_solving`
- [ ] 配置 `context7` 环境变量 (UPSTASH_REDIS_REST_URL)
- [ ] 验证所有 MCP servers 可用

---

## 🎓 总结: v1.0 → v2.0 的本质差异

| 维度 | v1.0 (角色描述) | v2.0 (过程引导) |
|------|----------------|----------------|
| **核心** | 告诉 LLM "你是谁" | 告诉 LLM "怎么思考" |
| **流程** | 隐式的 | 显式的 5-7 步 |
| **工具** | 无明确引导 | 明确的工具偏好 |
| **质量保证** | 依赖 LLM 自发 | 强制的反思问题 |
| **约束** | 模糊的"最佳实践" | 具体的"不允许" |
| **模型选择** | 统一使用最强模型 | 根据任务难度推荐 |
| **可扩展性** | 难以优化 | 易于调试和迭代 |

---

## 🔮 未来方向 (v3.0 展望)

### **可能的升级**

1. **动态 Skill 组合**
   - 根据任务自动组合多个 skills
   - 例如: "market_analyst + python_expert + technical_writer"

2. **学习反馈循环**
   - 根据任务成功率调整 logic_flow
   - A/B 测试不同的 reflection 问题

3. **多模态 Skills**
   - 图像分析技能
   - 语音交互技能

4. **协作 Skills**
   - 多个 AI Agent 协作的技能定义
   - 冲突解决机制

---

**当前状态**:
- ✅ v2.0 文件已创建: `resources/skill_prompts_v2.yaml`
- ⏳ 等待集成到 ResourceRegistry
- ⏳ 等待 A/B 测试验证

**建议下一步**:
1. 先在一个非关键任务上测试 v2.0
2. 对比输出质量和 token 使用
3. 根据结果调整 logic_flow 和 reflection 问题
4. 逐步迁移所有任务到 v2.0
