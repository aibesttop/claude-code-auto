# Claude Code Auto v3 - 代码执行流程图

本文档描述了 Claude Code Auto v3 的完整执行流程。

## 主流程图

```mermaid
flowchart TD
    Start([开始]) --> LoadConfig[加载配置 config.yaml]
    LoadConfig --> SetupLogger[初始化日志系统]
    SetupLogger --> HealthCheck{SDK 健康检查}
    
    HealthCheck -->|失败| Exit1([退出])
    HealthCheck -->|成功| InitAgents[初始化代理]
    
    InitAgents --> CreatePlanner[创建 PlannerAgent]
    CreatePlanner --> CreateExecutor[创建 ExecutorAgent]
    CreateExecutor --> CreateResearcher[创建 ResearcherAgent]
    CreateResearcher --> InitState[初始化状态管理器]
    
    InitState --> MainLoop{开始主循环<br/>iteration < max_iterations}
    
    MainLoop -->|否| GenerateReports[生成最终报告]
    MainLoop -->|是| CheckEmergency{检查紧急停止}
    
    CheckEmergency -->|是| EmergencyStop([紧急停止])
    CheckEmergency -->|否| CheckTimeout{检查超时}
    
    CheckTimeout -->|是| TimeoutStop([超时停止])
    CheckTimeout -->|否| PlanningPhase[规划阶段]
    
    PlanningPhase --> IsFirstIteration{iteration == 1<br/>且有 initial_prompt?}
    
    IsFirstIteration -->|是| UseInitialPrompt[使用 initial_prompt<br/>作为 next_task]
    IsFirstIteration -->|否| CallPlanner[调用 Planner.get_next_step]
    
    UseInitialPrompt --> PersonaCheck
    CallPlanner --> PlannerSuccess{Planner 成功?}
    
    PlannerSuccess -->|失败| HandlePlannerError[处理错误<br/>增加错误计数]
    PlannerSuccess -->|成功| PersonaCheck
    
    HandlePlannerError --> CheckMaxErrors{达到最大错误数?}
    CheckMaxErrors -->|是| FailedStop([失败停止])
    CheckMaxErrors -->|否| MainLoop
    
    PersonaCheck[Persona 推荐与切换] --> CheckTaskComplete{任务完成?}
    
    CheckTaskComplete -->|是| CompletedStop([完成退出])
    CheckTaskComplete -->|否| ExecutionPhase[执行阶段]
    
    ExecutionPhase --> CallExecutor[调用 Executor.execute_task]
    CallExecutor --> ExecutorSuccess{Executor 成功?}
    
    ExecutorSuccess -->|成功| RecordCost[记录成本与事件]
    ExecutorSuccess -->|失败| HandleExecutorError[处理执行错误]
    
    RecordCost --> SaveState[保存状态]
    HandleExecutorError --> SaveState
    
    SaveState --> MainLoop
    
    GenerateReports --> SaveEvents[保存事件日志]
    SaveEvents --> End([结束])
```

## 详细组件交互图

```mermaid
flowchart LR
    subgraph "主循环 Main Loop"
        Orchestrator[Orchestrator<br/>main.py]
    end
    
    subgraph "规划层 Planning Layer"
        Planner[PlannerAgent<br/>planner.py]
        Plan[(Plan State)]
    end
    
    subgraph "执行层 Execution Layer"
        Executor[ExecutorAgent<br/>executor.py]
        Persona[PersonaEngine<br/>persona.py]
    end
    
    subgraph "工具层 Tool Layer"
        ToolRegistry[ToolRegistry<br/>tool_registry.py]
        FileTools[File Tools]
        ShellTools[Shell Tools]
        SearchTools[Search Tools]
        Sandbox[Sandbox Wrapper]
    end
    
    subgraph "研究层 Research Layer"
        Researcher[ResearcherAgent<br/>researcher.py]
        Cache[Research Cache]
    end
    
    subgraph "支持系统 Support Systems"
        StateManager[StateManager<br/>state_manager.py]
        EventStore[EventStore<br/>events.py]
        CostTracker[CostTracker<br/>events.py]
        Logger[Logger<br/>logger.py]
    end
    
    Orchestrator -->|1. 请求下一步| Planner
    Planner -->|2. 返回 next_task| Orchestrator
    Orchestrator -->|3. 执行任务| Executor
    
    Executor -->|推荐 Persona| Persona
    Executor -->|调用工具| ToolRegistry
    
    ToolRegistry --> Sandbox
    Sandbox --> FileTools
    Sandbox --> ShellTools
    Sandbox --> SearchTools
    
    SearchTools -.->|可选| Researcher
    Researcher --> Cache
    
    Orchestrator --> StateManager
    Orchestrator --> EventStore
    Orchestrator --> CostTracker
    Orchestrator --> Logger
    
    Planner --> Plan
```

