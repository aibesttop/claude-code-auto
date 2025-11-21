"""
Web Search Tools
"""
import os
from core.tool_registry import tool

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None

@tool
def web_search(query: str) -> str:
    """
    Searches the web for information using Tavily API.
    Requires TAVILY_API_KEY environment variable.
    
    Args:
        query: The search query string.
        
    Returns:
        A summary of search results.
    """
    if not TavilyClient:
        return "Error: tavily-python not installed. Please run 'pip install tavily-python'."
        
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set."
        
    try:
        client = TavilyClient(api_key=api_key)
        # Search with advanced context
        response = client.search(
            query=query,
            search_depth="advanced",
            include_answer=True
        )
        
        # Format output
        output = []
        if response.get("answer"):
            output.append(f"Answer: {response['answer']}\n")
            
        output.append("Sources:")
        for result in response.get("results", [])[:3]: # Top 3 results
            output.append(f"- [{result['title']}]({result['url']}): {result['content'][:200]}...")
            
        return "\n".join(output)
        
    except Exception as e:
        return f"Error performing web search: {str(e)}"
