from typing import Dict, List, Optional, Callable
from backend.agents.base_agent import BaseAgent

class DisputeSkepticAgent(BaseAgent):
    """
    The Red Team / Devil's Advocate.
    Sole mission: Challenge assumptions, find contradictions, and demand evidence.
    """
    def __init__(self, llm, memory, comm):
        super().__init__(
            agent_name="Dispute Skeptic",
            codename="dispute_skeptic",
            profile_dir="dispute_skeptic",
            llm=llm,
            task_type="analysis"
        )
        self.llm = llm # Ensure llm is stored
        self.memory = memory
        self.comm = comm

    async def analyze_and_challenge(
        self,
        case_id: str,
        scenarios: List[Dict],
        thought_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Adversarial review of proposed scenarios.
        """
        prompt = f"""You are the DISPUTE SKEPTIC. Your role is ADVERSARIAL REVIEW.
Analyze the following proposed scenarios for case {case_id}.
Your goal is to be the 'Devil's Advocate':
1. Identify unsupported assumptions.
2. Flag 'Hallucinated Confidence' where an agent sounds too sure without data.
3. Demand specific citations from the provided evidence.
4. Search for logical contradictions between scenarios and context.

Scenarios to review:
{scenarios}

Output format: JSON with 'challenges' (list of critiques), 'risk_rating' (0-1), and 'consensus_veto' (boolean).
If you see any claim not backed by evidence, set 'consensus_veto' to true.
"""
        response = await self.llm.generate(
            prompt=prompt,
            task_complexity="analysis"
        )
        # Parse result (simplified)
        import json
        try:
            return json.loads(response.text)
        except:
            return {"challenges": ["Failed to parse skeptic output"], "consensus_veto": True}
