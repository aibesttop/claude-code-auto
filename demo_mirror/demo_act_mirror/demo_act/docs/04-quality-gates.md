# Quality Gates: Claude Code Auto v4.0

## Document Information
- **Version**: 1.0.0
- **Last Updated**: 2025-01-03
- **Status**: Final
- **Author**: Team Mode Documentation Team

---

## Overview

Claude Code Auto implements **dual-layer validation** to ensure output quality:

1. **Format Validation**: Fast, deterministic checks (always enabled)
2. **Semantic Quality Validation**: LLM-driven scoring (optional per role)

---

## Format Validation

### Validation Rules

#### 1. File Existence Check

```yaml
- type: "file_exists"
  file: "output.md"
```

**Purpose**: Ensures required files are created

**Error Message**: `File not found: output.md`

---

#### 2. Content Pattern Check

```yaml
- type: "content_check"
  file: "output.md"
  must_contain:
    - "## Executive Summary"
    - "## Analysis"
    - "key findings"
```

**Purpose**: Verifies content contains required sections/keywords

**Error Message**: `Missing required patterns in output.md: ["## Executive Summary"]`

---

#### 3. Minimum Length Check

```yaml
- type: "min_length"
  file: "output.md"
  min_chars: 2000
```

**Purpose**: Ensures sufficient content depth

**Adaptive Validation** (optional):
- Simple complexity: 0.7x multiplier (1400 chars)
- Medium complexity: 1.0x multiplier (2000 chars)
- Complex complexity: 1.5x multiplier (3000 chars)
- Expert complexity: 2.0x multiplier (4000 chars)

**Error Message**: `output.md is 1500 chars (minimum: 2000)`

---

#### 4. Placeholder Detection

```yaml
- type: "no_placeholders"
  files:
    - "output.md"
  forbidden_patterns:
    - "\\[TODO\\]"
    - "\\[PLACEHOLDER\\]"
    - "TBD"
    - "Coming soon"
```

**Purpose**: Catches incomplete work

**Error Message**: `Found forbidden patterns in output.md: ["[TODO]", "TBD"]`

---

### Format Validation Flow

```python
def validate_format(self, role: Role) -> ValidationResult:
    errors = []

    for rule in role.output_standard.validation_rules:
        if rule["type"] == "file_exists":
            if not self.check_file_exists(rule["file"]):
                errors.append(f"File not found: {rule['file']}")

        elif rule["type"] == "content_check":
            missing = self.check_content_patterns(rule)
            if missing:
                errors.append(f"Missing patterns: {missing}")

        elif rule["type"] == "min_length":
            if self.check_min_length(rule):
                errors.append(f"Content too short")

        elif rule["type"] == "no_placeholders":
            found = self.check_placeholders(rule)
            if found:
                errors.append(f"Found placeholders: {found}")

    return ValidationResult(
        passed=len(errors) == 0,
        errors=errors
    )
```

---

## Semantic Quality Validation

### Enable Quality Validation

In role YAML:

```yaml
enable_quality_check: true
```

### Quality Scoring Process

1. **LLM Evaluation**: Uses Claude Haiku for cost efficiency
2. **Success Criteria**: Scores output against role's success criteria
3. **Quality Score**: Returns 0-100 with breakdown

### Quality Score Structure

```python
@dataclass
class QualityScore:
    overall_score: float  # 0-100
    criteria_scores: Dict[str, float]  # Per-criteria scores
    issues: List[str]  # Problems found
    suggestions: List[str]  # Improvement recommendations
```

### Quality Threshold

Default threshold: 70.0 (configurable per role)

In `config.yaml`:

```yaml
leader:
  quality_threshold: 70.0
```

Per-role override:

```yaml
quality_threshold: 75.0  # Higher threshold for this role
```

---

## Adaptive Validation

### Enable Adaptive Validation

In role YAML:

```yaml
adaptive: true
base_chars: 2000  # Base length for "medium" complexity
```

### Complexity Estimation

System estimates complexity based on:

1. **Keywords**: Simple, medium, complex, expert keywords in goal
2. **Content Length**: Expected output length
3. **Criteria Count**: Number of success criteria

