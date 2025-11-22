# AI原生团队工作流程图

本文档展示了claude-code-auto系统中AI原生团队的完整工作流程。

---

## 1️⃣ 整体系统架构流程

```mermaid
graph TB
    Start([用户输入目标]) --> Config[加载配置config.yaml]
    Config --> ModeCheck{选择运行模式}

    ModeCheck -->|Original Mode| SingleAgent[单Agent迭代模式]
    ModeCheck -->|Team Mode| TeamFlow[团队协作模式]
    ModeCheck -->|Leader Mode v4.0| LeaderFlow[智能编排模式]

    SingleAgent --> PlanExec[Planner + Executor循环]
    PlanExec --> Monitor1[成本追踪 + 状态持久化]
    Monitor1 --> End1([输出结果])

    TeamFlow --> Assembly
    LeaderFlow --> MissionDecomp[Mission Decomposer<br/>任务智能分解]

    Assembly[Team Assembler<br/>角色选择] --> DepResolve[Dependency Resolver<br/>拓扑排序]
    DepResolve --> Orchestrate[Team Orchestrator<br/>线性执行]
    Orchestrate --> RoleLoop[角色执行循环]
    RoleLoop --> Monitor2[验证 + 成本追踪]
    Monitor2 --> End2([可交付成果])

    MissionDecomp --> LeaderOrchestrate[Leader Agent<br/>动态编排 + 干预]
    LeaderOrchestrate --> OutputIntegrate[Output Integrator<br/>成果集成]
    OutputIntegrate --> End3([智能交付])

    style TeamFlow fill:#4CAF50,color:#fff
    style LeaderFlow fill:#FF9800,color:#fff
    style Assembly fill:#2196F3,color:#fff
    style DepResolve fill:#2196F3,color:#fff
    style Orchestrate fill:#2196F3,color:#fff
```

---

## 2️⃣ Team Mode 详细工作流

```mermaid
flowchart TD
    Start([Initial Prompt<br/>初始任务描述]) --> TeamAssembler[Team Assembler<br/>LLM分析任务选择角色]

    TeamAssembler -->|选中的角色| LoadRoles[加载角色定义<br/>roles/*.yaml]
    LoadRoles --> BuildGraph[构建依赖图<br/>Dependency Graph]

    BuildGraph --> TopoSort[拓扑排序<br/>Kahn算法]
    TopoSort --> CheckCycle{检测循环依赖}

    CheckCycle -->|有循环| Error1([错误: 循环依赖])
    CheckCycle -->|无循环| SortedRoles[已排序角色列表]

    SortedRoles --> StartOrch[Team Orchestrator<br/>开始编排]

    StartOrch --> LoopCheck{还有角色?}
    LoopCheck -->|是| NextRole[取出下一个角色]
    LoopCheck -->|否| FinalOutput([所有角色完成<br/>输出可交付成果])

    NextRole --> CreateExecutor[创建 Role Executor]
    CreateExecutor --> PersonaSwitch[Persona切换<br/>根据角色推荐]

    PersonaSwitch --> TaskLoop[任务执行循环<br/>max_iterations次]

    TaskLoop --> UsePlanner{使用Planner?}
    UsePlanner -->|是| PlannerStep[Planner分解任务]
    UsePlanner -->|否| DirectExec

    PlannerStep --> DirectExec[Executor执行<br/>ReAct循环]
    DirectExec --> GetOutput[获取角色输出]

    GetOutput --> FormatValid{格式验证}
    FormatValid -->|失败| RetryCheck{重试次数 < max?}
    RetryCheck -->|是| TaskLoop
    RetryCheck -->|否| Error2([角色失败])

    FormatValid -->|通过| QualityCheck{启用质量检查?}
    QualityCheck -->|否| SaveOutput
    QualityCheck -->|是| LLMValidate[LLM语义质量评分<br/>Haiku模型]

    LLMValidate --> ScoreCheck{分数 >= 阈值?}
    ScoreCheck -->|否| RetryCheck
    ScoreCheck -->|是| SaveOutput[保存角色输出]

    SaveOutput --> ContextPrepare[准备上下文传递]
    ContextPrepare --> LengthCheck{输出长度}

    LengthCheck -->|< 500字符| FullEmbed[完整内容嵌入context]
    LengthCheck -->|>= 500字符| Summary[生成摘要<br/>前300+后100]

    Summary --> SaveTrace[完整内容保存到<br/>trace文件]
    SaveTrace --> FullEmbed

    FullEmbed --> UpdateContext[更新全局Context]
    UpdateContext --> LogTrace[记录Markdown Trace<br/>logs/trace/]

    LogTrace --> LoopCheck

    Error1 -.-> End([流程结束])
    Error2 -.-> End
    FinalOutput -.-> End

    style TeamAssembler fill:#4CAF50,color:#fff
    style TopoSort fill:#2196F3,color:#fff
    style DirectExec fill:#FF9800,color:#fff
    style LLMValidate fill:#9C27B0,color:#fff
    style SaveOutput fill:#4CAF50,color:#fff
```

