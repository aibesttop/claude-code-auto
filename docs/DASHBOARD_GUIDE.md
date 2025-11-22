# 实时可视化仪表盘使用指南

## 📊 功能概述

Claude Code Auto 现在支持实时可视化仪表盘，可以：

- **实时监控**: WebSocket自动推送状态更新
- **节点图可视化**: 使用vis.js展示任务、团队成员和依赖关系
- **多模式支持**: 支持Team模式和Leader模式的不同可视化
- **状态追踪**: 查看每个角色和任务的执行状态、进度和结果

## 🚀 快速开始

### 1. 启动仪表盘服务器

```bash
python start_dashboard.py
```

服务器将在 `http://localhost:8000` 启动

### 2. 访问仪表盘

在浏览器中打开：`http://localhost:8000`

### 3. 运行任务

在另一个终端中运行你的任务：

```bash
# Team模式示例
python -m src.main
```

仪表盘会自动显示实时进度！

## 📖 界面说明

### 主要区域

1. **顶部状态栏**
   - 工作流状态（初始化/运行中/已完成/失败）
   - 执行模式（Team/Leader/Original）
   - 进度百分比
   - 迭代计数
   - WebSocket连接状态

2. **中心节点图**
   - 蓝色圆形：目标节点
   - 蓝色方形：任务节点（Leader模式）
   - 绿色方形：角色节点
   - 橙色边框：正在执行
   - 绿色边框：已完成
   - 红色边框：失败

3. **右侧面板**
   - **团队成员列表**: 显示所有角色及其状态
   - **任务列表**: 显示所有子任务（Leader模式）

## 🎨 节点图说明

### Team模式

```
目标 → 角色1 → 角色2 → 角色3 → ...
```

线性流程，角色按顺序执行

### Leader模式

```
         目标
        / | \
       /  |  \
   任务1 任务2 任务3
     |    |    |
   角色A 角色B 角色C
```

层级结构，显示任务分解和角色分配

## 🔌 API端点

仪表盘提供以下REST API：

- `GET /api/status` - 获取工作流状态
- `GET /api/roles` - 获取所有角色状态
- `GET /api/missions` - 获取所有任务状态（Leader模式）
- `GET /api/graph` - 获取图数据（节点和边）
- `GET /api/history` - 获取执行历史
- `GET /api/stats` - 获取统计信息
- `GET /api/logs` - 获取日志
- `POST /api/control/emergency-stop` - 触发紧急停止

WebSocket端点：

- `ws://localhost:8000/ws` - 实时状态推送

## 💡 使用技巧

### 1. 实时监控长时间任务

仪表盘特别适合监控长时间运行的任务：

```bash
# 终端1：启动仪表盘
python start_dashboard.py

# 终端2：运行长时间任务
python -m src.main
```

### 2. 多客户端同时监控

多个浏览器窗口可以同时连接到仪表盘，所有窗口会同步更新。

### 3. 网络访问

如果需要从其他设备访问仪表盘：

```python
# 修改 start_dashboard.py 中的 host
host="0.0.0.0"  # 允许外部访问
```

然后通过 `http://<your-ip>:8000` 访问

### 4. 调试和日志

仪表盘会在终端输出详细的请求日志，帮助调试问题。

## 🔧 技术架构

### 后端

- **FastAPI**: Web框架
- **WebSocket**: 实时双向通信
- **StateManager**: 状态持久化和追踪
- **uvicorn**: ASGI服务器

### 前端

- **vis.js**: 节点图可视化库
- **原生JavaScript**: 无需额外依赖
- **WebSocket Client**: 实时数据接收

### 数据流

```
TeamOrchestrator/LeaderAgent
         ↓
    StateManager (更新状态)
         ↓
    state.json (持久化)
         ↓
    WebServer (读取状态)
         ↓
    WebSocket/REST API
         ↓
    浏览器 (实时显示)
```

## 🛠️ 高级配置

### 修改更新频率

编辑 `src/web/web_server.py`:

```python
async def broadcast_status_updates():
    while True:
        await asyncio.sleep(2)  # 改为你想要的秒数
        ...
```

### 自定义节点颜色

编辑 `src/web/templates/dashboard.html` 中的CSS样式。

### 添加自定义面板

在dashboard.html中添加新的 `.panel` div即可。

## ❓ 常见问题

### Q: 仪表盘显示"连接断开"

A: 检查Web服务器是否正在运行。重启 `start_dashboard.py`。

### Q: 节点图不更新

A: 检查浏览器控制台是否有JavaScript错误。刷新页面重新连接WebSocket。

### Q: 看不到任务或角色

A: 确保你的任务正在使用Team模式或Leader模式。原始模式不会显示角色信息。

### Q: 如何在生产环境部署

A: 考虑使用nginx反向代理，并配置HTTPS：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 📝 开发说明

### 扩展仪表盘

要添加新功能：

1. **后端**: 在 `src/web/web_server.py` 添加新的API端点
2. **前端**: 在 `src/web/templates/dashboard.html` 添加UI和JavaScript
3. **状态**: 在 `src/utils/state_manager.py` 扩展数据模型

### 集成到自己的项目

核心组件：

- `StateManager`: 状态追踪
- `RoleState/MissionState`: 数据模型
- `TeamOrchestrator`: 状态更新钩子

参考 `team_orchestrator.py` 中的集成方式。

## 🎯 未来改进

计划中的功能：

- [ ] React前端重构（使用React Flow）
- [ ] 更多图表和统计信息
- [ ] 执行回放功能
- [ ] 导出报告（PDF/HTML）
- [ ] 性能指标和成本追踪可视化
- [ ] 移动端适配

## 📞 反馈和支持

如有问题或建议，请在GitHub Issues中反馈。
