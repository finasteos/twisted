"""
Gemini Model Configuration
All available models with their capabilities and tier 1 rate limits
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


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
    tier_1_rpm: int  # Requests per minute
    tier_1_tpm: int  # Tokens per minute
    tier_1_rpd: int  # Requests per day
    is_deprecated: bool = False


GEMINI_MODELS: Dict[str, ModelInfo] = {
    # Gemini 3 Series (User's preferred models)
    "gemini-3-flash-preview": ModelInfo(
        name="gemini-3-flash-preview",
        display_name="Gemini 3 Flash Preview",
        description="Fast and efficient for most tasks",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=False,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
    ),
    "gemini-3.1-pro-preview": ModelInfo(
        name="gemini-3.1-pro-preview",
        display_name="Gemini 3.1 Pro Preview",
        description="Most capable model for complex reasoning",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=150,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_deprecated=True,  # Will be deprecated soon per user
    ),
    "gemini-3.1-flash-preview": ModelInfo(
        name="gemini-3.1-flash-preview",
        display_name="Gemini 3.1 Flash Preview",
        description="Fast with extended thinking",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
    ),
    "gemini-3-pro-preview": ModelInfo(
        name="gemini-3-pro-preview",
        display_name="Gemini 3 Pro Preview (DEPRECATED)",
        description="DEPRECATED - Use gemini-3.1-pro-preview instead",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=150,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
        is_deprecated=True,
    ),
    # Gemini 2.5 Series (Stable)
    "gemini-2.5-pro": ModelInfo(
        name="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro",
        description="Stable release (June 2025) - most capable",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=150,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
    ),
    "gemini-2.5-flash": ModelInfo(
        name="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash",
        description="Stable release (June 2025) - fast and capable",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=True,
        supports_caching=True,
        tier_1_rpm=300,
        tier_1_tpm=1_000_000,
        tier_1_rpd=1_500,
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
    ),
    # Gemini 2.0 Series
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
    ),
    # Deep Research
    "deep-research-pro-preview-12-2025": ModelInfo(
        name="deep-research-pro-preview-12-2025",
        display_name="Deep Research Pro",
        description="Exhaustive research model - takes longer but comprehensive",
        input_token_limit=1_048_576,
        output_token_limit=65_536,
        supports_thinking=True,
        supports_vision=False,
        supports_caching=True,
        tier_1_rpm=10,
        tier_1_tpm=1_000_000,
        tier_1_rpd=50,  # Very limited
    ),
}


def get_model_info(model_name: str) -> Optional[ModelInfo]:
    """Get model info by name"""
    return GEMINI_MODELS.get(model_name)


def get_all_models() -> List[ModelInfo]:
    """Get all available models"""
    return list(GEMINI_MODELS.values())


def get_active_models() -> List[ModelInfo]:
    """Get non-deprecated models"""
    return [m for m in GEMINI_MODELS.values() if not m.is_deprecated]


def get_preferred_models() -> List[ModelInfo]:
    """Get user's preferred models (non-deprecated, prioritize 3.x)"""
    preferred = [
        "gemini-3-pro-preview",
        "gemini-3.1-flash-preview",
        "gemini-3-flash-preview",
        "gemini-2.5-flash",
    ]
    result = []
    for name in preferred:
        if name in GEMINI_MODELS and not GEMINI_MODELS[name].is_deprecated:
            result.append(GEMINI_MODELS[name])
    return result


# Rate limit intervals (minimum seconds between requests)
def get_rate_limit_interval(model_name: str, percentage: float = 0.1) -> float:
    """Calculate rate limit interval based on RPM and desired usage percentage"""
    model = get_model_info(model_name)
    if not model:
        return 10.0  # Default

    # At 10% of max, interval = 60 / (RPM * 0.1)
    rpm = model.tier_1_rpm
    interval = 60.0 / (rpm * percentage)
    return max(interval, 1.0)  # Minimum 1 second
