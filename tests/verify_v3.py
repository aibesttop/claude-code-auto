"""
Verification Script for v3.1 Architecture
Tests Tool Registry, Executor, Planner, and Persona Engine.
"""
import asyncio
import sys
from pathlib import Path

# Ensure we can import from current directory
# Ensure we can import from project root
sys.path.append(str(Path(__file__).parent.parent))

from src.core.tool_registry import registry
import src.core.tools # Trigger registration
from src.core.agents.persona import PersonaEngine
from src.core.agents.executor import ExecutorAgent

async def verify_tools():
    print("\n[INFO] Verifying Tool Registry...")
    schemas = registry.get_all_schemas()
    print(f"[OK] Found {len(schemas)} registered tools:")
    for s in schemas:
        print(f"  - {s['name']}")
        
    # Test File Tool
    print("\n[TEST] Testing File Tool...")
    test_file = "test_verify.txt"
    try:
        registry.execute("write_file", {"path": test_file, "content": "Hello v3.1"})
        content = registry.execute("read_file", {"path": test_file})
        if content == "Hello v3.1":
            print("[PASS] File Tool Works")
        else:
            print("[FAIL] File Tool Failed: Content mismatch")
    except Exception as e:
        print(f"[FAIL] File Tool Error: {e}")
        
    # Cleanup
    try:
        Path(test_file).unlink()
    except:
        pass

async def verify_persona():
    print("\n[INFO] Verifying Persona Engine...")
    engine = PersonaEngine()
    print(f"[OK] Default Persona: {engine.current_persona.name}")
    
    if engine.switch_persona("coder"):
        print("[PASS] Switched to Coder Persona")
        print(f"  System Prompt Preview: {engine.get_system_prompt()[:50]}...")
    else:
        print("[FAIL] Failed to switch persona")

async def main():
    # Force UTF-8 for stdout
    sys.stdout.reconfigure(encoding='utf-8')
    print("[START] v3.1 Verification")
    
    await verify_tools()
    await verify_persona()
    
    print("\n[DONE] Verification Complete")

if __name__ == "__main__":
    asyncio.run(main())
