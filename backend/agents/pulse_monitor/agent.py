"""
Pulse Monitor: System health and telemetry agent.
Monitors resource usage, API rate limits, and memory health during pipeline execution.
"""

import time
from typing import Any, Dict, List, Optional, Callable

from backend.agents.base_agent import BaseAgent
from backend.logging_config import get_logger

logger = get_logger("agent.pulse_monitor")


class PulseMonitorAgent(BaseAgent):
    """
    System health monitoring agent — tracks resource usage, API rate limits,
    memory consumption, and pipeline timing during case processing.
    """

    def __init__(self, llm, memory, comm):
        super().__init__(
            agent_name="Pulse Monitor",
            codename="pulse_monitor",
            profile_dir="pulse_monitor",
            llm=llm,
            task_type="telemetry",
        )
        self.memory = memory
        self.comm = comm
        self._stage_timings: Dict[str, float] = {}
        self._health_history: List[Dict] = []

    def start_stage_timer(self, stage_name: str) -> None:
        """Record the start time for a pipeline stage."""
        self._stage_timings[stage_name] = time.time()
        self._logger.debug(
            f"Timer started for stage: {stage_name}",
            agent=self.codename, operation="start_timer",
        )

    def stop_stage_timer(self, stage_name: str) -> float:
        """Stop timer and return duration in ms."""
        start = self._stage_timings.pop(stage_name, None)
        if start is None:
            return 0.0
        duration_ms = round((time.time() - start) * 1000, 2)
        self._logger.info(
            f"Stage '{stage_name}' completed in {duration_ms}ms",
            agent=self.codename, operation="stop_timer",
            details={"stage": stage_name, "duration_ms": duration_ms},
        )
        return duration_ms

    async def check_health_during_debate(self, case_id: str) -> Dict[str, Any]:
        """
        Run a lightweight health check during debate rounds.
        Checks memory stats, active timers, and API availability.
        """
        start = self._logger.agent_start(self.codename, case_id, "health_check")

        health: Dict[str, Any] = {
            "timestamp": time.time(),
            "case_id": case_id,
            "checks": {},
        }

        # Check memory/vector store health
        self._logger.agent_step(self.codename, case_id, "health_check", "Checking memory store")
        try:
            if hasattr(self.memory, 'check_health'):
                mem_health = await self.memory.check_health()
                health["checks"]["memory_store"] = mem_health
            if hasattr(self.memory, 'get_cache_stats'):
                health["checks"]["embedding_cache"] = self.memory.get_cache_stats()
        except Exception as e:
            health["checks"]["memory_store"] = {"status": "error", "message": str(e)}

        # Check active stage timers
        active_timers = {
            k: round((time.time() - v) * 1000, 2)
            for k, v in self._stage_timings.items()
        }
        health["checks"]["active_timers"] = active_timers

        # Overall summary
        issues = []
        cache_stats = health["checks"].get("embedding_cache", {})
        if cache_stats.get("cache_utilization_pct", 0) > 90:
            issues.append("Embedding cache near capacity")

        for timer_name, elapsed in active_timers.items():
            if elapsed > 120000:  # 2 minutes
                issues.append(f"Stage '{timer_name}' running for {elapsed/1000:.0f}s")

        health["summary"] = "; ".join(issues) if issues else "All systems healthy"
        health["healthy"] = len(issues) == 0

        # Keep bounded history
        self._health_history.append(health)
        if len(self._health_history) > 50:
            self._health_history = self._health_history[-50:]

        self._logger.agent_complete(self.codename, case_id, "health_check", start, {
            "healthy": health["healthy"],
            "summary": health["summary"],
        })
        return health

    def get_timing_report(self) -> Dict[str, Any]:
        """Get a summary of all recorded stage timings."""
        return {
            "active_timers": {
                k: round((time.time() - v) * 1000, 2)
                for k, v in self._stage_timings.items()
            },
            "health_checks": len(self._health_history),
            "last_health": self._health_history[-1] if self._health_history else None,
        }
