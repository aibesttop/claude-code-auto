"""
实时监控脚本 - Monitor workflow execution in real-time

使用方法:
    python monitor.py                    # 监控主日志
    python monitor.py --trace            # 监控trace文件
    python monitor.py --events           # 监控事件
    python monitor.py --all              # 监控所有
"""

import asyncio
import time
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Set, Optional


class WorkflowMonitor:
    """工作流实时监控器"""

    def __init__(self, log_file: str = "logs/workflow.log"):
        self.log_file = Path(log_file)
        self.last_position = 0
        self.keywords: Set[str] = {
            "🎯", "🔄", "🎭", "✅", "❌", "⚠️", "🔍",
            "Leader", "ReAct", "Mission", "Role", "Reflection"
        }

    def print_header(self):
        """打印监控头部"""
        print("\n" + "=" * 80)
        print(f"🔍 WORKFLOW MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📄 File: {self.log_file}")
        print("=" * 80 + "\n")

    def print_line(self, line: str, highlight: bool = False):
        """打印一行"""
        if highlight:
            # 高亮重要行
            print(f">>> {line}")
        else:
            print(f"    {line}")

    def is_important(self, line: str) -> bool:
        """判断是否为重要日志"""
        line_upper = line.upper()
        return any(
            keyword in line or keyword.upper() in line_upper
            for keyword in self.keywords
        ) or any(
            level in line_upper
            for level in ["ERROR", "WARNING", "SUCCESS", "COMPLETED"]
        )

    async def monitor(self, follow: bool = True, important_only: bool = False):
        """
        监控日志文件

        Args:
            follow: 持续监控新日志
            important_only: 只显示重要日志
        """
        if not self.log_file.exists():
            print(f"⚠️ Log file not found: {self.log_file}")
            print(f"   Waiting for file to be created...")
            while not self.log_file.exists():
                await asyncio.sleep(1)

        self.print_header()

        # 初始读取
        if self.last_position == 0:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                # 读取最后100行
                lines = f.readlines()
                if len(lines) > 100:
                    lines = lines[-100:]
                for line in lines:
                    line = line.strip()
                    if line and (not important_only or self.is_important(line)):
                        self.print_line(line, self.is_important(line))
                self.last_position = f.tell()

        # 持续监控
        if follow:
            print(f"\n🔄 Monitoring for new logs... (Ctrl+C to stop)\n")
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    f.seek(self.last_position)

                    while True:
                        line = f.readline()
                        if line:
                            line = line.strip()
                            should_print = not important_only or self.is_important(line)

                            if should_print:
                                timestamp = datetime.now().strftime('%H:%M:%S')
                                print(f"[{timestamp}] {line}")

                            self.last_position = f.tell()
                        else:
                            await asyncio.sleep(0.1)
            except KeyboardInterrupt:
                print(f"\n\n✅ Monitoring stopped at {datetime.now().strftime('%H:%M:%S')}")