### Complexity Multipliers

| Complexity | Multiplier | Example |
|------------|-----------|---------|
| **Simple** | 0.7x | Basic summary, list generation |
| **Medium** | 1.0x | Standard analysis, documentation |
| **Complex** | 1.5x | Multi-faceted research, architecture |
| **Expert** | 2.0x | Deep technical analysis, innovation |

### Example

```yaml
# Base requirement: 2000 chars
adaptive: true
base_chars: 2000

# If estimated complexity: Complex
# Effective minimum: 2000 * 1.5 = 3000 chars
```

---

## Validation Pipeline

### Full Validation Flow

```
Role Execution Complete
         │
         ▼
┌─────────────────────────────┐
│  1. Format Validation        │
│     ├─ File existence        │
│     ├─ Content patterns      │
│     ├─ Minimum length        │
│     └─ Placeholder detection │
└──────────┬──────────────────┘
           │
           ▼
      Format Passed?
           │
    ┌──────┴──────┐
    │             │
   Yes           No
    │             │
    ▼             ▼
┌─────────┐  Format Error
│  2. LLM │  (Retry)
│Quality  │     │
│ Check   │     ▼
│(Optional│  Retry
│   ?)    │  (Up to
└────┬────┘ max_iters)
     │
     ▼
Quality Passed?
     │
  ┌──┴──┐
  │    │
 Yes   No
  │    │
  ▼    ▼
Success Retry
```

---

## Quality Metrics

### Role-Level Metrics

- **Format Pass Rate**: % of roles passing format validation
- **Quality Pass Rate**: % of roles passing semantic validation (if enabled)
- **Retry Count**: Average retries per role
- **Avg Quality Score**: Mean quality score across all roles

### Session-Level Metrics

- **Overall Success Rate**: % of missions completed successfully
- **Total Quality Score**: Aggregate score across all roles
- **Intervention Count**: Number of Leader interventions (RETRY, TERMINATE)

---

## Best Practices

### 1. Always Use Format Validation

Format validation is fast and catches obvious errors:
- Missing files
- Incomplete content (placeholders)
- Too short (insufficient depth)

### 2. Enable Semantic Validation for Critical Roles

Use semantic validation for roles where quality matters:
- AI-Native-Writer (documentation quality)
- Architect (design quality)
- Market-Researcher (analysis depth)

### 3. Use Adaptive Validation for Variable Tasks

Enable adaptive validation when task complexity varies:
- Research tasks (simple vs. deep dive)
- Development tasks (bug fix vs. feature)

### 4. Set Appropriate Thresholds

- **70.0**: Default threshold (good quality)
- **80.0+:** High-stakes outputs (production code, public docs)
- **60.0:** Draft quality (internal drafts, exploratory work)

### 5. Provide Clear Success Criteria

In role YAML:

```yaml
mission:
  success_criteria:
    - "Measurable criterion 1"  # Specific, not vague
    - "Measurable criterion 2"
```

Bad example:
```yaml
success_criteria:
  - "Good quality"  # Too vague
  - "Professional"  # Subjective
```

---

## Troubleshooting

### Issue: Format Validation Always Fails

**Possible Causes**:
1. Incorrect file paths in `required_files`
2. Role not creating files in expected location
3. File permissions issue

**Solution**:
- Check role output directory (default: `demo_act/`)
- Verify file paths in role YAML
- Check file write permissions

---

### Issue: Quality Score Always Low

**Possible Causes**:
1. Success criteria too vague
2. Quality threshold too high
3. LLM misinterpreting criteria

**Solution**:
- Refine success criteria (make specific)
- Lower quality threshold (e.g., 60.0)
- Check quality score breakdown in `logs/evaluations/`

---

### Issue: Adaptive Validation Too Strict

**Possible Causes**:
1. Base chars too high
2. Complexity overestimated

**Solution**:
- Lower `base_chars` (e.g., 1500 instead of 2000)
- Disable adaptive validation for simple tasks
- Manually set `min_chars` instead

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-03 | Initial quality gates documentation | Team Mode Documentation Team |

---

*This document is part of the comprehensive documentation suite for Claude Code Auto v4.0.*
