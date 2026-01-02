# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is **Claude Code Auto v3.1+**, an AI-native autonomous agent system built on top of the Claude Agent SDK. It implements a ReAct-based agent architecture with team collaboration capabilities, intelligent orchestration, and production-grade features.

**Current Version**: v4.0 (Leader-based orchestration architecture)
**Language**: Python 3.12+
**Key Dependencies**: claude-code-sdk, pydantic, pyyaml, fastapi, websockets, tavily-python

---

## Running the System

### Basic Execution

```bash
# Run with default config.yaml
python -m src.main

# Or using the batch script (Windows)
run_agent.bat

# The batch script sets the TAVILY_API_KEY environment variable
```

### Configuration

All configuration is managed through `config.yaml` at the project root. Key sections:

- **`task.goal`**: Main objective for the agent/team
- **`task.initial_prompt`**: Team mode trigger (when set, enables Team Mode with Leader orchestration)
- **`leader.enabled`**: Leader mode flag (NOTE: v4.0 architecture - Leader is now the internal orchestrator for Team Mode)
- **`cost_control`**: Budget limits and warnings
- **`safety.max_iterations`**: Safety limit for agent loops
- **`claude.model`**: Model selection (default: claude-sonnet-4-5)

### Testing

```bash
# Run tests (when pytest is available)
pytest tests/

# Run specific test
pytest tests/test_dependency_resolver.py -v
```

---

## Architecture Overview

### Two-Tier Mode System

The system operates in two primary modes:

**1. Original Mode** (Single Agent)
- Triggered when: `task.initial_prompt` is NOT set
- Simple Planner → Executor loop with ReAct reasoning
- Suitable for single-step or simple iterative tasks

**2. Team Mode** (Multi-Agent Collaboration)
- Triggered when: `task.initial_prompt` IS set
- Leader Agent orchestrates multiple specialized roles
- Intelligent mission decomposition, dependency resolution, quality validation
- Suitable for complex multi-step projects requiring different expertise

### Core Components (v4.0 Architecture)

**Leader Agent** (`src/core/leader/leader_agent.py`)
- Central orchestrator for Team Mode
- Decomposes user goals into SubMissions using LLM
- Assembles teams, resolves dependencies, monitors execution
- Implements 5 intervention strategies: CONTINUE, RETRY, ENHANCE, ESCALATE, TERMINATE
- Manages quality thresholds, budget limits, and retry logic

**Mission Decomposer** (`src/core/leader/mission_decomposer.py`)
- Breaks down high-level goals into structured SubMissions
- Defines dependencies, success criteria, and priorities per mission

**Team Assembler** (`src/core/team/team_assembler.py`)
- Selects appropriate roles for missions based on LLM analysis
- Loads role definitions from `roles/*.yaml`

**Dependency Resolver** (`src/core/team/dependency_resolver.py`)
- Implements Kahn's algorithm for topological sorting
- Detects circular dependencies
- Determines execution order for roles with dependencies

**Role Executor** (`src/core/team/role_executor.py`)
- Executes individual role tasks
- Optional Planner integration for sub-task decomposition
- Dual-layer validation: format rules + LLM semantic quality scoring
- Context passing between roles (smart summary for long content)

**Quality Validator** (`src/core/team/quality_validator.py`)
- LLM-driven semantic quality assessment (uses Haiku for cost efficiency)
- Scores outputs 0-100 against success criteria
- Identifies issues and provides improvement suggestions

**Planner Agent** (`src/core/agents/planner.py`)
- Decomposes tasks into structured action steps
- Optional per-role (controlled by `use_planner` in role definition)
- Exports decision traces to markdown

**Executor Agent** (`src/core/agents/executor.py`)
- ReAct loop execution (max 30 steps by default)
- Tool calls with JSON input parsing
- Observation tracking and error handling
- Exports execution traces to markdown

**Research Agent** (`src/core/agents/researcher.py`)
- Tavily-based web search with caching
- Available as both standalone agent and callable tools
- `quick_research()` and `deep_research()` modes

