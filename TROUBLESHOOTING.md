# 🔧 故障排除指南

## Web 监控服务器启动失败

### 问题1: 缺少依赖

**症状:**
```
❌ Web 监控服务器启动失败
ModuleNotFoundError: No module named 'fastapi'
```

**解决方案:**

#### 方法1: 使用批处理脚本（推荐 - Windows）
```bash
install_web_deps.bat
```

#### 方法2: 使用简化版服务器（自动安装）
```bash
python web_server_simple.py
```

#### 方法3: 手动安装
```bash
pip install fastapi "uvicorn[standard]" websockets
```

#### 方法4: 用户模式安装（避免权限问题）
```bash
pip install --user fastapi "uvicorn[standard]" websockets
```

#### 方法5: 使用管理员权限
```bash
# 右键"命令提示符" -> "以管理员身份运行"
pip install fastapi "uvicorn[standard]" websockets
```

---

### 问题2: 端口被占用

**症状:**
```
Error: Address already in use
OSError: [WinError 10048] 通常每个套接字地址只允许使用一次
```

**解决方案:**

#### 查找占用端口的进程
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>
```

#### 或修改端口
编辑 `web_server.py` 最后一行:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # 改为 8001
```

---

### 问题3: 配置文件不存在

**症状:**
```
FileNotFoundError: 配置文件不存在: config.yaml
```

**解决方案:**

确保 `config.yaml` 文件存在于项目根目录。如果不存在，请参考 `UPGRADE_GUIDE.md` 创建。

---

### 问题4: 权限错误（Windows）

**症状:**
```
ERROR: Could not install packages due to an OSError
```

**解决方案:**

#### 方法1: 使用 --user 标志
```bash
pip install --user fastapi uvicorn websockets
```

#### 方法2: 使用虚拟环境
```bash
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn websockets
python web_server.py
```

#### 方法3: 关闭其他 Python 进程
关闭所有正在运行的 Python 进程，然后重新安装。

---

## 快速启动指南

### 方案A: 最简单（推荐新手）

```bash
# 1. 运行批处理脚本
start_monitor.bat
```

### 方案B: Python 脚本

```bash
# 1. 使用简化版（自动安装依赖）
python web_server_simple.py
```

### 方案C: 标准流程

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务器
python web_server.py
```

---

## 验证安装

运行以下命令检查依赖:

```bash
python -c "import fastapi; import uvicorn; import websockets; print('✅ 所有依赖已安装')"
```

如果成功，应该看到:
```
✅ 所有依赖已安装
```

---

## 常见问题 FAQ

### Q1: 为什么不使用 run_with_monitor.py？

`run_with_monitor.py` 同时启动工作流和监控服务器，如果只想查看监控，使用:

```bash
python web_server_simple.py
```

或

```bash
python run_with_monitor.py --web-only
```

### Q2: 如何只启动监控（不运行工作流）？

```bash
python web_server_simple.py
```

### Q3: 监控界面显示空白？

确保至少运行过一次工作流，生成了状态文件:

```bash
python main_v2.py
```

### Q4: 无法访问 http://localhost:8000？

1. 检查服务器是否启动成功
2. 尝试 http://127.0.0.1:8000
3. 检查防火墙设置
4. 尝试其他端口（修改 web_server.py）

---

## 完整安装检查清单

- [ ] Python 3.8+ 已安装
- [ ] pip 可用
- [ ] config.yaml 存在
- [ ] 依赖已安装（fastapi, uvicorn, websockets）
- [ ] 端口 8000 未被占用
- [ ] 防火墙允许访问

---

## 获取帮助

如果以上方法都无效，请：

1. 运行诊断命令:
```bash
python -c "import sys; print(f'Python: {sys.version}'); import platform; print(f'OS: {platform.system()}')"
```

2. 收集错误信息（完整的错误堆栈）

3. 提交 Issue 并附上:
   - Python 版本
   - 操作系统
   - 完整错误信息
   - 已尝试的解决方案

---

**常用命令速查**

| 操作 | 命令 |
|------|------|
| 安装依赖 | `pip install -r requirements.txt` |
| 启动监控（简化） | `python web_server_simple.py` |
| 启动监控（标准） | `python web_server.py` |
| 启动工作流+监控 | `python run_with_monitor.py` |
| 只启动监控 | `python run_with_monitor.py --web-only` |
| 批处理安装（Win） | `install_web_deps.bat` |
| 批处理启动（Win） | `start_monitor.bat` |

---

祝你使用愉快！🚀
