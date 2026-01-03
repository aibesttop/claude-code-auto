# Project Context: Claude Code Auto v4.0

## Document Information
- **Version**: 1.0.0
- **Last Updated**: 2025-01-03
- **Status**: Final
- **Author**: Team Mode Documentation Team

---

## Executive Summary

**Claude Code Auto v4.0** is an AI-native autonomous agent system built on the Claude Agent SDK. It implements a sophisticated multi-agent architecture with intelligent orchestration, enabling both single-agent and team-based collaborative problem-solving.

### Key Highlights

- **Dual-Mode Operation**: Seamlessly switches between lightweight single-agent mode and powerful multi-agent team collaboration
- **Intelligent Orchestration**: Leader Agent with 5 intervention strategies (CONTINUE, RETRY, ENHANCE, ESCALATE, TERMINATE)
- **Dependency Management**: Topological sorting with circular dependency detection
- **Quality Assurance**: Dual-layer validation (format rules + LLM semantic quality scoring)
- **Cost Control**: Hierarchical budget tracking with circuit breakers
- **Full Observability**: Event logging, cost tracking, and markdown trace exports

---

## System Overview

### Core Philosophy

Claude Code Auto is built on the principle that **AI systems should be both autonomous and accountable**. Every decision is logged, every cost is tracked, and every output is validated.

### Architecture Type

**ReAct-based Multi-Agent System with Leader Orchestration**

- **ReAct Pattern**: Agents use iterative Reasoning + Acting loops
- **Multi-Agent**: Specialized roles collaborate on complex tasks
- **Leader Orchestration**: Central coordinator manages mission decomposition, dependency resolution, and quality control

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Core Framework** | Claude Agent SDK | Agent lifecycle and tool integration |
| **Language** | Python 3.12+ | Runtime environment |
| **Configuration** | PyYAML | YAML-based configuration |
| **Data Validation** | Pydantic | Type-safe configuration models |
| **Research** | Tavily Python SDK | Web search with caching |
| **Async I/O** | asyncio | Concurrent agent execution |
| **Logging** | Python logging + Structlog | Structured event logging |
| **State Management** | JSON files | Persistent workflow state |

---

## Project Goals

### Primary Objectives

1. **Autonomous Task Execution**: Execute complex multi-step tasks with minimal human intervention
2. **Quality Assurance**: Ensure outputs meet defined standards through dual-layer validation
3. **Cost Transparency**: Track and control API costs with hierarchical budget management
4. **Dependency Management**: Automatically resolve role dependencies and determine optimal execution order
5. **Observability**: Provide complete audit trails through markdown traces and event logs
6. **Extensibility**: Enable easy addition of new roles, tools, and capabilities

### Success Criteria

- ✅ Successfully decompose complex goals into executable sub-missions
- ✅ Detect and prevent circular dependencies
- ✅ Validate outputs with both format and semantic quality checks
- ✅ Track costs at session, mission, role, and action levels
- ✅ Generate human-readable markdown traces for all decisions
- ✅ Support dynamic role creation through YAML definitions

---

## Scope

### In Scope

#### Functionality
- **Single-Agent Mode**: Planner → Executor loop with ReAct reasoning
- **Team Mode**: Leader-orchestrated multi-agent collaboration
- **Mission Decomposition**: LLM-driven goal breakdown into SubMissions
- **Team Assembly**: Dynamic role selection based on mission requirements
- **Dependency Resolution**: Kahn's algorithm for topological sorting
- **Quality Validation**: Format rules + optional LLM semantic scoring
- **Cost Control**: Hierarchical budget tracking with warnings and auto-stop
- **Context Passing**: Smart summary generation to avoid token waste
- **Event Logging**: Structured event storage (SESSION_START, PLANNER_START, EXECUTOR_COMPLETE, etc.)
- **Markdown Traces**: Decision traces for Planner, Executor, and Leader interventions

