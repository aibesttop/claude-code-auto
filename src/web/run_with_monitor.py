"""
带监控的工作流启动器
同时启动工作流程和 Web 监控服务器
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path
import signal


class WorkflowWithMonitor:
    """工作流 + 监控服务器管理器"""

    def __init__(self):
        self.web_process = None
        self.workflow_task = None
        self.running = True

    def start_web_server(self):
        """启动 Web 监控服务器"""
        print("🌐 启动 Web 监控服务器...")

        # 启动 uvicorn 服务器
        self.web_process = subprocess.Popen(
            [sys.executable, "web_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 等待服务器启动
        time.sleep(2)

        if self.web_process.poll() is None:
            print("✅ Web 监控服务器已启动")
            print("📊 访问 http://localhost:8000 查看监控面板")
        else:
            print("❌ Web 监控服务器启动失败")
            return False

        return True

    async def run_workflow(self, skip_init: bool = False, resume: bool = True):
        """运行工作流"""
        print("\n🚀 启动工作流程...")

        from main_v2 import main

        try:
            success = await main(
                config_path="config.yaml",
                skip_init=skip_init,
                resume=resume
            )
            return success
        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")
            return False

    def stop_web_server(self):
        """停止 Web 监控服务器"""
        if self.web_process:
            print("\n🛑 停止 Web 监控服务器...")
            self.web_process.terminate()
            try:
                self.web_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.web_process.kill()
            print("✅ Web 监控服务器已停止")

    async def run(self, skip_init: bool = False, resume: bool = True):
        """主运行方法"""
        print("""
╔═══════════════════════════════════════════════════════════════╗
║     Claude Code 自主工作流系统 - 带 Web 监控 v2.0            ║
╚═══════════════════════════════════════════════════════════════╝
        """)

        # 启动 Web 服务器
        if not self.start_web_server():
            return False

        print("\n" + "=" * 70)
        print("提示:")
        print("  - 监控面板: http://localhost:8000")
        print("  - 按 Ctrl+C 安全退出")
        print("  - Web 服务器将在后台持续运行")
        print("=" * 70 + "\n")

        # 等待用户准备
        await asyncio.sleep(1)

        # 运行工作流
        try:
            success = await self.run_workflow(skip_init, resume)

            if success:
                print("\n🎉 工作流执行完成！")
            else:
                print("\n⚠️  工作流未完成")

            print("\n💡 Web 监控服务器仍在运行")
            print("   访问 http://localhost:8000 查看详细信息")
            print("   按 Ctrl+C 停止服务器\n")

            # 保持 Web 服务器运行
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⚠️  收到停止信号...")
            self.running = False

        finally:
            self.stop_web_server()

        return True


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Code 工作流 + Web 监控")
    parser.add_argument(
        "--skip-init",
        action="store_true",
        help="跳过 Step1 初始化"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="不恢复之前的状态"
    )
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="只启动 Web 监控服务器（不运行工作流）"
    )

    args = parser.parse_args()

    if args.web_only:
        # 只启动 Web 服务器
        print("🌐 只启动 Web 监控服务器模式\n")
        subprocess.run([sys.executable, "web_server.py"])
        return

    # 启动工作流 + 监控
    manager = WorkflowWithMonitor()

    # 注册信号处理
    def signal_handler(signum, frame):
        manager.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    await manager.run(
        skip_init=args.skip_init,
        resume=not args.no_resume
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")
