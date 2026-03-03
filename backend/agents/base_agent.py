"""
Agent Base Class
Base class for all agents with LLM integration, profile loading,
verbose logging, and bounded conversation history.
"""

import time
from typing import Any, Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

from backend.llm.wrapper import LLMWrapper
from backend.logging_config import get_logger

AGENTS_ROOT = Path(__file__).parent.parent.parent / "agents"

# Default limits (can be overridden via Settings)
DEFAULT_CONVERSATION_HISTORY_LIMIT = 50


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
    """Base class for all agents with verbose logging and bounded memory."""

    def __init__(
        self,
        agent_name: str,
        codename: str,
        profile_dir: str,
        llm: Optional[LLMWrapper] = None,
        task_type: str = "general",
        conversation_history_limit: int = DEFAULT_CONVERSATION_HISTORY_LIMIT,
    ):
        self.name = agent_name
        self.codename = codename
        self.profile_dir = profile_dir
        self.llm = llm
        self.profile = self._load_profile()
        self.conversation_history: List[Dict[str, str]] = []
        self.task_type = task_type
        self._history_limit = conversation_history_limit
        self._logger = get_logger(f"agent.{codename}")

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

    def _trim_conversation_history(self) -> None:
        """Trim conversation history to the configured limit (FIFO)."""
        if len(self.conversation_history) > self._history_limit:
            removed = len(self.conversation_history) - self._history_limit
            self.conversation_history = self.conversation_history[-self._history_limit:]
            self._logger.debug(
                f"Trimmed {removed} old messages from conversation history",
                agent=self.codename,
                operation="trim_history",
                details={"removed": removed, "remaining": len(self.conversation_history)},
            )

    async def think(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Have the agent think about something using LLM."""
        start = self._logger.agent_start(
            self.codename, "", "think",
            {"prompt_preview": prompt[:100], "has_context": context is not None},
        )

        full_prompt = self._build_prompt(prompt, context, retrieved_chunks)

        self._logger.agent_step(
            self.codename, "", "think",
            "Calling LLM",
            {"prompt_length": len(full_prompt), "temperature": temperature},
        )

        llm_start = time.time()
        response = await self.llm.generate(
            prompt=full_prompt,
            system_prompt=self.profile.system_prompt,
            temperature=temperature,
            task_type=self.task_type,
        )
        llm_duration = round((time.time() - llm_start) * 1000, 2)

        self._logger.llm_call(
            self.codename,
            getattr(self.llm, 'model', 'unknown'),
            len(full_prompt),
            len(response.content),
            llm_duration,
        )

        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append(
            {"role": "assistant", "content": response.content}
        )
        self._trim_conversation_history()

        self._logger.agent_complete(
            self.codename, "", "think", start,
            {"response_length": len(response.content)},
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
        start = self._logger.agent_start(
            self.codename, "", "debate",
            {"topic": topic[:100], "opponent": other_agent.codename},
        )

        self._logger.agent_step(
            self.codename, "", "debate", "Formulating position",
        )
        my_position = await self.think(
            f"Argue for your position on: {topic}", context=context
        )

        self._logger.agent_step(
            self.codename, "", "debate",
            f"Getting {other_agent.codename}'s position",
        )
        other_position = await other_agent.think(
            f"Argue for your position on: {topic}", context=context
        )

        self._logger.agent_step(
            self.codename, "", "debate", "Synthesizing positions",
        )
        synthesis = await self.think(
            f"Synthesize these two positions:\n\n1. {self.codename}: {my_position[:500]}\n\n2. {other_agent.codename}: {other_position[:500]}",
            context={"question": "What is the best synthesis of these arguments?"},
        )

        self._logger.agent_complete(
            self.codename, "", "debate", start,
            {"synthesis_length": len(synthesis)},
        )

        return {
            "topic": topic,
            "positions": {
                self.codename: my_position,
                other_agent.codename: other_position,
            },
            "synthesis": synthesis,
        }

    async def analyze(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {}

    async def generate_scenarios(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        return []

    async def validate_scenarios(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        return []

    async def revise_scenarios(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        return []

    async def generate_strategic_report(self, *args: Any, **kwargs: Any) -> str:
        return ""

    async def generate_emails(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        return []

    async def extract_contacts(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        return []

    async def generate_visuals(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        return []

    async def push_to_workspace(self, *args: Any, **kwargs: Any) -> Optional[Dict[str, Any]]:
        return None

    async def analyze_and_challenge(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return {}

    def reset_conversation(self) -> None:
        """Clear conversation history."""
        old_len = len(self.conversation_history)
        self.conversation_history = []
        self._logger.info(
            f"Reset conversation history (cleared {old_len} messages)",
            agent=self.codename,
            operation="reset_conversation",
        )

    def get_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            "name": self.name,
            "codename": self.codename,
            "provider": self.llm.get_provider_info() if self.llm else "unknown",
            "has_profile": bool(self.profile.system_agent),
            "conversation_history_size": len(self.conversation_history),
            "conversation_history_limit": self._history_limit,
        }