---

## 3️⃣ 角色依赖关系图 (示例场景)

**场景**: 漫画利基市场App开发

```mermaid
graph LR
    subgraph "执行顺序: 第1层"
        MR[Market Researcher<br/>市场研究员<br/>━━━━━━━━<br/>无依赖]
    end

    subgraph "执行顺序: 第2层"
        ANW[AI-Native Writer<br/>文档撰写者<br/>━━━━━━━━<br/>依赖: MR]
    end

    subgraph "执行顺序: 第3层"
        AND[AI-Native Developer<br/>全栈开发者<br/>━━━━━━━━<br/>依赖: ANW]
    end

    MR -->|输出: market_research.md| ANW
    ANW -->|输出: 8份AI原生文档<br/>00-07-*.md| AND
    AND -->|输出: 完整代码库<br/>src/ + tests/ + Docker| Final([可交付成果])

    style MR fill:#4CAF50,color:#fff
    style ANW fill:#2196F3,color:#fff
    style AND fill:#FF9800,color:#fff
    style Final fill:#9C27B0,color:#fff
```

---

## 4️⃣ 单个角色执行流程 (Role Executor)

```mermaid
flowchart TD
    Start([角色任务开始]) --> Init[初始化 Role Executor]
    Init --> LoadDef[加载角色定义<br/>role.yaml]

    LoadDef --> ReadContext[读取上游角色输出<br/>Context传递]
    ReadContext --> SetPersona[切换到推荐Persona<br/>coder/researcher等]

    SetPersona --> IterLoop{迭代 < max_iterations?}

    IterLoop -->|是| CheckPlanner{配置use_planner?}
    IterLoop -->|否| MaxIterFail([超出最大迭代])

    CheckPlanner -->|true| CallPlanner[调用 Planner Agent<br/>分解子任务]
    CheckPlanner -->|false| DirectCall

    CallPlanner --> ParsePlan[解析计划<br/>提取action_steps]
    ParsePlan --> DirectCall[调用 Executor Agent<br/>ReAct执行]

    DirectCall --> WaitReact[ReAct循环运行<br/>最大30步]
    WaitReact --> GetResult[获取执行结果]

    GetResult --> FormatVal[格式验证]
    FormatVal --> CheckFiles{required_files<br/>存在?}

    CheckFiles -->|否| RecordError1[记录错误]
    CheckFiles -->|是| CheckContent{content_check<br/>通过?}

    CheckContent -->|否| RecordError2[记录错误]
    CheckContent -->|是| CheckLength{满足min_length?}

    CheckLength -->|否| RecordError3[记录错误]
    CheckLength -->|是| CheckPlaceholder{有占位符<br/>TODO/PLACEHOLDER?}

    CheckPlaceholder -->|是| RecordError4[记录错误]
    CheckPlaceholder -->|否| QualityGate{启用质量检查?}

    RecordError1 --> DupeCheck
    RecordError2 --> DupeCheck
    RecordError3 --> DupeCheck
    RecordError4 --> DupeCheck

    DupeCheck{连续2次<br/>相同错误?}
    DupeCheck -->|是| InfiniteLoop([检测到无限循环<br/>退出])
    DupeCheck -->|否| IterLoop

    QualityGate -->|false| Success
    QualityGate -->|true| CallLLM[调用 Haiku LLM<br/>语义质量评分]

    CallLLM --> ParseScore[解析 QualityScore<br/>overall_score]
    ParseScore --> ScoreOK{score >= threshold?}

    ScoreOK -->|否| LogIssues[记录质量问题<br/>+ 改进建议]
    LogIssues --> IterLoop

    ScoreOK -->|是| Success[验证成功]

    Success --> CollectOutput[收集角色输出<br/>文件列表]
    CollectOutput --> PrepContext[准备上下文传递]

    PrepContext --> LenCheck{总长度 < 500?}
    LenCheck -->|是| EmbedFull[完整内容嵌入]
    LenCheck -->|否| GenSummary[生成摘要<br/>前300+后100]

    GenSummary --> SaveFull[保存完整内容<br/>trace/{role}_{filename}]
    SaveFull --> EmbedFull

    EmbedFull --> LogMD[记录 Markdown Trace<br/>logs/trace/{session}_{role}_stepX.md]
    LogMD --> Return([返回角色输出<br/>+ context])

    InfiniteLoop -.-> End([流程结束])
    MaxIterFail -.-> End
    Return -.-> End

    style CallPlanner fill:#4CAF50,color:#fff
    style DirectCall fill:#FF9800,color:#fff
    style CallLLM fill:#9C27B0,color:#fff
    style Success fill:#4CAF50,color:#fff
```

