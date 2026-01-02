#!/usr/bin/env python
"""Search for elderly care/pension research articles in The Lancet"""
import sys
sys.path.insert(0, '..')

from src.core.tools.research_tools import quick_research

def main():
    print("Searching The Lancet for elderly care/pension research articles...\n")

    # Search for recent research articles
    query = "site:thelancet.com elderly care pension research articles 2024 2025"
    result = quick_research(query)

    print("=" * 80)
    print("SEARCH RESULTS")
    print("=" * 80)
    print(result)
    print("=" * 80)

    return result

if __name__ == "__main__":
    main()
