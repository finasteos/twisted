"""
Intelligent routing between local LMStudio and Gemini cloud.
Respects M4 health, data sensitivity, and task characteristics.
"""

from typing import Optional
from dataclasses import dataclass
from backend.utils.resource_guardian import ThermalState

@dataclass
class RoutingDecision:
    provider: str  # "local" | "gemini-flash" | "gemini-pro"
    model_id: str
    reason: str
    estimated_latency: float
    privacy_level: str  # "on_device" | "encrypted_transit" | "cloud_processed"

class HybridLLMRouter:
    """
    The traffic controller for cognition.
    Every inference request gets routed optimally.
    """

    def __init__(self, gemini_wrapper, lmstudio_client, resource_guardian):
        self.gemini = gemini_wrapper
        self.local = lmstudio_client
        self.guardian = resource_guardian

    async def route(
        self,
        task_type: str,
        content: str,
        sensitivity: str = "normal",  # "low" | "normal" | "high" | "critical"
        context_size: int = 0,
        requires_tools: bool = False
    ) -> RoutingDecision:
        """
        Make optimal routing decision.
        """
        from backend.config.settings import settings

        # Hard Privacy Override: Force local if strict mode enabled
        if settings.DATA_PRIVACY_STRICT:
            return RoutingDecision(
                provider="local",
                model_id="llama3.2:8b",
                reason="Strict Privacy Mode: Forcing local execution",
                estimated_latency=3.5,
                privacy_level="on_device"
            )

        # Get current M4 health
        health = await self.guardian._capture_snapshot()

        # Decision tree
        if sensitivity == "critical" and health.thermal_state != ThermalState.CRITICAL:
            # Medical, legal privilege, trade secrets → local only
            return RoutingDecision(
                provider="local",
                model_id="llama3.2:8b",
                reason="Critical sensitivity: on-device processing required",
                estimated_latency=2.5,
                privacy_level="on_device"
            )

        if requires_tools and health.thermal_state != ThermalState.CRITICAL:
            # Tool use with custom endpoints
            return RoutingDecision(
                provider="gemini-pro-custom",
                model_id="gemini-3.1-pro-preview-customtools",
                reason="Custom tool execution required",
                estimated_latency=3.0,
                privacy_level="encrypted_transit"
            )

        if task_type == "image_ocr" and health.thermal_state == ThermalState.COOL:
            # MLX-optimized local vision
            return RoutingDecision(
                provider="local",
                model_id="llava-phi3",
                reason="MLX vision processing, thermal optimal",
                estimated_latency=1.2,
                privacy_level="on_device"
            )

        if context_size > 100000 or health.thermal_state in [ThermalState.HOT, ThermalState.CRITICAL]:
            # Large context or thermal stress → cloud
            return RoutingDecision(
                provider="gemini-pro",
                model_id="gemini-3.1-pro-preview",
                reason=f"{'Large context' if context_size > 100000 else 'Thermal protection'}",
                estimated_latency=4.0,
                privacy_level="cloud_processed"
            )

        # Default: Fast cloud for speed, local if privacy preferred
        if sensitivity == "high" and health.thermal_state == ThermalState.COOL:
            return RoutingDecision(
                provider="local",
                model_id="llama3.2:8b",
                reason="High sensitivity with optimal local conditions",
                estimated_latency=2.0,
                privacy_level="on_device"
            )

        # Using updated flash model as requested
        return RoutingDecision(
            provider="gemini-flash",
            model_id="gemini-2.5-flash-native-audio-preview-12-2025",
            reason="Default: speed and efficiency",
            estimated_latency=1.5,
            privacy_level="encrypted_transit"
        )
