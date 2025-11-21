# Team Mode Usage Guide

## Overview

The Dynamic Team Assembly System enables the AI agent to automatically form specialized teams based on your `initial_prompt`. Each team member (role) has specific expertise, missions, and quality gates.

## Quick Start

### 1. Enable Team Mode

Add an `initial_prompt` to your `config.yaml`:

```yaml
task:
  goal: "Generate complete app development documentation"
  initial_prompt: |
    I need comprehensive documentation for a mobile app including:
    1. Market research and competitive analysis
    2. Complete AI-Native development docs (8 files)
    3. SEO optimization strategy
```

### 2. Run the Agent

```bash
python src/main.py
```

The system will:
1. ✅ Detect `initial_prompt`
2. 🎭 Activate Team Mode
3. 📚 Load available roles
4. 🔍 Assemble optimal team using LLM
5. 🚀 Execute roles linearly with validation

### 3. Fallback Behavior

If team assembly fails, the system automatically falls back to original mode.

---

## Available Roles

### Market-Researcher
**Category**: Research  
**Persona**: `researcher`  
**Mission**: Complete in-depth market research

**Outputs**:
- `market-research.md` (2000+ chars)

**Validation**:
- Must include: Executive Summary, Target Users, Competitor Analysis, Market Size, User Pain Points, Opportunities
- No placeholders allowed

**Tools**: `web_search`, `write_file`, `read_file`

---

### AI-Native-Writer
**Category**: Documentation  
**Persona**: `coder`  
**Mission**: Generate complete AI-Native development documentation (8 files)

**Outputs**:
- `docs/00-project-context.md`
- `docs/01-requirements.md`
- `docs/02-architecture.md`
- `docs/03-implementation-guide.md`
- `docs/04-quality-gates.md`
- `docs/05-ai-prompt-template.md`
- `docs/06-testing-strategy.md`
- `docs/07-deployment-guide.md`

**Validation**:
- All 8 files must exist
- Specific sections required in each file
- Minimum character counts enforced
- No placeholders allowed

**Dependencies**: Market-Researcher

**Tools**: `write_file`, `read_file`, `list_files`

---

### SEO-Specialist
**Category**: Marketing  
**Persona**: `product_manager`  
**Mission**: Generate comprehensive SEO optimization strategy

**Outputs**:
- `seo-strategy.md` (1800+ chars)

**Validation**:
- Must include: Keyword Research, On-Page SEO, Technical SEO, Content Strategy, Link Building, Performance Metrics
- No placeholders allowed

**Dependencies**: Market-Researcher, AI-Native-Writer

**Tools**: `web_search`, `write_file`, `read_file`

---

### Architect
**Category**: Engineering  
**Persona**: `coder`  
**Mission**: Design comprehensive system architecture

**Outputs**:
- `architecture-design.md` (3000+ chars)

**Validation**:
- Must include: System Overview, Architecture Diagram, Component Design, Technology Stack, Data Models, API Specifications, Scalability, Security
- No placeholders allowed

**Dependencies**: Market-Researcher

**Tools**: `write_file`, `read_file`, `list_files`

---

## How It Works

### 1. Team Assembly

The `TeamAssembler` uses an LLM to analyze your `initial_prompt` and `goal`:

```
Input: initial_prompt + goal + available roles
  ↓
LLM Analysis
  ↓
Output: ["Market-Researcher", "AI-Native-Writer", "SEO-Specialist"]
```

### 2. Linear Execution

Roles execute **sequentially**, not in parallel:

```
Market-Researcher
  ↓ (outputs market-research.md)
AI-Native-Writer (reads market-research.md)
  ↓ (outputs 8 docs)
SEO-Specialist (reads market-research.md + docs)
  ↓ (outputs seo-strategy.md)
Complete!
```

### 3. Validation Gates

Each role's output is validated before proceeding:

```
Role Mission Loop:
  1. Execute task
  2. Validate output
  3. Pass? → Next role
  4. Fail? → Retry (max iterations)
```

