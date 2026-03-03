"""
MLX-optimized resource guardian for M4 MacBook Pro.
Prevents thermal throttling, manages unified memory pressure,
and orchestrates local/cloud handoffs.
"""

import asyncio
import psutil
from dataclasses import dataclass
from typing import Callable, Optional
from enum import Enum

class ThermalState(Enum):
    COOL = "cool"           # < 70°C
    WARM = "warm"           # 70-85°C
    HOT = "hot"             # 85-95°C
    CRITICAL = "critical"   # > 95°C

@dataclass
class M4HealthSnapshot:
    cpu_percent: float
    memory_pressure: float  # 0-1 scale
    thermal_state: ThermalState
    gpu_utilization: Optional[float]
    unified_memory_used: float  # GB
    unified_memory_total: float  # GB
    recommended_action: str

class M4ResourceGuardian:
    """
    Monitors M4 Silicon health in real-time.
    Makes intelligent routing decisions: local vs cloud.
    """

    THERMAL_THRESHOLDS = {
        ThermalState.COOL: 70,
        ThermalState.WARM: 85,
        ThermalState.HOT: 95
    }

    def __init__(self, check_interval: float = 5.0):
        self.check_interval = check_interval
        self.callbacks: list[Callable[[M4HealthSnapshot], None]] = []
        self._monitoring = False

    async def start_monitoring(self):
        """Begin continuous health monitoring."""
        self._monitoring = True
        while self._monitoring:
            snapshot = await self._capture_snapshot()

            # Notify subscribers (Pulse Monitor, Coordinator, etc.)
            for cb in self.callbacks:
                if asyncio.iscoroutinefunction(cb):
                    await cb(snapshot)
                else:
                    cb(snapshot)

            await asyncio.sleep(self.check_interval)

    async def _capture_snapshot(self) -> M4HealthSnapshot:
        """Capture current M4 health metrics."""
        # CPU and memory
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # Thermal state via macOS powermetrics (requires sudo, fallback to estimation)
        thermal = await self._detect_thermal_state(cpu, memory.percent)

        # Unified memory (Apple Silicon specific)
        mem_used = memory.used / (1024**3)
        mem_total = memory.total / (1024**3)

        # Recommendation logic
        action = self._generate_recommendation(cpu, memory.percent, thermal)

        return M4HealthSnapshot(
            cpu_percent=cpu,
            memory_pressure=memory.percent / 100,
            thermal_state=thermal,
            gpu_utilization=None,  # Would need IOKit bindings
            unified_memory_used=mem_used,
            unified_memory_total=mem_total,
            recommended_action=action
        )

    async def _detect_thermal_state(self, cpu: float, memory: float) -> ThermalState:
        """
        Estimate thermal state from system metrics.
        Real thermal data requires powermetrics or IOKit.
        """
        # Heuristic: high CPU + high memory = thermal stress
        stress_score = (cpu * 0.6) + (memory * 0.4)

        if stress_score > 90:
            return ThermalState.CRITICAL
        elif stress_score > 80:
            return ThermalState.HOT
        elif stress_score > 60:
            return ThermalState.WARM
        return ThermalState.COOL

    def _generate_recommendation(self, cpu: float, memory: float, thermal: ThermalState) -> str:
        """Generate routing recommendation based on health."""
        if thermal in [ThermalState.HOT, ThermalState.CRITICAL]:
            return "CLOUD_PRIORITY: M4 thermal protection active. Route to Gemini cloud."
        elif memory > 85:
            return "HYBRID: Large context to cloud, sensitive extraction local."
        elif cpu > 80:
            return "QUEUE_DEFER: Batch local jobs, prioritize real-time to cloud."
        return "LOCAL_FRIENDLY: M4 optimal for MLX acceleration."

    def should_route_local(self, task: dict, snapshot: M4HealthSnapshot) -> bool:
        """
        Decision engine: Should this task run locally or cloud?
        """
        from backend.config.settings import settings

        # Hard bypass for thermal relief
        if settings.DISABLE_LOCAL_MLX:
            return False

        # Force cloud for heavy inference when thermal stress
        if snapshot.thermal_state in [ThermalState.HOT, ThermalState.CRITICAL]:
            return False

        # Force cloud for large context windows
        estimated_tokens = task.get('estimated_tokens', 0)
        if estimated_tokens > 32768 and snapshot.memory_pressure > 0.7:
            return False

        # Prefer local for sensitive data
        if task.get('contains_pii', False) and snapshot.thermal_state == ThermalState.COOL:
            return True

        # Prefer local for image preprocessing (MLX advantage)
        if task.get('type') == 'image_preprocessing':
            return snapshot.thermal_state != ThermalState.CRITICAL

        return True  # Default local for MLX-optimized tasks

    async def emergency_cooldown(self):
        """Emergency measures if M4 overheating."""
        # Pause non-critical background jobs
        # Reduce batch sizes
        # Force cloud routing for 60 seconds
        pass
