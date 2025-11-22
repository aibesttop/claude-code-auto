# 主题偏离问题修复报告

**日期**: 2025-11-22
**会话**: claude/analyze-team-mode-arch-01JanBjCSpd4W6FerwfaFFq6
**问题**: AI员工输出内容偏离用户目标主题

---

## 📋 问题描述

用户反映：**前几轮的AI员工，输出的内容都是关于AI agents相关，而不是按照用户目标（漫画市场调研）工作**。

### 用户目标
- **Goal**: "挖掘出2个在漫画这个利基市场的app机会，最终输出分别输出两份详细的app需求文档，格式为.md文件。"
- **Initial Prompt**: "你们是一个顶级的app创业团队，从市场调研，和创意发掘，包括找投资人都有一套自己的一套方案，希望先从漫画这个利基市场调研开始。"

### 观察到的问题
AI员工（Market-Researcher, Creative-Explorer等）输出的内容聚焦在"AI agents"相关话题，而不是"漫画市场"相关内容。

---

## 🔍 根因分析

经过代码审查，发现了**两个关键问题**：

### 问题1: MissionDecomposer的Prompt不够明确

**位置**: `src/core/leader/mission_decomposer.py:55-86`

**原始Prompt的问题**：
```python
# 原始示例（第71-77行）
{
  "id": "mission_1",
  "type": "market_research",
  "goal": "Complete in-depth market research...",  # ⚠️ 太泛化
  "requirements": ["web access", "search capability"],
  "success_criteria": ["Identify 3+ user segments", "Analyze 5+ competitors"],
  ...
}
```

**问题分析**：
- **示例过于泛化**："Complete in-depth market research..."没有具体说明研究哪个领域/主题
- **缺少主题强调**：没有明确要求SubMission必须紧扣用户提供的具体目标
- **LLM可能参考自身知识**：当示例不够具体时，Claude可能会使用它最熟悉的领域（AI agents）作为填充内容

### 问题2: 缺少Context传递

**位置**: `src/main.py:96-99`, `src/core/leader/leader_agent.py:155`

**问题**：
- `main.py`调用`leader.execute()`时，**只传递了goal，没有传递initial_prompt**
- `leader_agent.py`调用`mission_decomposer.decompose()`时，**没有传递context**
- **Initial Prompt包含关键信息**："你们是一个顶级的app创业团队...希望先从漫画这个利基市场调研开始"

**后果**：
- MissionDecomposer缺少团队背景信息
- SubMission的goal没有继承"漫画"这个核心主题
- Agent执行时缺少领域上下文

---

## 🔧 修复方案

### 修复1: 改进MissionDecomposer的Prompt

**文件**: `src/core/leader/mission_decomposer.py`

**改动内容**：

1. **添加强调语句**：
```python
⚠️ CRITICAL: Your sub-missions MUST be directly related to the user's goal below.
- DO NOT create generic examples unrelated to the user's domain
- DO NOT use topics from other domains (e.g., if user asks about comics, don't talk about AI/ML)
- STAY FOCUSED on the exact domain/topic/market the user specified
- Use the user's exact terminology and context
```

2. **修改示例格式**：
```python
"goal": "YOUR SPECIFIC GOAL HERE - MUST MATCH USER'S DOMAIN"
```

3. **添加具体示例对比**：
```python
Example (if user asks about "comic app opportunities"):
- ✅ GOOD: "goal": "Conduct market research on comic reading apps in mobile market..."
- ❌ BAD: "goal": "Complete in-depth market research..." (too generic)
- ❌ BAD: "goal": "Research AI agent architecture..." (wrong domain!)
```

4. **修改结尾强调**：
```python
Now decompose this SPECIFIC goal into sub-missions. Remember: STAY ON THE USER'S TOPIC!
```

### 修复2: 传递Initial Prompt作为Context

**文件1**: `src/core/leader/mission_decomposer.py`

**改动**: 添加`context`参数

```python
async def decompose(
    self,
    goal: str,
    context: str = None  # 新增
) -> List[SubMission]:
    """
    Args:
        goal: User's high-level goal
        context: Optional context/background information  # 新增
    """
    # 合并context和goal
    goal_with_context = goal
    if context:
        goal_with_context = f"{context}\n\nGoal: {goal}"

    prompt = self.DECOMPOSITION_PROMPT.format(goal=goal_with_context)
```

**文件2**: `src/core/leader/leader_agent.py`

**改动**: `execute`方法接受`context`参数

```python
async def execute(
    self,
    goal: str,
    session_id: str,
    context: str = None  # 新增
) -> Dict[str, Any]:
    ...
    missions = await self.mission_decomposer.decompose(goal, context=context)
```

**文件3**: `src/main.py`

**改动**: 调用时传递`initial_prompt`

```python
result = await leader.execute(
    goal=config.task.goal,
    session_id=session_id,
    context=config.task.initial_prompt if config.task.initial_prompt else None  # 新增
)
```

---

## 🛠️ 诊断工具

创建了诊断脚本：`diagnose_mission_decomposition.py`

**功能**：
- 加载`config.yaml`中的goal和initial_prompt
- 调用MissionDecomposer进行任务分解
- 显示生成的SubMissions详情
- **自动检测主题偏离**：
  - 检查是否包含预期关键词（漫画、comic、manga、app等）
  - 检查是否包含无关关键词（AI、agent、LLM、GPT等）
  - 给出✅/⚠️/❌状态标记

**使用方法**：
```bash
python diagnose_mission_decomposition.py
```

---

## 📊 预期效果

