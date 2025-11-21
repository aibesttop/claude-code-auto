"""
简化版 Web 监控服务器 - 带依赖检查
"""
import sys
import subprocess

# 检查并安装依赖
def check_and_install_dependencies():
    """检查并安装必要的依赖"""
    required = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn[standard]',
        'websockets': 'websockets'
    }

    missing = []

    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if missing:
        print("❌ 缺少以下依赖:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n正在安装...")

        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install',
                '--quiet', '--user'
            ] + missing)
            print("✅ 依赖安装成功！\n")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ 安装失败: {e}")
            print("\n请手动运行以下命令:")
            print(f"    pip install {' '.join(missing)}")
            print("\n或运行:")
            print("    install_web_deps.bat")
            sys.exit(1)


# 检查依赖
check_and_install_dependencies()

# 导入 Web 服务器
try:
    from web_server import app
    import uvicorn

    if __name__ == "__main__":
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

except Exception as e:
    print(f"❌ 启动失败: {e}")
    print("\n请检查:")
    print("  1. 端口 8000 是否被占用")
    print("  2. config.yaml 文件是否存在")
    print("  3. 依赖是否正确安装")
    sys.exit(1)
