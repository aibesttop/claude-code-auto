# META-PROMPT: AI-Native Development Documentation Generation Standard

## Purpose
This META-PROMPT defines the standard structure and quality requirements for generating AI-native development documentation.

## Core Philosophy

### AI-Native Development Principles
1. **AI-First Architecture**: Systems designed from the ground up to leverage AI capabilities, not retrofitted
2. **Deterministic Outputs**: Predictable, testable results with clear validation criteria
3. **Human-AI Collaboration**: Clear boundaries between automated and human decision-making
4. **Iterative Improvement**: Built-in feedback loops for continuous enhancement

### Documentation Standards
- **No Placeholders**: Every section must be complete and actionable
- **Evidence-Based**: All claims backed by market research, user data, or technical constraints
- **Cross-Referenced**: Explicit links between related concepts across documents
- **Implementation-Ready**: Sufficient detail for developers to act without clarification

## Document Structure

### Required Documents (8 Core Files)

#### 1. Project Context (00-project-context.md)
**Purpose**: Define the problem space and success criteria

**Required Sections**:
- ## Problem Statement
  - Current system pain points (with sources)
  - Why existing solutions fail
  - Urgency/timing considerations

- ## Target Users
  - Primary user segments (demographics, psychographics)
  - User personas with detailed profiles
  - User journey mapping
  - Accessibility requirements

- ## Success Metrics
  - Key Performance Indicators (KPIs)
  - Measurable outcomes (quantitative targets)
  - User experience metrics
  - Technical performance benchmarks

**Validation Criteria**:
- Must reference market-research.md
- Minimum 1,500 characters
- No placeholders or TODOs
- At least 3 measurable success metrics
- Clear problem statement with supporting evidence

#### 2. Requirements (01-requirements.md)
**Purpose**: Detailed functional and non-functional requirements

**Required Sections**:
- ## Functional Requirements
  - User-facing features
  - System capabilities
  - Input/Output specifications
  - Integration requirements

- ## Non-Functional Requirements
  - Performance (response time, throughput)
  - Scalability (user load, data volume)
  - Security & Privacy (data protection, authentication)
  - Reliability (uptime, error handling)
  - Maintainability (code quality, documentation)
  - Accessibility (WCAG compliance, age-friendly design)

- ## Technical Constraints
  - Technology stack limitations
  - Budget/resource constraints
  - Timeline considerations
  - Regulatory/compliance requirements

**Validation Criteria**:
- Minimum 2,000 characters
- Must contain both functional and non-functional sections
- Requirements must be testable and measurable
- No placeholders or vague statements

#### 3. Architecture (02-architecture.md)
**Purpose**: System design and component architecture

**Required Sections**:
- ## System Overview
  - High-level architecture diagram
  - Technology stack justification
  - Design principles
  - Integration patterns

- ## Component Design
  - Frontend/UI components
  - Backend services
  - Data models and schemas
  - API specifications
  - External integrations

- ## Data Flow
  - User request lifecycle
  - Data processing pipeline
  - State management strategy
  - Caching and optimization

- ## Security Architecture
  - Authentication/authorization
  - Data encryption
  - Privacy protection measures
  - Audit logging

**Validation Criteria**:
- Minimum 2,500 characters
- Must include system overview and component design
- Clear component boundaries and responsibilities
- Security considerations addressed

#### 4. Implementation Guide (03-implementation-guide.md)
**Purpose**: Step-by-step development roadmap

**Required Sections**:
- ## Development Phases
  - Phase 1: MVP feature set
  - Phase 2: Core enhancements
  - Phase 3: Advanced features
  - Timeline and milestones

- ## Technical Setup
  - Development environment configuration
  - Dependency installation
  - Database setup
  - Local development server

- ## Coding Standards
  - Code organization patterns
  - Naming conventions
  - Error handling patterns
  - Testing requirements

- ## Integration Guide
  - Third-party service integration
  - API development standards
  - Data migration procedures
  - Deployment process

**Validation Criteria**:
- Actionable step-by-step instructions
- Clear phase boundaries and deliverables
- Specific commands and code examples
- No placeholders or "coming soon" sections

#### 5. Quality Gates (04-quality-gates.md)
**Purpose**: Testing, validation, and quality assurance standards

**Required Sections**:
- ## Testing Strategy
  - Unit testing requirements
  - Integration testing approach
  - End-to-end testing scenarios
  - Performance testing benchmarks

- ## Validation Criteria
  - Definition of Done for each feature
  - Acceptance testing checklist
  - User acceptance testing (UAT) process
  - Accessibility testing (WCAG 2.1 AA)

- ## Code Quality Standards
  - Linting and formatting rules
  - Code review checklist
  - Test coverage requirements (>80%)
  - Documentation standards

- ## Continuous Integration
  - Automated testing pipeline
  - Deployment gates
  - Rollback procedures
  - Monitoring and alerting

