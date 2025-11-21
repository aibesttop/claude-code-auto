# AI-Native-Developer Role - Usage Example

## Overview

The **AI-Native-Developer** role is designed to receive the 8-document system from **AI-Native-Writer** and implement a complete, production-ready codebase.

---

## Role Characteristics

| Attribute | Value |
|-----------|-------|
| **Name** | AI-Native-Developer |
| **Category** | Engineering |
| **Persona** | `coder` |
| **Dependencies** | AI-Native-Writer |
| **Max Iterations** | 20 |

---

## Mission

**Goal**: Implement a complete, deployable codebase following the AI-Native documentation system

### Success Criteria

1. ✅ Read and understand all 8 documentation files
2. ✅ Implement all functional requirements from `01-requirements.md`
3. ✅ Follow architecture from `02-architecture.md`
4. ✅ Adhere to coding standards from `03-implementation-guide.md`
5. ✅ Pass all quality gates from `04-quality-gates.md`
6. ✅ Achieve 80%+ test coverage
7. ✅ Create deployable Docker image
8. ✅ All tests pass successfully

---

## Required Deliverables

### 1. Source Code
- `src/main.py` - Main application entry point
- `src/requirements.txt` - Python dependencies
- Complete application logic with type hints and docstrings

### 2. Tests
- `tests/test_main.py` - Comprehensive test suite
- 80%+ code coverage
- Unit, integration, and security tests

### 3. Infrastructure
- `Dockerfile` - Multi-stage Docker build
- `.env.example` - Environment variable template
- Configuration files

### 4. Documentation
- `README.md` - Installation, usage, testing, deployment
- Inline code comments
- API documentation (if applicable)

---

## Validation Rules

### File Existence
All required files must exist:
- ✅ `src/main.py`
- ✅ `src/requirements.txt`
- ✅ `tests/test_main.py`
- ✅ `Dockerfile`
- ✅ `README.md`
- ✅ `.env.example`

### Content Requirements

**src/main.py**:
- Must contain `def main`
- Must contain `if __name__`
- Minimum 500 characters

**tests/test_main.py**:
- Must contain `def test_`
- Must contain `import pytest`
- Minimum 300 characters

**Dockerfile**:
- Must contain `FROM`
- Must contain `COPY`
- Must contain `CMD`

**README.md**:
- Must contain `## Installation`
- Must contain `## Usage`
- Must contain `## Testing`
- Must contain `## Deployment`
- Minimum 800 characters

### No Placeholders
The following patterns are forbidden:
- `[TODO]`
- `[PLACEHOLDER]`
- `[TBD]`
- `[FILL IN]`
- `[YOUR_*]`
- `REPLACE_ME`

---

## Quality Gates

Before completion, the role must pass:

1. **Tests**: All unit tests pass (`pytest tests/`)
2. **Coverage**: Code coverage ≥ 80%
3. **Linting**: No errors from `black`, `flake8`, `mypy`
4. **Security**: Security scan passes (`bandit`, `safety`)
5. **Performance**: P95 latency < 200ms
6. **Docker**: Image builds successfully
7. **Health**: Health check endpoint returns 200

---

## Usage Example

### config.yaml

```yaml
task:
  goal: "Build a complete user authentication system"
  initial_prompt: |
    I need a complete implementation of a user authentication system including:
    1. Market research on authentication best practices
    2. Complete AI-Native development documentation (8 files)
    3. Full implementation with tests and Docker deployment
```

### Expected Team Assembly

```
Team: [Market-Researcher, AI-Native-Writer, AI-Native-Developer]
```

### Execution Flow

```
1. Market-Researcher
   ↓ Outputs: market-research.md
   
2. AI-Native-Writer (reads market-research.md)
   ↓ Outputs: 8 documentation files
   - docs/00-project-context.md
   - docs/01-requirements.md
   - docs/02-architecture.md
   - docs/03-implementation-guide.md
   - docs/04-quality-gates.md
   - docs/05-ai-prompt-template.md
   - docs/06-testing-strategy.md
   - docs/07-deployment-guide.md
   
3. AI-Native-Developer (reads all 8 docs)
   ↓ Outputs: Complete codebase
   - src/main.py
   - src/requirements.txt
   - tests/test_main.py
   - Dockerfile
   - README.md
   - .env.example
```

---

## Context Requirements

The AI-Native-Developer **must read** all 8 documentation files:

