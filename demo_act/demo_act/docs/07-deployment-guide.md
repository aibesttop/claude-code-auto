# Deployment Guide: Claude Code Auto v4.0

## Document Information
- **Version**: 1.0.0
- **Last Updated**: 2025-01-03
- **Status**: Final
- **Author**: Team Mode Documentation Team

---

## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Running the System](#running-the-system)
4. [Deployment Options](#deployment-options)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Troubleshooting](#troubleshooting)

---

## Installation

### Prerequisites

- **Python 3.12+**
- **Git**
- **Anthropic API Key**
- **Tavily API Key** (for web search)

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd claude-code-auto
```

### Step 2: Create Virtual Environment

**Linux/Mac**:
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows**:
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Set Environment Variables

**Option 1: Environment Variables**
```bash
export ANTHROPIC_API_KEY="your-key-here"
export TAVILY_API_KEY="your-key-here"
```

**Option 2: .env File**
```
# Create .env file
ANTHROPIC_API_KEY=your-key-here
TAVILY_API_KEY=your-key-here
```

**Option 3: Windows Batch Script** (run_agent.bat)
```batch
@echo off
set ANTHROPIC_API_KEY=your-key-here
set TAVILY_API_KEY=your-key-here
python -m src.main
```

### Step 5: Verify Installation

```bash
python -m src.main --help
```

Expected output:
```
Claude Code Auto v4.0
Usage: python -m src.main [--config CONFIG_PATH]
```

---

## Configuration

### Basic Configuration (config.yaml)

```yaml
# Work directories
directories:
  work_dir: "demo_act"
  mirror_dir: "demo_mirror"
  logs_dir: "logs"

# Task configuration
task:
  goal: "Your task description here"
  initial_prompt: ""  # Leave empty for Original Mode, set for Team Mode

# Safety limits
safety:
  max_iterations: 50
  max_duration_hours: 8
  emergency_stop_file: ".emergency_stop"

# Claude SDK
claude:
  model: "claude-sonnet-4-5"
  permission_mode: "bypassPermissions"
  timeout_seconds: 300

# Cost control
cost_control:
  enabled: false
  max_budget_usd: 10.0
  warning_threshold: 0.8
  auto_stop_on_exceed: true

# Leader Agent (Team Mode)
leader:
  enabled: true
  max_mission_retries: 3
  quality_threshold: 70.0
  enable_intervention: true
```

### Advanced Configuration

#### Enable Cost Control

```yaml
cost_control:
  enabled: true
  max_budget_usd: 20.0
  warning_threshold: 0.8
  auto_stop_on_exceed: true
```

#### Enable Debug Logging

```yaml
logging:
  level: "DEBUG"
  format: "detailed"
  console_output: true
  file_output: true
```

#### Customize Timeouts

```yaml
claude:
  timeouts:
    planner: 600      # 10 minutes
    executor: 300     # 5 minutes per ReAct step
    validator: 120    # 2 minutes
    decomposer: 180   # 3 minutes
```

---

## Running the System

### Original Mode (Single Agent)

**Setup**:
```yaml
# config.yaml
task:
  goal: "Write a Python function to calculate fibonacci numbers"
  initial_prompt: ""  # Empty = Original Mode
```

**Run**:
```bash
python -m src.main
```

**Expected Behavior**:
- Planner creates execution plan
- Executor executes plan using ReAct loop
- Output saved to `demo_act/`

---

### Team Mode (Multi-Agent)

**Setup**:
```yaml
# config.yaml
task:
  goal: "Research elderly care market and create comprehensive report"
  initial_prompt: "You are a market research specialist"

leader:
  enabled: true
```

**Run**:
```bash
python -m src.main
```

**Expected Behavior**:
1. Leader decomposes goal into SubMissions
2. Team Assembler selects roles
3. Dependency Resolver determines execution order
4. Roles execute in dependency order
5. Leader evaluates quality and intervenes if needed
6. Output integrated and saved to `demo_act/`

---

### Emergency Stop

Create `.emergency_stop` file to halt execution:

```bash
touch .emergency_stop
```

System will stop gracefully on next iteration.

---

## Deployment Options

### Option 1: Local Development

**Use Case**: Development, testing, experimentation

**Setup**:
```bash
# Run from project root
python -m src.main
```

**Pros**:
- Full control
- Easy debugging
- Direct access to logs

**Cons**:
- Requires local machine
- Manual monitoring

---

### Option 2: Screen/Tmux Session (Linux/Mac)

**Use Case**: Long-running tasks on remote server

**Setup**:

**Using screen**:
```bash
screen -S claude-agent
python -m src.main
# Press Ctrl+A, D to detach
```

**Reattach**:
```bash
screen -r claude-agent
```

**Using tmux**:
```bash
tmux new -s claude-agent
python -m src.main
# Press Ctrl+B, D to detach
```

**Reattach**:
```bash
tmux attach -t claude-agent
```

---

### Option 3: Systemd Service (Linux)

**Use Case**: Production deployment, auto-restart

**Setup**:

Create `/etc/systemd/system/claude-agent.service`:
```ini
[Unit]
Description=Claude Code Auto v4.0
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/claude-code-auto
Environment="PATH=/path/to/claude-code-auto/.venv/bin"
Environment="ANTHROPIC_API_KEY=your-key"
Environment="TAVILY_API_KEY=your-key"
ExecStart=/path/to/.venv/bin/python -m src.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start**:
```bash
sudo systemctl enable claude-agent
sudo systemctl start claude-agent
sudo systemctl status claude-agent
```

**View logs**:
```bash
journalctl -u claude-agent -f
```

---

### Option 4: Docker Container

**Use Case**: Isolated deployment, reproducibility

**Dockerfile**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ANTHROPIC_API_KEY=""
ENV TAVILY_API_KEY=""

CMD ["python", "-m", "src.main"]
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  claude-agent:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
    volumes:
      - ./config.yaml:/app/config.yaml
      - ./demo_act:/app/demo_act
      - ./logs:/app/logs
```

**Run**:
```bash
docker-compose up -d
```

---

### Option 5: Cloud Deployment (AWS/GCP/Azure)

**Use Case**: Scalable, managed infrastructure

**AWS EC2**:
1. Launch EC2 instance (t3.medium or larger)
2. Install Python 3.12
3. Clone repository
4. Set up systemd service (see Option 3)
5. Configure security group (allow SSH only)

**AWS Lambda** (for short tasks):
1. Package code and dependencies
2. Create Lambda function
3. Set environment variables
4. Configure timeout (up to 15 minutes)

**Google Cloud Run**:
1. Containerize application (see Option 4)
2. Push to Google Container Registry
3. Deploy to Cloud Run
4. Set environment variables in console

---

## Monitoring and Maintenance

### Log Locations

| Log Type | Location | Format |
|----------|----------|--------|
| **Application Logs** | `logs/app.log` | Text |
| **Event Logs** | `logs/events/{session_id}_events.jsonl` | JSON Lines |
| **Planner Traces** | `logs/trace/{session_id}_{role}_step1.md` | Markdown |
| **Executor Traces** | `logs/trace/{session_id}_{role}_step2.md` | Markdown |
| **Intervention Logs** | `logs/interventions/{session_id}_interventions.md` | Markdown |
| **Cost Reports** | `logs/cost_report.json` | JSON |
| **Quality Evaluations** | `logs/evaluations/` | JSON |

---

### Health Checks

**Check if agent is running**:
```bash
ps aux | grep "python -m src.main"
```

**Check workflow state**:
```bash
cat demo_act/workflow_state.json | jq
```

**Check recent events**:
```bash
tail -n 20 logs/events/*_events.jsonl | jq
```

---

### Cost Monitoring

**View cost report**:
```bash
cat logs/cost_report.json | jq
```

**Example output**:
```json
{
  "session_id": "abc123",
  "total_tokens": 50000,
  "total_cost_usd": 0.75,
  "breakdown": {
    "claude-sonnet-4-5": {
      "tokens": 40000,
      "cost_usd": 0.60
    },
    "claude-3-5-haiku": {
      "tokens": 10000,
      "cost_usd": 0.15
    }
  }
}
```

---

### Automated Alerts

**Budget Alert Script** (`scripts/check_budget.sh`):
```bash
#!/bin/bash
BUDGET_LIMIT=10.0
CURRENT_COST=$(cat logs/cost_report.json | jq '.total_cost_usd')

if (( $(echo "$CURRENT_COST > $BUDGET_LIMIT" | bc -l) )); then
    echo "WARNING: Budget exceeded! Current: $CURRENT_COST, Limit: $BUDGET_LIMIT"
    # Send email or notification
fi
```

**Run as cron job**:
```bash
# Check every hour
0 * * * * /path/to/scripts/check_budget.sh
```

---

### Backup and Recovery

**Backup Critical Files**:
```bash
# Backup workflow state
cp demo_act/workflow_state.json backups/

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Backup config
cp config.yaml backups/
```

**Recover from Crash**:
```bash
# System auto-loads state from workflow_state.json
# Just restart agent
python -m src.main
```

---

## Troubleshooting

### Issue: Agent Not Starting

**Symptoms**: Command fails immediately

**Possible Causes**:
1. Python version < 3.12
2. Dependencies not installed
3. Config file missing/invalid
4. API keys not set

**Solutions**:
```bash
# Check Python version
python --version  # Should be 3.12+

# Install dependencies
pip install -r requirements.txt

# Validate config
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check API keys
echo $ANTHROPIC_API_KEY
echo $TAVILY_API_KEY
```

---

### Issue: Role Failures

**Symptoms**: Roles fail validation or quality checks

**Possible Causes**:
1. Validation rules too strict
2. Quality threshold too high
3. API rate limits
4. Insufficient context

**Solutions**:
1. Check traces: `logs/trace/{session_id}_{role}_step2.md`
2. Lower quality threshold in `config.yaml`
3. Reduce validation rules in role YAML
4. Increase timeout in `config.yaml`

---

### Issue: High Costs

**Symptoms**: Costs exceed budget quickly

**Possible Causes**:
1. Too many retries
2. LLM called too frequently
3. Semantic validation enabled on all roles
4. Long contexts

**Solutions**:
1. Reduce `max_mission_retries` in `config.yaml`
2. Disable semantic validation on non-critical roles
3. Reduce ReAct loop iterations
4. Enable cost control with auto-stop

---

### Issue: Slow Performance

**Symptoms**: Agent takes too long to complete

**Possible Causes**:
1. Network latency to APIs
2. Too many roles in workflow
3. Large contexts
4. Insufficient system resources

**Solutions**:
1. Use faster API endpoints
2. Reduce number of roles
3. Enable context summarization
4. Increase system resources (CPU/RAM)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-01-03 | Initial deployment guide | Team Mode Documentation Team |

---

*This document is part of the comprehensive documentation suite for Claude Code Auto v4.0. For the complete documentation package, refer to the related documents listed in the Project Context.*
