"""
Echo Vault: Historical pattern retrieval and memory-based insights.
Searches past case data and knowledge base for relevant patterns.
"""

import json
from typing import Dict, List, Optional, Callable

from backend.agents.base_agent import BaseAgent
from backend.logging_config import get_logger

logger = get_logger("agent.echo_vault")


class EchoVaultAgent(BaseAgent):
    """
    Memory specialist agent — retrieves historical patterns, past case
    similarities, and knowledge-base insights to inform the debate.
    """

    def __init__(self, llm, memory, comm):
        super().__init__(
            agent_name="Echo Vault",
            codename="echo_vault",
            profile_dir="echo_vault",
            llm=llm,
            task_type="memory",
        )
        self.memory = memory
        self.comm = comm

    async def retrieve_patterns(
        self, case_id: str, scenarios: List[Dict],
        thought_callback: Optional[Callable] = None,
    ) -> Dict:
        """
        Search memory for historical patterns relevant to current scenarios.
        Returns matched patterns and insights.
        """
        start = self._logger.agent_start(
            self.codename, case_id, "retrieve_patterns",
            {"scenario_count": len(scenarios)},
        )

        # Build search queries from scenario descriptions
        queries = []
        for s in scenarios[:5]:
            name = s.get("name", "")
            desc = s.get("description", "")
            queries.append(f"{name} {desc}"[:200])

        self._logger.agent_step(
            self.codename, case_id, "retrieve_patterns",
            "Searching knowledge base",
            {"query_count": len(queries)},
        )

        # Search knowledge base for similar patterns
        all_matches = []
        for query in queries:
            try:
                results = await self.memory.query(
                    collection="knowledge_base",
                    query_texts=[query],
                    n_results=5,
                )
                all_matches.extend(results)
            except Exception as e:
                self._logger.warning(
                    f"Knowledge base query failed: {e}",
                    agent=self.codename, operation="retrieve_patterns",
                )

        # Also search past case analyses
        self._logger.agent_step(
            self.codename, case_id, "retrieve_patterns",
            "Searching past case analyses",
        )
        try:
            case_results = await self.memory.query(
                collection="case_analysis",
                query_texts=[f"case {case_id} similar patterns outcomes"],
                n_results=10,
            )
            all_matches.extend(case_results)
        except Exception as e:
            self._logger.warning(
                f"Case analysis query failed: {e}",
                agent=self.codename, operation="retrieve_patterns",
            )

        # Synthesize findings via LLM
        self._logger.agent_step(
            self.codename, case_id, "retrieve_patterns",
            "Synthesizing pattern insights",
            {"total_matches": len(all_matches)},
        )

        if all_matches and self.llm:
            match_summaries = [
                m.get("document", m.get("text", ""))[:300] for m in all_matches[:10]
            ]
            prompt = (
                f"Given these historical data excerpts, identify patterns relevant to the "
                f"current case scenarios.\n\nExcerpts:\n"
                + "\n---\n".join(match_summaries)
                + "\n\nScenarios:\n"
                + json.dumps([s.get("name", "") for s in scenarios])
                + "\n\nOutput JSON: {{\"patterns\": [...], \"insights\": [...], \"confidence\": 0.0-1.0}}"
            )
            try:
                response = await self.think(prompt)
                result = json.loads(response)
            except Exception:
                result = {"patterns": [], "insights": [], "confidence": 0.3}
        else:
            result = {"patterns": [], "insights": ["No historical data available"], "confidence": 0.1}

        result["matches"] = all_matches[:10]

        self._logger.agent_complete(
            self.codename, case_id, "retrieve_patterns", start,
            {"pattern_count": len(result.get("patterns", [])),
             "match_count": len(result.get("matches", []))},
        )
        return result

    async def store_case_outcome(
        self, case_id: str, outcome: Dict,
    ) -> bool:
        """Store a case outcome for future pattern matching."""
        self._logger.agent_step(
            self.codename, case_id, "store_case_outcome",
            "Storing outcome for future reference",
        )
        try:
            await self.memory.add_knowledge(
                text=json.dumps(outcome, default=str)[:5000],
                metadata={"case_id": case_id, "type": "case_outcome"},
            )
            return True
        except Exception as e:
            self._logger.error(
                f"Failed to store case outcome: {e}",
                agent=self.codename, operation="store_case_outcome",
            )
            return False
