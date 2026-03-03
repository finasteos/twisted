"""
Deep Research orchestration using Gemini's research capabilities.
Integrates with SerpAPI/Tavily for real-time intelligence.
"""

import asyncio
import json
from typing import Callable, Dict, List, Optional

from google.genai import types


class DeepResearchOrchestrator:
    """
    Exhaustive background research for complex cases.

    Capabilities:
    - Multi-query research generation
    - Parallel web search (SerpAPI/Tavily)
    - Gemini Deep Research synthesis
    - Vector store integration
    """

    def __init__(self, gemini_wrapper):
        self.llm = gemini_wrapper

    async def execute(
        self,
        case_id: str,
        context_query: str,
        progress_callback: Optional[Callable] = None,
        max_parallel_queries: int = 5
    ) -> Dict:
        """
        Execute deep research pipeline.

        Duration: 5-15 minutes depending on complexity
        """

        # Step 1: Generate research queries
        if progress_callback:
            await progress_callback(0.1, "Generating research queries...")

        queries = await self._generate_research_queries(context_query)

        # Step 2: Parallel web search
        if progress_callback:
            await progress_callback(0.3, f"Executing {len(queries)} parallel searches...")

        search_results = await self._parallel_search(queries)

        # Step 3: Gemini Deep Research synthesis
        if progress_callback:
            await progress_callback(0.6, "Synthesizing findings with Deep Research...")

        deep_findings = await self._deep_research_synthesis(
            context_query=context_query,
            search_results=search_results
        )

        # Step 4: Structure for vector storage
        if progress_callback:
            await progress_callback(0.9, "Structuring research for agent access...")

        structured_findings = self._structure_findings(deep_findings, search_results)

        if progress_callback:
            await progress_callback(1.0, "Deep research complete")

        return structured_findings

    async def _generate_research_queries(self, context: str) -> List[str]:
        """
        Generate diverse research queries from case context.
        Uses Gemini Flash for speed.
        """
        prompt = f"""Based on this case context, generate 3-5 specific research queries to gather background intelligence.

Context: {context}

Generate queries covering:
1. Applicable laws or regulations
2. Similar cases or precedents
3. Relevant organizations or contacts
4. Current events or news that might affect the case
5. Industry standards or best practices

Output JSON array of query strings."""

        response = await self.llm.generate(
            contents=prompt,
            task_complexity="analysis",
            response_mime_type="application/json"
        )

        return json.loads(response.text)

    async def _parallel_search(self, queries: List[str]) -> List[Dict]:
        """
        Execute parallel web searches via SerpAPI/Tavily.
        Respects rate limits (10 queries/minute).
        """
        from backend.enrichment.web_search import WebSearcher

        searcher = WebSearcher()

        results = []
        # Run searches sequentially to respect 10 queries/minute
        semaphore = asyncio.Semaphore(1)

        async def search_with_limit(query: str):
            async with semaphore:
                result = await searcher.search(query)
                # Rate limit: 6 seconds between calls (10/min)
                await asyncio.sleep(6)
                return result

        # Execute all searches
        tasks = [search_with_limit(q) for q in queries]
        search_results = await asyncio.gather(*tasks, return_exceptions=True)

        for query, result in zip(queries, search_results):
            if isinstance(result, Exception):
                results.append({
                    'query': query,
                    'error': str(result),
                    'results': []
                })
            else:
                results.append({
                    'query': query,
                    'results': result
                })

        return results

    async def _deep_research_synthesis(
        self,
        context_query: str,
        search_results: List[Dict]
    ) -> Dict:
        """
        Use Gemini Deep Research model for exhaustive synthesis.

        Model: deep-research-pro-preview-12-2025
        """
        # Compile search results into research context
        research_context = self._compile_research_context(search_results)

        prompt = f"""Conduct deep research synthesis on this case.

Case Context: {context_query}

Research Findings:
{research_context}

Provide comprehensive analysis including:
1. Key legal/regulatory frameworks applicable
2. Relevant precedents and case law
3. Strategic implications of current events
4. Recommended expert resources
5. Potential risks and opportunities not obvious from surface analysis

Be thorough. This is background intelligence for a high-stakes decision."""

        # Use Gemini 3.1 Pro with extended thinking for deep research
        response = await self.llm.generate(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            task_complexity="legal",
            thinking_config={
                "thinking_budget": 32768,  # Extended thinking for deep analysis
                "include_thoughts": True
            }
        )

        synthesis_text = getattr(response, "text", None) or getattr(response, "content", None) or str(response)
        raw_response = getattr(response, "raw", response)

        thinking = None
        try:
            first_part = raw_response.candidates[0].content.parts[0]
            thinking = getattr(first_part, "thought", None)
        except Exception:
            thinking = None

        return {
            "synthesis": synthesis_text,
            "thinking_process": thinking,
            "sources": [r["query"] for r in search_results],
        }

    def _compile_research_context(self, search_results: List[Dict]) -> str:
        """Compile search results into formatted context."""
        sections = []

        for result in search_results:
            if 'error' in result:
                continue

            section = f"\n\n## Query: {result['query']}\n"

            for item in result.get('results', [])[:5]:  # Top 5 per query
                title = item.get('title', 'Untitled')
                snippet = item.get('snippet', item.get('content', ''))
                url = item.get('url', 'No URL')

                section += f"- **{title}**: {snippet[:200]}... [Source]({url})\n"

            sections.append(section)

        return "\n".join(sections)

    def _structure_findings(self, deep_findings: Dict, search_results: List[Dict]) -> Dict:
        """Structure for vector store ingestion."""
        documents = []
        metadatas = []

        # Main synthesis
        documents.append(deep_findings['synthesis'])
        metadatas.append({
            'type': 'deep_research_synthesis',
            'thinking_included': deep_findings.get('thinking_process') is not None,
            'source_queries': deep_findings.get('sources', [])
        })

        # Individual search results for granular retrieval
        for result in search_results:
            if 'error' in result:
                continue

            for item in result.get('results', []):
                content = f"{item.get('title', '')}: {item.get('snippet', '')}"
                documents.append(content)
                metadatas.append({
                    'type': 'web_search_result',
                    'query': result['query'],
                    'url': item.get('url', ''),
                    'date': item.get('date', 'unknown')
                })

        return {
            'documents': documents,
            'metadatas': metadatas,
            'summary': deep_findings['synthesis'][:500] + "...",
            'query_count': len(search_results),
            'source_count': len(documents) - 1  # Exclude synthesis
        }
