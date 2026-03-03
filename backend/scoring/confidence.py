"""
Confidence Scorer
Calculates analysis confidence based on data quality, model agreement, and retrieval relevance.
"""

from typing import List, Dict, Any, Optional

class ConfidenceScorer:
    """Calculates a confidence score (0-100%) for the final analysis."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def calculate_confidence(self, context: Dict[str, Any], results: Dict[Any, Any]) -> float:
        """
        Derive confidence from multiple dimensions:
        1. Data Density: Number of documents and total context size.
        2. Model Agreement: Consistency in sentiment/direction across different agents.
        3. Retrieval Quality: Average similarity scores for retrieved chunks.
        4. Research Coverage: Presence of external web research.
        """
        score = 0.0
        weights = {
            "data_density": 0.3,
            "consistency": 0.3,
            "retrieval": 0.2,
            "enrichment": 0.2
        }

        # 1. Data Density (Simplified: 0-10 based on doc count)
        doc_count = len(context.get("processed_docs", []))
        density_score = min(doc_count * 2, 10) # 5 docs = max density score
        score += density_score * weights["data_density"]

        # 2. Consistency (Simplified: 0-10 based on debate rounds)
        # More rounds usually means more refinement, higher confidence in result
        debate_rounds = context.get("debate_rounds", 0)
        consistency_score = min(debate_rounds * 2, 10)
        score += consistency_score * weights["consistency"]

        # 3. Retrieval (Simplified: check if RAG was used)
        retrieval_score = 10 if context.get("rag_active", False) else 5
        score += retrieval_score * weights["retrieval"]

        # 4. Enrichment
        enrichment_score = 10 if context.get("external_research") else 2
        score += enrichment_score * weights["enrichment"]

        return round(score * 10, 1) # Convert to percentage 0-100