**Validation Types**:
- `file_exists`: Check if file exists
- `all_files_exist`: Check multiple files
- `content_check`: Verify required sections
- `no_placeholders`: Detect [TODO], [PLACEHOLDER], etc.
- `min_length`: Minimum character count
- `code_blocks_valid`: (future) Syntax validation

### 4. Context Passing

Each role receives outputs from previous roles:

```python
context = {
    "Market-Researcher": {
        "outputs": ["market-research.md"],
        "iterations": 3
    },
    "AI-Native-Writer": {
        "outputs": ["docs/00-project-context.md", ...],
        "iterations": 8
    }
}
```

---

## Configuration

### config.yaml

```yaml
task:
  goal: "Your overall goal"
  initial_prompt: |
    Detailed description of what you need.
    The LLM will analyze this to determine which roles to activate.

# Team mode uses existing settings:
claude:
  model: "claude-3-5-sonnet-20241022"
  timeout_seconds: 300
  permission_mode: "bypassPermissions"

safety:
  max_iterations: 50  # Per-role max iterations
```

### Role YAML Structure

```yaml
name: "Role-Name"
description: "Role description"
category: "research|documentation|marketing|engineering"

mission:
  goal: "What this role accomplishes"
  success_criteria:
    - "Criterion 1"
    - "Criterion 2"
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
        - "## Section 1"
        - "## Section 2"
    
    - type: "min_length"
      file: "output-file.md"
      min_chars: 2000
    
    - type: "no_placeholders"
      files:
        - "output-file.md"
      forbidden_patterns:
        - "\\[TODO\\]"
        - "\\[PLACEHOLDER\\]"

recommended_persona: "researcher|coder|product_manager"

tools:
  - "web_search"
  - "write_file"
  - "read_file"

dependencies:
  - "Other-Role-Name"  # Optional
```

---

## Example Workflows

### Workflow 1: App Documentation

**Config**:
```yaml
task:
  goal: "Create complete app development package"
  initial_prompt: |
    Generate comprehensive documentation for a fitness tracking app:
    1. Market research on fitness app market
    2. Complete development documentation (8 files)
    3. SEO strategy for app store optimization
```

**Expected Team**: `[Market-Researcher, AI-Native-Writer, SEO-Specialist]`

**Outputs**:
- `market-research.md`
- `docs/00-project-context.md` through `docs/07-deployment-guide.md`
- `seo-strategy.md`

---

### Workflow 2: Technical Architecture

**Config**:
```yaml
task:
  goal: "Design system architecture for e-commerce platform"
  initial_prompt: |
    I need:
    1. Market analysis of e-commerce platforms
    2. Complete system architecture design
```

**Expected Team**: `[Market-Researcher, Architect]`

**Outputs**:
- `market-research.md`
- `architecture-design.md`

---

## Monitoring & Debugging

### Log Output

Team mode provides detailed logging:

```
🎭 Team Mode Activated
📚 Loaded 4 roles: ['Market-Researcher', 'AI-Native-Writer', 'SEO-Specialist', 'Architect']
🔍 Assembling team based on initial_prompt...
✅ Team assembled: ['Market-Researcher', 'AI-Native-Writer', 'SEO-Specialist']
🚀 Starting team orchestration...

============================================================
Role 1/3: Market-Researcher
============================================================
🎭 Switched Persona to: researcher
📋 Mission: Complete in-depth market research...
✅ Iteration 1: Success
✅ Validation passed: market-research.md

============================================================
Role 2/3: AI-Native-Writer
============================================================
🎭 Switched Persona to: coder
📋 Mission: Generate complete AI-Native development documentation...
✅ Iteration 1: Success
...
✅ Validation passed: All 8 files created

============================================================
Role 3/3: SEO-Specialist
============================================================
🎭 Switched Persona to: product_manager
📋 Mission: Generate comprehensive SEO optimization strategy...
✅ Iteration 1: Success
✅ Validation passed: seo-strategy.md

✅ Team mission accomplished!
📊 Completed 3/3 roles
```

