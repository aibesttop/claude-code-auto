"""
预算监控工具 (Budget Monitoring Tool)

提供实时预算监控和可视化报告

用法:
    python budget_monitor.py status              # 查看当前预算状态
    python budget_monitor.py report              # 生成详细报告
    python budget_monitor.py watch               # 实时监控（每5秒刷新）
    python budget_monitor.py reset               # 重置日预算
    python budget_monitor.py history [days]      # 查看历史数据

作者: Claude + Human
版本: 1.0.0
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime, date, timedelta
import json
from typing import List, Dict
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.layout import Layout
from rich import box

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from core.budget_manager import BudgetManager


console = Console()


def create_budget_status_panel(manager: BudgetManager) -> Panel:
    """创建预算状态面板"""
    status = manager.get_budget_status()

    # 状态颜色
    status_colors = {
        "healthy": "green",
        "caution": "yellow",
        "warning": "orange",
        "critical": "red"
    }
    color = status_colors.get(status["status"], "white")

    # 构建状态文本
    lines = []
    lines.append(f"[bold]Status:[/bold] [{color}]{status['status'].upper()}[/{color}]")
    lines.append(f"[bold]Budget:[/bold] ${status['current_usage']:.4f} / ${status['budget_limit']:.2f}")
    lines.append(f"[bold]Usage:[/bold] {status['usage_percentage']:.1f}%")
    lines.append(f"[bold]Remaining:[/bold] ${status['remaining_budget']:.4f}")

    # 进度条
    percentage = status['usage_percentage']
    bar_length = 40
    filled = int(bar_length * (percentage / 100))
    bar = "█" * filled + "░" * (bar_length - filled)
    lines.append(f"\n[{color}]{bar}[/{color}] {percentage:.1f}%")

    content = "\n".join(lines)
    return Panel(content, title="💰 Budget Status", border_style=color)


def create_agent_usage_table(manager: BudgetManager) -> Table:
    """创建Agent使用情况表格"""
    status = manager.get_budget_status()

    table = Table(title="🤖 Agent Budget Breakdown", box=box.ROUNDED)
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Used", justify="right", style="green")
    table.add_column("Allocated", justify="right", style="blue")
    table.add_column("Usage %", justify="right", style="yellow")

    for agent, usage in status["agent_usage"].items():
        allocated = manager.daily_budget.total * manager.agent_budget_ratios.get(agent, 0.0)
        usage_pct = (usage / allocated * 100) if allocated > 0 else 0

        # 根据使用率设置颜色
        if usage_pct > 100:
            usage_style = "red"
        elif usage_pct > 80:
            usage_style = "yellow"
        else:
            usage_style = "green"

        table.add_row(
            agent.capitalize(),
            f"${usage:.4f}",
            f"${allocated:.4f}",
            f"[{usage_style}]{usage_pct:.1f}%[/{usage_style}]"
        )

    return table


def create_operation_breakdown_table(manager: BudgetManager) -> Table:
    """创建操作分解表格"""
    report = manager.generate_report()

    table = Table(title="⚙️ Operation Breakdown", box=box.ROUNDED)
    table.add_column("Operation", style="cyan")
    table.add_column("Count", justify="right", style="magenta")
    table.add_column("Total Cost", justify="right", style="green")
    table.add_column("Avg Cost", justify="right", style="yellow")

    for operation, stats in report.get("operation_breakdown", {}).items():
        count = stats["count"]
        total_cost = stats["cost"]
        avg_cost = total_cost / count if count > 0 else 0

        table.add_row(
            operation,
            str(count),
            f"${total_cost:.4f}",
            f"${avg_cost:.4f}"
        )

    return table


def show_status():
    """显示当前预算状态"""
    try:
        config = get_config()
        manager = BudgetManager(
            daily_budget=config.budget.daily_budget,
            weekly_budget=config.budget.weekly_budget,
            monthly_budget=config.budget.monthly_budget,
            agent_budget_ratios=config.budget.agent_ratios,
            enable_auto_fallback=config.budget.enable_auto_fallback,
            storage_dir=config.budget.storage_dir
        )

        console.print("\n")
        console.print(create_budget_status_panel(manager))
        console.print("\n")
        console.print(create_agent_usage_table(manager))
        console.print("\n")

    except Exception as e:
        console.print(f"[red]Error loading budget data: {e}[/red]")


def show_report():
    """显示详细报告"""
    try:
        config = get_config()
        manager = BudgetManager(
            daily_budget=config.budget.daily_budget,
            weekly_budget=config.budget.weekly_budget,
            monthly_budget=config.budget.monthly_budget,
            agent_budget_ratios=config.budget.agent_ratios,
            enable_auto_fallback=config.budget.enable_auto_fallback,
            storage_dir=config.budget.storage_dir
        )

        report = manager.generate_report()

        console.print("\n")
        console.print(Panel.fit(
            f"[bold]Period:[/bold] {report['period']}\n"
            f"[bold]Total Cost:[/bold] ${report['total_cost']:.4f}\n"
            f"[bold]Budget Limit:[/bold] ${report['budget_limit']:.2f}\n"
            f"[bold]Usage:[/bold] {report['usage_percentage']:.2f}%\n"
            f"[bold]Remaining:[/bold] ${report['remaining_budget']:.4f}\n"
            f"[bold]Total Operations:[/bold] {report['total_operations']}\n"
            f"[bold]Fallback Count:[/bold] {report['fallback_count']}",
            title="📊 Budget Report",
            border_style="blue"
        ))

        console.print("\n")
        console.print(create_agent_usage_table(manager))
        console.print("\n")
        console.print(create_operation_breakdown_table(manager))
        console.print("\n")

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]")


def watch_budget():
    """实时监控预算（每5秒刷新）"""
    try:
        config = get_config()

        console.print("[yellow]Starting real-time budget monitor... (Press Ctrl+C to exit)[/yellow]\n")

        while True:
            # 重新加载管理器以获取最新数据
            manager = BudgetManager(
                daily_budget=config.budget.daily_budget,
                weekly_budget=config.budget.weekly_budget,
                monthly_budget=config.budget.monthly_budget,
                agent_budget_ratios=config.budget.agent_ratios,
                enable_auto_fallback=config.budget.enable_auto_fallback,
                storage_dir=config.budget.storage_dir
            )

            # 清屏
            console.clear()

            # 显示时间戳
            console.print(f"[dim]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]\n")

            # 显示状态
            console.print(create_budget_status_panel(manager))
            console.print("\n")
            console.print(create_agent_usage_table(manager))

            # 等待5秒
            time.sleep(5)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def reset_budget():
    """重置日预算"""
    try:
        config = get_config()
        manager = BudgetManager(
            daily_budget=config.budget.daily_budget,
            weekly_budget=config.budget.weekly_budget,
            monthly_budget=config.budget.monthly_budget,
            agent_budget_ratios=config.budget.agent_ratios,
            enable_auto_fallback=config.budget.enable_auto_fallback,
            storage_dir=config.budget.storage_dir
        )

        console.print(f"[yellow]Current usage: ${manager._get_period_usage(manager._get_current_period('daily')):.4f}[/yellow]")

        confirm = console.input("[bold]Are you sure you want to reset the daily budget? (yes/no): [/bold]")

        if confirm.lower() == "yes":
            manager.reset_daily_budget()
            console.print("[green]✓ Daily budget has been reset.[/green]")
        else:
            console.print("[yellow]Reset cancelled.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error resetting budget: {e}[/red]")


def show_history(days: int = 7):
    """显示历史数据"""
    try:
        config = get_config()
        storage_dir = Path(config.budget.storage_dir)

        if not storage_dir.exists():
            console.print("[yellow]No history data found.[/yellow]")
            return

        console.print(f"\n[bold]Budget History (Last {days} days)[/bold]\n")

        table = Table(box=box.ROUNDED)
        table.add_column("Date", style="cyan")
        table.add_column("Total Cost", justify="right", style="green")
        table.add_column("Operations", justify="right", style="magenta")
        table.add_column("Fallbacks", justify="right", style="yellow")

        # 收集最近N天的数据
        history_data = []
        for i in range(days):
            target_date = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            filepath = storage_dir / f"budget_usage_{target_date}.json"

            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                total_cost = sum(r["cost_usd"] for r in data.get("records", []))
                operation_count = len(data.get("records", []))
                fallback_count = sum(1 for r in data.get("records", []) if r.get("fallback_applied", False))

                history_data.append({
                    "date": target_date,
                    "total_cost": total_cost,
                    "operations": operation_count,
                    "fallbacks": fallback_count
                })

        # 排序并显示
        history_data.sort(key=lambda x: x["date"], reverse=True)

        for item in history_data:
            table.add_row(
                item["date"],
                f"${item['total_cost']:.4f}",
                str(item["operations"]),
                str(item["fallbacks"])
            )

        if history_data:
            console.print(table)
            console.print("\n")

            # 总结
            total_cost_sum = sum(item["total_cost"] for item in history_data)
            total_ops_sum = sum(item["operations"] for item in history_data)
            console.print(f"[bold]Summary:[/bold]")
            console.print(f"  Total Cost: ${total_cost_sum:.4f}")
            console.print(f"  Total Operations: {total_ops_sum}")
            console.print(f"  Average Cost/Day: ${total_cost_sum / len(history_data):.4f}\n")
        else:
            console.print("[yellow]No data found for the specified period.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error loading history: {e}[/red]")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Budget Monitoring Tool for Claude Code Auto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python budget_monitor.py status            # Show current budget status
  python budget_monitor.py report            # Generate detailed report
  python budget_monitor.py watch             # Real-time monitoring
  python budget_monitor.py history 7         # Show last 7 days history
  python budget_monitor.py reset             # Reset daily budget
        """
    )

    parser.add_argument(
        "command",
        choices=["status", "report", "watch", "reset", "history"],
        help="Command to execute"
    )

    parser.add_argument(
        "days",
        nargs="?",
        type=int,
        default=7,
        help="Number of days for history command (default: 7)"
    )

    args = parser.parse_args()

    try:
        if args.command == "status":
            show_status()
        elif args.command == "report":
            show_report()
        elif args.command == "watch":
            watch_budget()
        elif args.command == "reset":
            reset_budget()
        elif args.command == "history":
            show_history(args.days)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
