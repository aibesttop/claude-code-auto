@echo off
echo ================================================
echo 安装 Web 监控依赖
echo ================================================
echo.

echo 正在安装 FastAPI...
python -m pip install --upgrade fastapi --user

echo.
echo 正在安装 Uvicorn...
python -m pip install --upgrade "uvicorn[standard]" --user

echo.
echo 正在安装 Websockets...
python -m pip install --upgrade websockets --user

echo.
echo ================================================
echo 验证安装
echo ================================================
python -c "import fastapi; print('✅ FastAPI 已安装')"
python -c "import uvicorn; print('✅ Uvicorn 已安装')"
python -c "import websockets; print('✅ Websockets 已安装')"

echo.
echo ================================================
echo 安装完成！
echo ================================================
pause
