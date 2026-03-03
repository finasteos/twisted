"""
Context Analyzer Agent
Analyzes documents and extracts structured intelligence.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
import re

AGENTS_ROOT = Path(__file__).parent.parent.parent / "agents"


class ContextAnalyzerAgent:
    """The Archivist - extracts and organizes information from documents."""

    def __init__(self):
        self.name = "Context Analyzer"
        self.codename = "The Archivist"
        self.profile = self._load_profile()

    def _load_profile(self) -> Dict[str, str]:
        """Load agent profile from markdown files."""
        profile = {}

        for file_name in ["IDENTITY.md", "SKILLS.md", "SOUL.md"]:
            file_path = AGENTS_ROOT / "context_analyzer" / file_name
            if file_path.exists():
                profile[file_name.replace(".md", "").lower()] = file_path.read_text()

        return profile

    async def analyze(
        self, processed_data: Dict[str, Any], target_names: List[str], task_id: str
    ) -> Dict[str, Any]:
        """Run context analysis on processed documents."""

        await asyncio.sleep(0.2)

        processed_files = processed_data.get("processed", [])

        entities = self._extract_entities(processed_files, target_names)
        timeline = self._extract_timeline(processed_files)
        key_findings = self._extract_findings(processed_files, target_names)
        sentiment = self._analyze_sentiment(processed_files)

        brief = {
            "agent": self.name,
            "codename": self.codename,
            "task_id": task_id,
            "target_names": target_names,
            "executive_summary": self._generate_summary(key_findings, target_names),
            "entities": entities,
            "timeline": timeline,
            "key_findings": key_findings,
            "sentiment": sentiment,
            "information_gaps": self._identify_gaps(processed_files),
            "confidence": self._calculate_confidence(processed_files),
        }

        return brief

    def _extract_entities(
        self, files: List[Dict[str, Any]], target_names: List[str]
    ) -> Dict[str, List[str]]:
        """Extract named entities from documents."""

        all_text = " ".join([f.get("content", "")[:5000] for f in files])

        entities = {
            "people": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "money": [],
            "target_beneficiaries": target_names,
        }

        person_pattern = r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"
        entities["people"] = list(set(re.findall(person_pattern, all_text)))[:20]

        org_pattern = (
            r"\b(?:Corp|Inc|LLC|Ltd|AB|Sweden|USA|EU|Google|Apple|Microsoft)\b"
        )
        entities["organizations"] = list(set(re.findall(org_pattern, all_text)))[:15]

        money_pattern = r"(?:SEK|EUR|USD|kr|€|$)\s*\d+(?:,\d{3})*(?:\.\d{2})?"
        entities["money"] = list(set(re.findall(money_pattern, all_text)))[:10]

        return entities

    def _extract_timeline(self, files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract timeline of events."""

        timeline = []

        date_patterns = [
            r"\b(\d{4}-\d{2}-\d{2})\b",
            r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b",
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
        ]

        all_text = " ".join([f.get("content", "") for f in files])

        for pattern in date_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            for match in matches[:5]:
                timeline.append(
                    {"date": match, "description": "Date reference found in documents"}
                )

        return timeline[:10]

    def _extract_findings(
        self, files: List[Dict[str, Any]], target_names: List[str]
    ) -> List[str]:
        """Extract key findings from documents."""

        findings = []

        keywords = [
            "important",
            "critical",
            "significant",
            "must",
            "should",
            "recommend",
            "require",
            "decision",
            "action",
            "deadline",
            "offer",
            "contract",
            "agreement",
            "dispute",
            "issue",
        ]

        for file in files:
            content = file.get("content", "")
            content_lower = content.lower()

            for keyword in keywords:
                if keyword in content_lower:
                    idx = content_lower.find(keyword)
                    context = content[max(0, idx - 30) : idx + 50]

                    if context not in findings:
                        findings.append(context.strip())

        return findings[:15]

    def _analyze_sentiment(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall sentiment."""

        all_text = " ".join([f.get("content", "") for f in files])
        all_lower = all_text.lower()

        positive_words = [
            "good",
            "great",
            "excellent",
            "success",
            "benefit",
            "positive",
            "agree",
            "happy",
        ]
        negative_words = [
            "bad",
            "poor",
            "fail",
            "loss",
            "negative",
            "disagree",
            "problem",
            "issue",
            "dispute",
        ]

        positive_count = sum(1 for w in positive_words if w in all_lower)
        negative_count = sum(1 for w in negative_words if w in all_lower)

        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "overall": sentiment,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
        }

    def _identify_gaps(self, files: List[Dict[str, Any]]) -> List[str]:
        """Identify missing information."""

        gaps = []

        if len(files) < 3:
            gaps.append("Limited number of documents provided")

        total_content = sum(len(f.get("content", "")) for f in files)
        if total_content < 1000:
            gaps.append("Limited content volume for comprehensive analysis")

        return gaps

    def _calculate_confidence(self, files: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on data quality."""

        if not files:
            return 0.0

        volume_score = min(len(files) / 10.0, 1.0)

        total_content = sum(len(f.get("content", "")) for f in files)
        content_score = min(total_content / 50000.0, 1.0)

        return round((volume_score * 0.4 + content_score * 0.6) * 100, 1)

    def _generate_summary(self, findings: List[str], target_names: List[str]) -> str:
        """Generate executive summary."""

        names_str = ", ".join(target_names)

        summary = f"""
Analysis of provided documents concerning: {names_str}

Based on the document review, this analysis identifies {len(findings)} key 
information points that may be relevant to decision-making for the named 
beneficiaries.

The documents have been processed and structured for strategic analysis.
        """.strip()

        return summary


async def run_analysis(
    processed_data: Dict[str, Any], target_names: List[str], task_id: str
) -> Dict[str, Any]:
    """Standalone function to run context analysis."""
    agent = ContextAnalyzerAgent()
    return await agent.analyze(processed_data, target_names, task_id)
