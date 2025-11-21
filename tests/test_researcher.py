import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.agents.researcher import ResearcherAgent
from src.utils.logger import setup_logger

# Mock config for testing
WORK_DIR = "test_work_dir"
os.makedirs(WORK_DIR, exist_ok=True)

async def test_researcher():
    print("[START] Testing Researcher Agent...")
    
    # Ensure API key is set (it should be set by the environment or we set it here for testing if needed)
    # In this context, we expect it to be set in the environment or passed via config
    if not os.environ.get("TAVILY_API_KEY"):
        print("[WARN] TAVILY_API_KEY not found in env, setting it manually for test...")
        os.environ["TAVILY_API_KEY"] = "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"

    researcher = ResearcherAgent(
        work_dir=WORK_DIR,
        provider="tavily",
        enabled=True,
        enable_cache=False # Disable cache to force real search
    )

    query = "latest trends in chemistry calculators for university students"
    print(f"[INFO] Running search for: {query}")
    
    try:
        result = await researcher.research(query)
        print("\n[RESULT] Search Result Summary:")
        print("-" * 50)
        print(result[:500] + "..." if len(result) > 500 else result)
        print("-" * 50)
        
        if "Error" not in result and len(result) > 50:
            print("\n[PASS] Researcher Agent works!")
        else:
            print("\n[FAIL] Researcher Agent returned error or empty result.")
            
    except Exception as e:
        print(f"\n[FAIL] Exception during research: {e}")

if __name__ == "__main__":
    asyncio.run(test_researcher())