---

## 5️⃣ ReAct执行引擎循环

```mermaid
flowchart TD
    Start([Executor启动]) --> InitReact[初始化 ReAct Agent<br/>加载工具注册表]
    InitReact --> BuildPrompt[构建系统提示<br/>+ 角色定义 + 工具列表]

    BuildPrompt --> StepLoop{step < 30?}

    StepLoop -->|是| SendPrompt[发送消息到 Claude SDK]
    StepLoop -->|否| MaxStep([达到最大步数<br/>返回当前结果])

    SendPrompt --> WaitResp[等待 Claude 响应]
    WaitResp --> ParseResp[解析响应内容]

    ParseResp --> TypeCheck{响应类型?}

    TypeCheck -->|文本| CheckFinal{包含 Final Answer?}
    TypeCheck -->|工具调用| ExtractTool[提取工具调用<br/>tool_name + input]

    CheckFinal -->|是| ExtractAnswer[提取最终答案]
    CheckFinal -->|否| AddThought[添加思考内容<br/>到历史]

    ExtractAnswer --> Success([ReAct成功完成])
    AddThought --> StepLoop

    ExtractTool --> ValidateTool{工具存在?}
    ValidateTool -->|否| ErrorMsg1[返回错误消息<br/>"工具不存在"]
    ValidateTool -->|是| ParseInput[解析工具输入<br/>JSON]

    ErrorMsg1 --> AddObserv1[添加 Observation<br/>到历史]
    AddObserv1 --> StepLoop

    ParseInput --> JSONValid{JSON合法?}
    JSONValid -->|否| ErrorMsg2[返回错误消息<br/>"JSON解析失败"]
    JSONValid -->|是| CallTool[调用工具函数<br/>沙箱执行]

    ErrorMsg2 --> AddObserv2[添加 Observation]
    AddObserv2 --> StepLoop

    CallTool --> TryCatch{执行成功?}
    TryCatch -->|异常| CatchError[捕获异常<br/>格式化错误消息]
    TryCatch -->|成功| GetResult[获取工具返回值]

    CatchError --> AddObserv3[添加错误 Observation]
    GetResult --> AddObserv4[添加成功 Observation]

    AddObserv3 --> StepLoop
    AddObserv4 --> StepLoop

    Success -.-> End([返回结果])
    MaxStep -.-> End

    style SendPrompt fill:#4CAF50,color:#fff
    style CallTool fill:#FF9800,color:#fff
    style Success fill:#4CAF50,color:#fff

    classDef thoughtNode fill:#2196F3,color:#fff
    class AddThought,CheckFinal thoughtNode
```

---

## 6️⃣ 依赖解析算法 (Kahn拓扑排序)

