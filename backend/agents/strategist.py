"""
Strategist Agent
Develops strategic options and recommendations.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio

AGENTS_ROOT = Path(__file__).parent.parent.parent / "agents"


class StrategistAgent:
    """The Grandmaster - develops strategic options."""

    def __init__(self):
        self.name = "Strategist"
        self.codename = "The Grandmaster"
        self.profile = self._load_profile()

    def _load_profile(self) -> Dict[str, str]:
        """Load agent profile from markdown files."""
        profile = {}

        for file_name in ["IDENTITY.md", "SKILLS.md", "SOUL.md"]:
            file_path = AGENTS_ROOT / "strategist" / file_name
            if file_path.exists():
                profile[file_name.replace(".md", "").lower()] = file_path.read_text()

        return profile

    async def analyze(
        self,
        context_brief: Dict[str, Any],
        legal_brief: Dict[str, Any],
        target_names: List[str],
        task_id: str,
    ) -> Dict[str, Any]:
        """Develop strategic options based on all analyses."""

        await asyncio.sleep(0.3)

        key_findings = context_brief.get("key_findings", [])
        risks = legal_brief.get("identified_risits", [])
        opportunities = legal_brief.get("career_analysis", {}).get("opportunities", [])

        options = self._generate_options(
            key_findings, risks, opportunities, target_names
        )
        ranked_options = self._rank_options(options)
        consequences = self._analyze_consequences(ranked_options[:3])

        brief = {
            "agent": self.name,
            "codename": self.codename,
            "task_id": task_id,
            "target_names": target_names,
            "strategic_options": ranked_options,
            "consequence_analysis": consequences,
            "primary_recommendation": ranked_options[0] if ranked_options else None,
            "implementation_roadmap": self._create_roadmap(ranked_options[:3]),
        }

        return brief

    def _generate_options(
        self,
        findings: List[str],
        risks: List[Dict[str, str]],
        opportunities: List[str],
        target_names: List[str],
    ) -> List[Dict[str, Any]]:
        """Generate strategic options."""

        options = [
            {
                "id": "opt_1",
                "title": "Proactive Engagement",
                "description": "Take immediate action to address identified issues before they escalate",
                "pros": [
                    "Prevents escalation",
                    "Shows good faith",
                    "Maintains control",
                ],
                "cons": ["Requires resources", "May reveal strategy"],
                "probability": 0.75,
                "impact": 0.8,
            },
            {
                "id": "opt_2",
                "title": "Defensive Positioning",
                "description": "Strengthen position while awaiting more information",
                "pros": ["Reduces risk", "Buys time", "Lower initial cost"],
                "cons": ["May lose opportunities", "Issues may escalate"],
                "probability": 0.85,
                "impact": 0.5,
            },
            {
                "id": "opt_3",
                "title": "Strategic Alliance",
                "description": "Seek partnerships or alliances to strengthen position",
                "pros": ["Shared risk", "Combined resources", "Enhanced credibility"],
                "cons": [
                    "Shared control",
                    "Potential conflicts",
                    "Complex negotiations",
                ],
                "probability": 0.6,
                "impact": 0.9,
            },
            {
                "id": "opt_4",
                "title": "Wait and Monitor",
                "description": "Monitor situation closely without immediate action",
                "pros": ["Preserves resources", "No premature commitment"],
                "cons": ["May miss windows", "Issues may worsen"],
                "probability": 0.7,
                "impact": 0.3,
            },
        ]

        if opportunities:
            options.append(
                {
                    "id": "opt_5",
                    "title": "Capitalize on Opportunity",
                    "description": "Immediately pursue identified opportunities",
                    "pros": ["First-mover advantage", "Potential high returns"],
                    "cons": ["Resource intensive", "Higher risk"],
                    "probability": 0.65,
                    "impact": 0.95,
                }
            )

        return options

    def _rank_options(self, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank options by expected value."""

        for option in options:
            prob = option.get("probability", 0.5)
            impact = option.get("impact", 0.5)
            option["expected_value"] = round(prob * impact, 2)
            option["score"] = round((prob + impact) / 2, 2)

        return sorted(options, key=lambda x: x.get("expected_value", 0), reverse=True)

    def _analyze_consequences(
        self, options: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """Analyze consequences for top options."""

        consequences = {}

        for option in options:
            option_id = option.get("id", "unknown")

            consequences[option_id] = [
                {
                    "order": "first",
                    "description": f"Immediate {option.get('title')} implementation",
                },
                {
                    "order": "second",
                    "description": "Stakeholder reactions and market response",
                },
                {
                    "order": "third",
                    "description": "Long-term positioning and relationship impacts",
                },
            ]

        return consequences

    def _create_roadmap(self, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create implementation roadmap."""

        roadmap = []

        phases = [
            {
                "phase": "Immediate (0-7 days)",
                "actions": "Gather additional information, notify key stakeholders",
            },
            {
                "phase": "Short-term (1-4 weeks)",
                "actions": "Execute primary strategy, establish monitoring",
            },
            {
                "phase": "Medium-term (1-3 months)",
                "actions": "Evaluate results, adjust approach as needed",
            },
            {
                "phase": "Long-term (3+ months)",
                "actions": "Finalize outcomes, document learnings",
            },
        ]

        roadmap.extend(phases)

        return roadmap


async def run_analysis(
    context_brief: Dict[str, Any],
    legal_brief: Dict[str, Any],
    target_names: List[str],
    task_id: str,
) -> Dict[str, Any]:
    """Standalone function to run strategic analysis."""
    agent = StrategistAgent()
    return await agent.analyze(context_brief, legal_brief, target_names, task_id)
