# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **AI-era team efficiency amplification framework** that demonstrates how to systematically放大 team efficiency through the entire product development lifecycle. This is a **documentation-based framework** (not executable code) organized into four phases, with Chinese as the primary language.

## Architecture & Structure

### Core Framework Organization

```
docs/
├── README.md                           # Main framework overview - START HERE
├── ai-efficiency-framework.md          # Complete framework methodology
├── practical-evaluation-report.md      # Implementation evaluation report
├── 01-creative-concept-phase/          # Phase 1: Dynamic AI role generation
├── 02-specification-phase/            # Phase 2: Multi-AI specification generation
├── 03-development-phase/              # Phase 3: AI collaborative development
└── 04-future-iteration-phase/         # Phase 4: Continuous evolution

legacy-project-analysis/                # Legacy project enhancement methodology
└── java-project-analyzer/             # Java project analysis tools and docs
```

### Four-Phase Framework

1. **Creative Concept Phase** - Dynamic AI role generation through conversational exploration
2. **Specification Phase** - 5 specialized AI roles generate complete specifications in 2 hours
3. **Development Phase** - 6 AI roles implement code using SPARC methodology
4. **Iteration Phase** - Self-evolving AI collaborative ecosystem with dual-loop feedback

### Key Concepts

- **AI-Augmented Human Intelligence**: AI amplifies rather than replaces human capabilities
- **Multi-AI Collaboration**: Each phase employs multiple specialized AI roles working in parallel
- **SPARC Methodology**: Specification → Pseudocode → Architecture → Refinement → Completion
- **Dynamic Role Generation**: AI roles are generated based on project needs, not pre-defined

## Working with This Framework

### Key Principles

- **AI-Augmented Human Intelligence**: AI amplifies rather than replaces human capabilities
- **Multi-AI Collaboration**: Each phase employs multiple specialized AI roles working in parallel
- **Dynamic Role Generation**: AI roles are generated based on project needs, not pre-defined
- **SPARC Methodology**: Specification → Pseudocode → Architecture → Refinement → Completion

### Document Language
- All framework documentation is in **Chinese**
- Case studies and examples are practical implementation-focused
- Emphasis on practical application over theoretical concepts

### File Organization Rules (CRITICAL)
- **NEVER save files to root directory** - always use appropriate subdirectories
- Documentation files go in `/docs` or phase-specific directories
- Use `/src`, `/tests`, `/config` for any code implementation (when applicable)
- Maintain the existing four-phase structure

## Common Development Tasks

Since this is a documentation framework:
- **No build system** - no package.json, Makefile, or build scripts
- **No testing framework** - documentation quality through manual review
- **No linting tools** - no ESLint, Prettier, or similar tools
- **No CI/CD** - documentation updates are manual

### When Adding Content
1. **Follow phase structure** - place content in appropriate phase directory
2. **Use Chinese** - maintain language consistency with existing docs
3. **Include practical examples** - focus on real-world application
4. **Add case studies** - demonstrate framework effectiveness

## Framework Integration

### SPARC Commands (when applicable)
```bash
# List available modes
npx claude-flow sparc modes

# Execute specific mode
npx claude-flow sparc run <mode> "<task>"

# Run TDD workflow
npx claude-flow sparc tdd "<feature>"

# Parallel execution
npx claude-flow sparc batch <modes> "<task>"
```

### AI Role Templates
Each phase includes ready-to-use AI role prompt templates:
- **Phase 1**: Dynamic role generation through dialogue
- **Phase 2**: Product, UI, Data, System, and API Design AIs
- **Phase 3**: Design Evaluation, Architecture, Development, and Testing AIs
- **Phase 4**: Evolution and Optimization AIs

## Project Types Supported (Phase 3)

When implementing code based on Phase 2 specifications:
- **Admin dashboards**: React + Ant Design Pro
- **C-end applications**: Next.js + Tailwind CSS
- **Mobile applications**: UniApp + Vue3

## Legacy Project Analysis

The `/legacy-project-analysis` directory provides methodologies for:
- Interface scanning and documentation generation
- Implementation relationship mapping
- Static analysis and call chain tracing
- Knowledge base construction and API-ification
- Change impact analysis

## Important Notes

- This is a **knowledge repository**, not an executable project
- Focus is on **process optimization** and **AI workflow design**
- All content is in **Chinese** - maintain language consistency
- Framework emphasizes **practical implementation** over theory
- Each phase is standalone but part of complete lifecycle

## Document Maintenance

When updating framework documentation:
1. Preserve the four-phase structure
2. Update phase-specific READMEs
3. Maintain consistency with core principles
4. Add new case studies to appropriate phases
5. Keep practical focus

## Quick Start

1. **Read `/docs/README.md`** for complete framework overview
2. **Select phase** based on current needs
3. **Use provided templates** for AI role prompts
4. **Reference case studies** for implementation examples
5. **Follow methodology** for systematic AI integration

## Configuration Rules

- **Concurrent execution**: Use batch operations for efficiency
- **No git usage** unless explicitly requested
- **Modular design**: Keep documents focused and under 500 lines when possible
- **Test-driven approach**: Validate methodologies through practical application