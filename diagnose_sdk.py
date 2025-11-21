"""
SDK Diagnostic Script
Tests different approaches to understand how claude-code-sdk should be used.
"""
import asyncio
import sys
import os
from pathlib import Path

print("="*70)
print("Claude Code SDK Diagnostic")
print("="*70)

# Test 1: Check if running inside Claude Code environment
print("\n[Test 1] Environment Check:")
print(f"CWD: {os.getcwd()}")
print(f"Python: {sys.version}")

# Check for Claude Code environment variables
env_vars = [
    'ANTHROPIC_API_KEY',
    'CLAUDE_CODE_SESSION',
    'CLAUDE_SESSION_ID',
]
for var in env_vars:
    value = os.getenv(var)
    if value:
        print(f"{var}: {value[:20]}...")
    else:
        print(f"{var}: NOT SET")

# Test 2: Check SDK availability
print("\n[Test 2] SDK Import:")
try:
    from claude_code_sdk import ClaudeSDKClient, ClaudeCodeOptions
    print("[OK] SDK imported successfully")
except ImportError as e:
    print(f"[FAIL] SDK import failed: {e}")
    sys.exit(1)

# Test 3: Understand SDK design
print("\n[Test 3] SDK Documentation:")
import inspect
print(inspect.getdoc(ClaudeSDKClient))

# Test 4: Check Options
print("\n[Test 4] ClaudeCodeOptions Parameters:")
import inspect
sig = inspect.signature(ClaudeCodeOptions)
for param_name, param in sig.parameters.items():
    print(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'Any'}")
    if param.default != inspect.Parameter.empty:
        print(f"    Default: {param.default}")

print("\n" + "="*70)
print("Diagnostic Complete")
print("="*70)
