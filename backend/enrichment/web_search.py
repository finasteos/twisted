"""
Web Search Enrichment
Wrappers for SerpAPI and Tavily for real-time contextual research.
"""

import os
import httpx
from typing import List, Dict, Any, Optional

class WebSearcher:
    """Handles web search queries via SerpAPI or Tavily."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.serpapi_key = os.getenv("SERPAPI_KEY") or self.config.get("serpapi_key")
        self.tavily_key = os.getenv("TAVILY_API_KEY") or self.config.get("tavily_api_key")

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform a web search using available engines."""

        # Prefer Tavily for research-heavy tasks if available
        if self.tavily_key:
            return await self._search_tavily(query, max_results)

        # Fallback to SerpAPI
        if self.serpapi_key:
            return await self._search_serpapi(query, max_results)

        return []

    async def check_health(self) -> Dict[str, Dict[str, Any]]:
        """Check connectivity to search APIs."""
        health = {}

        # Check Tavily
        if self.tavily_key:
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get("https://api.tavily.com/status", timeout=5.0)
                    health["tavily"] = {"status": "ok" if resp.status_code == 200 else "error", "code": resp.status_code}
            except Exception as e:
                health["tavily"] = {"status": "error", "message": str(e)}
        else:
            health["tavily"] = {"status": "missing_key"}

        # Check SerpAPI
        if self.serpapi_key:
            try:
                async with httpx.AsyncClient() as client:
                    # Simple call to check key validity
                    resp = await client.get(f"https://serpapi.com/account?api_key={self.serpapi_key}", timeout=5.0)
                    health["serpapi"] = {"status": "ok" if resp.status_code == 200 else "error", "code": resp.status_code}
            except Exception as e:
                health["serpapi"] = {"status": "error", "message": str(e)}
        else:
            health["serpapi"] = {"status": "missing_key"}

        return health

    async def _search_tavily(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using Tavily API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": self.tavily_key,
                        "query": query,
                        "search_depth": "smart",
                        "max_results": max_results
                    },
                    timeout=20.0
                )
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get("results", []):
                        results.append({
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "content": item.get("content"),
                            "source": "tavily"
                        })
                    return results
            except Exception:
                pass
        return []

    async def _search_serpapi(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search using SerpAPI."""
        async with httpx.AsyncClient() as client:
            try:
                params = {
                    "engine": "google",
                    "q": query,
                    "api_key": self.serpapi_key,
                    "num": max_results
                }
                response = await client.get(
                    "https://serpapi.com/search",
                    params=params,
                    timeout=20.0
                )
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get("organic_results", []):
                        results.append({
                            "title": item.get("title"),
                            "url": item.get("link"),
                            "content": item.get("snippet"),
                            "source": "serpapi"
                        })
                    return results
            except Exception:
                pass
        return []
