# Optimization Plan: Enhanced Team Mode, Research & Traceability

## Goal Description
Address the observation that `PlannerAgent` is bypassed in Team Mode and `ResearcherAgent` is unused. Additionally, ensure **organic combination** of Agent/Team modes, **full traceability** of the team's thinking process, and **strict dependency enforcement**.

**Evolutionary Goal**: Move towards an **AI-Native Team Architecture** where a "Leader Agent" dynamically assembles the team and allocates resources (MCP Tools, Skills).
**Security Goal**: Introduce a **Sandbox (Outsourcing Manager)** for safe execution of dynamic/temporary agents.

## v3.1 Upgrade Scope (Current)
- Detailed v3.1 delivery plan: see [`docs/v3.1-upgrade.md`](./v3.1-upgrade.md).
- Focus: strict dependency enforcement, per-role planning with trace logs, planner plan export, and deep research as a reusable tool.
- Out of scope here: Leader/resource injection (v3.2) and Sandbox manager (v3.3).

## User Review Required
> [!IMPORTANT]
> **Phase 1 (Immediate)**: Fixes the broken workflow (Developer doing Research) using **Strict Dependencies** and **Traceability**.
> **Phase 2 (Evolution)**: Introduces the **Leader Agent** to replace the static Assembler, enabling dynamic resource injection.
> **Phase 3 (Security)**: Adds a **Sandbox** for running untrusted/dynamic agents safely.

## Proposed Changes

### Phase 1: Stability & Traceability (Immediate)

#### Core Agents
- **[MODIFY] [planner.py](file:///d:/AI-agnet/claude-code-auto/src/core/agents/planner.py)**: Add `export_plan_to_markdown()`.
- **[MODIFY] [researcher.py](file:///d:/AI-agnet/claude-code-auto/src/core/agents/researcher.py)**: Refactor `deep_research` into a standalone tool logic.

#### Core Team
- **[MODIFY] [team_assembler.py](file:///d:/AI-agnet/claude-code-auto/src/core/team/team_assembler.py)**:
    - Implement **Topological Sort** to strictly enforce dependencies (Researcher -> Architect -> Developer).
- **[MODIFY] [role_executor.py](file:///d:/AI-agnet/claude-code-auto/src/core/team/role_executor.py)**:
    - **Integrate PlannerAgent**: Each role plans its own mission.
    - **Traceability**: Log all steps to `logs/trace/{session_id}_{role}_{step}.md`.

#### Core Tools
- **[NEW] [research_tools.py](file:///d:/AI-agnet/claude-code-auto/src/core/tools/research_tools.py)**: Create `DeepResearchTool`.

### Phase 2: AI-Native Leader (Next Steps)

#### New Components
- **[NEW] [leader_agent.py](file:///d:/AI-agnet/claude-code-auto/src/core/team/leader_agent.py)**:
    - Replaces `TeamAssembler`.
    - dynamically selects Roles and **injects Tools/Skills**.
- **[NEW] [resource_registry.py](file:///d:/AI-agnet/claude-code-auto/src/core/team/resource_registry.py)**:
    - Manages available MCP Servers and Skill Prompts.

### Phase 3: The Sandbox (Security)

#### New Components
- **[NEW] [sandbox_manager.py](file:///d:/AI-agnet/claude-code-auto/src/core/security/sandbox_manager.py)**:
    - Manages isolated execution environments (e.g., Docker).
    - Acts as a proxy for "Outsourced" tasks.

## Verification Plan

### Automated Tests
- **Dependency Test**: Verify Topological Sort ensures correct order.
- **Traceability Test**: Verify markdown logs are created.
- **Deep Research Tool Smoke**: Ensure the exposed `deep_research` tool returns structured results.

### Manual Verification
- **Run Team Mode (Comics)**:
    - Verify `Market-Researcher` runs FIRST.
    - Verify `market-research.md` is high quality (using Deep Research).
    - Check `logs/trace/` to see the "Thinking" of each agent.
