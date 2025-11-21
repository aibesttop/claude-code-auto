# v3.1 Architecture Specification: Dynamic Super-Agent

## 1. Vision & Value Proposition (愿景与价值)

The goal is to build a **"Self-Evolving Super-Agent"** that is not limited by static code or roles. It adapts its persona, tools, and knowledge base dynamically to solve any problem.

| Feature | v3.0 (ReAct) | v3.1 (Super-Agent) | Value |
| :--- | :--- | :--- | :--- |
| **Role** | Static (Planner/Executor) | **Dynamic Persona** | Can be a "CTO", "Hacker", or "Researcher" on demand. |
| **Knowledge** | Local Files | **Live Internet** | Solves problems using *latest* 2024/2025 solutions. |
| **Tools** | Pre-defined Registry | **Self-Building** | Writes its own tools (e.g., "I need a PDF parser, I'll write one"). |
| **Prompts** | Hardcoded Templates | **Meta-Prompting** | Optimizes its own prompts for best results. |

---

## 2. Feasibility Assessment (可行性评估)

Implementing this vision is **Feasible** but carries **High Complexity** and **Risks**.

| Capability | Feasibility | Technical Challenge | Risk |
| :--- | :--- | :--- | :--- |
| **Dynamic Roles** | ✅ High | Context management, Prompt injection. | Low. |
| **Web Search** | ✅ High | Integration with Search APIs (Tavily/SerpAPI). | Token cost, Info overload. |
| **Sub-Agents** | ✅ Medium | Orchestrating state between agents. | Infinite loops, Deadlocks. |
| **Tool Building** | ⚠️ Medium | **Sandboxing**: Executing AI-written code is dangerous. | **High**: System crash, Security breach. |
| **Meta-Prompting**| ✅ High | Evaluating prompt quality. | Degradation of performance. |

**Conclusion**: We can build this, but we must implement a **"Sandbox Layer"** for dynamic tools and a **"Cost Monitor"** for web search.

---

## 3. High-Level Architecture (系统架构)

The architecture evolves from a simple "Brain + Hands" to a **"Dynamic Organism"**.

### Core Components

1.  **The Orchestrator (The Soul)**:
    *   Manages the high-level goal.
    *   **Dynamic Persona Engine**: Decides "Who should I be right now?" (e.g., switches to "Security Expert" to audit code).
    *   **Meta-Cognition**: "My current prompt isn't working, let me rewrite it."

2.  **The Tool Builder (The Engineer)**:
    *   Detects missing capabilities.
    *   **Writes Python code** for new tools.
    *   **Validates** the tool in a Sandbox.
    *   **Hot-loads** the tool into the registry.

3.  **The Researcher (The Explorer)**:
    *   Access to **Web Search** (Google/Bing/Tavily).
    *   Access to **Documentation Scraper**.
    *   Summarizes findings into the context.

4.  **The Sub-Agent Swarm (The Team)**:
    *   Spawns specialized sub-agents (e.g., "Frontend Coder", "QA Tester") for parallel tasks.

### Architecture Diagram

```mermaid
graph TD
    User[User Goal] --> Orchestrator
    
    subgraph "Dynamic Core"
        Orchestrator[Orchestrator / Persona Engine] -- "1. Spawn" --> SubAgent[Sub-Agent]
        Orchestrator -- "2. Research" --> Researcher[Researcher Agent]
        Orchestrator -- "3. Build Tool" --> Builder[Tool Builder Agent]
    end
    
    subgraph "Capabilities"
        Researcher <--> Internet[Web Search / Docs]
        Builder -- "Write & Test" --> Sandbox[Code Sandbox]
        Sandbox -- "Register" --> ToolRegistry[Dynamic Tool Registry]
    end
    
    subgraph "Execution"
        SubAgent <--> ToolRegistry
        SubAgent <--> FileSystem
    end
```

---

## 4. Dynamic Workflows (动态工作流)

### Scenario: "I need to parse a specific binary format, but I don't have a tool for it."

