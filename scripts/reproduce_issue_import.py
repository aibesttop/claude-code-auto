
import sys
import os

# Add the project root to python path
sys.path.append(os.getcwd())

try:
    from core.agents.planner import PLANNER_SYSTEM_PROMPT
    print("Loaded prompt length:", len(PLANNER_SYSTEM_PROMPT))
    
    formatted = PLANNER_SYSTEM_PROMPT.format(goal="test", plan_state="[]")
    print("Success!")
except KeyError as e:
    print(f"KeyError: {repr(e)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