### Event Tracking

All team activities are logged to `logs/events/`:

```json
{
  "type": "SESSION_START",
  "mode": "team",
  "goal": "...",
  "initial_prompt": "..."
},
{
  "type": "PLANNER_COMPLETE",
  "team_roles": ["Market-Researcher", "AI-Native-Writer"],
  "team_size": 2
},
{
  "type": "SESSION_END",
  "status": "success",
  "completed_roles": 2,
  "total_roles": 2
}
```

---

## Troubleshooting

### Team Assembly Fails

**Symptom**: `❌ Failed to assemble team. Falling back to original mode.`

**Causes**:
1. No roles in `roles/` directory
2. LLM timeout or error
3. Invalid JSON response from LLM

**Solution**:
- Ensure `roles/*.yaml` files exist
- Check LLM connectivity
- Review `initial_prompt` clarity

---

### Role Validation Fails

**Symptom**: `❌ Validation failed after 10 iterations`

**Causes**:
1. Output file not created
2. Missing required sections
3. Placeholders detected
4. File too short

**Solution**:
- Review role's `output_standard` in YAML
- Check validation rules
- Increase `max_iterations` if needed

---

### Fallback to Original Mode

**Symptom**: `⚠️ Team mode failed, falling back to original mode`

**Behavior**: System continues with standard ReAct loop

**When**: Team assembly or execution fails

**Impact**: No data loss, original functionality preserved

---

## Advanced Usage

### Creating Custom Roles

1. Create `roles/my_custom_role.yaml`
2. Define mission, outputs, and validation
3. Restart agent (roles loaded at startup)

### Role Dependencies

Specify dependencies to ensure execution order:

```yaml
dependencies:
  - "Market-Researcher"  # Must complete first
```

### Persona Recommendations

Each role can recommend a persona:

```yaml
recommended_persona: "researcher"  # or "coder", "product_manager"
```

The `ExecutorAgent` automatically switches personas per role.

---

## Architecture

```
main.py
  ↓
Detect initial_prompt?
  ↓ Yes
run_team_mode()
  ↓
RoleRegistry.load_roles()
  ↓
TeamAssembler.assemble_team()
  ↓
TeamOrchestrator.execute()
  ↓
For each role:
  RoleExecutor.execute_role()
    ↓
  Validate outputs
    ↓
  Pass context to next role
```

---

## Testing

Run unit tests:

```bash
pytest tests/test_role_registry.py tests/test_team_assembler.py tests/test_role_executor.py tests/test_team_orchestrator.py -v
```

**Expected**: 32 tests pass

---

## Backward Compatibility

Team mode is **fully backward compatible**:

- ✅ If `initial_prompt` is empty → Original mode
- ✅ If team assembly fails → Original mode
- ✅ All existing configs work unchanged

---

## Performance

**Team Mode**:
- Roles execute sequentially (not parallel)
- Each role has independent iteration limit
- Total time = Sum of role execution times

**Original Mode**:
- Single agent, single iteration limit
- Faster for simple tasks

**Recommendation**: Use team mode for complex, multi-stage workflows

---

## Limits

- **Max Roles**: No hard limit (LLM decides)
- **Max Iterations per Role**: Defined in role YAML (default: 10-15)
- **Max Team Size**: Practical limit ~5 roles (LLM context)
- **Validation Rules**: 6 types currently supported

---

## Future Enhancements

- [ ] Parallel role execution (for independent roles)
- [ ] Dynamic role creation (LLM generates roles on-the-fly)
- [ ] Role templates (reusable role patterns)
- [ ] Advanced validation (code syntax, API calls)
- [ ] Role marketplace (community-contributed roles)

---

## Support

For issues or questions:
1. Check logs in `logs/`
2. Review event files in `logs/events/`
3. Verify role YAML syntax
4. Test with simpler `initial_prompt`

---

**Version**: 1.0  
**Last Updated**: 2025-11-22