```mermaid
flowchart TD
    Start([输入: 角色列表 + 依赖关系]) --> BuildGraph[构建有向图<br/>节点=角色<br/>边=依赖]

    BuildGraph --> CalcIndegree[计算每个节点的入度<br/>indegree[node]]
    CalcIndegree --> FindZero[找到所有入度=0的节点<br/>无依赖角色]

    FindZero --> InitQueue[初始化队列 Q<br/>Q = [入度0的节点]]
    InitQueue --> InitResult[初始化结果列表<br/>result = []]

    InitResult --> LoopCheck{Q 非空?}

    LoopCheck -->|是| Dequeue[Q.pop 取出节点 u]
    LoopCheck -->|否| FinalCheck{result长度 == 总节点数?}

    Dequeue --> AddResult[result.append(u)]
    AddResult --> GetNeighbors[获取 u 的所有邻居<br/>依赖u的角色]

    GetNeighbors --> ForEach{遍历每个邻居 v}
    ForEach -->|还有| DecreaseIndegree[indegree[v] -= 1]
    ForEach -->|完成| LoopCheck

    DecreaseIndegree --> CheckZero{indegree[v] == 0?}
    CheckZero -->|是| Enqueue[Q.append(v)]
    CheckZero -->|否| ForEach

    Enqueue --> ForEach

    FinalCheck -->|是| Success([成功: 返回排序结果<br/>执行顺序确定])
    FinalCheck -->|否| DetectCycle[检测到循环依赖]

    DetectCycle --> FindCycle[找出循环路径<br/>DFS回溯]
    FindCycle --> Error([错误: 循环依赖<br/>列出循环路径])

    Success -.-> End([流程结束])
    Error -.-> End

    style BuildGraph fill:#4CAF50,color:#fff
    style CalcIndegree fill:#2196F3,color:#fff
    style Dequeue fill:#FF9800,color:#fff
    style Success fill:#4CAF50,color:#fff
    style Error fill:#f44336,color:#fff
```

---

## 7️⃣ Leader Mode (v4.0) 智能编排流程

```mermaid
flowchart TD
    Start([用户高层目标]) --> MissionDecomp[Mission Decomposer<br/>LLM分解为子任务]

    MissionDecomp --> ParseMissions[解析 Mission列表<br/>type, goal, dependencies]
    ParseMissions --> ValidateDep[验证依赖关系<br/>检测循环]

    ValidateDep --> DepOK{依赖合法?}
    DepOK -->|否| Error1([错误: 依赖冲突])
    DepOK -->|是| TopoSort[拓扑排序 Missions]

    TopoSort --> InitLeader[初始化 Leader Agent<br/>预算控制 + 质量阈值]

    InitLeader --> MissionLoop{还有 Mission?}

    MissionLoop -->|是| NextMission[取出下一个 Mission]
    MissionLoop -->|否| Integrate

    NextMission --> SelectRole[根据 Mission type<br/>选择角色]
    SelectRole --> CreateExecutor[创建 Role Executor]

    CreateExecutor --> Monitor[监控执行<br/>实时成本追踪]
    Monitor --> ExecuteRole[Role Executor执行]

    ExecuteRole --> EvalQuality[评估质量分数<br/>LLM语义评分]
    EvalQuality --> DecideIntervention{决策干预策略}

    DecideIntervention -->|CONTINUE| Success[Mission成功]
    DecideIntervention -->|RETRY| RetryCheck{重试 < max_retries?}
    DecideIntervention -->|ENHANCE| EnhanceMission[增强任务定义<br/>LLM细化需求]
    DecideIntervention -->|ESCALATE| AddHelper[添加辅助角色<br/>组成临时团队]
    DecideIntervention -->|TERMINATE| Fail[Mission失败]

    RetryCheck -->|是| Monitor
    RetryCheck -->|否| Fail

    EnhanceMission --> Monitor
    AddHelper --> Monitor

    Success --> CollectOutput[收集 Mission输出]
    CollectOutput --> CheckBudget{预算检查}

    CheckBudget -->|超限| BudgetStop([预算超限停止])
    CheckBudget -->|正常| MissionLoop

    Fail --> LogFailure[记录失败原因<br/>Markdown日志]
    LogFailure --> UserDecision{用户决策}
    UserDecision -->|继续| MissionLoop
    UserDecision -->|停止| End

    Integrate[Output Integrator<br/>智能集成所有输出]
    Integrate --> GenDeliverable[生成可交付成果<br/>README + 汇总文档]

    GenDeliverable --> FinalReport[生成执行报告<br/>成本 + 质量 + 决策路径]
    FinalReport --> End([Leader编排完成])

    Error1 -.-> End
    BudgetStop -.-> End

    style MissionDecomp fill:#4CAF50,color:#fff
    style DecideIntervention fill:#FF9800,color:#fff
    style Integrate fill:#9C27B0,color:#fff
    style FinalReport fill:#2196F3,color:#fff
```

