"""
Agent Base Class
Base class for all agents with LLM integration and profile loading.
"""

import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

from backend.llm.wrapper import LLMWrapper

AGENTS_ROOT = Path(__file__).parent.parent.parent / "agents"


@dataclass
class AgentProfile:
    """Agent profile loaded from markdown files."""

    system_agent: str = ""
    smart_library: str = ""
    smart_memory: str = ""

    @property
    def system_prompt(self) -> str:
        """Combine all profile parts into system prompt."""
        parts = []
        if self.system_agent:
            parts.append(f"### CORE SYSTEM PROMPT\n{self.system_agent}")
        if self.smart_library:
            parts.append(f"### SMART LIBRARY (TOOLS & SKILLS)\n{self.smart_library}")
        if self.smart_memory:
            parts.append(f"### SMART MEMORY (EXPERIENCE & RULES)\n{self.smart_memory}")
        return "\n\n".join(parts)


class BaseAgent:
    """Base class for all agents."""

    def __init__(
        self,
        agent_name: str,
        codename: str,
        profile_dir: str,
        llm: Optional[LLMWrapper] = None,
        task_type: str = "general",
    ):
        self.name = agent_name
        self.codename = codename
        self.profile_dir = profile_dir
        self.llm = llm
        self.profile = self._load_profile()
        self.conversation_history: List[Dict[str, str]] = []
        self.task_type = task_type

    def _load_profile(self) -> AgentProfile:
        """Load agent profile from markdown files."""
        profile = AgentProfile()

        system_path = AGENTS_ROOT / "profiles" / self.profile_dir / "SystemAgent.md"
        library_path = AGENTS_ROOT / "profiles" / self.profile_dir / "SmartLibrary.md"
        memory_path = AGENTS_ROOT / "profiles" / self.profile_dir / "SmartMemory.md"

        if system_path.exists():
            profile.system_agent = system_path.read_text()
        if library_path.exists():
            profile.smart_library = library_path.read_text()
        if memory_path.exists():
            profile.smart_memory = memory_path.read_text()

        return profile

    async def think(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Have the agent think about something using LLM."""

        full_prompt = self._build_prompt(prompt, context, retrieved_chunks)

        response = await self.llm.generate(
            prompt=full_prompt,
            system_prompt=self.profile.system_prompt,
            temperature=temperature,
            task_type=self.task_type,
        )

        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append(
            {"role": "assistant", "content": response.content}
        )

        return response.content

    def _build_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Build prompt with context and RAG-retrieved document excerpts."""

        parts = [prompt]

        # Add RAG-retrieved document excerpts
        if retrieved_chunks:
            parts.append("\n\n### RELEVANT DOCUMENT EXCERPTS")
            for i, chunk in enumerate(retrieved_chunks[:10], 1):
                source = chunk.get("metadata", {}).get("source", "unknown")
                text = chunk.get("text", "")[:800]
                parts.append(f"\n**[{i}] Source: {source}**\n{text}")

        # Add structured context
        if context:
            parts.append("\n\n### CONTEXT")

            if "target_names" in context:
                parts.append(
                    f"Target Beneficiaries: {', '.join(context['target_names'])}"
                )

            if "data" in context:
                data = context["data"]
                if isinstance(data, dict):
                    parts.append(f"\n```json\n{str(data)[:2000]}\n```")
                elif isinstance(data, str):
                    parts.append(f"\n{data[:2000]}")

            if "question" in context:
                parts.append(f"\n### QUESTION\n{context['question']}")

        return "\n".join(parts)

    async def debate(
        self, topic: str, other_agent: "BaseAgent", context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Debate with another agent."""

        my_position = await self.think(
            f"Argue for your position on: {topic}", context=context
        )

        other_position = await other_agent.think(
            f"Argue for your position on: {topic}", context=context
        )

        synthesis = await self.think(
            f"Synthesize these two positions:\n\n1. {self.codename}: {my_position[:500]}\n\n2. {other_agent.codename}: {other_position[:500]}",
            context={"question": "What is the best synthesis of these arguments?"},
        )

        return {
            "topic": topic,
            "positions": {
                self.codename: my_position,
                other_agent.codename: other_position,
            },
            "synthesis": synthesis,
        }

    async def analyze(self, *args, **kwargs): return {}
    async def generate_scenarios(self, *args, **kwargs): return []
    async def validate_scenarios(self, *args, **kwargs): return []
    async def revise_scenarios(self, *args, **kwargs): return []
    async def generate_strategic_report(self, *args, **kwargs): return ""
    async def generate_emails(self, *args, **kwargs): return []
    async def extract_contacts(self, *args, **kwargs): return []
    async def generate_visuals(self, *args, **kwargs): return []
    async def push_to_workspace(self, *args, **kwargs): return None
    async def analyze_and_challenge(self, *args, **kwargs): return {}

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []

    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "name": self.name,
            "codename": self.codename,
            "provider": self.llm.get_provider_info() if self.llm else "unknown",
            "has_profile": bool(self.profile.system_agent),
        }