#### Roles (Pre-built)
- Market-Researcher (market analysis and competitive intelligence)
- AI-Native-Writer (technical documentation)
- AI-Native-Developer (full-stack development)
- Architect (system architecture design)
- SEO-Specialist (SEO optimization)
- Creative-Explorer (creative ideation)
- Role-Definition-Expert (meta-role for creating new roles)
- Multidimensional-Observer (quality analysis)

#### Tools
- File tools (write_file, read_file, list_directory)
- Shell tools (execute_command)
- Research tools (web_search with Tavily)

### Out of Scope (Future Enhancements)

#### Functionality
- **Parallel Execution**: Concurrent role execution (dependency graph allows but not implemented)
- **Human-in-the-Loop**: Manual approval gates during execution
- **Distributed Execution**: Multi-machine deployment
- **Persistent Memory**: Long-term knowledge storage across sessions
- **Real-time Monitoring**: WebSocket-based live execution monitoring
- **Version Control Integration**: Git operations (commit, PR, etc.)

#### Intervention Strategies
- **ENHANCE**: Requirements refinement using LLM (designed but not implemented)
- **ESCALATE**: Dynamic helper role injection (designed but not implemented)

#### Advanced Features
- **Context Versioning**: VersionedContextManager for traceability
- **Helper Role Governance**: Dynamic helper lifecycle management
- **Output Integration**: Automated markdown report generation

---

## Target Audience

### Primary Users
1. **AI Researchers**: Experimenting with multi-agent orchestration patterns
2. **Software Engineers**: Automating development workflows
3. **Content Creators**: Generating documentation, marketing copy, etc.
4. **Business Analysts**: Market research and competitive intelligence

### Secondary Users
1. **System Integrators**: Embedding Claude Code Auto into larger systems
2. **DevOps Engineers**: Deploying and monitoring in production
3. **Technical Writers**: Understanding system architecture for documentation

---

## Key Constraints

### Technical Constraints
1. **Python 3.12+ Required**: Uses modern type hinting and asyncio features
2. **Claude API Access**: Requires valid Anthropic API key
3. **Tavily API Access**: Required for web search functionality
4. **File System Access**: Needs read/write permissions for working directory
5. **No External Database**: All state stored in JSON files (simplicity over scalability)

### Operational Constraints
1. **Max Iterations**: 50 iterations safety limit (configurable)
2. **Max Duration**: 8 hours timeout (configurable)
3. **ReAct Loop**: Max 30 steps per Executor (configurable)
4. **Budget**: Optional cost control with auto-stop at 100% (disabled by default)
5. **Retries**: Max 3 retries per role (configurable)

### Quality Constraints
1. **Format Validation**: Always enforced (file existence, content checks, length, placeholders)
2. **Semantic Validation**: Optional per role (LLM scoring against success criteria)
3. **Quality Threshold**: Default 70.0 (configurable per role)
4. **Adaptive Validation**: Optional complexity-based thresholds (simple/medium/complex/expert)

---

## Assumptions

### Technical Assumptions
1. **API Stability**: Anthropic and Tavily APIs remain stable and compatible
2. **Single Machine**: All agents run on the same machine (no distributed execution)
3. **File System**: Working directory is persistent and accessible
4. **Network**: Internet access available for web search and API calls

### Functional Assumptions
1. **Role Definitions**: YAML files are valid and properly structured
2. **Tool Availability**: Required tools are registered and accessible
3. **Configuration**: `config.yaml` is present and valid
4. **Dependencies**: Role dependency graphs are acyclic (circular deps detected but not resolvable)

### User Assumptions
1. **Technical Proficiency**: Users are comfortable with YAML configuration and Python
2. **API Keys**: Users have obtained valid API keys for Claude and Tavily
3. **Review Process**: Users will review markdown traces and intervene if needed
4. **Cost Awareness**: Users understand API costs and set appropriate budgets

---

## Risks and Mitigations

