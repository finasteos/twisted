"""
Test M4 resource management.
"""

import pytest
from enum import Enum

class ThermalState(Enum):
    COOL = "cool"
    WARM = "warm"
    HOT = "hot"
    CRITICAL = "critical"

class M4ResourceGuardian:
    """Mock guardian for testing."""
    def _detect_thermal_state(self, cpu_usage: float, mem_usage: float) -> ThermalState:
        if cpu_usage > 90 or mem_usage > 90:
            return ThermalState.CRITICAL
        if cpu_usage > 80 or mem_usage > 80:
            return ThermalState.HOT
        if cpu_usage > 60 or mem_usage > 60:
            return ThermalState.WARM
        return ThermalState.COOL

    def should_route_local(self, task: dict, snapshot: any) -> bool:
        """
        Policy:
        - If CRITICAL or HOT, always Cloud.
        - If WARM, Cloud unless highly sensitive.
        - If COOL, Local.
        """
        if snapshot.thermal_state in [ThermalState.CRITICAL, ThermalState.HOT]:
            return False
        if snapshot.thermal_state == ThermalState.WARM:
            return task.get("contains_pii", False) # Local only if sensitive
        return True

def test_thermal_state_detection():
    """Test thermal state calculation from metrics."""
    guardian = M4ResourceGuardian()

    # Cool: low CPU, low memory
    assert guardian._detect_thermal_state(30, 40) == ThermalState.COOL

    # Warm: moderate stress
    assert guardian._detect_thermal_state(65, 60) == ThermalState.WARM

    # Hot: high stress
    assert guardian._detect_thermal_state(85, 85) == ThermalState.HOT

    # Critical: extreme stress
    assert guardian._detect_thermal_state(95, 95) == ThermalState.CRITICAL

def test_routing_decisions():
    """Test that routing respects thermal state."""
    guardian = M4ResourceGuardian()

    class Snapshot:
        def __init__(self, state, cpu, mem):
            self.thermal_state = state
            self.cpu_percent = cpu
            self.memory_pressure = mem

    cool_snapshot = Snapshot(ThermalState.COOL, 30, 0.4)
    warm_snapshot = Snapshot(ThermalState.WARM, 65, 0.6)
    hot_snapshot = Snapshot(ThermalState.HOT, 85, 0.9)

    # Cool: prefer local for sensitive
    task = {"contains_pii": True, "type": "analysis"}
    assert guardian.should_route_local(task, cool_snapshot) == True

    # Warm: still local for sensitive
    assert guardian.should_route_local(task, warm_snapshot) == True

    # Warm: cloud for non-sensitive
    task_non_sensitive = {"contains_pii": False, "type": "analysis"}
    assert guardian.should_route_local(task_non_sensitive, warm_snapshot) == False

    # Hot: force cloud despite sensitivity
    assert guardian.should_route_local(task, hot_snapshot) == False