### 修复前
```
Mission 1: market_research
Goal: "Complete in-depth market research..." ❌
(太泛化，可能被解读为AI agents相关)
```

### 修复后
```
Mission 1: market_research
Goal: "进行漫画阅读app市场调研，分析用户需求、竞品和市场规模" ✅
(紧扣用户的"漫画"主题)
```

### Context传递效果

**修复前**：
- MissionDecomposer只看到："挖掘出2个在漫画这个利基市场的app机会..."
- 缺少"顶级app创业团队"、"市场调研"等背景信息

**修复后**：
- MissionDecomposer看到完整上下文：
  ```
  你们是一个顶级的app创业团队，从市场调研，和创意发掘，包括找投资人都有一套自己的一套方案，希望先从漫画这个利基市场调研开始。

  Goal: 挖掘出2个在漫画这个利基市场的app机会...
  ```
- 生成的SubMissions会继承团队角色定位和"漫画"主题

---

## ✅ 验证步骤

1. **运行诊断脚本**：
   ```bash
   python diagnose_mission_decomposition.py
   ```
   检查生成的SubMissions是否包含"漫画"相关内容。

2. **完整测试**：
   ```bash
   # 1. 启用Leader模式
   # 编辑config.yaml，设置 leader.enabled: true

   # 2. 运行完整工作流
   python src/main.py

   # 3. 检查输出文件
   cat demo_act/market-research.md
   cat demo_act/creative_exploration_worksheet.md

   # 4. 验证内容是否关于"漫画"而非"AI agents"
   ```

3. **查看日志**：
   ```bash
   # 检查Mission分解日志
   grep "Mission" logs/*.log

   # 确认每个Mission的goal包含"漫画"/"comic"等关键词
   ```

---

## 📝 修改文件清单

| 文件 | 类型 | 改动说明 |
|------|------|----------|
| `src/core/leader/mission_decomposer.py` | 修复 | 改进Prompt，添加context参数 |
| `src/core/leader/leader_agent.py` | 修复 | execute方法接受context参数 |
| `src/main.py` | 修复 | 传递initial_prompt作为context |
| `diagnose_mission_decomposition.py` | 工具 | 新增诊断脚本，检测主题偏离 |
| `src/core/team/role_executor.py` | 已修 | （之前已修复文件路径问题） |
| `docs/TOPIC_DRIFT_FIX.md` | 文档 | 本文档 |

---

## 🎯 关键要点

### 为什么会出现主题偏离？

1. **LLM的"舒适区"效应**：当Prompt中的示例过于泛化时，LLM倾向于使用它最熟悉、最有信心的领域来填充内容。对于Claude来说，"AI agents"是它非常熟悉的领域。

2. **Context缺失的链式影响**：
   ```
   用户 → Main → LeaderAgent → MissionDecomposer
          ❌           ❌
      未传递context  未传递context
   ```
   每一层都丢失了一些关键信息，最终MissionDecomposer无法获得完整的领域上下文。

3. **示例的强大影响力**：Prompt中的示例对LLM行为有很强的引导作用。一个泛化的示例（"Complete in-depth market research..."）相当于告诉LLM"你可以自由选择任何领域"。

### 修复的核心思想

1. **明确禁止偏离**：使用⚠️ CRITICAL标记和DO NOT指令
2. **提供正反对比**：✅ GOOD vs ❌ BAD的具体示例
3. **传递完整上下文**：确保initial_prompt的重要信息传递到MissionDecomposer
4. **强调用户主题**："STAY ON THE USER'S TOPIC!"

---

## 🔄 后续建议

### 短期建议
1. 在每次运行后检查`demo_act/`中的输出文件，确认主题正确
2. 使用诊断脚本定期验证SubMission生成质量
3. 如果仍有主题偏离，考虑在角色定义（roles/*.yaml）中也强调领域

### 长期改进
1. **添加主题一致性验证器**：
   - 在RoleExecutor执行前，使用LLM检查任务描述是否与用户目标主题一致
   - 如果偏离超过阈值，自动触发任务重新细化

2. **改进ResourceRegistry的skill_prompts**：
   - 使skill_prompts支持动态主题注入
   - 例如：market_analyst的prompt可以包含 `You are analyzing the {DOMAIN} market...`，其中`{DOMAIN}`从用户goal中提取

3. **添加主题跟踪指标**：
   - 在报告中显示"主题一致性得分"
   - 追踪每个Agent输出的关键词分布
   - 预警主题偏离

---

## 💡 相关问题预防

### Q: 如果用户的goal本身很模糊怎么办？

A: 在MissionDecomposer前添加一个goal clarification步骤，使用LLM提取核心主题关键词，然后注入到所有SubMissions中。

### Q: 如果不同SubMission需要不同的领域怎么办？

A: 这是合理的，修复后的Prompt仍然允许多领域，只要它们都服务于用户的最终目标。例如：
- Mission 1: 漫画市场调研 ✅
- Mission 2: iOS/Android技术架构设计 ✅（为漫画app）
- Mission 3: AI agents架构设计 ❌（偏离了用户目标）

### Q: 如何处理隐式的主题需求？

A: 建议在config.yaml中添加一个`domain`或`industry`字段，明确指定领域：
```yaml
task:
  domain: "漫画"  # 或 "comics", "manga"
  industry: "移动应用"
  goal: "挖掘出2个在漫画这个利基市场的app机会..."
```

---

**状态**: ✅ 修复完成，待验证

**下一步**: 运行诊断脚本和完整测试，验证修复效果
