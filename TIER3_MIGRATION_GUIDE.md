# Tier-3 Agentic Workflow - Migration Guide

## Overview

The RoleRegistry system has been upgraded from **Tier-2 (Configuration-Driven)** to **Tier-3 (Agentic Workflow)** with:

1. **Reflection/Review Loops** - Self-correction through critic cycles
2. **Workflow State Machine** - Dynamic role transitions
3. **Prompt Template Composition** - Flexible system prompts
4. **100% Backward Compatibility** - All existing roles work unchanged

---

## What's New (Tier-3 Features)

### 1. ReviewConfig - Reflection Loop

Roles can now self-correct by switching to a "critic" persona after generating output.

```yaml
reflection:
  enabled: true
  reviewer_role: "SRE-Auditor"  # Who reviews? (None = self-review)
  aspects: ["scalability", "security", "fault_tolerance"]
  max_retries: 3  # Max refinement iterations
  critic_prompt_template: "Custom template..."  # Optional
```

**How it works:**
1. Role completes initial output
2. Switches to `reviewer_role` (or self-review)
3. Reviews work for specified `aspects`
4. Iteratively refines until quality threshold or `max_retries`
5. Returns refined output

### 2. WorkflowConfig - State Machine

Roles can dynamically route to next roles based on output content.

```yaml
workflow:
  next_state: "AI-Native-Writer"  # Default next role
  strategy: "conditional"  # fixed | conditional | llm_decide
  transition_rules:
    "needs_security": "Security-Auditor"
    "needs_optimization": "Performance-Engineer"
```

**Three strategies:**

- **`fixed`**: Always go to `next_state`
- **`conditional`**: Check output for keywords, route accordingly
- **`llm_decide`**: Ask LLM to determine next step dynamically

### 3. Enhanced Prompt Composition

Roles can now use custom instructions:

```yaml
# Option 1: Inline instructions
base_instructions: |
  Always think step-by-step.
  Consider edge cases first.

# Option 2: Load from file
instructions_path: "prompts/architect_custom.md"
```

The `RoleRegistry.get_full_prompt()` method composes:
1. Custom instructions (if any)
2. Mission and success criteria
3. Output standards and validation rules
4. Reflection requirements (if enabled)
5. Context (if provided)

---

## Migration Path

### Existing Roles (No Changes Required!)

**All existing YAML files work without modification.**

New fields are **Optional** with sensible defaults:

```yaml
# OLD (still works perfectly)
name: "Market-Researcher"
description: "Market research specialist"
mission:
  goal: "Research market trends"
  success_criteria: ["Comprehensive report"]
output_standard:
  required_files: ["research.md"]
  validation_rules: []

# NEW (with Tier-3 features)
name: "System-Architect-T3"
description: "Tier-3 Architect"
mission:
  goal: "Design system architecture"
  success_criteria: ["Complete design"]
output_standard:
  required_files: ["architecture.md"]
  validation_rules: []

# Tier-3 additions (optional)
reflection:
  enabled: true
  aspects: ["security", "scalability"]
  max_retries: 3

workflow:
  next_state: "AI-Native-Writer"
  strategy: "conditional"
```

---

## New API Methods

### RoleRegistry.get_full_prompt()

```python
from src.core.team.role_registry import RoleRegistry

registry = RoleRegistry()

# Get composed system prompt for a role
prompt = registry.get_full_prompt("System-Architect-T3", context="User goal here")

# Returns:
# # Role: System-Architect-T3
# Tier-3 Autonomous System Architect...
#
# # Persona
# You are acting as: Principal Software Architect...
#
# # Mission
# Goal: Design a resilient...
# Success Criteria:
# - System Overview aligns...
#
# # Output Standards
# Required Files: architecture-design.md, technical-decisions.log
#
# Validation Requirements:
# - Must contain: ## System Overview, ## Trade-offs & Decisions...
#
# # Self-Review Process
# After completing your output, you MUST:
# - Review your work for: scalability, security, fault_tolerance
# - Perform up to 3 refinement iterations
# - Address any issues found during review
```

### RoleExecutor._execute_reflection_loop()

Automatically called after successful validation (if `reflection.enabled`):

```python
result = await executor.execute(mission)

# If role.reflection.enabled = True:
# 1. Executes initial mission
# 2. Validates outputs
# 3. Runs reflection loop:
#    - Switch to critic persona
#    - Review work
#    - Refine if issues found
#    - Repeat up to max_retries
# 4. Returns refined outputs
```

### LeaderAgent._determine_next_workflow_state()

Automatically called after mission completion (if `workflow` configured):

```python
# After mission succeeds:
if role.workflow:
    next_role = await leader._determine_next_workflow_state(
        role, result, current_mission
    )
    # Automatically executes next role
```

---

## Usage Examples

### Example 1: Architect with Self-Review

```yaml
name: "System-Architect"
reflection:
  enabled: true
  reviewer_role: "SRE-Auditor"
  aspects: ["scalability", "security", "operational_complexity"]
  max_retries: 3
```