### Supporting Systems

**Event & Cost Tracking** (`src/core/events.py`)
- EventStore: Records all session events (SESSION_START, PLANNER_START, EXECUTOR_COMPLETE, etc.)
- CostTracker: Real-time token and cost tracking
- Budget control with warnings and auto-stop

**State Management** (`src/utils/state_manager.py`)
- Persistent workflow state in `workflow_state.json`
- Session ID management
- WorkflowStatus tracking (PENDING, IN_PROGRESS, COMPLETED, FAILED)

**Tool Registry** (`src/core/tool_registry.py`)
- Centralized tool registration and discovery
- File tools (write_file, read_file, list_directory)
- Shell tools (execute_command)
- Research tools (web_search, get_research_stats)

---

## Role Definitions

Roles are defined in YAML files in the `roles/` directory. Available roles:

- **Market-Researcher** (`roles/market_researcher.yaml`): Market analysis and competitive intelligence
- **AI-Native-Writer** (`roles/ai_native_writer.yaml`): Technical documentation
- **AI-Native-Developer** (`roles/ai_native_developer.yaml`): Full-stack development
- **Architect** (`roles/architect.yaml`): System architecture design
- **SEO-Specialist** (`roles/seo_specialist.yaml`): SEO optimization
- **Creative-Explorer** (`roles/creative_explorer.yaml`): Creative ideation
- **Role-Definition-Expert** (`roles/role_definition_expert.yaml`): Meta-role for creating new roles
- **Multidimensional-Observer** (`roles/multidimensional_observer.yaml`): Quality analysis

### Role Definition Structure

```yaml
name: "Role-Name"
description: "Human-readable description"
category: "research|development|writing|..."

mission:
  goal: "Primary mission statement"
  success_criteria:
    - "Specific success criterion 1"
    - "Specific success criterion 2"
  max_iterations: 10

output_standard:
  required_files:
    - "output-file.md"
  validation_rules:
    - type: "file_exists"
      file: "output-file.md"
    - type: "content_check"
      file: "output-file.md"
      must_contain:
        - "## Required Heading"
        - "Required keyword"
    - type: "min_length"
      file: "output-file.md"
      min_chars: 2000
    - type: "no_placeholders"
      files:
        - "output-file.md"
      forbidden_patterns:
        - "\\[TODO\\]"
        - "\\[PLACEHOLDER\\]"

recommended_persona: "researcher|coder|writer|..."

tools:
  - "web_search"
  - "write_file"
  - "read_file"

dependencies:
  - "Role-Name-That-Must-Complete-First"
```

### Role Validation

- **Format Validation**: File existence, content checks, minimum length, placeholder detection
- **Quality Validation** (optional per role): LLM semantic scoring against success criteria
- **Adaptive Thresholds** (optional): Adjusts validation based on task complexity (simple/medium/complex/expert)

---

## Key Workflows

### Team Mode Execution Flow

1. **User sets goal** in `config.yaml` with `task.initial_prompt` populated
2. **Leader Agent** decomposes goal into SubMissions (missions with dependencies)
3. **TeamAssembler** selects appropriate roles for each mission
4. **DependencyResolver** topologically sorts roles by dependencies
5. **Leader** iterates through sorted roles:
   - Injects resources (tools, MCP servers, skill prompts)
   - Creates RoleExecutor for each role
   - Passes context from upstream roles
   - Monitors execution (cost, quality, time)
6. **RoleExecutor** executes role mission:
   - Optional Planner breaks down mission into steps
   - Executor runs ReAct loop (max 30 iterations)
   - Dual-layer validation (format + semantic quality)
   - Retry on failure (up to max_iterations)
7. **Leader evaluates** quality and makes intervention decision:
   - CONTINUE (quality ≥ threshold): Pass to next role
   - RETRY (temporary failure): Retry same role
   - ENHANCE (requirements unclear): Refine requirements with LLM
   - ESCALATE (capability gap): Add helper role
   - TERMINATE (unrecoverable): Stop with failure report