```mermaid
sequenceDiagram
    participant O as Orchestrator
    participant B as Tool Builder
    participant S as Sandbox
    participant R as Registry
    participant E as Executor

    O->>E: Task: "Parse data.bin"
    E->>E: Thought: "I don't have a binary parser."
    E-->>O: Error: "Missing Tool"
    
    O->>B: Task: "Create a tool to parse .bin format X"
    B->>B: Writes Python Code (parser.py)
    B->>S: Run Tests on parser.py
    S-->>B: Tests Passed
    
    B->>R: Register Tool: parse_binary()
    R-->>O: Tool Available
    
    O->>E: Retry Task
    E->>R: Call: parse_binary("data.bin")
    R-->>E: Parsed Data
```

---

## 5. Technical Implementation Details (技术细节)

### 5.1 Dynamic Persona Engine
We use **System Message Injection** to change roles.

```python
class PersonaEngine:
    def switch_persona(self, role: str):
        base_prompt = load_prompt("base_agent")
        role_prompt = load_prompt(f"roles/{role}") # e.g., "senior_architect"
        self.current_system_message = base_prompt + "\n" + role_prompt
```

### 5.2 Dynamic Tool Builder (The Risky Part)
To safely allow the agent to build tools:
1.  **Code Generation**: Agent writes the function string.
2.  **Static Analysis**: Use `ast` to check for forbidden imports (e.g., `os.system`, `subprocess` - unless authorized).
3.  **Sandboxed Execution**: Run the tool in a separate process or Docker container first.
4.  **Hot-Loading**: Use `importlib` to load the validated module.

### 5.3 Web Search Integration
We will integrate a search provider (e.g., Tavily API for AI-optimized results).

```python
@tool
def web_search(query: str) -> str:
    """Searches the internet for current info."""
    results = tavily.search(query)
    return summarize(results)
```

## 6. Roadmap to Super-Agent

1.  **Phase 1: The Foundation (v3.0)**
    *   Implement ReAct Loop.
    *   Implement Basic Tool Registry.

2.  **Phase 2: Connectivity (v3.1)**
    *   Add **Web Search Tool**.
    *   Add **Persona Switching** (Prompt Management).

3.  **Phase 3: Self-Evolution (v3.2)**
    *   Implement **Tool Builder** (Code-writing-code).
    *   Implement **Sandbox** for safety.

---

## 7. Development Plan & Priorities (开发计划与优先级)

**目标**：在现有 v3.0 ReAct 基础上，逐步落地 v3.1 “动态超级体”能力，同时沿用 v2 的安全/状态护栏。

### P0（安全护栏 & 可靠性，先做）
- [ ] 将 v2 的状态管理/超时/紧急停止与日志体系移植到 `main_v3.py`（使用 `state_manager.py`、统一 `logger.py` 配置）。
- [ ] 修复 Executor 对话上下文累积（保证 ReAct 历史保留，避免仅覆盖 Observation）。
- [ ] 为工具增加基础沙箱：`run_command` 加入超时/白名单/工作目录限制，去掉不必要的 shell 权限；工具执行加 try/except 与输入校验。
- [ ] 增加循环/成本防护：最大步数、深度/递归限制、调用费用/时间预算与超限停止提示。

### P1（核心能力升级，v3.1 目标）
- [ ] Persona 引擎增强：支持动态切换/注入，Planner 能请求 Persona 角色；新增 Persona 配置入口。
- [ ] 研究员链路：独立 Researcher 代理，统一检索→摘要→引用链；接 Tavily/或可配置 provider。
- [ ] 观测性：结构化事件流（trace/iteration_id），成本/延迟/失败率指标与简单可视化（日志即可）。
- [ ] 配置与安全基础：权限/超时/预算集中配置（config.yaml），统一加载校验。

### P2（自进化 & 子代理，v3.2 方向）
- [ ] Tool Builder MVP：AST 黑名单/依赖审计→沙箱运行→自动单测（合成用例）→热加载/回滚注册。
- [ ] Sub-Agent Swarm：任务分解到专职子代理（Coder/QA/Research）；合并策略与冲突解决。
- [ ] Prompt/Persona 治理：模板版本化、注入检测、降级策略；Prompt 评测基准与回归测试。

### 里程碑交付
- v3.0.1：P0 全部完成（安全护栏、上下文修复、成本/循环防护）。
- v3.1.0：P1 完成（Persona/Research/观测性/配置安全），保持工具静态。
- v3.2.0：P2 完成（Tool Builder + 子代理协作 + Prompt 治理）。
