import json
from typing import Dict, List, Optional, Callable
from backend.agents.base_agent import BaseAgent
from backend.utils.google_maps import MapsClient


class ContextWeaverAgent(BaseAgent):
    def __init__(self, llm, memory, comm):
        super().__init__(
            agent_name="Context Weaver",
            codename="context_weaver",
            profile_dir="context_weaver",
            llm=llm,
            task_type="analysis"
        )
        self.memory = memory
        self.comm = comm
        self.maps = MapsClient()

    async def verify_location_data(self, entities: List[Dict]) -> List[Dict]:
        """Verify location entities using Google Maps."""
        verified = []
        for entity in entities:
            # Check if name exists and is a string before checking lower()
            name = entity.get('name')
            if entity.get('type') == 'location' or (isinstance(name, str) and 'address' in name.lower()):
                address = str(name) if name else ""
                info = await self.maps.verify_location(address)
                if info:
                    entity['verified_location'] = info
                    verified.append(entity)
        return verified

    async def analyze(self, case_id: str, documents: List[Dict], thought_callback: Optional[Callable] = None) -> Dict:
        prompt = f"Analyze the following documents for case {case_id} and extract structured context (entities, relationships, timeline, risk_flags). Output JSON."
        response = await self.think(prompt, context={"data": documents})
        try:
            return json.loads(response)
        except:
            return {"entities":[], "relationships":[], "timeline":[], "risk_flags":[]}

    async def validate_scenarios(self, case_id: str, scenarios: List[Dict], thought_callback: Optional[Callable] = None) -> Dict:
        prompt = f"Validate the following scenarios for case {case_id} against the known context. Identify challenges or contradictions. Output JSON."
        response = await self.think(prompt, context={"data": scenarios})
        try:
            return json.loads(response)
        except:
            return {"challenges": [], "confidence": 0.5}
