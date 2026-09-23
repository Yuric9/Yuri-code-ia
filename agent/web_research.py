"""Optional high-quality web search provider used alongside browser research."""

from __future__ import annotations

import os

from .database import log_research


def search_web(query: str, max_results: int = 20) -> dict:
    """Search the public web through Tavily when configured.

    There is deliberately no application-level daily/session quota here. The
    actual provider account may still enforce its own billing/rate limits.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {
            "enabled": False,
            "message": "TAVILY_API_KEY não configurada. A Yuri Code AI pode usar o BrowserToolSet para pesquisar diretamente na web.",
            "results": [],
        }

    from tavily import TavilyClient

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth=os.getenv("TAVILY_SEARCH_DEPTH", "advanced"),
        max_results=max_results,
        include_answer=True,
        include_raw_content=True,
    )

    results = response.get("results", [])
    for item in results:
        log_research(query, item.get("url"), item.get("content") or item.get("raw_content"))

    return {
        "enabled": True,
        "answer": response.get("answer"),
        "results": results,
    }