class TraceMonitor:
    """Trace文件监控器"""

    def __init__(self, trace_dir: str = "logs/trace"):
        self.trace_dir = Path(trace_dir)
        self.seen_files: Set[Path] = set()

    async def monitor(self):
        """监控trace目录中的新文件"""
        print("\n" + "=" * 80)
        print(f"🔍 TRACE MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Directory: {self.trace_dir}")
        print("=" * 80 + "\n")

        if not self.trace_dir.exists():
            print(f"⚠️ Trace directory not found: {self.trace_dir}")
            print(f"   Waiting for directory to be created...")
            self.trace_dir.mkdir(parents=True, exist_ok=True)

        print("🔄 Monitoring for new trace files... (Ctrl+C to stop)\n")

        try:
            while True:
                # 查找新文件
                current_files = set(self.trace_dir.glob("*.md"))
                new_files = current_files - self.seen_files

                for trace_file in sorted(new_files, key=lambda p: p.stat().st_mtime):
                    print(f"\n📄 NEW TRACE: {trace_file.name}")
                    print(f"   Size: {trace_file.stat().st_size:,} bytes")
                    print(f"   Time: {datetime.fromtimestamp(trace_file.stat().st_mtime).strftime('%H:%M:%S')}")

                    # 读取并显示前20行
                    try:
                        with open(trace_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[:20]
                            print("   Preview:")
                            for line in lines[:5]:
                                print(f"     {line.rstrip()}")
                            if len(lines) > 5:
                                print(f"     ... ({len(lines)} more lines)")
                    except Exception as e:
                        print(f"   ⚠️ Error reading file: {e}")

                    self.seen_files.add(trace_file)

                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print(f"\n\n✅ Monitoring stopped at {datetime.now().strftime('%H:%M:%S')}")


class EventMonitor:
    """事件监控器"""

    def __init__(self, events_dir: str = "logs/events"):
        self.events_dir = Path(events_dir)

    async def monitor(self):
        """监控事件文件"""
        print("\n" + "=" * 80)
        print(f"🔍 EVENT MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Directory: {self.events_dir}")
        print("=" * 80 + "\n")

        if not self.events_dir.exists():
            print(f"⚠️ Events directory not found: {self.events_dir}")
            return

        # 查找最新的事件文件
        event_files = sorted(self.events_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)

        if not event_files:
            print("No event files found. Waiting...")
            event_files = []

        latest_file = event_files[-1] if event_files else None

        if latest_file:
            print(f"📄 Latest event file: {latest_file.name}")
            print(f"   Size: {latest_file.stat().st_size:,} bytes")
            print(f"   Modified: {datetime.fromtimestamp(latest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # 解析并显示事件统计
            try:
                import json
                with open(latest_file, 'r', encoding='utf-8') as f:
                    events = json.load(f)

                print(f"📊 Event Statistics:")
                print(f"   Total Events: {len(events)}")

                # 统计事件类型
                event_types = {}
                for event in events:
                    event_type = event.get('type', 'unknown')
                    event_types[event_type] = event_types.get(event_type, 0) + 1

                print(f"   Event Types:")
                for event_type, count in sorted(event_types.items(), key=lambda x: -x[1]):
                    print(f"     - {event_type}: {count}")

                # 显示最近5个事件
                print(f"\n   Recent Events:")
                for event in events[-5:]:
                    event_type = event.get('type', 'unknown')
                    timestamp = event.get('timestamp', 'N/A')[:19]
                    print(f"     [{timestamp}] {event_type}")

            except Exception as e:
                print(f"⚠️ Error parsing events: {e}")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor workflow execution")
    parser.add_argument("--log", default="logs/workflow.log", help="Log file to monitor")
    parser.add_argument("--trace", action="store_true", help="Monitor trace files")
    parser.add_argument("--events", action="store_true", help="Monitor event files")
    parser.add_argument("--all", action="store_true", help="Monitor everything")
    parser.add_argument("--important", action="store_true", help="Show only important logs")
    parser.add_argument("--once", action="store_true", help="Don't follow, just show current content")

    args = parser.parse_args()

    if args.all:
        args.trace = True
        args.events = True

    if args.trace and args.events:
        # 同时监控多个
        print("🚀 Starting multi-monitor mode...")
        monitor = WorkflowMonitor(args.log)
        trace_monitor = TraceMonitor()
        event_monitor = EventMonitor()

        await asyncio.gather(
            monitor.monitor(follow=not args.once, important_only=args.important),
            trace_monitor.monitor(),
            event_monitor.monitor()
        )
    elif args.trace:
        trace_monitor = TraceMonitor()
        await trace_monitor.monitor()
    elif args.events:
        event_monitor = EventMonitor()
        await event_monitor.monitor()
        if not args.once:
            print("\n⚠️ Event monitor runs once. Use --all to continuously monitor.")
    else:
        # 默认:只监控日志
        monitor = WorkflowMonitor(args.log)
        await monitor.monitor(follow=not args.once, important_only=args.important)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
