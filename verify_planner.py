
import sys
import json
from pathlib import Path

# Ensure we can import from current directory
sys.path.append(str(Path(__file__).parent))

from core.agents.planner import PlannerAgent, PLANNER_SYSTEM_PROMPT

def test_planner_prompt_formatting():
    print("\n[TEST] Testing Planner Prompt Formatting...")
    
    goal = "Test Goal"
    plan_state = "[]"
    
    try:
        # Test raw formatting first
        formatted = PLANNER_SYSTEM_PROMPT.format(
            goal=goal,
            plan_state=plan_state
        )
        print("[PASS] Raw PLANNER_SYSTEM_PROMPT format successful")
        
        # Test via Agent class
        agent = PlannerAgent(work_dir=".", goal=goal)
        # We can't easily call get_next_step without mocking ClaudeSDK, 
        # but we can verify the prompt construction logic if we extract it or just rely on the above.
        # Actually, let's try to verify the format call inside the class context if possible, 
        # but the above raw format is the critical test for KeyError.
        
        print(f"[INFO] Prompt length: {len(formatted)}")
        
    except KeyError as e:
        print(f"[FAIL] KeyError during formatting: {e}")
        print("Check for missing double braces {{ }} in JSON template")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_planner_prompt_formatting()