1. `docs/00-project-context.md` - Project overview and goals
2. `docs/01-requirements.md` - Detailed functional requirements
3. `docs/02-architecture.md` - System design and structure
4. `docs/03-implementation-guide.md` - Coding standards and patterns
5. `docs/04-quality-gates.md` - Quality criteria and checks
6. `docs/05-ai-prompt-template.md` - AI interaction patterns
7. `docs/06-testing-strategy.md` - Testing approach
8. `docs/07-deployment-guide.md` - Deployment procedures

---

## Implementation Guidelines

### Code Quality
- ✅ Type hints for all functions
- ✅ Comprehensive docstrings
- ✅ Error handling and logging
- ✅ Input validation
- ✅ Security best practices

### Testing
- ✅ Unit tests for all functions
- ✅ Integration tests for workflows
- ✅ Security tests for vulnerabilities
- ✅ Performance tests for critical paths
- ✅ 80%+ code coverage

### Infrastructure
- ✅ Multi-stage Docker builds
- ✅ Environment variable configuration
- ✅ Health check endpoints
- ✅ Proper logging and monitoring

### Documentation
- ✅ Clear README with examples
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Inline comments for complex logic
- ✅ Migration scripts if needed

---

## Example Output Structure

```
project/
├── src/
│   ├── main.py              # Application entry point
│   ├── requirements.txt     # Dependencies
│   ├── config.py            # Configuration management
│   ├── models.py            # Data models
│   ├── services.py          # Business logic
│   └── utils.py             # Utility functions
├── tests/
│   ├── test_main.py         # Main tests
│   ├── test_models.py       # Model tests
│   ├── test_services.py     # Service tests
│   └── conftest.py          # Test fixtures
├── docs/
│   └── (8 AI-Native docs from previous role)
├── Dockerfile               # Container definition
├── docker-compose.yml       # Multi-container setup (optional)
├── .env.example             # Environment template
├── .gitignore               # Git ignore rules
└── README.md                # Project documentation
```

---

## Typical Workflow

### Iteration 1-3: Setup & Core Implementation
- Read all 8 documentation files
- Set up project structure
- Implement core functionality
- Create basic tests

### Iteration 4-8: Feature Implementation
- Implement all functional requirements
- Add comprehensive error handling
- Expand test coverage
- Add logging and monitoring

### Iteration 9-12: Quality & Optimization
- Achieve 80%+ test coverage
- Fix linting errors
- Optimize performance
- Security hardening

### Iteration 13-16: Infrastructure
- Create Dockerfile
- Set up environment configuration
- Add health checks
- Test deployment

### Iteration 17-20: Documentation & Polish
- Complete README.md
- Add API documentation
- Final testing
- Validation checks

---

## Success Indicators

When the role completes successfully, you should have:

✅ **Functional Code**
- All requirements implemented
- All tests passing
- 80%+ coverage

✅ **Production Ready**
- Docker image builds
- Health checks work
- No security vulnerabilities

✅ **Well Documented**
- Clear README
- API docs (if applicable)
- Inline comments

✅ **Quality Assured**
- No linting errors
- Performance optimized
- Security hardened

---

## Common Pitfalls to Avoid

❌ **Don't**:
- Skip reading the documentation files
- Hardcode secrets or configuration
- Skip tests to save time
- Use deprecated libraries
- Ignore quality gates

✅ **Do**:
- Read all 8 docs thoroughly
- Use environment variables
- Write tests first (TDD)
- Use modern, maintained libraries
- Run all quality checks

---

## Integration with Other Roles

### Receives from AI-Native-Writer:
- `docs/00-project-context.md`
- `docs/01-requirements.md`
- `docs/02-architecture.md`
- `docs/03-implementation-guide.md`
- `docs/04-quality-gates.md`
- `docs/05-ai-prompt-template.md`
- `docs/06-testing-strategy.md`
- `docs/07-deployment-guide.md`

### Can work with:
- **Architect**: For complex system designs
- **SEO-Specialist**: For web applications
- **Market-Researcher**: For product features

---

## Monitoring Progress

The role executor will log:

```
🎭 AI-Native-Developer starting mission...
📖 Reading docs/00-project-context.md...
📖 Reading docs/01-requirements.md...
...
🔨 Implementing core functionality...
✅ src/main.py created
✅ tests/test_main.py created
🧪 Running tests...
✅ All tests passed (coverage: 85%)
🐳 Building Docker image...
✅ Docker image built successfully
✅ AI-Native-Developer mission completed!
```

---

**Role File**: [`roles/ai_native_developer.yaml`](file:///d:/AI-agnet/claude-code-auto/roles/ai_native_developer.yaml)  
**Category**: Engineering  
**Complexity**: High  
**Typical Duration**: 15-20 iterations
