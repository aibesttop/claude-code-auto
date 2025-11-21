# 🌐 Web 监控面板 - 快速开始

## ⚡ 3分钟启动

### 1. 安装依赖

```bash
pip install fastapi uvicorn websockets
```

### 2. 一键启动

```bash
python run_with_monitor.py
```

### 3. 打开浏览器

访问: **http://localhost:8000**

完成！🎉

---

## 📊 功能一览

<table>
<tr>
<td width="50%">

### 实时监控
- ✅ 进度可视化
- ✅ 状态实时更新
- ✅ 日志流
- ✅ 执行历史

</td>
<td width="50%">

### 控制操作
- 🔄 刷新数据
- 🛑 紧急停止
- 📊 统计分析
- 📝 日志查看

</td>
</tr>
</table>

---

## 🎯 使用场景

| 场景 | 命令 |
|------|------|
| **完整运行** | `python run_with_monitor.py` |
| **仅监控** | `python run_with_monitor.py --web-only` |
| **跳过初始化** | `python run_with_monitor.py --skip-init` |

---

## 🌟 界面预览

```
╔═══════════════════════════════════════════╗
║  🤖 Claude Workflow Monitor  [运行中]    ║
╠═══════════════════════════════════════════╣
║  进度: ████████░░░░░░░░░░ 40%            ║
║  当前: 第 20/50 轮                        ║
║  成功率: 85%                              ║
╠═══════════════════════════════════════════╣
║  📜 实时日志                              ║
║  ✅ 第 20 轮 - 成功 (45.2s)              ║
║  ✅ 第 19 轮 - 成功 (38.1s)              ║
║  ❌ 第 18 轮 - 失败 (12.3s)              ║
╚═══════════════════════════════════════════╝
```

---

## 🔧 端口配置

默认端口: `8000`

修改端口:
```python
# web_server.py 最后一行
uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

## 📚 详细文档

查看完整文档: [WEB_MONITOR_GUIDE.md](WEB_MONITOR_GUIDE.md)

- API 端点文档
- WebSocket 使用
- 高级用法
- 故障排除

---

## ⭐ 核心功能

### 1. 实时状态监控

监控面板每2秒自动更新，显示：
- 当前迭代进度
- 成功/失败次数
- 平均执行时间
- 工作流状态

### 2. WebSocket 推送

建立 WebSocket 连接后，所有状态变更实时推送到浏览器。

### 3. RESTful API

完整的 REST API，可集成到其他系统：

```bash
# 获取状态
curl http://localhost:8000/api/status

# 查看日志
curl http://localhost:8000/api/logs

# 紧急停止
curl -X POST http://localhost:8000/api/control/emergency-stop
```

### 4. 控制操作

通过 Web 界面控制工作流：
- 刷新数据
- 紧急停止
- 查看完整日志

---

## 💡 提示

- 监控面板可在工作流运行前后随时打开
- 支持多个浏览器同时查看
- WebSocket 断开会自动重连
- 所有操作都是安全的，不会影响工作流执行

---

**快速访问**: http://localhost:8000
**API 文档**: http://localhost:8000/docs
**健康检查**: http://localhost:8000/api/health

---

享受实时监控带来的便利！🚀
