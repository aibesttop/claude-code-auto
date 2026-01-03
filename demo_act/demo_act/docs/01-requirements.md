# Requirements: Claude Code Auto v4.0

## Document Information
- **Version**: 1.0.0
- **Last Updated**: 2025-01-03
- **Status**: Final
- **Author**: Team Mode Documentation Team

---

## Table of Contents
1. [Functional Requirements](#functional-requirements)
2. [Non-Functional Requirements](#non-functional-requirements)
3. [Data Requirements](#data-requirements)
4. [Interface Requirements](#interface-requirements)
5. [Compliance and Security](#compliance-and-security)
6. [Constraints and Assumptions](#constraints-and-assumptions)

---

## Functional Requirements

### FR-001: Dual-Mode Operation
**Priority**: P0 (Critical)
**Description**: The system MUST support two distinct operational modes.

#### Requirements
1. **FR-001.1**: Original Mode (Single Agent)
   - Triggered when `task.initial_prompt` is NOT set in config.yaml
   - Simple Planner → Executor loop with ReAct reasoning
   - Suitable for single-step or simple iterative tasks

2. **FR-001.2**: Team Mode (Multi-Agent Collaboration)
   - Triggered when `task.initial_prompt` IS set in config.yaml
   - Leader Agent orchestrates multiple specialized roles
   - Intelligent mission decomposition, dependency resolution, quality validation
   - Suitable for complex multi-step projects requiring different expertise

**Acceptance Criteria**:
- System automatically detects mode based on `initial_prompt` presence
- Mode detection happens at startup before agent creation
- Clear logging of selected mode to console and event log

---

### FR-002: Mission Decomposition
**Priority**: P0 (Critical)
**Description**: Leader Agent MUST decompose high-level user goals into executable SubMissions.

#### Requirements
1. **FR-002.1**: LLM-Driven Decomposition
   - Use Claude Sonnet 4.5 to analyze goal and break into sub-missions
   - Each SubMission includes: goal, success_criteria, dependencies, priority
   - Dependencies reference other SubMissions by name

2. **FR-002.2**: SubMission Structure
   - `mission_id`: Unique identifier (UUID)
   - `goal`: Clear, actionable mission statement
   - `success_criteria`: List of measurable outcomes
   - `dependencies`: List of `mission_id` dependencies
   - `priority`: HIGH, MEDIUM, or LOW

**Acceptance Criteria**:
- Decomposition completes within 3 minutes (configurable timeout: `claude.timeouts.decomposer`)
- Result includes at least 1 SubMission
- Each SubMission has valid structure (all required fields present)
- Circular dependencies detected and reported with error

---

### FR-003: Team Assembly
**Priority**: P0 (Critical)
**Description**: System MUST dynamically assemble teams for each SubMission.

#### Requirements
1. **FR-003.1**: Role Selection
   - Use LLM to analyze SubMission requirements
   - Select appropriate roles from `roles/*.yaml` definitions
   - Support multiple roles per SubMission

2. **FR-003.2**: Role Loading
   - Load role definitions from YAML files
   - Validate role structure (mission, output_standard, tools, dependencies)
   - Register role tools with ToolRegistry

**Acceptance Criteria**:
- At least 1 role selected per SubMission
- Selected roles have required tools for mission
- Invalid role definitions cause startup failure with clear error message

---

### FR-004: Dependency Resolution
**Priority**: P0 (Critical)
**Description**: System MUST resolve role dependencies and determine execution order.

#### Requirements
1. **FR-004.1**: Topological Sorting
   - Implement Kahn's algorithm for dependency resolution
   - Produce layered execution order (Layer 1: no deps, Layer 2: depends on Layer 1, etc.)
   - Detect circular dependencies

2. **FR-004.2**: Dependency Validation
   - Validate all dependency references exist
   - Reject circular dependency graphs with clear error message
   - Log resolved execution order

**Acceptance Criteria**:
- Kahn's algorithm completes in O(V+E) time where V=roles, E=dependencies
- Circular dependencies detected before execution starts
- Execution order is deterministic (same graph → same order)
- Dependency graph with no circular deps always produces valid order

---

### FR-005: Role Execution
**Priority**: P0 (Critical)
**Description**: Each role MUST execute its mission with validation and retry logic.

#### Requirements
1. **FR-005.1**: Optional Planner Integration
   - If `use_planner: true` in role definition, Planner decomposes mission into steps
   - Planner exports decision trace to `logs/trace/{session_id}_{role}_step1.md`
   - Planner timeout: 600 seconds (first call: 2x = 1200 seconds)

2. **FR-005.2**: ReAct Loop Execution
   - Executor runs ReAct loop (max 30 iterations)
   - Each iteration: Thought → Action → Observation
   - Actions call tools registered in ToolRegistry
   - Executor timeout: 300 seconds per ReAct step
   - Export trace to `logs/trace/{session_id}_{role}_step2.md`

3. **FR-005.3**: Dual-Layer Validation
   - **Format Validation** (always on):
     - File existence checks
     - Content pattern matching
     - Minimum length validation
     - Placeholder detection (TODO, PLACEHOLDER, TBD)
   - **Semantic Quality Validation** (optional per role):
     - If `enable_quality_check: true`, use LLM (Haiku) to score output
     - Score 0-100 against success criteria
     - Return QualityScore with overall_score, criteria_scores, issues, suggestions

4. **FR-005.4**: Retry Logic
   - On validation failure, retry same role up to `max_iterations`
   - Retry with same context but different random seed
   - Log retry attempts to event log

**Acceptance Criteria**:
- ReAct loop completes within max_iterations (default: 10 per role)
- Format validation catches all missing files and placeholders
- Semantic validation (if enabled) provides scores and suggestions
- Retries attempt up to max_iterations before failing
- All traces exported to markdown files

---

### FR-006: Leader Intervention
**Priority**: P0 (Critical)
**Description**: Leader Agent MUST intelligently intervene based on quality, cost, and budget.

#### Requirements
1. **FR-006.1**: Intervention Strategies
   - **CONTINUE**: Quality score ≥ threshold, within budget → Proceed to next role
   - **RETRY**: Transient failure (e.g., API timeout) → Retry same role (max `leader.max_mission_retries`)
   - **ENHANCE**: Requirements unclear → Use LLM to refine requirements and retry (NOT IMPLEMENTED)
   - **ESCALATE**: Capability gap detected → Add helper role (NOT IMPLEMENTED)
   - **TERMINATE**: Unrecoverable failure → Stop execution and generate recovery guide

2. **FR-006.2**: Decision Logging
   - Log each intervention decision to `logs/interventions/{session_id}_interventions.md`
   - Include: role, quality_score, cost, decision, reasoning

**Acceptance Criteria**:
- Leader evaluates every role completion
- Intervention decision respects `quality_threshold` (default: 70.0)
- CONTINUE allows progression to next role
- RETRY re-executes same role with same context
- TERMINATE stops execution with clear failure report
- All interventions logged to markdown

---

### FR-007: Context Passing
**Priority**: P1 (High)
**Description**: System MUST pass outputs between roles efficiently.

#### Requirements
1. **FR-007.1**: Smart Content Handling
   - **< 500 characters**: Embed full content in downstream role context
   - **≥ 500 characters**: Generate summary + save full content to trace file
   - Summary format: first 300 chars + "..." + last 100 chars
   - Trace files saved to `logs/trace/context_{role}_{filename}.md`

2. **FR-007.2**: Context Structure
   - Include role name, output files, and content/summary
   - Add reference to trace file for full content
   - Clear separation between different roles' outputs

**Acceptance Criteria**:
- Context length < 500 chars uses full content
- Context length ≥ 500 chars uses summary + trace file
- Trace files contain complete unmodified content
- Downstream roles receive all required information

---

### FR-008: Cost Tracking
**Priority**: P1 (High)
**Description**: System MUST track costs at multiple levels with budget control.

#### Requirements
1. **FR-008.1**: Hierarchical Budgets
   - **Session-level**: Total budget (`cost_control.max_budget_usd`)
   - **Mission-level**: Allocated per mission (30%, 20%, 10% by priority)
   - **Role-level**: Sub-budget per role execution
   - **Action-level**: Individual tool calls tracked

2. **FR-008.2**: Budget Checks
   - **Warning**: 80% of budget consumed → COST_WARNING event
   - **Critical**: 95% → Circuit breaker opens
   - **Exceeded**: 100% → Auto-stop (if `auto_stop_on_exceed=true`)

3. **FR-008.3**: Cost Reporting
   - Log costs to event log (COST_UPDATE event)
   - Export cost summary to `logs/cost_report.json`
   - Include: total_tokens, total_cost_usd, breakdown by model

**Acceptance Criteria**:
- Costs tracked at all 4 levels (session, mission, role, action)
- Warnings issued at 80% and 95% of budget
- Auto-stop at 100% if enabled
- Cost report contains accurate breakdown

---

### FR-009: Event Logging
**Priority**: P1 (High)
**Description**: System MUST log all session events for observability.

#### Requirements
1. **FR-009.1**: Event Types
   - SESSION_START, SESSION_END
   - PLANNER_START, PLANNER_COMPLETE
   - EXECUTOR_START, EXECUTOR_COMPLETE
   - VALIDATION_START, VALIDATION_COMPLETE, VALIDATION_FAILED
   - COST_UPDATE, COST_WARNING, BUDGET_EXCEEDED
   - LEADER_INTERVENTION
   - ROLE_START, ROLE_COMPLETE, ROLE_FAILED
   - ERROR, FATAL_ERROR

2. **FR-009.2**: Event Structure
   - `event_id`: Unique identifier
   - `timestamp`: ISO 8601 format
   - `event_type`: One of the types above
   - `session_id`: Current session ID
   - `data`: Event-specific payload

3. **FR-009.3**: Storage
   - Events stored in `logs/events/{session_id}_events.jsonl`
   - One event per line (JSON Lines format)
   - Appended atomically to prevent corruption

**Acceptance Criteria**:
- All operations logged with appropriate event types
- Event IDs are unique within session
- Timestamps in ISO 8601 format
- JSONL format valid (one JSON object per line)

---

### FR-010: State Management
**Priority**: P1 (High)
**Description**: System MUST maintain persistent workflow state.

#### Requirements
1. **FR-010.1**: State File
   - State stored in `demo_act/workflow_state.json`
   - Backed up to `demo_mirror/workflow_state.json`

2. **FR-010.2**: State Structure
   - `session_id`: Current session ID
   - `workflow_status`: PENDING, IN_PROGRESS, COMPLETED, FAILED
   - `current_mode`: "original" or "team"
   - `current_role`: Currently executing role (if any)
   - `completed_roles`: List of completed role names
   - `failed_roles`: List of failed role names
   - `total_cost_usd`: Total cost for session
   - `last_updated`: ISO 8601 timestamp

3. **FR-010.3**: State Updates
   - State updated after each major operation (role completion, intervention, etc.)
   - Atomic write to prevent corruption
   - Backup copy updated after successful write

**Acceptance Criteria**:
- State file exists after session starts
- State updated after each role completion
- Backup copy synchronized
- State can be loaded after crash/resume

---

### FR-011: Tool Registry
**Priority**: P1 (High)
**Description**: System MUST provide centralized tool registration and discovery.

#### Requirements
1. **FR-011.1**: Tool Registration
   - Tools registered at startup with metadata
   - Metadata includes: name, description, input_schema, output_schema

2. **FR-011.2**: Tool Discovery
   - Agents query ToolRegistry for available tools
   - Filter by role permissions (if configured)
   - Get tool schemas for validation

3. **FR-011.3**: Built-in Tools
   - **File Tools**: write_file, read_file, list_directory
   - **Shell Tools**: execute_command
   - **Research Tools**: web_search, get_research_stats

**Acceptance Criteria**:
- All tools registered before agent execution starts
- Tool discovery returns correct schemas
- Tool calls validated against schemas before execution
- Tool errors logged and propagated to agent

---

### FR-012: Markdown Traces
**Priority**: P2 (Medium)
**Description**: System MUST export human-readable decision traces.

#### Requirements
1. **FR-012.1**: Planner Traces
   - Export to `logs/trace/{session_id}_{role}_step1.md`
   - Include: goal, context, action_steps, reasoning

2. **FR-012.2**: Executor Traces
   - Export to `logs/trace/{session_id}_{role}_step2.md`
   - Include: ReAct loop steps (thought, action, observation)

3. **FR-012.3**: Intervention Traces
   - Export to `logs/interventions/{session_id}_interventions.md`
   - Include: role, quality_score, decision, reasoning

4. **FR-012.4**: Context Traces
   - Export to `logs/trace/context_{role}_{filename}.md`
   - Include: full content when summary passed to downstream roles

**Acceptance Criteria**:
- All traces exported in markdown format
- Traces contain all required sections
- Traces readable by non-technical users
- Trace filenames follow naming convention

---

### FR-013: Role Definitions
**Priority**: P2 (Medium)
**Description**: System MUST support extensible role definitions through YAML files.

#### Requirements
1. **FR-013.1**: Role Structure
   - `name`: Unique role name
   - `description`: Human-readable description
   - `category`: research|development|writing|...
   - `mission`: goal, success_criteria, max_iterations
   - `output_standard`: required_files, validation_rules
   - `recommended_persona`: researcher|coder|writer|...
   - `tools`: List of tool names
   - `dependencies`: List of role names
   - `use_planner`: Boolean (optional)
   - `enable_quality_check`: Boolean (optional)
   - `adaptive`: Boolean (optional)

2. **FR-013.2**: Validation Rules
   - `file_exists`: Check file exists
   - `content_check`: Must contain patterns
   - `min_length`: Minimum character count
   - `no_placeholders`: Forbidden patterns

3. **FR-013.3**: Pre-built Roles
   - Market-Researcher
   - AI-Native-Writer
   - AI-Native-Developer
   - Architect
   - SEO-Specialist
   - Creative-Explorer
   - Role-Definition-Expert
   - Multidimensional-Observer

**Acceptance Criteria**:
- Role YAML files validate against schema
- New roles added without code changes
- Role dependencies resolved correctly
- Validation rules enforced correctly

---

## Non-Functional Requirements

### NFR-001: Performance
**Priority**: P1 (High)
**Description**: System MUST meet performance targets.

#### Requirements
1. **NFR-001.1**: Response Time
   - Mission decomposition: <3 minutes
   - Role execution: <30 minutes (including retries)
   - Tool calls: <30 seconds (excluding API latency)

2. **NFR-001.2**: Throughput
   - Support concurrent tool calls (async I/O)
   - Non-blocking event logging

3. **NFR-001.3**: Resource Usage
   - Memory: <2 GB during normal operation
   - CPU: <50% on modern multi-core processor
   - Disk: <100 MB for logs (per session)

**Acceptance Criteria**:
- Performance targets met under normal load
- No memory leaks during long-running sessions
- Async operations don't block main thread

---

### NFR-002: Reliability
**Priority**: P0 (Critical)
**Description**: System MUST be reliable and fault-tolerant.

#### Requirements
1. **NFR-002.1**: Error Handling
   - All errors caught and logged
   - Graceful degradation on API failures
   - Retry with exponential backoff for transient errors

2. **NFR-002.2**: Data Integrity
   - Atomic state file writes
   - Backup copies of critical files
   - JSON validation before parsing

3. **NFR-002.3**: Recovery
   - Emergency stop file (`.emergency_stop`) for manual termination
   - State recovery from crash using `workflow_state.json`
   - Mirror directory for disaster recovery

**Acceptance Criteria**:
- No unhandled exceptions crash the system
- State files never corrupted (even if crash occurs)
- Emergency stop file causes graceful shutdown

---

### NFR-003: Scalability
**Priority**: P2 (Medium)
**Description**: System MUST scale to handle complex workflows.

#### Requirements
1. **NFR-003.1**: Role Scalability
   - Support 20+ roles in single workflow
   - Support 5+ layers of dependencies

2. **NFR-003.2**: Session Scalability
   - Support long-running sessions (8+ hours)
   - Support 1000+ events per session

**Acceptance Criteria**:
- System handles 20 roles without performance degradation
- Event log grows linearly with events (not quadratic)

---

### NFR-004: Maintainability
**Priority**: P1 (High)
**Description**: System MUST be maintainable and extensible.

#### Requirements
1. **NFR-004.1**: Code Quality
   - Follow PEP 8 style guide
   - Type hints for all public functions
   - Docstrings for all modules and classes

2. **NFR-004.2**: Modularity
   - Clear separation of concerns
   - Pluggable tool system
   - YAML-based configuration

3. **NFR-004.3**: Documentation
   - Comprehensive inline comments
   - Architecture documentation
   - User guides for common tasks

**Acceptance Criteria**:
- New contributors can understand code within 1 day
- New tools added without modifying core code
- New roles added via YAML only

---

### NFR-005: Usability
**Priority**: P1 (High)
**Description**: System MUST be easy to use and configure.

#### Requirements
1. **NFR-005.1**: Configuration
   - Single config.yaml file for all settings
   - Sensible defaults for all values
   - Clear error messages for invalid config

2. **NFR-005.2**: Logging
   - Structured logging with severity levels
   - Human-readable log messages
   - Console and file output

3. **NFR-005.3**: Debugging
   - Markdown traces for all decisions
   - Event log for replay
   - Clear error messages with context

**Acceptance Criteria**:
- New users can run system in <5 minutes
- Errors indicate root cause and suggested fix
- Traces contain enough info to debug issues

---

### NFR-006: Security
**Priority**: P1 (High)
**Description**: System MUST be secure and protect sensitive data.

#### Requirements
1. **NFR-006.1**: API Key Management
   - API keys loaded from environment variables
   - Never logged or traced
   - Support for .env file

2. **NFR-006.2**: Command Execution
   - Shell tools execute with user permissions
   - No privilege escalation
   - Command injection prevention

3. **NFR-006.3**: File Access
   - File operations restricted to working directory
   - No access to system files
   - Path traversal prevention

**Acceptance Criteria**:
- API keys never appear in logs or traces
- Shell commands executed with least privilege
- File operations cannot escape working directory

---

## Data Requirements

### DR-001: Configuration Data
**Description**: System configuration stored in YAML format.

#### Schema
- See `config.yaml` structure in project documentation
- Validated using Pydantic models

---

### DR-002: Role Definition Data
**Description**: Role definitions stored in YAML format.

#### Schema
- See role structure in FR-013
- Validated against JSON schema in `schemas/` directory

---

### DR-003: Event Log Data
**Description**: Session events stored in JSON Lines format.

#### Schema
```json
{
  "event_id": "uuid",
  "timestamp": "2025-01-03T12:00:00Z",
  "event_type": "SESSION_START",
  "session_id": "uuid",
  "data": {}
}
```

---

### DR-004: State Data
**Description**: Workflow state stored in JSON format.

#### Schema
```json
{
  "session_id": "uuid",
  "workflow_status": "IN_PROGRESS",
  "current_mode": "team",
  "current_role": "Market-Researcher",
  "completed_roles": [],
  "failed_roles": [],
  "total_cost_usd": 0.0,
  "last_updated": "2025-01-03T12:00:00Z"
}
```

---

### DR-005: Cost Report Data
**Description**: Cost breakdown stored in JSON format.

#### Schema
```json
{
  "session_id": "uuid",
  "total_tokens": 10000,
  "total_cost_usd": 0.15,
  "breakdown": {
    "claude-sonnet-4-5": {
      "tokens": 8000,
      "cost_usd": 0.12
    },
    "claude-3-5-haiku": {
      "tokens": 2000,
      "cost_usd": 0.03
    }
  }
}
```

---

## Interface Requirements

### IR-001: Command-Line Interface
**Description**: System invoked via command line with optional arguments.

#### Interface
```bash
python -m src.main [--config CONFIG_PATH]
```

**Arguments**:
- `--config`: Path to config.yaml (default: ../config.yaml)

---

### IR-002: Python API
**Description**: System can be imported and used as a library.

#### Interface
```python
from src.main import run_agent

result = run_agent(config_path="config.yaml")
```

---

## Compliance and Security

### CS-001: API Compliance
**Description**: System MUST comply with Anthropic and Tavily API terms of service.

- Rate limits respected
- Usage within free tier or paid quota
- No prohibited use cases

---

### CS-002: Data Privacy
**Description**: System MUST protect user privacy.

- No personal data collected without consent
- API keys stored locally only
- No telemetry or analytics (unless opted-in)

---

### CS-003: Open Source Compliance
**Description**: System MUST comply with open source license (MIT License).

- License included in all distributions
- Attribution preserved in derivative works
- No warranty provided

---

## Constraints and Assumptions

### Constraints
1. Single-machine execution (no distributed deployment)
2. Python 3.12+ required
3. Claude and Tavily API access required
4. File system access required
5. No external database (JSON storage only)

### Assumptions
1. APIs remain stable and compatible
2. Network access available for API calls
3. Configuration file is valid
4. Role definitions are valid
5. Users have technical proficiency

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-03 | Initial requirements documentation | Team Mode Documentation Team |

---

*This document is part of the comprehensive documentation suite for Claude Code Auto v4.0. For the complete documentation package, refer to the related documents listed in the Project Context.*
