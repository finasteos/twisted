"""
Self-Improvement Agent
Analyzes the analysis process itself to suggest improvements for future runs.
"""

from typing import Dict, Any, List
from backend.llm.wrapper import get_llm

class SelfImprovementAgent:
    """Agent that suggests improvements to the user's data quality or app configuration."""

    def __init__(self):
        self.llm = get_llm()

    async def suggest_improvements(self, context: Dict[str, Any], results: Dict[Any, Any]) -> str:
        """Analyze the results and context to suggest what was missing."""

        confidence = context.get("analysis_confidence", 0)

        prompt = f"""
        As an AI Meta-Analyzer, review the following analysis summary and suggest improvements for the NEXT run.

        CONTEXT SUMMARY:
        - Confidence Score: {confidence}%
        - Document Count: {len(context.get("processed_docs", []))}
        - External Research: {'Used' if context.get("external_research") else 'Not Used'}
        - Deliverables Requested: {context.get("help_package", [])}

        AGENT RESULTS:
        { {k.value if hasattr(k, 'value') else str(k): getattr(v, 'codename', 'Agent') for k, v in results.items()} }

        YOUR TASK:
        Provide 3-5 concise, actionable suggestions to improve the quality of future analyses.
        Focus on:
        1. Missing data types (e.g., "Add more bank statements").
        2. Process improvements (e.g., "Run more debate rounds").
        3. Clarification needs (e.g., "Define the beneficiary's goals better").

        Format as a Markdown list.
        """

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt="You are an expert in AI analysis optimization.",
            task_type="fast"
        )
        return response.content
