@echo off
echo ================================================
echo Claude Code Web 监控服务器
echo ================================================
echo.

REM 检查依赖
python -c "import fastapi; import uvicorn" 2>nul
if errorlevel 1 (
    echo ❌ 缺少依赖，正在安装...
    echo.
    python -m pip install --quiet fastapi "uvicorn[standard]" websockets --user
    echo.
)

echo ✅ 依赖检查完成
echo.
echo 启动 Web 监控服务器...
echo 访问: http://localhost:8000
echo.
echo 按 Ctrl+C 停止服务器
echo ================================================
echo.

python web_server.py

pause