**Behavior:**
1. Architect designs system
2. SRE-Auditor reviews for scalability, security, ops complexity
3. Architect refines based on feedback
4. Loop continues 3 times or until no issues found

### Example 2: Market Research with Workflow

```yaml
name: "Market-Researcher"
workflow:
  next_state: "AI-Native-Writer"
  strategy: "conditional"
  transition_rules:
    "needs_deeper_research": "Market-Researcher"  # Self-loop
    "needs_technical_validation": "Technical-Advisor"
```

**Behavior:**
- If output contains "needs_deeper_research" → Run Market-Researcher again
- If output contains "needs_technical_validation" → Run Technical-Advisor
- Otherwise → Run AI-Native-Writer

### Example 3: Quality Gate with LLM Decision

```yaml
name: "Content-Strategist"
workflow:
  next_state: "SEO-Optimized"
  strategy: "llm_decide"  # Let LLM decide next step
```

**Behavior:**
- LLM analyzes content quality
- Decides whether to:
  - End workflow (output "COMPLETE")
  - Send to SEO-Optimized
  - Send to another reviewer

---

## Testing & Validation

### Test Backward Compatibility

```python
# All existing roles should load without errors
from src.core.team.role_registry import RoleRegistry

registry = RoleRegistry()

# Test loading old roles
role = registry.get_role("Market-Researcher")
assert role is not None
assert role.reflection is None  # Old roles have no reflection config
assert role.workflow is None  # Old roles have no workflow config

print("✅ Backward compatibility confirmed")
```

### Test Tier-3 Features

```python
# Test new Tier-3 role
role = registry.get_role("System-Architect-T3")

assert role.reflection is not None
assert role.reflection.enabled == True
assert "scalability" in role.reflection.aspects

assert role.workflow is not None
assert role.workflow.strategy == "conditional"

# Test prompt composition
prompt = registry.get_full_prompt("System-Architect-T3")
assert "Self-Review Process" in prompt
assert "scalability, security, fault_tolerance" in prompt

print("✅ Tier-3 features working")
```

---

## Performance Considerations

### Reflection Loop Cost

Each reflection iteration adds:
- **1 LLM call** for review (120s timeout)
- **1 LLM call** for refinement (uses executor timeout)

**Estimated cost per iteration**: ~$0.05-$0.15 (Sonnet)

**Mitigation**: Set `max_retries` appropriately (3 is good default)

### Workflow Decision Cost

- **`fixed`**: No cost (instant transition)
- **`conditional`**: Minimal cost (keyword matching)
- **`llm_decide`**: 1 LLM call (60s timeout, ~$0.02)

---

## Best Practices

### 1. Use Reflection For:
- ✅ Critical roles (Architect, Security-Auditor)
- ✅ Complex outputs requiring review
- ✅ High-stakes deliverables

### 2. Use Workflow For:
- ✅ Dynamic branching based on output quality
- ✅ Conditional specialist consultation
- ✅ Multi-stage validation pipelines

### 3. Avoid:
- ❌ Reflection on simple tasks (wastes cost)
- ❌ Overly complex workflow chains (hard to debug)
- ❌ Mixing `llm_decide` with many transition rules (unpredictable)

### 4. Prompt Templates:
- ✅ Use `instructions_path` for long custom prompts
- ✅ Use `base_instructions` for short inline instructions
- ✅ Leverage `get_full_prompt()` for testing

---

## Troubleshooting

### Issue: Reflection loop never converges

**Symptom**: Reaches `max_retries` with issues still found

**Solutions:**
1. Reduce `max_retries` from 3 to 2
2. Simplify `aspects` (remove less critical dimensions)
3. Improve critic prompt template
4. Check if outputs are fundamentally flawed

### Issue: Workflow always routes to same state

**Symptom**: `conditional` strategy never matches keywords

**Solutions:**
1. Check keyword spelling in `transition_rules`
2. Use lowercase keywords (matching is case-insensitive)
3. Add logging to see actual output content
4. Consider using `llm_decide` for complex logic

### Issue: Old role fails to load

**Symptom**: `ValidationError` on existing YAML

**Solutions:**
1. Check YAML syntax (use online validator)
2. Ensure all required fields present
3. Verify no typos in field names
4. Check indentation (YAML is strict)

---

## Future Enhancements (Planned)

1. **Tool Schema Support**: `tools` as list of ToolConfig objects
2. **Reflection History Tracking**: Store all refinement iterations
3. **Workflow Visualization**: Auto-generate workflow diagrams
4. **Reflection Metrics**: Track refinement success rates
5. **Workflow Debugging**: Step-through workflow execution

---

## Summary

✅ **Backward Compatible**: All existing roles work unchanged
✅ **Opt-In Features**: Only use Tier-3 features when needed
✅ **Production Ready**: Tested with existing roles
✅ **Well Documented**: Examples, guides, and migration paths

**Status**: Ready for production use

**Recommendation**: Start with new roles using Tier-3 features. Migrate existing roles incrementally based on need.

---

*Generated: 2026-01-02*
*Version: 4.0.0-tier3*
*Author: Claude Code Auto v4*
