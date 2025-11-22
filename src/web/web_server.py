"""
Web 监控服务器
提供 RESTful API 和 WebSocket 实时推送
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime
import logging

from src.config import get_config
from src.utils.state_manager import StateManager, WorkflowStatus
from src.utils.logger import get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print("Web 监控服务器启动")
    print("访问 http://localhost:8000 查看监控面板")
    
    # 启动后台任务
    broadcast_task = asyncio.create_task(broadcast_status_updates())
    
    yield
    
    # 关闭时执行
    print("Web 监控服务器关闭")
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Claude Workflow Monitor", version="2.0", lifespan=lifespan)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 连接管理
class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """接受新连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """断开连接"""
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)


manager = ConnectionManager()


# ============ API 端点 ============

@app.get("/")
async def root():
    """返回监控面板 HTML"""
    html_path = Path(__file__).parent / "templates" / "dashboard.html"
    if html_path.exists():
        return FileResponse(html_path)
    return {"message": "Dashboard not found. Please create templates/dashboard.html"}


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0"
    }


@app.get("/api/config")
async def get_current_config():
    """获取当前配置"""
    try:
        config = get_config()
        return {
            "task": {
                "goal": config.task.goal,
                "initial_prompt": config.task.initial_prompt
            },
            "safety": {
                "max_iterations": config.safety.max_iterations,
                "max_duration_hours": config.safety.max_duration_hours
            },
            "directories": {
                "work_dir": config.directories.work_dir,
                "mirror_dir": config.directories.mirror_dir
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status():
    """获取当前工作流状态"""
    try:
        config = get_config()
        state_file = config.get_state_file_path()

        if not state_file.exists():
            return {
                "exists": False,
                "message": "工作流尚未启动"
            }

        state_manager = StateManager(state_file)
        state = state_manager.get_state()

        return {
            "exists": True,
            "session_id": state.session_id,
            "goal": state.goal,
            "status": state.status.value,
            "current_iteration": state.current_iteration,
            "max_iterations": state.max_iterations,
            "progress_percentage": state.get_progress_percentage(),
            "start_time": state.start_time,
            "last_update": state.last_update,
            "total_duration_seconds": state.total_duration_seconds,
            "successful_iterations": state.successful_iterations,
            "failed_iterations": state.failed_iterations,
            "success_rate": state.get_success_rate(),
            "average_iteration_time": state.get_average_iteration_time(),
            "error_count": state.error_count,
            "last_error": state.last_error
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history")
async def get_history(limit: int = 10):
    """获取执行历史"""
    try:
        config = get_config()
        state_file = config.get_state_file_path()

        if not state_file.exists():
            return {"history": []}

        state_manager = StateManager(state_file)
        state = state_manager.get_state()

        # 获取最近的历史记录
        history = state.history[-limit:] if len(state.history) > limit else state.history

        return {
            "total_count": len(state.history),
            "limit": limit,
            "history": [record.to_dict() for record in history]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
async def get_logs(lines: int = 50, log_type: str = "main"):
    """获取日志内容"""
    try:
        config = get_config()
        log_dir = Path(config.directories.logs_dir)

        if log_type == "error":
            log_file = log_dir / "main_error.log"
        else:
            log_file = log_dir / "main.log"

        if not log_file.exists():
            return {"logs": [], "message": "日志文件不存在"}

        # 读取最后 N 行
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "log_type": log_type,
            "lines": lines,
            "total_lines": len(all_lines),
            "logs": [line.strip() for line in recent_lines]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/control/emergency-stop")
async def emergency_stop():
    """触发紧急停止"""
    try:
        config = get_config()
        stop_file = config.get_emergency_stop_file_path()

        # 创建停止文件
        stop_file.touch()

        # 广播消息
        await manager.broadcast({
            "type": "control",
            "action": "emergency_stop",
            "timestamp": datetime.now().isoformat(),
            "message": "紧急停止信号已发送"
        })

        return {
            "success": True,
            "message": "紧急停止信号已发送，系统将在下一轮迭代前安全退出"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/control/emergency-stop")
async def cancel_emergency_stop():
    """取消紧急停止"""
    try:
        config = get_config()
        stop_file = config.get_emergency_stop_file_path()

        if stop_file.exists():
            stop_file.unlink()
            return {
                "success": True,
                "message": "紧急停止信号已取消"
            }
        else:
            return {
                "success": False,
                "message": "没有活动的紧急停止信号"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_statistics():
    """获取统计信息"""
    try:
        config = get_config()
        state_file = config.get_state_file_path()

        if not state_file.exists():
            return {"message": "工作流尚未启动"}

        state_manager = StateManager(state_file)
        state = state_manager.get_state()

        # 计算各种统计数据
        iteration_times = [record.duration_seconds for record in state.history]

        stats = {
            "overview": {
                "total_iterations": len(state.history),
                "successful": state.successful_iterations,
                "failed": state.failed_iterations,
                "success_rate": state.get_success_rate()
            },
            "timing": {
                "total_duration_seconds": state.total_duration_seconds,
                "average_iteration_time": state.get_average_iteration_time(),
                "min_iteration_time": min(iteration_times) if iteration_times else 0,
                "max_iteration_time": max(iteration_times) if iteration_times else 0
            },
            "progress": {
                "current_iteration": state.current_iteration,
                "max_iterations": state.max_iterations,
                "progress_percentage": state.get_progress_percentage(),
                "estimated_remaining_time": (
                    state.get_average_iteration_time() *
                    (state.max_iterations - state.current_iteration)
                ) if state.current_iteration > 0 else 0
            }
        }

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/roles")
async def get_roles():
    """获取所有角色状态（用于可视化）"""
    try:
        config = get_config()
        state_file = config.get_state_file_path()

        if not state_file.exists():
            return {
                "exists": False,
                "roles": [],
                "message": "工作流尚未启动"
            }

        state_manager = StateManager(state_file)
        state = state_manager.get_state()

        return {
            "exists": True,
            "mode": state.mode,
            "current_role": state.current_role,
            "roles": [role.to_dict() for role in state.roles]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/missions")
async def get_missions():
    """获取所有任务状态（用于可视化）"""
    try:
        config = get_config()
        state_file = config.get_state_file_path()

        if not state_file.exists():
            return {
                "exists": False,
                "missions": [],
                "message": "工作流尚未启动"
            }

        state_manager = StateManager(state_file)
        state = state_manager.get_state()

        return {
            "exists": True,
            "mode": state.mode,
            "current_mission": state.current_mission,
            "missions": [mission.to_dict() for mission in state.missions],
            "goal": state.goal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/graph")
async def get_graph_data():
    """获取图数据（nodes和edges）用于React Flow可视化"""
    try:
        config = get_config()
        state_file = config.get_state_file_path()

        if not state_file.exists():
            return {
                "exists": False,
                "nodes": [],
                "edges": [],
                "message": "工作流尚未启动"
            }

        state_manager = StateManager(state_file)
        state = state_manager.get_state()

        nodes = []
        edges = []

        # 根据模式构建不同的图结构
        if state.mode == "leader":
            # Leader模式：显示任务层级和角色
            # 1. 添加目标节点
            nodes.append({
                "id": "goal",
                "type": "goal",
                "data": {
                    "label": state.goal[:50] + "..." if len(state.goal) > 50 else state.goal,
                    "status": state.status.value
                },
                "position": {"x": 400, "y": 50}
            })

            # 2. 添加任务节点
            y_offset = 200
            for i, mission in enumerate(state.missions):
                mission_node = {
                    "id": mission.id,
                    "type": "mission",
                    "data": {
                        "label": f"{mission.type}\n{mission.goal[:30]}...",
                        "status": mission.status.value,
                        "assigned_role": mission.assigned_role,
                        "iterations": mission.iteration_count
                    },
                    "position": {"x": 150 + i * 250, "y": y_offset}
                }
                nodes.append(mission_node)

                # 连接到目标
                edges.append({
                    "id": f"goal-{mission.id}",
                    "source": "goal",
                    "target": mission.id,
                    "animated": mission.status.value == "in_progress"
                })

                # 处理依赖
                for dep_id in mission.dependencies:
                    edges.append({
                        "id": f"{dep_id}-{mission.id}",
                        "source": dep_id,
                        "target": mission.id,
                        "type": "smoothstep"
                    })

            # 3. 添加角色节点
            y_offset = 400
            for i, role in enumerate(state.roles):
                role_node = {
                    "id": f"role-{role.name}",
                    "type": "role",
                    "data": {
                        "label": role.name,
                        "status": role.status.value,
                        "category": role.category,
                        "iterations": role.iterations
                    },
                    "position": {"x": 150 + i * 200, "y": y_offset}
                }
                nodes.append(role_node)

                # 连接角色到任务
                for mission in state.missions:
                    if mission.assigned_role == role.name:
                        edges.append({
                            "id": f"{mission.id}-role-{role.name}",
                            "source": mission.id,
                            "target": f"role-{role.name}",
                            "label": "assigned",
                            "animated": role.status.value == "in_progress"
                        })

        elif state.mode == "team":
            # Team模式：显示角色序列
            # 1. 添加目标节点
            nodes.append({
                "id": "goal",
                "type": "goal",
                "data": {
                    "label": state.goal[:50] + "..." if len(state.goal) > 50 else state.goal,
                    "status": state.status.value
                },
                "position": {"x": 50, "y": 50}
            })

            # 2. 添加角色节点（线性流程）
            prev_id = "goal"
            for i, role in enumerate(state.roles):
                role_node = {
                    "id": f"role-{role.name}",
                    "type": "role",
                    "data": {
                        "label": role.name,
                        "status": role.status.value,
                        "category": role.category,
                        "iterations": role.iterations,
                        "outputs": len(role.outputs)
                    },
                    "position": {"x": 50 + i * 200, "y": 200}
                }
                nodes.append(role_node)

                # 连接到前一个节点
                edges.append({
                    "id": f"{prev_id}-role-{role.name}",
                    "source": prev_id,
                    "target": f"role-{role.name}",
                    "animated": role.status.value == "in_progress"
                })
                prev_id = f"role-{role.name}"

        return {
            "exists": True,
            "mode": state.mode,
            "nodes": nodes,
            "edges": edges,
            "session_id": state.session_id,
            "goal": state.goal
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ WebSocket 端点 ============

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接，用于实时推送状态更新"""
    await manager.connect(websocket)

    try:
        # 发送初始状态
        try:
            config = get_config()
            state_file = config.get_state_file_path()

            if state_file.exists():
                state_manager = StateManager(state_file)
                state = state_manager.get_state()

                await websocket.send_json({
                    "type": "initial_state",
                    "data": {
                        "session_id": state.session_id,
                        "status": state.status.value,
                        "current_iteration": state.current_iteration,
                        "progress": state.get_progress_percentage()
                    }
                })
        except:
            pass

        # 保持连接并监听状态变化
        while True:
            # 接收客户端消息（心跳）
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)

                # 处理客户端请求
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data == "status":
                    # 发送最新状态
                    try:
                        config = get_config()
                        state_file = config.get_state_file_path()

                        if state_file.exists():
                            state_manager = StateManager(state_file)
                            state = state_manager.get_state()

                            await websocket.send_json({
                                "type": "status_update",
                                "data": {
                                    "current_iteration": state.current_iteration,
                                    "status": state.status.value,
                                    "progress": state.get_progress_percentage()
                                }
                            })
                    except:
                        pass

            except asyncio.TimeoutError:
                # 超时，发送心跳
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# ============ 后台任务 ============

async def broadcast_status_updates():
    """后台任务：定期广播状态更新"""
    while True:
        try:
            await asyncio.sleep(2)  # 每2秒更新一次

            config = get_config()
            state_file = config.get_state_file_path()

            if state_file.exists():
                state_manager = StateManager(state_file)
                state = state_manager.get_state()

                # 广播基础状态
                await manager.broadcast({
                    "type": "status_update",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "current_iteration": state.current_iteration,
                        "status": state.status.value,
                        "progress": state.get_progress_percentage(),
                        "last_update": state.last_update,
                        "mode": state.mode,
                        "current_role": state.current_role,
                        "current_mission": state.current_mission
                    }
                })

                # 广播角色更新（如果有）
                if state.roles:
                    await manager.broadcast({
                        "type": "roles_update",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "roles": [role.to_dict() for role in state.roles],
                            "current_role": state.current_role
                        }
                    })

                # 广播任务更新（如果有）
                if state.missions:
                    await manager.broadcast({
                        "type": "missions_update",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "missions": [mission.to_dict() for mission in state.missions],
                            "current_mission": state.current_mission
                        }
                    })
        except asyncio.CancelledError:
            break
        except Exception as e:
            # 忽略错误，继续运行
            pass


if __name__ == "__main__":
    import uvicorn

    print("""
╔═══════════════════════════════════════════════════════════╗
║         Claude Code 工作流监控服务器 v2.0                 ║
╚═══════════════════════════════════════════════════════════╝

启动中...

访问地址:
  - 监控面板: http://localhost:8000
  - API 文档: http://localhost:8000/docs
  - 健康检查: http://localhost:8000/api/health

按 Ctrl+C 停止服务器
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
