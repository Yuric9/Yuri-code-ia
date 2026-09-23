"""Optional high-quality web search provider used alongside browser research."""
from __future__ import annotations
import os
from .database import get_db, log_research

def search_web(query: str, max_results: int = 20) -> dict:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {"enabled": False, "message": "TAVILY_API_KEY não configurada. Use o BrowserToolSet para pesquisa direta.", "results": []}
    from tavily import TavilyClient
    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, search_depth=os.getenv("TAVILY_SEARCH_DEPTH", "advanced"), max_results=max_results, include_answer=True, include_raw_content=True)
    db = next(get_db())
    try:
        for item in response.get("results", []):
            log_research(db, query, item.get("url"), item.get("content") or item.get("raw_content"))
    finally:
        db.close()
    return {"enabled": True, "answer": response.get("answer"), "results": response.get("results", [])}
