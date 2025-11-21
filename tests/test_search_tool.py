import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.core.tools.search_tools import web_search

# Ensure API key is set
if not os.environ.get("TAVILY_API_KEY"):
    os.environ["TAVILY_API_KEY"] = "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"

def test_search():
    print("[START] Testing web_search tool directly...")
    query = "python 3.12 release date"
    
    try:
        result = web_search(query)
        print("\n[RESULT] Raw Web Search Output:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
        if "Error" in result and "Answer:" not in result:
            print("[FAIL] Search returned error.")
        else:
            print("[PASS] Search tool returned content.")
            
    except Exception as e:
        print(f"[FAIL] Exception: {e}")

if __name__ == "__main__":
    test_search()