---

## 8️⃣ 质量验证双层架构

```mermaid
flowchart LR
    subgraph "第1层: 格式验证"
        Input([角色输出]) --> FileCheck[文件存在性检查<br/>required_files]
        FileCheck --> ContentCheck[内容检查<br/>content_check]
        ContentCheck --> LenCheck[最小长度检查<br/>min_length × complexity]
        LenCheck --> PlaceholderCheck[占位符检查<br/>TODO/PLACEHOLDER禁止]
    end

    PlaceholderCheck -->|通过| Gate{启用<br/>质量检查?}
    PlaceholderCheck -->|失败| FormatFail([格式验证失败])

    Gate -->|否| DirectPass([验证通过])
    Gate -->|是| Layer2

    subgraph "第2层: 语义质量验证"
        Layer2[调用 Haiku LLM] --> BuildPrompt[构建评分提示<br/>+ 成功标准]
        BuildPrompt --> GetScore[获取 QualityScore<br/>overall_score: 0-100]
        GetScore --> ParseCriteria[解析各项评分<br/>criteria_scores]
        ParseCriteria --> ExtractIssues[提取问题列表<br/>issues]
        ExtractIssues --> ExtractSuggest[提取改进建议<br/>suggestions]
    end

    ExtractSuggest --> ThresholdCheck{score >= threshold?}
    ThresholdCheck -->|是| QualityPass([质量验证通过])
    ThresholdCheck -->|否| QualityFail([质量验证失败<br/>+改进建议])

    FormatFail -.-> Retry[重新执行角色任务]
    QualityFail -.-> Retry
    DirectPass -.-> NextRole[下一个角色]
    QualityPass -.-> NextRole

    style FileCheck fill:#2196F3,color:#fff
    style Layer2 fill:#9C27B0,color:#fff
    style QualityPass fill:#4CAF50,color:#fff
    style QualityFail fill:#f44336,color:#fff
```

---

## 9️⃣ 成本控制和预算追踪

```mermaid
flowchart TD
    Start([Agent执行开始]) --> Record[记录调用信息<br/>model, token_usage]

    Record --> Calculate[计算成本<br/>input_tokens × $price_in<br/>+ output_tokens × $price_out]

    Calculate --> Store[存储 CostRecord<br/>session_id, agent_type, cost]
    Store --> UpdateTotal[更新总成本累计]

    UpdateTotal --> BudgetEnabled{启用预算控制?}

    BudgetEnabled -->|否| Continue([继续执行])
    BudgetEnabled -->|是| CheckBudget[检查预算状态]

    CheckBudget --> CalcUsage[计算使用比例<br/>used / max_budget]

    CalcUsage --> WarningCheck{使用 >= 警告阈值<br/>80%?}
    WarningCheck -->|是| SendWarning[触发警告事件<br/>COST_WARNING]
    WarningCheck -->|否| ExceededCheck

    SendWarning --> ExceededCheck{使用 >= 100%?}
    ExceededCheck -->|否| Continue
    ExceededCheck -->|是| AutoStop{auto_stop_on_exceed?}

    AutoStop -->|true| Stop([强制停止执行<br/>BUDGET_EXCEEDED])
    AutoStop -->|false| WarnContinue[警告但继续<br/>COST_EXCEEDED_CONTINUE]

    WarnContinue --> Continue

    Continue --> LogEvent[记录事件<br/>events.json]
    LogEvent --> ExportReport[导出成本报告<br/>logs/cost_report.json]

    ExportReport --> End([成本追踪完成])
    Stop -.-> End

    style Calculate fill:#4CAF50,color:#fff
    style SendWarning fill:#FF9800,color:#fff
    style Stop fill:#f44336,color:#fff
    style ExportReport fill:#2196F3,color:#fff
```

---

## 🔟 Markdown Trace日志系统

