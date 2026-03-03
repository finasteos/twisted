"""
Enrichment Router
Orchestrates connectivity between document RAG, web search, and MCP tools.
"""

from typing import List, Dict, Any, Optional
from backend.enrichment.web_search import WebSearcher
import json

class EnrichmentRouter:
    """Routes enrichment requests to RAG, Web, or MCP."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.web_searcher = WebSearcher(self.config)

    async def enrich_context(self, query: str, task_type: str = "general") -> str:
        """Fetch additional context and return as high-density string for the LLM."""

        results = []

        # 1. Web Search (if query is research-worthy)
        web_results = await self.web_searcher.search(query)
        if web_results:
            results.append("### EXTERNAL WEB RESEARCH RESULTS")
            for i, res in enumerate(web_results, 1):
                results.append(f"[{i}] {res['title']}\nURL: {res['url']}\nSnippet: {res['content']}\n")

        # 2. To be added: MCP Tool execution

        if not results:
            return ""

        return "\n".join(results)
