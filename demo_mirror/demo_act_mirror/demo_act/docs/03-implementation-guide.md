# Implementation Guide: Claude Code Auto v4.0

## Document Information
- **Version**: 1.0.0
- **Last Updated**: 2025-01-03
- **Status**: Final
- **Author**: Team Mode Documentation Team

---

## Table of Contents
1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Adding a New Role](#adding-a-new-role)
4. [Adding a New Tool](#adding-a-new-tool)
5. [Modifying Validation Rules](#modifying-validation-rules)
6. [Debugging Tips](#debugging-tips)
7. [Common Workflows](#common-workflows)

---

## Development Environment Setup

### Prerequisites

1. **Python 3.12+**
   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **API Keys**
   - Anthropic API Key (for Claude)
   - Tavily API Key (for web search)

### Installation Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd claude-code-auto
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # OR
   .venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Environment Variables**
   ```bash
   export ANTHROPIC_API_KEY="your-key-here"
   export TAVILY_API_KEY="your-key-here"
   ```

   Or create `.env` file:
   ```
   ANTHROPIC_API_KEY=your-key-here
   TAVILY_API_KEY=your-key-here
   ```

5. **Verify Installation**
   ```bash
   python -m src.main --help
   ```

---

## Project Structure

```
claude-code-auto/
├── src/
│   ├── main.py                      # Entry point, mode detection
│   ├── config.py                    # Pydantic configuration models
│   ├── core/
│   │   ├── leader/                  # Leader Agent
│   │   │   ├── leader_agent.py
│   │   │   └── mission_decomposer.py
│   │   ├── team/                    # Team collaboration
│   │   │   ├── team_assembler.py
│   │   │   ├── dependency_resolver.py
│   │   │   ├── role_executor.py
│   │   │   ├── role_registry.py
│   │   │   └── quality_validator.py
│   │   ├── agents/                  # Agent implementations
│   │   │   ├── planner.py
│   │   │   ├── executor.py
│   │   │   ├── researcher.py
│   │   │   └── sdk_client.py
│   │   ├── tools/                   # Tool implementations
│   │   │   ├── file_tools.py
│   │   │   ├── shell_tools.py
│   │   │   └── research_tools.py
│   │   └── events.py                # EventStore & CostTracker
│   └── utils/
│       ├── logger.py
│       ├── json_parser.py
│       └── state_manager.py
├── roles/                           # Role definitions (YAML)
│   ├── market_researcher.yaml
│   ├── ai_native_writer.yaml
│   └── ...
├── resources/                       # Resource configurations
│   ├── mcp_servers.yaml
│   ├── skill_prompts.yaml
│   └── tool_mappings.yaml
├── config.yaml                      # Main configuration
├── requirements.txt                 # Python dependencies
└── run_agent.bat                   # Windows launch script
```

---

## Adding a New Role

### Step 1: Create Role YAML File

Create `roles/data_analyst.yaml`:

```yaml
name: "Data-Analyst"
description: "Analyzes data and generates insights"
category: "analysis"

mission:
  goal: "Analyze data and generate actionable insights"
  success_criteria:
    - "Data analysis report with visualizations"
    - "Statistical summary with key metrics"
    - "Actionable recommendations based on findings"
  max_iterations: 10

output_standard:
  required_files:
    - "analysis_report.md"
  validation_rules:
    - type: "file_exists"
      file: "analysis_report.md"
    - type: "content_check"
      file: "analysis_report.md"
      must_contain:
        - "## Summary"
        - "## Key Findings"
        - "## Recommendations"
    - type: "min_length"
      file: "analysis_report.md"
      min_chars: 2000
    - type: "no_placeholders"
      files:
        - "analysis_report.md"
      forbidden_patterns:
        - "\\[TODO\\]"
        - "\\[PLACEHOLDER\\]"

recommended_persona: "analyst"

tools:
  - "read_file"
  - "write_file"
  - "execute_command"  # For running analysis scripts

dependencies: []  # Depends on no other roles

use_planner: true
enable_quality_check: true
adaptive: true
base_chars: 2000
```

### Step 2: Validate Role Definition

```bash
python -c "
import yaml
from pathlib import Path
role = yaml.safe_load(Path('roles/data_analyst.yaml').read_text())
print('Role loaded successfully:', role['name'])
"
```

### Step 3: Test Role

1. Create `config.yaml`:
   ```yaml
   task:
     goal: "Analyze sales data and generate insights"
     initial_prompt: "You are a data analyst"

   leader:
     enabled: true
   ```

2. Run system:
   ```bash
   python -m src.main
   ```

3. Check output in `demo_act/analysis_report.md`

---

## Adding a New Tool

### Step 1: Implement Tool Handler

Create `src/core/tools/custom_tools.py`:

```python
from typing import Dict, Any
from pathlib import Path

async def send_email_handler(input_data: Dict[str, Any]) -> str:
    """Send an email using SMTP"""
    to = input_data["to"]
    subject = input_data["subject"]
    body = input_data["body"]

    # Implementation here
    # ...

    return f"Email sent to {to}"
```

### Step 2: Register Tool

Modify `src/core/tool_registry.py`:

```python
from src.core.tools.custom_tools import send_email_handler

class ToolRegistry:
    def __init__(self):
        self.tools = {
            # Existing tools...

            "send_email": Tool(
                name="send_email",
                description="Send an email using SMTP",
                input_schema={
                    "type": "object",
                    "properties": {
                        "to": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["to", "subject", "body"]
                },
                handler=send_email_handler
            )
        }
```

### Step 3: Add Tool to Role

Update role YAML:

```yaml
tools:
  - "send_email"
  - "write_file"
```

---

## Modifying Validation Rules

### Add New Validation Rule Type

1. **Implement Validator** in `src/core/team/role_executor.py`:

```python
def validate_max_files(self, output: str, rule: dict) -> ValidationResult:
    """Validate maximum number of files created"""
    max_files = rule["max_files"]
    files_created = len(list(Path("demo_act").glob("*")))
    passed = files_created <= max_files
    return ValidationResult(
        passed=passed,
        message=f"Created {files_created} files (max: {max_files})"
    )
```

2. **Add to Validation Pipeline**:

```python
async def validate_output(self, output: str) -> ValidationResult:
    for rule in self.role.output_standard.validation_rules:
        if rule["type"] == "max_files":
            result = self.validate_max_files(output, rule)
        # ... other rules
```

3. **Use in Role YAML**:

```yaml
output_standard:
  validation_rules:
    - type: "max_files"
      max_files: 5
```

---

## Debugging Tips

### Enable Detailed Logging

In `config.yaml`:

```yaml
logging:
  level: "DEBUG"
  format: "detailed"
  console_output: true
  file_output: true
```

### Check Markdown Traces

1. **Planner Traces**: `logs/trace/{session_id}_{role}_step1.md`
2. **Executor Traces**: `logs/trace/{session_id}_{role}_step2.md`
3. **Intervention Logs**: `logs/interventions/{session_id}_interventions.md`

### Inspect Workflow State

```bash
cat demo_act/workflow_state.json
```

### Check Event Log

```bash
cat logs/events/{session_id}_events.jsonl | jq
```

### Common Issues

| Issue | Solution |
|-------|----------|
| **Role fails validation** | Check `logs/trace/` for executor output, verify validation rules |
| **Circular dependency** | Check role dependencies in YAML files |
| **API timeout** | Increase timeout in `config.yaml` under `claude.timeouts` |
| **Budget exceeded** | Check `logs/cost_report.json`, increase `max_budget_usd` |
| **Missing files** | Verify role output files match `required_files` list |

---

## Common Workflows

### Workflow 1: Create Multi-Step Documentation

1. **Define Goal** in `config.yaml`:
   ```yaml
   task:
     goal: "Create API documentation for REST endpoints"
     initial_prompt: "You are a technical writer"
   ```

2. **System Decomposes**:
   - Mission 1: Research API specifications
   - Mission 2: Write documentation
   - Mission 3: Review and refine

3. **Leader Assembles Team**:
   - Mission 1: Researcher
   - Mission 2: AI-Native-Writer
   - Mission 3: Multidimensional-Observer

4. **Execute in Dependency Order**

### Workflow 2: Debug Role Execution

1. **Enable Debug Logging**:
   ```yaml
   logging:
     level: "DEBUG"
   ```

2. **Run Single Role** (skip others):
   - Comment out other roles in mission decomposition output

3. **Inspect Traces**:
   - Read Planner trace for reasoning
   - Read Executor trace for ReAct steps
   - Check validation errors

4. **Fix and Retry**

### Workflow 3: Add Quality Validation to Existing Role

1. **Edit Role YAML**:
   ```yaml
   enable_quality_check: true
   ```

2. **Set Quality Threshold**:
   ```yaml
   quality_threshold: 75.0  # Higher threshold
   ```

3. **Test**:
   - Run role
   - Check `logs/evaluations/` for quality scores
   - Adjust threshold based on results

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-03 | Initial implementation guide | Team Mode Documentation Team |

---

*This document is part of the comprehensive documentation suite for Claude Code Auto v4.0.*
