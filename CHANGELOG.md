# Changelog

All notable changes to claude-code-auto will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2025-01-22

### Added

#### Core Architecture Improvements
- **Dependency Topological Sorting**: Implemented Kahn's algorithm for deterministic role execution order
  - Circular dependency detection with detailed error messages
  - Dependency level calculation for parallel execution opportunities
  - 100% test coverage (19 unit tests)
  - Files: `src/core/team/dependency_resolver.py`, `tests/test_dependency_resolver.py`

- **Markdown Trace Logging**: Complete decision process auditability
  - Planner trace export (`planner.export_plan_to_markdown()`)
  - ReAct execution trace export (`executor.export_react_trace()`)
  - Structured markdown format in `logs/trace/{session_id}_{role}_step{n}.md`
  - Files: `src/core/agents/planner.py`, `src/core/agents/executor.py`

- **Full Context Passing**: Intelligent context preservation for role collaboration
  - Short content (<500 chars): Full inclusion
  - Long content: Intelligent summary + trace file reference
  - Prevents information loss in multi-role workflows
  - Files: `src/core/team/role_executor.py`

- **Planner Integration**: Role executor now supports planner-driven task decomposition
  - Optional planner usage per role (`use_planner=True`)
  - Automatic trace export for planning decisions
  - Backward compatible (default: direct execution)
  - Files: `src/core/team/role_executor.py`

#### Tool Enhancements
- **Research Tools**: ResearcherAgent now available as callable tools
  - `quick_research()`: Single-round research with caching
  - `deep_research()`: Multi-round iterative research
  - `get_research_stats()`: Usage statistics
  - Global singleton pattern for efficiency
  - Files: `src/core/tools/research_tools.py`

#### Cost Management
- **Cost Budget Control**: Real-time budget tracking and enforcement
  - Configurable budget limits and warning thresholds
  - Auto-stop on budget exceeded
  - Detailed budget status reporting
  - Configuration: `cost_control` section in `config.yaml`
  - Files: `src/config.py`, `src/core/events.py`, `src/main.py`

#### Quality Assurance
- **Semantic Quality Validation**: LLM-driven output quality assessment
  - Numerical scoring (0-100) against success criteria
  - Issue identification and improvement suggestions
  - Configurable quality thresholds per role
  - Uses Haiku model for cost efficiency
  - Files: `src/core/team/quality_validator.py`

- **Adaptive Validation Rules**: Dynamic validation thresholds based on task complexity
  - Automatic complexity estimation (simple/medium/complex/expert)
  - Complexity multipliers: simple (0.7x), medium (1.0x), complex (1.5x), expert (2.0x)
  - Keyword + length + criteria count heuristics
  - Backward compatible with static rules
  - Files: `src/core/team/role_registry.py`, `src/core/team/role_executor.py`

### Changed
- **RoleExecutor**: Now async-compatible for quality validation
  - `_validate_outputs()` is now async
  - Split into `_validate_format()` and `_validate_quality()`
  - Enhanced error messages with complexity information

- **Role Definition**: Extended with optional v3.1 fields
  - `enable_quality_check`: Enable semantic quality validation (default: False)
  - `quality_threshold`: Minimum quality score 0-100 (default: 70.0)
  - `adaptive`: Enable adaptive validation rules (default: False)
  - `base_chars`: Base character count for adaptive validation

- **CostTracker**: Enhanced with budget control methods
  - `check_budget()`: Returns detailed budget status
  - `is_budget_exceeded()`: Simple boolean check
  - `get_budget_status_message()`: Human-readable status
  - Constructor accepts `max_budget_usd` and `warning_threshold`

### Fixed
- Context truncation in role collaboration (Day 4)
- Validation method now properly handles async quality checks

### Performance
- Research tool singleton pattern reduces initialization overhead
- Quality validation uses Haiku model for 10x cost reduction
- Trace logging uses file I/O (zero API calls)
- Adaptive validation eliminates over-validation for simple tasks

### Documentation
- Added `docs/v3.1_UPGRADE_SUMMARY.md` with comprehensive feature overview
- Added migration guide from v3.0 to v3.1
- Added performance impact analysis
- Added recommended testing procedures

### Testing
- 19 unit tests for dependency resolver (100% passing)
- Manual integration tests for all major features
- Backward compatibility verified

### Breaking Changes
None. All new features are optional and backward compatible.

---

## [3.0.0] - 2025-01-15

### Added
- ReAct-based autonomous agent architecture
- Team mode with role registry and orchestrator
- Persona system for dynamic role-switching
- Event logging and cost tracking
- Research agent with caching
- State management and workflow persistence

### Changed
- Complete architecture refactor from v2.x
- Configuration now uses Pydantic models
- Logging system redesigned

---

## [2.x] - Earlier

See git history for v2.x changes.