## ReAct 循环详细流程

```mermaid
flowchart TD
    Start([Executor 接收任务]) --> InitReAct[初始化 ReAct 循环<br/>max_steps=10]
    
    InitReAct --> ReActLoop{step < max_steps}
    
    ReActLoop -->|否| MaxStepsReached[达到最大步数]
    ReActLoop -->|是| BuildPrompt[构建提示词<br/>包含历史记录]
    
    BuildPrompt --> CallLLM[调用 Claude SDK]
    CallLLM --> ParseResponse[解析响应]
    
    ParseResponse --> CheckFinalAnswer{包含 Final Answer?}
    
    CheckFinalAnswer -->|是| ReturnResult([返回结果])
    CheckFinalAnswer -->|否| ParseAction[解析 Action 和 Action Input]
    
    ParseAction --> ParseSuccess{解析成功?}
    
    ParseSuccess -->|否| LogError[记录解析错误]
    ParseSuccess -->|是| ExecuteTool[执行工具]
    
    LogError --> ReActLoop
    
    ExecuteTool --> ToolSuccess{工具执行成功?}
    
    ToolSuccess -->|是| RecordObservation[记录 Observation]
    ToolSuccess -->|否| RecordError[记录错误 Observation]
    
    RecordObservation --> ReActLoop
    RecordError --> ReActLoop
    
    MaxStepsReached --> ReturnPartial([返回部分结果])
```

## 配置驱动流程

```mermaid
flowchart LR
    subgraph "配置文件 config.yaml"
        TaskConfig[task:<br/>- goal<br/>- initial_prompt]
        SafetyConfig[safety:<br/>- max_iterations<br/>- max_duration_hours]
        ClaudeConfig[claude:<br/>- model<br/>- timeout_seconds]
        PersonaConfig[persona:<br/>- default_persona<br/>- personas]
        ResearchConfig[research:<br/>- provider<br/>- enabled]
    end
    
    TaskConfig --> Orchestrator
    SafetyConfig --> Orchestrator
    ClaudeConfig --> AllAgents[所有代理]
    PersonaConfig --> PersonaEngine
    ResearchConfig --> ResearcherAgent
    
    Orchestrator[Orchestrator] --> FirstIteration{第一次迭代?}
    FirstIteration -->|是| UseInitialPrompt[使用 initial_prompt]
    FirstIteration -->|否| UsePlanner[使用 Planner]
```

## 关键特性

### 1. 显式初始步骤 (Explicit Initial Step)
- **触发条件**: `iteration == 1` 且 `config.task.initial_prompt` 已设置
- **行为**: 跳过 Planner，直接使用 `initial_prompt` 作为第一个任务
- **目的**: 允许用户手动驱动工作流的启动

### 2. Persona 动态切换
- **推荐**: 基于任务关键词自动推荐合适的 Persona
- **切换**: 自动切换到推荐的 Persona
- **记录**: 所有切换都被记录到状态历史中

### 3. 研究缓存
- **缓存**: 研究结果缓存 60 分钟
- **命中率**: 跟踪缓存命中率以优化性能

### 4. 安全护栏
- **最大迭代数**: 防止无限循环
- **超时控制**: 全局和单次迭代超时
- **紧急停止**: 通过文件触发紧急停止
- **错误计数**: 连续错误达到阈值后停止

### 5. 工具沙箱
- **异常捕获**: 所有工具执行都在沙箱中
- **错误返回**: 工具错误作为字符串返回，而非抛出异常
- **日志记录**: 详细记录工具执行情况

## 数据流

```mermaid
flowchart TD
    Config[config.yaml] --> Main[main.py]
    Main --> State[workflow_state.json]
    Main --> Events[events/*.json]
    Main --> Logs[logs/workflow.log]
    
    Executor --> WorkDir[demo_act/*]
    Tools --> WorkDir
    
    State -.->|恢复| Main
```
