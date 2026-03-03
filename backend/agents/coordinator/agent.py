from typing import Dict, List, Optional, Callable
from backend.agents.base_agent import BaseAgent

class CoordinatorAlphaAgent(BaseAgent):
    def __init__(self, llm, memory, comm):
        super().__init__(
            agent_name="Coordinator Alpha",
            codename="coordinator",
            profile_dir="coordinator",
            llm=llm,
            task_type="general"
        )
        self.memory = memory
        self.comm = comm
