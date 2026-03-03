"""
Decision Matrix Scoring Engine
Implements weighted scoring for strategic options based on the v1 blueprint.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ScoringCriteria:
    name: str
    weight: float
    description: str

class DecisionMatrix:
    """Calculates weighted scores for strategic recommendations."""

    DEFAULT_CRITERIA = [
        ScoringCriteria("Impact", 0.30, "Potential for significant positive change"),
        ScoringCriteria("Feasibility", 0.20, "Ease of implementation / technical difficulty"),
        ScoringCriteria("Risk", 0.15, "Potential negative consequences (lower is better, but here we score 0-10 where 10 is safe)"),
        ScoringCriteria("Benefit", 0.20, "Direct value to the beneficiary"),
        ScoringCriteria("Timeline", 0.10, "Speed of execution"),
        ScoringCriteria("Cost", 0.05, "Financial efficiency")
    ]

    def __init__(self, criteria: Optional[List[ScoringCriteria]] = None):
        self.criteria = criteria or self.DEFAULT_CRITERIA

    def score_option(self, scores: Dict[str, float]) -> float:
        """Calculate weighted score for a single option (0.0 - 10.0)."""
        weighted_total = 0.0
        for criterion in self.criteria:
            score = scores.get(criterion.name, 5.0) # Default to mid-range
            weighted_total += score * criterion.weight
        return round(weighted_total, 2)

    def rank_options(self, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank a list of options based on their internal scores."""
        for opt in options:
            opt["weighted_score"] = self.score_option(opt.get("scores", {}))

        return sorted(options, key=lambda x: x["weighted_score"], reverse=True)
