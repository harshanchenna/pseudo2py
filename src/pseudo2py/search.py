"""Web search tool — Brave Search primary, DuckDuckGo fallback."""

from __future__ import annotations

import httpx

from pseudo2py.config import SearchConfig


def search(query: str, config: SearchConfig, *, max_results: int = 5) -> str:
    """Search the web and return formatted results for LLM context."""
    if config.provider == "brave":
        return _brave_search(query, config.brave_api_key, max_results=max_results)
    return _ddg_search(query, max_results=max_results)


def _brave_search(query: str, api_key: str, *, max_results: int = 5) -> str:
    """Search via Brave Search API."""
    resp = httpx.get(
        "https://api.search.brave.com/res/v1/web/search",
        params={"q": query, "count": max_results},
        headers={
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": api_key,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("web", {}).get("results", [])
    if not results:
        return "No results found."

    return _format_results(
        [
            (r.get("title", ""), r.get("url", ""), r.get("description", ""))
            for r in results[:max_results]
        ]
    )


def _ddg_search(query: str, *, max_results: int = 5) -> str:
    """Search via DuckDuckGo (no API key needed)."""
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))

    if not results:
        return "No results found."

    return _format_results(
        [(r["title"], r["href"], r["body"]) for r in results]
    )


def _format_results(results: list[tuple[str, str, str]]) -> str:
    """Format search results as clean text for LLM consumption."""
    parts = []
    for i, (title, url, snippet) in enumerate(results, 1):
        parts.append(f"{i}. {title}\n   {url}\n   {snippet}")
    return "\n\n".join(parts)