### High-Priority Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **API Outage** | High | Low | Emergency stop file, graceful degradation |
| **Cost Overrun** | Medium | Medium | Hierarchical budget control, auto-stop at 100% |
| **Infinite Loops** | High | Low | Max iterations (50), timeout (8h), ReAct limit (30) |
| **Quality Failures** | Medium | Medium | Dual-layer validation, retry logic, Leader intervention |
| **Circular Dependencies** | Medium | Low | Kahn's algorithm detection, early failure with clear error |

### Medium-Priority Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Token Waste** | Low | High | Smart context summarization (500-char threshold) |
| **State Corruption** | Medium | Low | JSON validation, backup to mirror directory |
| **Role Malfunction** | Medium | Medium | Format validation, semantic validation, retry |
| **Tool Failures** | Low | Medium | Error logging, retry with exponential backoff |

---

## Success Metrics

### Quantitative Metrics
1. **Task Completion Rate**: >90% of missions succeed without manual intervention
2. **Cost Efficiency**: <15% budget variance from estimates
3. **Quality Score**: Average semantic score ≥70.0
4. **Execution Speed**: <50% time spent on non-value-added activities (logging, tracing)
5. **Uptime**: >99% availability (excluding API outages)

### Qualitative Metrics
1. **User Satisfaction**: Positive feedback on trace readability and debuggability
2. **Extensibility**: New roles added without core code changes
3. **Observability**: All decisions traceable through markdown logs
4. **Maintainability**: Code follows Python best practices and is well-documented

---

## Related Documentation

### Internal Documentation
1. **Requirements**: `01-requirements.md` - Detailed functional and non-functional requirements
2. **Architecture**: `02-architecture.md` - System design, components, and data flows
3. **Implementation Guide**: `03-implementation-guide.md` - Development setup and workflows
4. **Quality Gates**: `04-quality-gates.md` - Validation rules and quality assurance
5. **AI Prompt Template**: `05-ai-prompt-template.md` - Prompt engineering guidelines
6. **Testing Strategy**: `06-testing-strategy.md` - Test plans and coverage
7. **Deployment Guide**: `07-deployment-guide.md` - Installation and configuration

### External Documentation
1. **CLAUDE.md** - Quick reference for Claude Code when working with this codebase
2. **Architecture Refactor v4.0**: `docs/Architecture-Refactor-v4.0.md` - Rationale for v4.0 redesign
3. **System Enhancements v4.1**: `docs/System-Enhancements-v4.1.md` - Production-grade features
4. **Leader Mode Guide**: `docs/LEADER_MODE_GUIDE.md` - Leader mode usage and configuration
5. **Changelog**: `CHANGELOG.md` - Version history and changes

---

## Glossary

| Term | Definition |
|------|------------|
| **ReAct** | Reasoning + Acting pattern for iterative agent decision-making |
| **Leader Agent** | Central orchestrator for Team Mode, manages missions and interventions |
| **SubMission** | A decomposed unit of work with dependencies, success criteria, and priority |
| **Role** | Specialized agent type (e.g., Market-Researcher, AI-Native-Developer) |
| **Planner Agent** | Decomposes tasks into structured action steps |
| **Executor Agent** | Executes tasks using ReAct loops with tool calls |
| **Quality Validator** | LLM-driven semantic quality assessment using Haiku |
| **Dependency Resolver** | Component that determines optimal role execution order |
| **Context Passing** | Smart transfer of outputs between roles (summary vs. full content) |
| **Markdown Trace** | Human-readable log of agent decisions and executions |
| **Intervention Strategy** | Leader's response to quality/budget issues (CONTINUE, RETRY, etc.) |
| **Kahn's Algorithm** | Topological sorting algorithm for dependency resolution |
| **Dual-Layer Validation** | Format rules + LLM semantic quality scoring |
| **Adaptive Validation** | Complexity-based threshold adjustment (simple/medium/complex/expert) |
| **EventStore** | Persistent storage of session events (SESSION_START, etc.) |
| **CostTracker** | Real-time token and cost tracking with hierarchical budgets |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-03 | Initial project context documentation | Team Mode Documentation Team |

---

*This document is part of the comprehensive documentation suite for Claude Code Auto v4.0. For the complete documentation package, refer to the related documents listed above.*
