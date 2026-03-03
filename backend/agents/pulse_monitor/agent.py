from typing import Dict, List, Optional, Callable
from backend.agents.base_agent import BaseAgent

class PulseMonitorAgent(BaseAgent):
    def __init__(self, llm, memory, comm):
        super().__init__(
            agent_name="Pulse Monitor",
            codename="pulse_monitor",
            profile_dir="pulse_monitor",
            llm=llm,
            task_type="telemetry"
        )
        self.memory = memory
        self.comm = comm
