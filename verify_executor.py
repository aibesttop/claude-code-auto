
import sys
import json
from pathlib import Path

# Ensure we can import from current directory
sys.path.append(str(Path(__file__).parent))

from core.agents.executor import ExecutorAgent, REACT_SYSTEM_PROMPT
import core.tools # Trigger registration

def test_executor_components():
    print("\n[TEST] Testing Executor Components...")
    
    agent = ExecutorAgent(work_dir=".")
    
    # 1. Test Tool Descriptions
    print("\n[TEST] Tool Descriptions...")
    desc = agent._get_tool_descriptions()
    print(f"Description length: {len(desc)}")
    if "read_file" in desc:
        print("[PASS] 'read_file' found in descriptions")
    else:
        print("[FAIL] 'read_file' NOT found in descriptions")
        
    # 2. Test Prompt Formatting
    print("\n[TEST] Prompt Formatting...")
    try:
        formatted = REACT_SYSTEM_PROMPT.format(tool_descriptions=desc)
        print("[PASS] REACT_SYSTEM_PROMPT format successful")
    except KeyError as e:
        print(f"[FAIL] KeyError during formatting: {e}")
        sys.exit(1)
        
    # 3. Test Action Parsing
    print("\n[TEST] Action Parsing...")
    
    # Case A: Standard
    response_a = """
    Thought: I need to read a file.
    Action: read_file
    Action Input: {
        "path": "test.txt"
    }
    """
    action, args = agent._parse_action(response_a)
    if action == "read_file" and args.get("path") == "test.txt":
        print("[PASS] Standard Action Parsing")
    else:
        print(f"[FAIL] Standard Parsing failed: {action}, {args}")

    # Case B: Markdown JSON
    response_b = """
    Action: write_file
    Action Input: ```json
    {
        "path": "out.txt",
        "content": "hello"
    }
    ```
    """
    action, args = agent._parse_action(response_b)
    if action == "write_file" and args.get("content") == "hello":
        print("[PASS] Markdown JSON Parsing")
    else:
        print(f"[FAIL] Markdown JSON Parsing failed: {action}, {args}")

if __name__ == "__main__":
    test_executor_components()
