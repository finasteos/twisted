import json
from typing import Dict, List, Optional, Callable
from backend.agents.base_agent import BaseAgent

class OutcomeArchitectAgent(BaseAgent):
    def __init__(self, llm, memory, comm):
        super().__init__(
            agent_name="Outcome Architect",
            codename="outcome_architect",
            profile_dir="outcome_architect",
            llm=llm,
            task_type="reasoning"
        )
        self.memory = memory
        self.comm = comm

    async def generate_scenarios(self, case_id: str, thought_callback: Optional[Callable] = None) -> List[Dict]:
        prompt = f"Based on the analyzed context for case {case_id}, generate 3-5 potential outcome scenarios. Each scenario should have a name, description, steps, risks, and success_criteria. Output JSON list."
        response = await self.think(prompt)
        try:
            return json.loads(response)
        except:
            return []

    async def revise_scenarios(self, scenarios: List[Dict], challenges: List[str], thought_callback: Optional[Callable] = None) -> List[Dict]:
        prompt = f"Revise the following scenarios based on these challenges: {challenges}. Provide updated weighted_score and implementation details. Output JSON list."
        response = await self.think(prompt, context={"data": scenarios})
        try:
            return json.loads(response)
        except:
            return scenarios