**Validation Criteria**:
- Specific test coverage targets
- Clear acceptance criteria
- Automated quality checks
- Manual testing procedures

#### 6. AI Prompt Template (05-ai-prompt-template.md)
**Purpose**: AI agent interaction patterns and prompt engineering

**Required Sections**:
- ## AI Agent Architecture
  - Agent roles and responsibilities
  - Agent communication protocols
  - State management for AI workflows
  - Error handling and fallback strategies

- ## Prompt Engineering Standards
  - System prompt templates for each agent type
  - Context injection patterns
  - Tool calling conventions
  - Output parsing and validation

- ## Agent Orchestration
  - Multi-agent workflow design
  - Agent handoff protocols
  - Shared memory and context management
  - Conflict resolution strategies

- ## AI-Powered Features
  - Natural language interfaces
  - Intelligent automation
  - Adaptive UI/UX
  - Predictive features

**Validation Criteria**:
- Concrete prompt templates with examples
- Clear agent interaction patterns
- Error recovery strategies
- Performance optimization for AI calls

#### 7. Testing Strategy (06-testing-strategy.md)
**Purpose**: Comprehensive testing approach for AI-native systems

**Required Sections**:
- ## Testing Pyramid
  - Unit tests (80% of tests)
  - Integration tests (15% of tests)
  - E2E tests (5% of tests)

- ## AI-Specific Testing
  - Prompt injection testing
  - Hallucination detection
  - Bias testing
  - Adversarial testing

- ## User Testing
  - Usability testing with elderly users
  - Accessibility testing (screen readers, magnification)
  - A/B testing for UX variations
  - Beta testing program

- ## Performance Testing
  - Load testing scenarios
  - Stress testing thresholds
  - AI response time benchmarks
  - Database query optimization

**Validation Criteria**:
- Test coverage metrics
- Specific test scenarios
- Testing tools and frameworks
- Continuous testing integration

#### 8. Deployment Guide (07-deployment-guide.md)
**Purpose**: Production deployment and operational procedures

**Required Sections**:
- ## Deployment Architecture
  - Cloud infrastructure setup
  - Container configuration (Docker/Kubernetes)
  - CI/CD pipeline configuration
  - Environment variables and secrets management

- ## Monitoring & Observability
  - Application monitoring (APM)
  - Error tracking and alerting
  - Performance metrics dashboards
  - User analytics integration

- ## Scaling Strategy
  - Horizontal vs vertical scaling
  - Load balancing configuration
  - Database scaling (read replicas, sharding)
  - CDN configuration for static assets

- ## Maintenance & Support
  - Backup and disaster recovery
  - Update and rollback procedures
  - Security patching schedule
  - Incident response plan

**Validation Criteria**:
- Production-ready deployment scripts
- Monitoring configuration examples
- Clear runbook for common issues
- Security best practices

## Cross-Cutting Concerns

### Accessibility (Age-Friendly Design)
All documents must address elderly user accessibility:
- **Visual**: Large text (minimum 16px), high contrast (WCAG AAA), resizable UI
- **Cognitive**: Simplified navigation, clear error messages, progressive disclosure
- **Motor**: Large touch targets (44x44px minimum), voice input alternatives
- **Hearing**: Visual alternatives to audio cues, caption support

### Evidence-Based Design
All design decisions must be backed by:
- User research data (cite market-research.md)
- Academic studies (peer-reviewed sources)
- Industry best standards (WCAG, ISO 9241-171)
- User testing feedback

### Iterative Refinement
Documentation should evolve based on:
- User feedback and testing results
- Technical constraints discovered during implementation
- Performance optimization opportunities
- Emerging AI capabilities and limitations

## Quality Validation Checklist

Before marking documentation complete, verify:

- [ ] All 8 documents exist with correct filenames
- [ ] Each document meets minimum character count
- [ ] No placeholders, TODOs, or TBD statements
- [ ] Cross-references between documents are accurate
- [ ] Market research findings are integrated throughout
- [ ] Accessibility requirements are addressed in all relevant sections
- [ ] AI capabilities are clearly defined and bounded
- [ ] Implementation details are specific and actionable
- [ ] Testing strategies are comprehensive and measurable
- [ ] Deployment procedures are production-ready

## Document Relationships

```
00-project-context.md
    ↓ defines problem and metrics
01-requirements.md
    ↓ specifies what to build
02-architecture.md
    ↓ defines how it's structured
03-implementation-guide.md
    ↓ provides step-by-step build process
04-quality-gates.md
    ↓ defines quality standards
05-ai-prompt-template.md
    ↓ defines AI interaction patterns
06-testing-strategy.md
    ↓ validates the implementation
07-deployment-guide.md
    ↓ deploys to production
```

## Revision History

- **v1.0** (2025-01-03): Initial META-PROMPT standard for AI-native development documentation