8. **Context Preparation** for downstream roles:
   - Short content (<500 chars): Full inclusion
   - Long content (≥500 chars): Summary + full content saved to trace file
9. **Output Integration**: Leader aggregates all outputs into deliverable
10. **Report Generation**: Cost report, quality report, intervention log

### Dependency Resolution Example

Given roles with dependencies:
```
Market-Researcher: []
AI-Native-Writer: [Market-Researcher]
AI-Native-Developer: [AI-Native-Writer]
```

DependencyResolver produces execution order:
1. Market-Researcher (Layer 1: no dependencies)
2. AI-Native-Writer (Layer 2: depends on MR)
3. AI-Native-Developer (Layer 3: depends on ANW)

### Context Passing Strategy

To avoid token waste and context loss:

- **< 500 characters**: Embed full content in context
- **≥ 500 characters**: Generate summary (first 300 + last 100 chars) + save full content to trace file
- **Trace files**: Saved to `logs/trace/{session_id}_{role}_{filename}.md`
- **Downstream roles** receive summary + reference to trace file

---

## File Structure

```
claude-code-auto/
├── config.yaml                 # Main configuration (task, safety, costs, Leader settings)
├── requirements.txt            # Python dependencies
├── run_agent.bat              # Windows launch script (sets TAVILY_API_KEY)
├── CLAUDE.md                  # This file
├── src/
│   ├── main.py                # Entry point, mode detection (Original vs Team)
│   ├── config.py              # Pydantic configuration models
│   ├── core/
│   │   ├── leader/            # Leader Agent (v4.0 orchestration)
│   │   │   ├── leader_agent.py
│   │   │   └── mission_decomposer.py
│   │   ├── team/              # Team collaboration
│   │   │   ├── team_assembler.py
│   │   │   ├── dependency_resolver.py
│   │   │   ├── role_executor.py
│   │   │   ├── role_registry.py
│   │   │   ├── quality_validator.py
│   │   │   └── team_orchestrator.py
│   │   ├── agents/            # Agent implementations
│   │   │   ├── planner.py
│   │   │   ├── executor.py
│   │   │   ├── researcher.py
│   │   │   ├── persona.py
│   │   │   └── sdk_client.py
│   │   ├── tools/             # Tool implementations
│   │   │   ├── file_tools.py
│   │   │   ├── shell_tools.py
│   │   │   └── research_tools.py
│   │   ├── events.py          # EventStore & CostTracker
│   │   ├── tool_registry.py   # Central tool registration
│   │   ├── budget/            # Hierarchical budget control
│   │   ├── governance/        # Helper role governance
│   │   ├── isolation/         # Permission & rate limiting
│   │   ├── observability/     # Structured logging & tracing
│   │   ├── quality/           # Multi-dim evaluation
│   │   ├── recovery/          # Checkpoints & idempotency
│   │   └── output/            # Output integration & reporting
│   └── utils/
│       ├── logger.py          # Structured logging setup
│       ├── json_parser.py     # Robust JSON parsing
│       └── state_manager.py   # Workflow state persistence
├── roles/                     # Role definitions (YAML)
│   ├── market_researcher.yaml
│   ├── ai_native_writer.yaml
│   ├── ai_native_developer.yaml
│   └── ...
├── resources/                 # Resource configurations
│   ├── mcp_servers.yaml       # MCP server configs
│   ├── skill_prompts.yaml     # Skill prompt templates
│   └── tool_mappings.yaml     # Tool-to-role mappings
├── schemas/                   # JSON schemas for validation
├── logs/                      # Runtime logs
│   ├── trace/                 # Markdown execution traces
│   ├── interventions/         # Leader intervention decisions
│   └── evaluations/           # Quality evaluation results
├── demo_act/                  # Default work directory
├── demo_mirror/               # Mirror directory for recovery
└── docs/                      # Architecture documentation
    ├── Architecture-Refactor-v4.0.md
    ├── System-Enhancements-v4.1.md
    └── LEADER_MODE_GUIDE.md
```

