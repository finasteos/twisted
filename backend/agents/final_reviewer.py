"""
Final Reviewer Agent
Validates analysis and ensures quality.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio

AGENTS_ROOT = Path(__file__).parent.parent.parent / "agents"


class FinalReviewerAgent:
    """The Judge - validates and finalizes analysis."""

    def __init__(self):
        self.name = "Final Reviewer"
        self.codename = "The Judge"
        self.profile = self._load_profile()

    def _load_profile(self) -> Dict[str, str]:
        """Load agent profile from markdown files."""
        profile = {}

        for file_name in ["IDENTITY.md", "SKILLS.md", "SOUL.md"]:
            file_path = AGENTS_ROOT / "final_reviewer" / file_name
            if file_path.exists():
                profile[file_name.replace(".md", "").lower()] = file_path.read_text()

        return profile

    async def review(
        self,
        context_brief: Dict[str, Any],
        legal_brief: Dict[str, Any],
        strategy_brief: Dict[str, Any],
        target_names: List[str],
        task_id: str,
    ) -> Dict[str, Any]:
        """Perform final quality review."""

        await asyncio.sleep(0.2)

        logic_check = self._validate_logic(context_brief, strategy_brief)
        completeness_check = self._check_completeness(
            context_brief, legal_brief, strategy_brief
        )
        risks_check = self._identify_blind_spots(context_brief, strategy_brief)

        quality_metrics = {
            "coherence_score": logic_check.get("score", 0.5),
            "completeness_score": completeness_check.get("score", 0.5),
            "actionability_score": 0.8,
            "risk_coverage": risks_check.get("score", 0.5),
        }

        overall_quality = sum(quality_metrics.values()) / len(quality_metrics)

        brief = {
            "agent": self.name,
            "codename": self.codename,
            "task_id": task_id,
            "target_names": target_names,
            "quality_metrics": quality_metrics,
            "overall_quality": round(overall_quality, 2),
            "logic_validation": logic_check,
            "completeness_check": completeness_check,
            "blind_spots": risks_check.get("gaps", []),
            "approval_status": "approved"
            if overall_quality >= 0.6
            else "needs_revision",
            "final_recommendation": self._final_recommendation(
                strategy_brief, overall_quality
            ),
        }

        return brief

    def _validate_logic(
        self, context: Dict[str, Any], strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate logical consistency."""

        issues = []
        score = 0.9

        key_findings = context.get("key_findings", [])
        if not key_findings:
            issues.append("No key findings to base strategy on")
            score -= 0.3

        options = strategy.get("strategic_options", [])
        if not options:
            issues.append("No strategic options generated")
            score -= 0.4

        return {
            "score": max(0, score),
            "issues": issues,
            "status": "valid" if score >= 0.6 else "invalid",
        }

    def _check_completeness(
        self, context: Dict[str, Any], legal: Dict[str, Any], strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check completeness of analysis."""

        missing = []
        score = 1.0

        if not context.get("entities", {}).get("people"):
            missing.append("No entities identified")
            score -= 0.2

        if not legal.get("rights_obligations", {}).get("rights"):
            missing.append("No rights identified")
            score -= 0.15

        if not strategy.get("strategic_options"):
            missing.append("No strategic options")
            score -= 0.3

        roadmap = strategy.get("implementation_roadmap", [])
        if len(roadmap) < 2:
            missing.append("Limited implementation plan")
            score -= 0.1

        return {
            "score": max(0, score),
            "missing_elements": missing,
            "status": "complete" if score >= 0.7 else "incomplete",
        }

    def _identify_blind_spots(
        self, context: Dict[str, Any], strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify potential blind spots."""

        gaps = []
        score = 0.8

        confidence = context.get("confidence", 100)
        if confidence < 70:
            gaps.append(f"Low confidence in data ({confidence}%)")
            score -= 0.2

        sentiment = context.get("sentiment", {}).get("overall", "neutral")
        if sentiment == "negative":
            gaps.append("Negative sentiment detected - consider emotional factors")
            score -= 0.1

        risks = strategy.get("strategic_options", [{}])[0].get("cons", [])
        if len(risks) > 3:
            gaps.append("High number of cons in primary option - reconsider")
            score -= 0.1

        return {
            "score": max(0, score),
            "gaps": gaps,
            "status": "adequate" if score >= 0.6 else "concerning",
        }

    def _final_recommendation(self, strategy: Dict[str, Any], quality: float) -> str:
        """Generate final recommendation."""

        if quality < 0.5:
            return "DO NOT PROCEED - Insufficient analysis quality"

        primary = strategy.get("primary_recommendation", {})
        if primary:
            title = primary.get("title", "Unknown")
            ev = primary.get("expected_value", 0)

            if quality >= 0.8:
                return f"PROCEED with '{title}' (Expected Value: {ev})"
            else:
                return f"PROCEED WITH CAUTION - '{title}' (Quality: {quality:.0%})"

        return "REVIEW REQUIRED - Insufficient data for recommendation"


async def run_review(
    context_brief: Dict[str, Any],
    legal_brief: Dict[str, Any],
    strategy_brief: Dict[str, Any],
    target_names: List[str],
    task_id: str,
) -> Dict[str, Any]:
    """Standalone function to run final review."""
    agent = FinalReviewerAgent()
    return await agent.review(
        context_brief, legal_brief, strategy_brief, target_names, task_id
    )
