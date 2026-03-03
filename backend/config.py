"""
Configuration Manager
Handles environment variables and app settings.
"""

import os
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Application configuration."""

    # LLM Settings
    gemini_api_key: str = ""
    openai_api_key: str = ""
    use_llm: bool = True
    debate_rounds: int = 2

    # Server Settings
    backend_port: int = 8000
    debug: bool = True

    # ML Settings
    use_mlx: bool = True
    ocr_engine: str = "vision"

    # Paths
    project_root: Path = Path(__file__).parent.parent
    data_dir: Path = None
    output_dir: Path = None
    vector_store_dir: Path = None

    def __post_init__(self):
        self.data_dir = self.project_root / "data"
        self.output_dir = self.project_root / "output"
        self.vector_store_dir = self.data_dir / "vector_store"

        # Load from environment
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", self.gemini_api_key)
        self.openai_api_key = os.getenv("OPENAI_API_KEY", self.openai_api_key)
        self.llm_provider = os.getenv("LLM_PROVIDER", "").lower()

        if os.getenv("USE_LLM"):
            self.use_llm = os.getenv("USE_LLM").lower() == "true"

        if os.getenv("DEBATE_ROUNDS"):
            self.debate_rounds = int(os.getenv("DEBATE_ROUNDS"))

        if os.getenv("BACKEND_PORT"):
            self.backend_port = int(os.getenv("BACKEND_PORT"))

        if os.getenv("DEBUG"):
            self.debug = os.getenv("DEBUG").lower() == "true"

        if os.getenv("USE_MLX"):
            self.use_mlx = os.getenv("USE_MLX").lower() == "true"

        if os.getenv("OCR_ENGINE"):
            self.ocr_engine = os.getenv("OCR_ENGINE")

    def ensure_directories(self):
        """Create necessary directories."""
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.vector_store_dir.mkdir(exist_ok=True)

    def get_llm_config(self) -> dict:
        """Get LLM configuration."""
        return {
            "llm_provider": getattr(self, "llm_provider", ""),
            "use_lmstudio": True,
            "use_gemini": bool(self.gemini_api_key),
            "use_openai": bool(self.openai_api_key),
            "use_mlx": getattr(self, "use_mlx", True),
        }


_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get global configuration instance."""
    global _config
    if _config is None:
        _config = AppConfig()
        _config.ensure_directories()
    return _config
