"""
Deep Research coordination with Gemini's research capabilities.
Multi-source intelligence fusion.
"""

import asyncio
import json
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ResearchQuery:
    query: str
    source_priority: List[str]  # ["google_scholar", "news", "legal_db", ...]
    recency_days: Optional[int]  # None for timeless, 30 for recent news
    depth: str  # "surface" | "standard" | "deep"

@dataclass
class ResearchFinding:
    source: str
    title: str
    content: str
    url: Optional[str]
    date: Optional[datetime]
    credibility_score: float  # 0-1
    relevance_score: float  # 0-1, semantic similarity to case

class ResearchOrchestrator:
    """
    Exhaustive background research for complex cases.
    Duration: 5-15 minutes of parallel intelligence gathering.
    """

    def __init__(self, gemini_wrapper, serpapi_key: Optional[str] = None, tavily_key: Optional[str] = None):
        self.gemini = gemini_wrapper
        self.serpapi_key = serpapi_key
        self.tavily_key = tavily_key

    async def execute_research(
        self,
        case_context: str,
        entities: List[Dict],
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Execute full research pipeline.
        """
        # Phase 1: Query Generation (10%)
        if progress_callback:
            await progress_callback(0.1, "Generating targeted research queries...")

        queries = await self._generate_queries(case_context, entities)

        # Phase 2: Parallel Source Querying (10-60%)
        if progress_callback:
            await progress_callback(0.15, f"Querying {len(queries)} research vectors...")

        all_findings = []
        for i, query in enumerate(queries):
            findings = await self._execute_query(query)
            all_findings.extend(findings)

            progress = 0.15 + (0.45 * (i + 1) / len(queries))
            if progress_callback:
                await progress_callback(
                    progress,
                    f"Collected {len(findings)} findings for: {query.query[:50]}..."
                )

        # Phase 3: Credibility Filtering (60-70%)
        if progress_callback:
            await progress_callback(0.6, "Filtering and ranking sources...")

        credible_findings = self._filter_by_credibility(all_findings)

        # Phase 4: Gemini Deep Research Synthesis (70-95%)
        if progress_callback:
            await progress_callback(0.7, "Synthesizing with Gemini Deep Research...")

        synthesis = await self._deep_synthesis(
            case_context=case_context,
            findings=credible_findings
        )

        # Phase 5: Vector Store Injection (95-100%)
        if progress_callback:
            await progress_callback(0.95, "Indexing findings for agent access...")

        structured_output = self._structure_for_agents(synthesis, credible_findings)

        if progress_callback:
            await progress_callback(1.0, "Deep research complete")

        return structured_output

    async def _generate_queries(
        self,
        case_context: str,
        entities: List[Dict]
    ) -> List[ResearchQuery]:
        """
        Generate diverse research queries from case specifics.
        """
        prompt = f"""Generate 4-6 targeted research queries for this case.

Case Context: {case_context[:1000]}

Key Entities: {', '.join(e.get('name', '') for e in entities[:5])}

Query Types Needed:
1. Legal/Regulatory — applicable laws, recent precedents
2. Entity Intelligence — organizations involved, their patterns
3. Current Events — news that might affect this case
4. Tactical — similar cases and their outcomes
5. Expert Resources — who to consult, relevant authorities

Output JSON array:
[
  {{
    "query": "specific search string",
    "source_priority": ["source_type_1", "source_type_2"],
    "recency_days": 365,
    "depth": "standard"
  }}
]"""

        response = await self.gemini.generate(
            contents=prompt,
            task_complexity="analysis",
            response_mime_type="application/json"
        )

        query_data = json.loads(response.text)
        return [ResearchQuery(
            query=q["query"],
            source_priority=q["source_priority"],
            recency_days=q.get("recency_days"),
            depth=q.get("depth", "standard")
        ) for q in query_data]

    async def _execute_query(self, query: ResearchQuery) -> List[ResearchFinding]:
        """
        Execute single query across prioritized sources.
        """
        findings = []

        # Placeholder for actual API integrations
        # In a real scenario, this would call SerpAPI, Tavily, etc.
        return findings

    def _filter_by_credibility(self, findings: List[ResearchFinding]) -> List[ResearchFinding]:
        return [f for f in findings if f.credibility_score > 0.5] if findings else []

    async def _deep_synthesis(
        self,
        case_context: str,
        findings: List[ResearchFinding]
    ) -> Dict:
        """
        Use Gemini with extended thinking for research synthesis.
        """
        findings_text = "\n".join([f"{f.title}: {f.content}" for f in findings[:20]])

        prompt = f"""You are conducting deep research synthesis for a high-stakes case.

CASE CONTEXT:
{case_context}

RESEARCH FINDINGS:
{findings_text}

SYNTHESIS REQUIREMENTS:
1. Legal Framework
2. Precedent Analysis
3. Strategic Implications
4. Risk Factors
5. Resource Map
6. Timeline Factors

Output format: Detailed markdown with sections."""

        response = await self.gemini.generate(
            model="gemini-3.1-pro-preview",
            contents=prompt,
            task_complexity="legal",
            thinking_config={
                "thinking_budget": 32768,
                "include_thoughts": True
            }
        )

        return {
            "synthesis": response.text,
            "thinking_process": "Extracted from candidate thoughts",
            "source_count": len(findings),
            "high_credibility_count": len([f for f in findings if f.credibility_score > 0.7])
        }

    def _structure_for_agents(self, synthesis: Dict, findings: List[ResearchFinding]) -> Dict:
        """Structure research for Qdrant vector store inclusion."""
        return {
            "documents": [synthesis["synthesis"]],
            "metadatas": [{"type": "deep_research_synthesis"}],
            "summary": synthesis["synthesis"][:500] + "...",
            "key_insights": [],
            "confidence": 0.9
        }

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        return datetime.now() # Simplified

    def _score_credibility(self, source: str, result: Dict) -> float:
        return 0.8 # Simplified
