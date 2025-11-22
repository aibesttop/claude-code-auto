# Architecture V2: Dynamic Multi-Agent Collaboration System

## 1. Core Philosophy: Tool-First & Dynamic Generation

This architecture evolves the system from **Static Role Selection** to **Dynamic Agent Generation**, based on the "Three-Layer Design Pattern" (Generation, Organization, Scheduling).

### The Paradigm Shift
- **V1 (Current)**: "I have a Writer Role. What tools does it need?"
- **V2 (Target)**: "I need to analyze this dataset. What tools do I need? -> Create an Agent with those tools."

---

## 2. Layer 1: Dynamic Agent Generation (智能体生成)

### Concept
Instead of loading pre-defined YAMLs, the system analyzes the sub-task and "compiles" an agent on the fly.

### Implementation: `RoleGenerator`
```python
class RoleGenerator:
    def generate_role(self, subtask: str, context: str) -> Role:
        # 1. Analyze Task Requirements
        capabilities = self.analyze_requirements(subtask)
        
        # 2. Select Tools (Tool-First)
        selected_tools = self.tool_registry.match_tools(capabilities)
        
        # 3. Define Persona
        persona = self.persona_engine.synthesize_persona(selected_tools)
        
        # 4. Create Role Object
        return Role(
            name=f"Agent_{hash(subtask)}",
            mission=Mission(goal=subtask),
            tools=selected_tools,
            persona=persona
        )
```

---

## 3. Layer 2: Agent Organization (智能体组织)

### Concept
Move from Linear Sequence (`[A, B, C]`) to **Adaptive Dependency Graph**.

### Implementation: `CollaborativeGraph`
- **Nodes**: Agents/Roles
- **Edges**: Data flow & Dependencies
- **Logic**:
    - "Agent A (Research)" runs first.
    - "Agent B (Writer)" and "Agent C (Coder)" run in parallel once A finishes.
    - "Agent D (Reviewer)" runs only after B and C finish.

```python
class TeamTopology:
    def build_graph(self, goal: str) -> DiGraph:
        # Decompose goal into subtasks with dependencies
        subtasks = self.planner.decompose(goal)
        return self.graph_builder.build(subtasks)
```

---

## 4. Layer 3: Agent Scheduling (智能体调度)

### Concept
Real-time monitoring and dynamic adjustment based on execution state.

### Implementation: `ContextAwareScheduler`
- **Monitor**: Watch `validation_result` and `context`.
- **Decision Engine**:
    - *Case 1*: Agent A fails validation 3 times -> **Spawn "Debugger Agent"**.
    - *Case 2*: Agent A discovers new info -> **Dynamically add "Specialist Agent"** to the queue.
    - *Case 3*: Task completed early -> **Prune remaining agents**.

```python
class Scheduler:
    async def run_loop(self):
        while not self.graph.is_empty():
            ready_agents = self.graph.get_ready_nodes()
            
            for agent in ready_agents:
                result = await agent.execute()
                
                # Dynamic Adjustment
                if result.status == 'needs_help':
                    helper = self.generate_helper_agent(result.error)
                    self.graph.add_node(helper, priority=HIGH)
```

---

## 5. Tool System Methodology (工具体系)

### Tool Definition Schema
Tools define the agent's boundaries. We need a rich metadata layer for tools.

```python
class ToolMetadata:
    name: str
    category: str  # "Information", "Processing", "Interaction", "Creation"
    capabilities: List[str]  # ["read_code", "network_access"]
    complexity: int
```

### Workflow
1. **Task Analysis**: "Need to scrape website and summarize."
2. **Tool Deduction**: Needs `web_search`, `browser_interaction`, `summarization_model`.
3. **Agent Synthesis**: Create "WebScraperAgent" with these specific tools.

---

## 6. Integration Roadmap

### Phase 1: Foundation (Current) ✅
- Static Roles (YAML)
- Linear Execution
- Basic Validation

### Phase 2: Dynamic Tools (Next Step)
- [ ] Implement `ToolRegistry` with capability tagging
- [ ] Modify `Role` to accept dynamic tool lists
- [ ] Update `TeamAssembler` to select tools based on prompt

### Phase 3: Dynamic Generation
- [ ] Create `RoleGenerator` class (LLM-based)
- [ ] Allow `TeamAssembler` to create "Custom Roles" if no YAML fits

### Phase 4: Adaptive Scheduling
- [ ] Implement `DependencyGraph` for non-linear execution
- [ ] Add `RuntimeMonitor` to `TeamOrchestrator`

---

## 7. Example Scenario: "Fix a Bug in Legacy Code"

1. **User Request**: "Fix the race condition in module X."
2. **Generation Layer**:
    - Analyzes request.
    - Identifies need for: `CodeAnalysisTool`, `TestRunner`, `GitInterface`.
    - Generates: **"BugFixSpecialist"** agent.
3. **Organization Layer**:
    - Creates plan: Analyze -> Reproduce -> Fix -> Verify.
4. **Execution & Scheduling**:
    - **Agent** runs "Reproduce". Fails to reproduce.
    - **Scheduler** detects failure.
    - **Scheduler** dynamically spawns **"TestGenAgent"** to create better reproduction scripts.
    - **TestGenAgent** succeeds.
    - **Scheduler** hands control back to **BugFixSpecialist**.
5. **Completion**: Bug fixed and verified.