```mermaid
flowchart LR
    subgraph "执行过程"
        Planner[Planner决策] --> Executor[Executor执行<br/>ReAct循环]
        Executor --> Validation[验证结果]
    end

    Planner -->|决策追踪| PlanTrace["📄 logs/trace/<br/>{session}_{role}_step1.md<br/>━━━━━━━━<br/>## Planner Decision<br/>Goal: ...<br/>Action Steps: [...]"]

    Executor -->|执行追踪| ExecTrace["📄 logs/trace/<br/>{session}_{role}_step2.md<br/>━━━━━━━━<br/>## ReAct Execution<br/>Step 1: Thought...<br/>Action: write_file<br/>Observation: ..."]

    Validation -->|长内容保存| ContentTrace["📄 logs/trace/<br/>context_{role}_{filename}<br/>━━━━━━━━<br/>[完整文件内容]<br/>避免token截断"]

    subgraph "追踪文件"
        PlanTrace
        ExecTrace
        ContentTrace
    end

    subgraph "用途"
        Audit[审计决策路径]
        Debug[调试错误]
        Context[保留完整上下文]
    end

    PlanTrace -.-> Audit
    ExecTrace -.-> Debug
    ContentTrace -.-> Context

    style PlanTrace fill:#4CAF50,color:#fff
    style ExecTrace fill:#2196F3,color:#fff
    style ContentTrace fill:#FF9800,color:#fff
```

---

## 📊 完整执行示例: 漫画App开发项目

```mermaid
gantt
    title AI原生团队执行时间线 (漫画利基市场App)
    dateFormat  HH:mm
    axisFormat %H:%M

    section 第1层 (无依赖)
    Market Researcher           :mr, 00:00, 25m
    - 市场调研                  :00:00, 10m
    - 竞品分析                  :10:00, 8m
    - 输出报告                  :18:00, 7m

    section 第2层 (依赖MR)
    AI-Native Writer            :anw, after mr, 40m
    - 读取研究报告              :25:00, 3m
    - 生成8份文档               :28:00, 32m
    - 验证文档质量              :60:00, 5m

    section 第3层 (依赖ANW)
    AI-Native Developer         :and, after anw, 50m
    - 读取8份文档               :65:00, 5m
    - 实现代码                  :70:00, 25m
    - 编写测试                  :95:00, 10m
    - Docker配置                :105:00, 5m
    - 质量验证                  :110:00, 5m

    section 可交付成果
    最终输出                    :crit, after and, 5m
```

**总执行时间**: ~2小时
**总成本**: ~$1.50 USD (预估)
**输出文件**:
- `market_research.md`
- `docs/00-07-*.md` (8份)
- `src/main.py`
- `tests/test_main.py`
- `Dockerfile`
- `README.md`
- `.env.example`
- `requirements.txt`

---

## 📝 关键流程说明

### 1. **Team Assembly (团队组建)**
- LLM分析`initial_prompt`，识别需要的角色
- 从`roles/`目录加载角色定义
- 验证角色依赖关系

### 2. **Dependency Resolution (依赖解析)**
- 使用Kahn算法进行拓扑排序
- O(V+E)时间复杂度
- 检测并拒绝循环依赖
- 计算执行层级（可视化/并行化）

### 3. **Role Execution (角色执行)**
- 每个角色独立执行，最大`max_iterations`次
- 可选Planner分解任务
- Executor执行ReAct循环
- 双层验证（格式+语义）

### 4. **Context Passing (上下文传递)**
- 短内容(<500字符)：完整嵌入
- 长内容(>=500字符)：摘要+完整保存
- 避免token浪费和内容截断

### 5. **Quality Control (质量控制)**
- 格式验证：文件存在、内容检查、长度、占位符
- 语义验证：LLM评分（0-100）、问题识别、改进建议
- 自适应标准：基于任务复杂度调整阈值

### 6. **Cost Management (成本管理)**
- 实时token追踪
- 预算警告（80%阈值）
- 自动停止（可选）
- 详细成本报告

### 7. **Trace Logging (追踪日志)**
- Planner决策日志
- ReAct执行日志
- 完整上下文保存
- Markdown格式，便于审计

---

## 🎯 总结

这个AI原生团队工作流系统通过以下创新实现了真正的自主协作：

✅ **智能编排**: 三层模式适应不同复杂度
✅ **依赖管理**: 拓扑排序保证执行顺序
✅ **质量保证**: 双层验证（格式+语义）
✅ **成本控制**: 实时追踪+预算门
✅ **可审计性**: 完整Trace日志
✅ **角色专业化**: YAML定义清晰职责
✅ **上下文保留**: 避免截断和信息丢失

这是一个完整的生产级AI原生自主工作流系统！🚀
