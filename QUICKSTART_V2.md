# 🚀 快速开始指南 - v2.0

## 5分钟上手优化版系统

### 步骤 1: 安装依赖

```bash
pip install claude-code-sdk pydantic pyyaml
```

### 步骤 2: 配置任务

编辑 `config.yaml`:

```yaml
task:
  goal: "写一篇关于 AI 的博客"
  initial_prompt: "写一篇关于 AI 发展的博客文章，包含历史、现状和未来展望"
```

### 步骤 3: 运行！

```bash
python main_v2.py
```

就这么简单！系统会：
1. ✅ 自动初始化任务
2. ✅ 启动自主循环
3. ✅ 自动保存状态
4. ✅ 安全退出和恢复

---

## 常用命令

```bash
# 完整运行
python main_v2.py

# 查看当前状态
python main_v2.py --show-status

# 紧急停止
touch .emergency_stop

# 从断点恢复
python main_v2.py

# 查看帮助
python main_v2.py --help
```

---

## 文件位置

- **配置**: `config.yaml`
- **日志**: `logs/main.log`
- **状态**: `demo_act/workflow_state.json`
- **会话**: `demo_act/session_id.txt`

---

## 安全保护

系统已内置多重保护：

- ✅ 最大50次循环
- ✅ 最长8小时运行
- ✅ 紧急停止机制
- ✅ 自动异常恢复
- ✅ 断点续传

放心使用！

---

更多详细信息请查看 [UPGRADE_GUIDE.md](UPGRADE_GUIDE.md)
