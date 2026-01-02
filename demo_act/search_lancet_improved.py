"""
Improved Lancet Research Search

Uses the system's research tools to find elderly care and pension articles
from The Lancet for 2024-2025.
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.tools.research_tools import deep_research, get_research_stats


def main():
    """Main search function"""
    print("=" * 80)
    print("SEARCHING THE LANCET FOR ELDERLY CARE & PENSION RESEARCH (2024-2025)")
    print("=" * 80)
    print()

    # Search query focused on The Lancet
    query = """
    site:thelancet.com elderly care pension aging population social welfare
    long-term care healthcare systems research articles 2024 2025
    """

    print(f"🔍 Query: {query.strip()}\n")
    print("-" * 80)
    print("EXECUTING DEEP RESEARCH (3 rounds)")
    print("-" * 80)
    print()

    try:
        # Execute deep research
        result = deep_research(query, max_results=3)

        # Display results
        print("\n" + "=" * 80)
        print("RESEARCH RESULTS")
        print("=" * 80)
        print()

        # Query summary
        print(f"**Query**: {result['query']}")
        print(f"**Rounds Completed**: {result['rounds']}")
        print(f"**Quality Score**: {result['quality_score']}/10")
        print()

        # Progressive findings
        if result.get('findings'):
            print("## 📊 Progressive Findings")
            print()
            for i, finding in enumerate(result['findings'], 1):
                print(f"### Round {i}")
                print(finding)
                print()

        # Final summary
        if result.get('final_summary'):
            print("## 🎯 Final Synthesis")
            print()
            print(result['final_summary'])
            print()

        # Sources
        if result.get('sources'):
            print("## 📚 Sources")
            print()
            for i, source in enumerate(result['sources'], 1):
                title = source.get('title', 'Untitled')
                url = source.get('url', '')
                print(f"{i}. **{title}**")
                if url:
                    print(f"   {url}")
                print()

        # Research stats
        stats = get_research_stats()
        print("=" * 80)
        print("RESEARCH STATISTICS")
        print("=" * 80)
        print()
        print(f"Total Queries: {stats['total_queries']}")
        print(f"Cache Hits: {stats['cache_hits']}")
        print(f"Deep Research Count: {stats['deep_research_count']}")
        print(f"Cache Hit Rate: {stats['cache_hit_rate']:.1%}")
        print()

    except Exception as e:
        print(f"\n❌ Error during research: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("=" * 80)
    print("✅ SEARCH COMPLETE")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    exit(main())