---

## Important Implementation Details

### Leader Intervention Strategies

The Leader Agent makes intelligent decisions based on quality, cost, and budget:

- **CONTINUE**: Quality score ≥ threshold, within budget → Proceed to next role
- **RETRY**: Transient failure (e.g., API timeout) → Retry same role (max `leader.max_mission_retries`)
- **ENHANCE**: Requirements unclear → Use LLM to refine requirements and retry
- **ESCALATE**: Capability gap detected → Add helper role (Debugger, Reviewer, etc.)
- **TERMINATE**: Unrecoverable failure → Stop execution and generate recovery guide

### Quality Validation

**Dual-Layer Architecture**:

1. **Format Validation** (always on):
   - File existence checks
   - Content pattern matching
   - Minimum length (× complexity multiplier)
   - Placeholder detection (TODO, PLACEHOLDER, TBD)

2. **Semantic Quality Validation** (optional per role):
   - LLM (Haiku) scores output 0-100 against success criteria
   - Returns QualityScore with:
     - `overall_score`: 0-100
     - `criteria_scores`: Per-criteria breakdown
     - `issues`: List of problems found
     - `suggestions`: Improvement recommendations
   - Configurable threshold (default: 70.0)

**Adaptive Validation** (optional per role):
- Automatically estimates complexity: simple, medium, complex, expert
- Applies complexity multiplier to min_length: 0.7x, 1.0x, 1.5x, 2.0x
- Based on keywords + content length + criteria count

### Cost Control

Hierarchical budget tracking:

- **Session-level**: Total budget (`cost_control.max_budget_usd`)
- **Mission-level**: Allocated per mission (30%, 20%, 10% by priority)
- **Role-level**: Sub-budget per role execution
- **Action-level**: Individual tool calls tracked

Budget checks:
- **Warning**: 80% of budget consumed → COST_WARNING event
- **Critical**: 95% → Circuit breaker opens
- **Exceeded**: 100% → Auto-stop (if `auto_stop_on_exceed=true`)

### ReAct Loop

The Executor uses the ReAct (Reasoning + Acting) pattern:

```
1. Thought: Analyze current state
2. Action: Select and call tool
3. Observation: Get tool result
4. Repeat until Final Answer or max_steps (30)
```

Tool call format:
```json
{
  "tool_name": "write_file",
  "input": {
    "path": "output.md",
    "content": "..."
  }
}
```

### Markdown Trace Logs

All decisions and executions are logged to markdown for auditability:

- **Planner traces**: `logs/trace/{session_id}_{role}_step1.md`
  - Goal, context, action steps, reasoning

- **Executor traces**: `logs/trace/{session_id}_{role}_step2.md`
  - ReAct loop steps (thought, action, observation)

- **Content traces**: `logs/trace/context_{role}_{filename}`
  - Full content saved when summary is passed to avoid truncation

- **Intervention logs**: `logs/interventions/{session_id}_interventions.md`
  - Leader intervention decisions with reasoning

---

## Common Development Tasks

### Adding a New Role

1. Create YAML file in `roles/` (e.g., `roles/data_analyst.yaml`)
2. Define mission, output standards, tools, dependencies
3. Set `recommended_persona` for optimal performance
4. Test by creating a mission that requires this role
5. Optionally enable quality validation with `enable_quality_check: true`

### Enabling Leader Mode

In `config.yaml`:
```yaml
task:
  goal: "Your complex goal here"
  initial_prompt: "Set this to enable Team Mode with Leader"

leader:
  enabled: true  # Optional in v4.0 (auto-enabled when initial_prompt is set)
  max_mission_retries: 3
  quality_threshold: 70.0
  enable_intervention: true
```

### Modifying Validation Rules

Edit role YAML file's `output_standard.validation_rules` section:

- `file_exists`: Check file exists
- `content_check`: Must contain patterns
- `min_length`: Minimum character count
- `no_placeholders`: Forbidden patterns (TODO, PLACEHOLDER)

