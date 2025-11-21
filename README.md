# Claude Code Autonomous Workflow System

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Claude SDK](https://img.shields.io/badge/Claude-SDK-orange.svg)](https://docs.anthropic.com/claude/docs)
[![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)](https://github.com/yourusername/claude-autonomous-workflow)

**English** | [中文](README_CN.md)

## Why repeat the same input in the chat box?

Let Claude Code work 24/7 infinitely, making autonomous decisions for next steps!

## 🚀 Features

- **Autonomous Decision Making**: AI analyzes progress and decides next actions
- **Session Persistence**: Maintains conversation continuity across sessions  
- **Mirror Analysis**: Analyzes task progress in isolated environments
- **Zero Human Intervention**: Fully autonomous after startup
- **24/7 Operation**: Runs continuously until task completion

## 📋 System Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Step 1    │ →   │   Step 3    │ →   │   Step 2    │
│ Initialize  │    │  Main Loop  │    │  Decision   │
│   Session   │    │             │    │   Engine    │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 🏗️ Workflow

1. **Step 1**: Initialize task and establish session
2. **Step 3**: Enter autonomous loop
   - Call Step 2 for decision making
   - Execute decisions
   - Save session state
3. **Step 2**: Intelligent analysis
   - Create working directory mirror
   - Analyze task progress
   - Generate JSON decisions

## 💡 Example Workflow

**Goal**: "Write a Python program to design an addition"

1. **Round 1**: Generate design document
2. **Round 2**: Write implementation code  
3. **Round 3**: Add test cases
4. **Round 4**: Review and optimize
5. **Round 5**: Final validation → Task Complete

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/yourusername/claude-autonomous-workflow.git
cd claude-autonomous-workflow

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

```bash
# Start autonomous workflow
python main.py
```

## ⚙️ Configuration

Edit `main.py` to customize:
- `goal`: Task objective
- `cwd_dir`: Working directory
- Mirror directory settings

## 📖 Documentation

- [English Documentation](README_EN.md)
- [中文文档](README_CN.md)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏷️ Keywords

`claude` `autonomous` `workflow` `automation` `ai` `decision-making` `session-persistence` `python` `sdk` `24/7`