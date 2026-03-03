from typing import Dict, List, Optional, Callable
from backend.agents.base_agent import BaseAgent

class EchoVaultAgent(BaseAgent):
    def __init__(self, llm, memory, comm):
        super().__init__(
            agent_name="Echo Vault",
            codename="echo_vault",
            profile_dir="echo_vault",
            llm=llm,
            task_type="memory"
        )
        self.memory = memory
        self.comm = comm