For adaptive validation, add to role definition:
```yaml
adaptive: true
base_chars: 2000  # Base length for "medium" complexity
```

### Debugging Execution

1. Check `logs/trace/` for markdown decision traces
2. Check `logs/interventions/` for Leader decisions
3. Check `workflow_state.json` for current workflow state
4. Enable DEBUG logging in `config.yaml`: `logging.level: "DEBUG"`

### Working with Cost Tracking

```bash
# Check current costs in logs
cat logs/cost_report.json

# Enable budget control in config.yaml
cost_control:
  enabled: true
  max_budget_usd: 10.0
  warning_threshold: 0.8
  auto_stop_on_exceed: true
```

---

## Key Design Decisions

### Why Two Modes?

- **Original Mode**: Fast, lightweight for simple tasks
- **Team Mode**: Powerful, orchestrated for complex projects
- Clear decision boundary based on `initial_prompt` presence

### Why Leader as Orchestrator?

- Separates concerns: Leader decides, Roles execute
- Intelligent intervention beyond simple retry loops
- Budget and quality awareness at orchestration level
- Easier to extend with new strategies (ENHANCE, ESCALATE)

### Why Kahn's Algorithm for Dependencies?

- O(V+E) time complexity (optimal)
- Detects circular dependencies (prevents deadlocks)
- Produces deterministic execution order
- Enables parallel execution opportunities (future enhancement)

### Why Dual-Layer Validation?

- **Format**: Fast, deterministic, catches obvious errors
- **Semantic**: Slow, expensive, catches subtle quality issues
- Optional semantic validation reduces cost for simple tasks
- Adaptive validation avoids over-validation

### Why Markdown Traces?

- Human-readable audit trail
- No external dependencies (unlike databases)
- Git-friendly for version control
- Easy to share with stakeholders

---

## Known Limitations & TODOs

See `ARCHITECTURE_STATUS.md` for detailed implementation status:

**High Priority (P0)**:
- Complete OutputIntegrator (markdown report generation)
- Implement Resource Injection (dynamic tool allocation)
- Implement ENHANCE and ESCALATE intervention strategies

**Medium Priority (P1)**:
- Integrate Helper Role Management (ESCALATE support)
- Integrate Context Versioning (VersionedContextManager in context passing)

**Low Priority (P2)**:
- Additional documentation
- Expanded test coverage

---

## Related Documentation

- **Architecture Status**: [ARCHITECTURE_STATUS.md](ARCHITECTURE_STATUS.md) - Detailed implementation status
- **Team Workflow**: [AI-Native-Team-Workflow.md](AI-Native-Team-Workflow.md) - Visual workflow diagrams
- **Architecture Refactor**: [docs/Architecture-Refactor-v4.0.md](docs/Architecture-Refactor-v4.0.md) - v4.0 redesign rationale
- **System Enhancements**: [docs/System-Enhancements-v4.1.md](docs/System-Enhancements-v4.1.md) - Production-grade features
- **Leader Mode Guide**: [docs/LEADER_MODE_GUIDE.md](docs/LEADER_MODE_GUIDE.md) - Leader mode usage
- **Changelog**: [CHANGELOG.md](CHANGELOG.md) - Version history

---

## Summary

This is a sophisticated AI-native agent system with:

- **Two operating modes**: Single agent (Original) vs. multi-agent team (Team with Leader)
- **Intelligent orchestration**: Leader Agent with 5 intervention strategies
- **Dependency management**: Topological sort with circular dependency detection
- **Quality assurance**: Dual-layer validation (format + semantic)
- **Cost control**: Hierarchical budget tracking with circuit breakers
- **Full observability**: Event logging, cost tracking, markdown traces
- **Extensibility**: YAML-based role definitions, pluggable tools

When working with this codebase:
1. Read the architecture docs first to understand the v4.0 design
2. Check role definitions in `roles/` to understand capabilities
3. Enable detailed logging to see execution flow
4. Review markdown traces for debugging decisions
5. Respect the separation: Leader orchestrates, Roles execute
