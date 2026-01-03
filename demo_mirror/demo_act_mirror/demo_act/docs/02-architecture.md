# Architecture: Claude Code Auto v4.0

## Document Information
- **Version**: 1.0.0
- **Last Updated**: 2025-01-03
- **Status**: Final
- **Author**: Team Mode Documentation Team

---

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Component Design](#component-design)
3. [Data Flow](#data-flow)
4. [Technology Stack](#technology-stack)
5. [Design Patterns](#design-patterns)
6. [Sequence Diagrams](#sequence-diagrams)

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User / Developer                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ config.yaml
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Entry Point                            │
│                    src/main.py                              │
│                  (Mode Detection)                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
            ▼                               ▼
┌──────────────────────┐        ┌──────────────────────────┐
│   Original Mode      │        │      Team Mode            │
│  (Single Agent)      │        │   (Multi-Agent Team)      │
│                      │        │                           │
│  Planner → Executor  │        │  Leader Agent             │
│  ReAct Loop          │        │  ├─ Mission Decomposer    │
│                      │        │  ├─ Team Assembler        │
│                      │        │  ├─ Dependency Resolver   │
│                      │        │  └─ Role Executors        │
└──────────────────────┘        │                           │
                                │  For Each Role:            │
                                │  ├─ Optional Planner       │
                                │  ├─ Executor (ReAct)       │
                                │  └─ Quality Validator      │
                                └──────────────────────────┘
```

### Architectural Principles

1. **Separation of Concerns**: Each component has a single, well-defined responsibility
2. **Dependency Injection**: Components receive dependencies rather than creating them
3. **Event-Driven**: Components communicate via events (EventStore)
4. **Configuration over Code**: Behavior controlled via YAML configuration
5. **Observability First**: All decisions logged and traceable

---

## Component Design

### Core Components

#### 1. Main Entry Point (`src/main.py`)

**Responsibility**: Detect mode and initialize appropriate workflow

**Key Functions**:
- `detect_mode()`: Check if `task.initial_prompt` is set
- `run_original_mode()`: Launch single-agent workflow
- `run_team_mode()`: Launch multi-agent team workflow

**Dependencies**:
- ConfigLoader
- EventStore
- CostTracker

---

#### 2. Leader Agent (`src/core/leader/leader_agent.py`)

**Responsibility**: Orchestrate multi-agent team execution

**Key Attributes**:
- `mission_decomposer`: Breaks down goals into SubMissions
- `team_assembler`: Selects roles for missions
- `dependency_resolver`: Determines execution order
- `quality_threshold`: Minimum quality score (default: 70.0)

**Key Methods**:
```python
async def orchestrate(goal: str) -> TeamResult:
    """Orchestrate team execution from goal to result"""
    missions = await self.decompose_goal(goal)
    team = await self.assemble_team(missions)
    sorted_roles = self.resolve_dependencies(team)
    results = []
    for role in sorted_roles:
        result = await self.execute_role(role, context)
        intervention = self.evaluate(result)
        if intervention == Strategy.CONTINUE:
            results.append(result)
        elif intervention == Strategy.RETRY:
            # Retry same role
        elif intervention == Strategy.TERMINATE:
            # Stop execution
    return TeamResult(results)
```

**Intervention Strategies**:
- `CONTINUE`: Quality ≥ threshold, proceed
- `RETRY`: Transient failure, retry (max 3 times)
- `ENHANCE`: Refine requirements (NOT IMPLEMENTED)
- `ESCALATE`: Add helper role (NOT IMPLEMENTED)
- `TERMINATE`: Unrecoverable failure, stop

---

#### 3. Mission Decomposer (`src/core/leader/mission_decomposer.py`)

**Responsibility**: Decompose high-level goals into SubMissions

**Input**:
- `goal`: User's high-level objective (e.g., "Research elderly care market")

**Output**:
- `List[SubMission]` where each SubMission has:
  - `mission_id`: UUID
  - `goal`: Actionable mission statement
  - `success_criteria`: List of measurable outcomes
  - `dependencies`: List of mission_id dependencies
  - `priority`: HIGH, MEDIUM, LOW

**Implementation**:
- Uses Claude Sonnet 4.5 with structured output
- Prompt includes goal and desired output format
- LLM returns JSON matching SubMission schema
- Validates all mission_id dependencies exist

**Example**:
```python
# Input: "Research elderly care market"
# Output:
[
    SubMission(
        mission_id="mission_1",
        goal="Conduct market research on elderly care industry",
        success_criteria=[
            "Market size report with TAM/SAM/SOM",
            "Competitor analysis with top 5 competitors",
            "User pain points identified"
        ],
        dependencies=[],
        priority="HIGH"
    ),
    SubMission(
        mission_id="mission_2",
        goal="Create market research report document",
        success_criteria=[
            "Professional markdown document",
            "Includes all research findings",
            "Formatted with clear sections"
        ],
        dependencies=["mission_1"],
        priority="MEDIUM"
    )
]
```

---

#### 4. Team Assembler (`src/core/team/team_assembler.py`)

**Responsibility**: Select appropriate roles for each SubMission

**Input**:
- `missions`: List of SubMissions
- `role_definitions`: Loaded from `roles/*.yaml`

**Output**:
- `Dict[mission_id, List[Role]]`: Mapping of missions to roles

**Implementation**:
- For each SubMission, use LLM to analyze requirements
- Match requirements against role descriptions
- Return ranked list of suitable roles
- Validate selected roles have required tools

**Example**:
```python
# Input: SubMission(goal="Conduct market research...")
# Output:
{
    "mission_1": [
        Role(name="Market-Researcher", tools=["web_search", "write_file"])
    ]
}
```

---

#### 5. Dependency Resolver (`src/core/team/dependency_resolver.py`)

**Responsibility**: Resolve role dependencies using Kahn's algorithm

**Input**:
- `roles`: List of Role with dependencies

**Output**:
- `List[List[Role]]`: Layered execution order

**Algorithm**:
```python
def resolve_dependencies(roles: List[Role]) -> List[List[Role]]:
    """Kahn's algorithm for topological sorting"""
    # Build graph
    in_degree = {role: len(role.dependencies) for role in roles}
    graph = {role: role.dependencies for role in roles}

    # Initialize queue with nodes having in_degree 0
    queue = [role for role in roles if in_degree[role] == 0]
    result = []

    while queue:
        layer = []
        for role in queue:
            layer.append(role)
            # Decrement in_degree for neighbors
            for neighbor in graph[role]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        result.append(layer)
        queue = [role for role in roles if in_degree[role] == 0 and role not in result]

    # Check for circular dependencies
    if len(flatten(result)) != len(roles):
        raise CircularDependencyError("Circular dependency detected")

    return result
```

**Example**:
```python
# Input:
# Market-Researcher: []
# AI-Native-Writer: [Market-Researcher]
# AI-Native-Developer: [AI-Native-Writer]

# Output:
[
    [Market-Researcher],           # Layer 1: No dependencies
    [AI-Native-Writer],             # Layer 2: Depends on MR
    [AI-Native-Developer]           # Layer 3: Depends on ANW
]
```

---

#### 6. Role Executor (`src/core/team/role_executor.py`)

**Responsibility**: Execute individual role missions

**Key Attributes**:
- `role`: Role definition
- `context`: Context from upstream roles
- `use_planner`: Whether to use Planner (from role definition)
- `enable_quality_check`: Whether to validate quality (from role definition)

**Workflow**:
```python
async def execute(self, context: str) -> RoleResult:
    # 1. Optional Planner
    if self.role.use_planner:
        planner = PlannerAgent(self.role)
        steps = await planner.plan(self.role.mission, context)
        self.export_planner_trace(steps)

    # 2. Executor (ReAct Loop)
    executor = ExecutorAgent(self.role)
    result = await executor.execute(
        mission=self.role.mission,
        context=context,
        max_iterations=30
    )
    self.export_executor_trace(result)

    # 3. Format Validation
    format_valid = self.validate_format(result)
    if not format_valid:
        raise FormatValidationError("Format validation failed")

    # 4. Semantic Quality Validation (optional)
    if self.role.enable_quality_check:
        validator = QualityValidator()
        quality_score = await validator.validate(
            output=result,
            success_criteria=self.role.mission.success_criteria
        )
        self.export_quality_trace(quality_score)

        if quality_score.overall_score < self.quality_threshold:
            raise QualityValidationError(
                f"Quality score {quality_score.overall_score} < threshold {self.quality_threshold}"
            )

    return RoleResult(
        output=result,
        quality_score=quality_score,
        format_valid=format_valid
    )
```

---

#### 7. Quality Validator (`src/core/team/quality_validator.py`)

**Responsibility**: LLM-driven semantic quality assessment

**Implementation**:
- Uses Claude Haiku for cost efficiency
- Prompts LLM with success criteria and output
- Returns QualityScore (0-100) with breakdown

**Prompt Template**:
```
You are a Quality Assurance Evaluator. Evaluate the following output against the success criteria.

Output:
{output}

Success Criteria:
{criteria}

Return a JSON object with:
{
  "overall_score": 0-100,
  "criteria_scores": {
    "criterion_1": 0-100,
    ...
  },
  "issues": ["List of problems found"],
  "suggestions": ["List of improvement suggestions"]
}
```

---

#### 8. Planner Agent (`src/core/agents/planner.py`)

**Responsibility**: Decompose tasks into structured action steps

**Output Format**:
```markdown
# Goal: {mission.goal}

# Context
{context}

# Action Steps
1. [Step 1]
   - Thought: {reasoning}
   - Action: {tool_name}
   - Input: {json_input}

2. [Step 2]
   ...
```

---

#### 9. Executor Agent (`src/core/agents/executor.py`)

**Responsibility**: Execute tasks using ReAct loop

**ReAct Loop**:
```python
async def execute(self, mission: Mission, context: str, max_iterations: int = 30):
    for i in range(max_iterations):
        # Thought
        thought = await self.llm.generate(f"Current state: {observation}\nWhat should I do next?")

        # Action
        action = self.parse_action(thought)

        # Observation
        result = await self.call_tool(action.tool_name, action.input)
        observation = f"Called {action.tool_name} with {action.input}\nResult: {result}"

        # Check for completion
        if "Final Answer" in thought:
            return result
```

**Tool Call Format**:
```json
{
  "tool_name": "write_file",
  "input": {
    "path": "output.md",
    "content": "..."
  }
}
```

---

#### 10. Event & Cost Tracking (`src/core/events.py`)

**EventStore**:
```python
class EventStore:
    def record(self, event_type: str, data: dict):
        event = {
            "event_id": uuid4(),
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "session_id": self.session_id,
            "data": data
        }
        self.events.append(event)
        self.append_to_file(event)
```

**CostTracker**:
```python
class CostTracker:
    def track_token_usage(self, model: str, input_tokens: int, output_tokens: int):
        cost = self.calculate_cost(model, input_tokens, output_tokens)
        self.total_cost += cost
        self.breakdown[model]["tokens"] += input_tokens + output_tokens
        self.breakdown[model]["cost_usd"] += cost

        if self.total_cost >= self.budget * 0.8:
            self.event_store.record("COST_WARNING", {"budget_used": 0.8})
```

---

#### 11. Tool Registry (`src/core/tool_registry.py`)

**Responsibility**: Centralized tool registration and discovery

**API**:
```python
registry = ToolRegistry()

# Register tool
registry.register_tool(
    name="write_file",
    description="Write content to a file",
    input_schema={"type": "object", "properties": {"path": "...", "content": "..."}},
    handler=write_file_handler
)

# Get tool
tool = registry.get_tool("write_file")

# List tools
tools = registry.list_tools()
```

---

#### 12. State Manager (`src/utils/state_manager.py`)

**Responsibility**: Persistent workflow state

**State Structure**:
```python
class WorkflowState:
    session_id: str
    workflow_status: WorkflowStatus  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    current_mode: str  # "original" or "team"
    current_role: Optional[str]
    completed_roles: List[str]
    failed_roles: List[str]
    total_cost_usd: float
    last_updated: datetime
```

**Operations**:
- `save_state()`: Atomic write to `workflow_state.json`
- `load_state()`: Load from `workflow_state.json`
- `update_status()`: Update workflow_status
- `add_completed_role()`: Add role to completed_roles

---

## Data Flow

### Team Mode Execution Flow

```
User Goal (config.yaml task.goal)
         │
         ▼
┌────────────────────────────────────────┐
│  1. Leader Agent decomposes goal       │
│     → SubMissions (LLM)                │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  2. Team Assembler selects roles       │
│     → Mission → Roles mapping (LLM)    │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  3. Dependency Resolver sorts roles    │
│     → Layered execution order          │
│     (Kahn's algorithm)                 │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  4. For each layer (in order):         │
│                                        │
│  4a. Prepare Context                   │
│      - From upstream roles             │
│      - Smart summary if ≥500 chars     │
│      - Save full content to trace      │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  4b. Execute Role (Role Executor)      │
│                                        │
│      IF use_planner:                   │
│        ┌──────────────────────────┐    │
│        │ Planner → Action Steps   │    │
│        └───────────┬──────────────┘    │
│                    │                    │
│                    ▼                    │
│      ┌──────────────────────────┐      │
│      │ Executor (ReAct Loop)    │      │
│      │ ├─ Tool calls            │      │
│      │ ├─ Observations          │      │
│      │ └─ Format validation     │      │
│      └───────────┬──────────────┘      │
│                  │                      │
│                  ▼                      │
│      IF enable_quality_check:           │
│        ┌──────────────────────────┐    │
│        │ Quality Validator (LLM)  │    │
│        └───────────┬──────────────┘    │
└────────────────────┼────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────┐
│  5. Leader evaluates quality           │
│     → Intervention decision            │
│                                        │
│     IF quality ≥ threshold:            │
│        → CONTINUE (next role)          │
│     ELSE IF transient failure:         │
│        → RETRY (same role)             │
│     ELSE IF requirements unclear:      │
│        → ENHANCE (refine requirements) │
│     ELSE IF capability gap:            │
│        → ESCALATE (add helper role)    │
│     ELSE:                              │
│        → TERMINATE (stop execution)    │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  6. Output Integration                 │
│     → Aggregate all role outputs       │
│     → Generate deliverable             │
└────────────┬───────────────────────────┘
             │
             ▼
┌────────────────────────────────────────┐
│  7. Report Generation                  │
│     ├─ Cost report (JSON)              │
│     ├─ Quality report (markdown)       │
│     └─ Intervention log (markdown)     │
└────────────────────────────────────────┘
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.12+ | Runtime environment |
| **Agent Framework** | Claude Agent SDK | Latest | Agent lifecycle and tools |
| **Configuration** | PyYAML | 6.0+ | YAML parsing |
| **Data Validation** | Pydantic | 2.0+ | Type-safe models |
| **Research** | Tavily Python SDK | Latest | Web search |
| **Async I/O** | asyncio | Built-in | Concurrent operations |
| **Logging** | Structlog | 23.0+ | Structured logging |
| **State Storage** | JSON | Built-in | Persistent state |

### Development Tools

| Tool | Purpose |
|------|---------|
| **pytest** | Unit testing |
| **black** | Code formatting |
| **mypy** | Type checking |
| **ruff** | Linting |

---

## Design Patterns

### 1. Strategy Pattern
**Usage**: Leader intervention strategies

```python
class InterventionStrategy(ABC):
    @abstractmethod
    def execute(self, context: ExecutionContext) -> Decision:
        pass

class ContinueStrategy(InterventionStrategy):
    def execute(self, context: ExecutionContext) -> Decision:
        return Decision(action="CONTINUE", reasoning="Quality meets threshold")

class RetryStrategy(InterventionStrategy):
    def execute(self, context: ExecutionContext) -> Decision:
        return Decision(action="RETRY", reasoning="Transient failure detected")
```

### 2. Chain of Responsibility
**Usage**: Validation pipeline

```python
class Validator(ABC):
    def __init__(self, next_validator: Optional['Validator'] = None):
        self.next_validator = next_validator

    def validate(self, output: str) -> ValidationResult:
        result = self._validate(output)
        if not result.passed and self.next_validator:
            return self.next_validator.validate(output)
        return result

class FileExistsValidator(Validator):
    def _validate(self, output: str) -> ValidationResult:
        # Check file exists
        pass

class ContentCheckValidator(Validator):
    def _validate(self, output: str) -> ValidationResult:
        # Check content patterns
        pass
```

### 3. Observer Pattern
**Usage**: Event logging

```python
class EventStore:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, observer):
        self.subscribers.append(observer)

    def record(self, event_type: str, data: dict):
        event = self._create_event(event_type, data)
        for observer in self.subscribers:
            observer.notify(event)

class CostTracker:
    def notify(self, event):
        if event.event_type in ["COST_UPDATE", "COST_WARNING"]:
            self.update_budget(event.data)
```

### 4. Factory Pattern
**Usage**: Agent creation

```python
class AgentFactory:
    def create_agent(self, agent_type: str, config: dict) -> Agent:
        if agent_type == "planner":
            return PlannerAgent(config)
        elif agent_type == "executor":
            return ExecutorAgent(config)
        elif agent_type == "researcher":
            return ResearcherAgent(config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
```

### 5. Template Method Pattern
**Usage**: Role execution workflow

```python
class RoleExecutor:
    async def execute(self, context: str) -> RoleResult:
        # Template method defining workflow
        pre_result = await self.pre_execute(context)
        main_result = await self.do_execute(pre_result)
        post_result = await self.post_execute(main_result)
        return post_result

    async def do_execute(self, context: str) -> RoleResult:
        # Subclasses override this
        raise NotImplementedError
```

---

## Sequence Diagrams

### Team Mode Execution Sequence

```
User          Main          Leader         Decomposer      Assembler       Resolver       RoleExecutor
 │              │              │                │               │              │               │
 │─goal─────────>│              │                │               │              │               │
 │              │              │                │               │              │               │
 │              │─orchestrate─>│                │               │              │               │
 │              │              │                │               │              │               │
 │              │              │─decompose─────>│               │              │               │
 │              │              │                │               │              │               │
 │              │              │<─SubMissions───│               │              │               │
 │              │              │                                │              │               │
 │              │              │─assemble──────────────────────>│              │               │
 │              │              │                                │              │               │
 │              │              │<─Roles─────────────────────────│              │               │
 │              │              │                                               │               │
 │              │              │─resolve──────────────────────────────────────>│               │
 │              │              │                                               │               │
 │              │              │<─Sorted Roles─────────────────────────────────│               │
 │              │              │                                               │               │
 │              │              │─execute_role──────────────────────────────────────────────────>│
 │              │              │                                               │               │
 │              │              │                                               │               │─Planner──>│
 │              │              │                                               │               │<─Steps────│
 │              │              │                                               │               │
 │              │              │                                               │               │─Executor─>│
 │              │              │                                               │               │<─Result───│
 │              │              │                                               │               │
 │              │              │                                               │               │─Validate─>│
 │              │              │                                               │               │<─Score────│
 │              │              │                                               │               │
 │              │              │<─RoleResult─────────────────────────────────────────────────────│
 │              │              │                                               │               │
 │              │              │─evaluate───────────────>│                       │              │
 │              │              │                        │                       │              │
 │              │              │<─intervention─────────│                       │              │
 │              │              │                        │                       │              │
 │              │              │─execute_role──────────────────────────────────────────────────>│
 │              │              │              (next role or retry)             │               │
 │              │              │                                               │               │
 │              │              │<─TeamResult─────────────────────────────────────────────────────│
 │              │              │                                               │               │
 │<─result──────│              │                                               │               │
 │              │              │                                               │               │
```

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-03 | Initial architecture documentation | Team Mode Documentation Team |

---

*This document is part of the comprehensive documentation suite for Claude Code Auto v4.0. For the complete documentation package, refer to the related documents listed in the Project Context.*
