"""
Gemini Model Configuration
VERIFIED MODELS ONLY - Always check https://ai.google.dev/models for latest

⚠️ RULE: Never add model names without verifying against the Gemini API first!
Use get_available_models_from_api() to fetch real-time model list.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
import httpx


@dataclass
class ModelInfo:
    name: str
    display_name: str
    description: str
    input_token_limit: int
    output_token_limit: int
    supports_thinking: bool
    supports_vision: bool
    supports_caching: bool
    tier_1_rpm: int
    tier_1_tpm: int
    tier_1_rpd: int
    is_deprecated: bool = False
    is_verified: bool = False  # Must be True for all verified models


# ⚠️ USER-VERIFIED MODELS - These work for this deployment
# Note: API list may not show preview models, but they work!
GEMINI_MODELS: Dict[str, ModelInfo] = {
    # Gemini 3 Series (User's main agents - VERIFIED BY USER)
    # Flash = gemini-3-flash-preview (NOT 3.1)
    # Pro = gemini-3.1-pro-preview (3.1)
    "gemini-3-flash-preview": ModelInfo(
        name="gemini-3-flash-preview",
        display_name="Gemini 3 Flash Preview",
        description="User's main fast model",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=False,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
    "gemini-3.1-pro-preview": ModelInfo(
        name="gemini-3.1-pro-preview",
        display_name="Gemini 3.1 Pro Preview",
        description="User's main pro model - may return 503 under high load",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=150,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
    # Gemini 2.5 Series (Stable - VERIFIED)
    "gemini-2.5-pro": ModelInfo(
        name="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        description="Stable release - most capable thinking model",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=150,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
    "gemini-2.5-flash": ModelInfo(
        name="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        description="Stable release - fast and capable",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
    "gemini-2.5-flash-lite": ModelInfo(
        name="gemini-2.5-flash-lite",
        display_name="Gemini 2.5 Flash-Lite",
        description="Most cost-effective option",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
    # Gemini 2.0 Series (VERIFIED)
    "gemini-2.0-flash": ModelInfo(
        name="gemini-2.0-flash",
        display_name="Gemini 2.0 Flash",
        description="Fast and versatile multimodal",
        input_token_limit=1_048_576,
        output_token_limit=8_192,
        supports_thinking=False,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
    "gemini-2.0-flash-001": ModelInfo(
        name="gemini-2.0-flash-001",
        display_name="Gemini 2.0 Flash 001",
        description="Stable version (January 2025)",
        input_token_limit=1_048_576,
        output_token_limit=8_192,
        supports_thinking=False,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
    "gemini-2.0-flash-lite": ModelInfo(
        name="gemini-2.0-flash-lite",
        display_name="Gemini 2.0 Flash-Lite",
        description="Lightweight and fast",
        input_token_limit=1_048_576,
        output_token_limit=8_192,
        supports_thinking=False,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
    "gemini-2.0-flash-lite-001": ModelInfo(
        name="gemini-2.0-flash-lite-001",
        display_name="Gemini 2.0 Flash-Lite 001",
        description="Stable lite version",
        input_token_limit=1_048_576,
        output_token_limit=8_192,
        supports_thinking=False,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_verified=True,
    ),
}


async def get_available_models_from_api() -> List[str]:
    """Fetch available models from Gemini API - USE THIS TO VERIFY MODELS"""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return []

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            )
            if resp.status_code == 200:
                data = resp.json()
                return [
                    m["name"].replace("models/", "") for m in data.get("models", [])
                ]
    except Exception:
        pass
    return []


def get_verified_models() -> List[ModelInfo]:
    """Get only verified models (is_verified=True)"""
    return [m for m in GEMINI_MODELS.values() if m.is_verified]


def get_model_info(model_name: str) -> Optional[ModelInfo]:
    """Get model info by name"""
    return GEMINI_MODELS.get(model_name)


def get_all_models() -> List[ModelInfo]:
    """Get all available models"""
    return list(GEMINI_MODELS.values())


def get_active_models() -> List[ModelInfo]:
    """Get non-deprecated verified models"""
    return [m for m in GEMINI_MODELS.values() if not m.is_deprecated and m.is_verified]


def get_preferred_models() -> List[ModelInfo]:
    """Get preferred models - user's main agents first"""
    preferred = [
        "gemini-3-flash-preview",  # User's main fast
        "gemini-3.1-pro-preview",  # User's main pro (may 503)
        "gemini-2.5-flash",  # Fallback 1
        "gemini-2.0-flash",  # Fallback 2
    ]
    return [GEMINI_MODELS[n] for n in preferred if n in GEMINI_MODELS]


# Rate limit intervals
def get_rate_limit_interval(model_name: str, percentage: float = 0.1) -> float:
    """Calculate rate limit interval based on RPM and percentage of max"""
    model = get_model_info(model_name)
    if not model:
        return 2.0

    rpm = model.tier_1_rpm
    interval = 60.0 / (rpm * percentage) if percentage > 0 else 60.0 / rpm
    return max(interval, 1.0)


_current_percentage: float = 0.1


def set_rate_limit_percentage(percentage: float) -> None:
    """Set the rate limit percentage (0.1 = 10%, 0.5 = 50%)"""
    global _current_percentage
    _current_percentage = max(0.01, min(1.0, percentage))


def get_rate_limit_percentage() -> float:
    """Get current rate limit percentage"""
    return _current_percentage


def get_current_rate_limit(model_name: str) -> float:
    """Get rate limit interval using current percentage setting"""
    return get_rate_limit_interval(model_name, _current_percentage)
