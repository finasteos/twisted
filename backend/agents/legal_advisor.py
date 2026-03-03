"""
Legal & Career Advisor Agent
Provides domain-specific legal and career analysis.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
import re

AGENTS_ROOT = Path(__file__).parent.parent.parent / "agents"


class LegalAdvisorAgent:
    """The Counsel - provides legal and career domain expertise."""

    def __init__(self):
        self.name = "Legal & Career Advisor"
        self.codename = "The Counsel"
        self.profile = self._load_profile()

    def _load_profile(self) -> Dict[str, str]:
        """Load agent profile from markdown files."""
        profile = {}

        for file_name in ["IDENTITY.md", "SKILLS.md", "SOUL.md"]:
            file_path = AGENTS_ROOT / "legal_advisor" / file_name
            if file_path.exists():
                profile[file_name.replace(".md", "").lower()] = file_path.read_text()

        return profile

    async def analyze(
        self, context_brief: Dict[str, Any], target_names: List[str], task_id: str
    ) -> Dict[str, Any]:
        """Run legal and career analysis."""

        await asyncio.sleep(0.2)

        key_findings = context_brief.get("key_findings", [])
        entities = context_brief.get("entities", {})

        legal_analysis = self._analyze_legal_implications(key_findings, entities)
        career_analysis = self._analyze_career_implications(key_findings, entities)
        rights_obligations = self._map_rights_obligations(key_findings)
        risks = self._identify_risks(key_findings, target_names)

        brief = {
            "agent": self.name,
            "codename": self.codename,
            "task_id": task_id,
            "target_names": target_names,
            "legal_analysis": legal_analysis,
            "career_analysis": career_analysis,
            "rights_obligations": rights_obligations,
            "identified_risks": risks,
            "recommendations": self._generate_recommendations(
                legal_analysis, career_analysis, risks
            ),
        }

        return brief

    def _analyze_legal_implications(
        self, findings: List[str], entities: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Analyze legal implications from findings."""

        legal_keywords = {
            "contract": ["contract", "agreement", "terms", "breach", "party"],
            "employment": ["employee", "employer", "termination", "salary", "benefits"],
            "liability": ["liable", "responsibility", "damages", "compensation"],
            "dispute": ["dispute", "conflict", "claim", "lawsuit", "arbitration"],
        }

        analysis = {
            "potential_issues": [],
            "relevant_contracts": [],
            "jurisdiction": "Unknown",
        }

        all_text = " ".join(findings).lower()

        for category, keywords in legal_keywords.items():
            matches = [kw for kw in keywords if kw in all_text]
            if matches:
                analysis["potential_issues"].append(
                    {
                        "category": category,
                        "indicators": matches,
                        "severity": "high" if len(matches) > 2 else "medium",
                    }
                )

        return analysis

    def _analyze_career_implications(
        self, findings: List[str], entities: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Analyze career implications from findings."""

        career_keywords = {
            "opportunity": ["offer", "promotion", "increase", "advance", "growth"],
            "negotiation": ["salary", "bonus", "benefits", "equity", "stock"],
            "risk": ["layoff", "termination", "quit", "resign", "fired"],
            "professional": ["skill", "experience", "certification", "license"],
        }

        analysis = {"opportunities": [], "negotiation_points": [], "risk_factors": []}

        all_text = " ".join(findings).lower()

        for category, keywords in career_keywords.items():
            matches = [kw for kw in keywords if kw in all_text]
            if matches:
                if category == "opportunity":
                    analysis["opportunities"].extend(matches)
                elif category == "negotiation":
                    analysis["negotiation_points"].extend(matches)
                elif category == "risk":
                    analysis["risk_factors"].extend(matches)

        return analysis

    def _map_rights_obligations(self, findings: List[str]) -> Dict[str, List[str]]:
        """Map rights and obligations from content."""

        rights = []
        obligations = []

        rights_keywords = ["right to", "entitled to", "can", "allowed to", "may"]
        obligation_keywords = [
            "must",
            "shall",
            "required to",
            "obligated to",
            "have to",
        ]

        for finding in findings:
            finding_lower = finding.lower()

            for kw in rights_keywords:
                if kw in finding_lower:
                    rights.append(finding[:100])
                    break

            for kw in obligation_keywords:
                if kw in finding_lower:
                    obligations.append(finding[:100])
                    break

        return {"rights": rights[:5], "obligations": obligations[:5]}

    def _identify_risks(
        self, findings: List[str], target_names: List[str]
    ) -> List[Dict[str, str]]:
        """Identify potential risks to beneficiaries."""

        risks = []
        risk_keywords = [
            "risk",
            "danger",
            "threat",
            "problem",
            "issue",
            "concern",
            "warning",
        ]

        for finding in findings:
            finding_lower = finding.lower()

            for name in target_names:
                if name.lower() in finding_lower:
                    for kw in risk_keywords:
                        if kw in finding_lower:
                            risks.append(
                                {
                                    "description": finding[:100],
                                    "severity": "high"
                                    if "danger" in finding_lower
                                    or "threat" in finding_lower
                                    else "medium",
                                }
                            )
                            break

        return risks[:5]

    def _generate_recommendations(
        self, legal: Dict[str, Any], career: Dict[str, Any], risks: List[Dict[str, str]]
    ) -> List[str]:
        """Generate domain-specific recommendations."""

        recommendations = []

        if legal.get("potential_issues"):
            recommendations.append(
                "Review all contracts and agreements mentioned in documents with legal counsel"
            )

        if career.get("opportunities"):
            recommendations.append(
                "Capitalize on identified career opportunities; prepare negotiation strategy"
            )

        if risks:
            high_severity = [r for r in risks if r.get("severity") == "high"]
            if high_severity:
                recommendations.append(
                    "Address high-severity risks immediately; develop mitigation plan"
                )

        if not recommendations:
            recommendations.append(
                "Continue monitoring situation; maintain documentation"
            )

        return recommendations


async def run_analysis(
    context_brief: Dict[str, Any], target_names: List[str], task_id: str
) -> Dict[str, Any]:
    """Standalone function to run legal/career analysis."""
    agent = LegalAdvisorAgent()
    return await agent.analyze(context_brief, target_names, task_id)
