"""
TWISTED configuration using Pydantic Settings.
Environment variables and sensible defaults.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # API Keys
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API key")
    SERPAPI_KEY: Optional[str] = Field(None, description="SerpAPI key for web search")
    TAVILY_API_KEY: Optional[str] = Field(
        None, description="Tavily API key alternative"
    )
    GITHUB_TOKEN: Optional[str] = Field(
        None, description="GitHub Personal Access Token for repo operations"
    )
    BROWSER_USE_API_KEY: Optional[str] = Field(
        None, description="Browser Use Cloud API key for web automation"
    )
    BROWSER_USE_ENABLED: bool = Field(
        False, description="Enable Browser Use Cloud integration for web research"
    )

    # Google Cloud
    GOOGLE_CLOUD_PROJECT: Optional[str] = Field(
        None, description="Google Cloud Project ID"
    )
    GOOGLE_CLOUD_LOCATION: str = Field(
        "us", description="Google Cloud Location (e.g., us, eu)"
    )
    DOCUMENT_AI_PROCESSOR_ID: Optional[str] = Field(
        None, description="Document AI Processor ID"
    )
    GOOGLE_WORKSPACE_DELEGATED_USER: Optional[str] = Field(
        None, description="Email to delegate as for Workspace APIs"
    )

    # Gemini Configuration
    GEMINI_TIER: str = Field("tier_1", description="API tier for rate limiting")
    RATE_LIMIT_PERCENTAGE: float = Field(
        0.1, description="Percentage of max rate limit to use (0.1 = 10%, 0.5 = 50%)"
    )
    RATE_LIMIT_FLASH: float = Field(
        2.0, description="Seconds between Flash calls (calculated from percentage)"
    )
    RATE_LIMIT_PRO: float = Field(
        4.0, description="Seconds between Pro calls (calculated from percentage)"
    )
    EMBEDDING_MODEL: str = Field("text-embedding-004", description="Embedding model")

    # Qdrant Cloud Vector Store (replaces ChromaDB)
    QDRANT_URL: str = Field(..., description="Qdrant cloud URL")
    QDRANT_API_KEY: str = Field(..., description="Qdrant API key")
    QDRANT_COLLECTION: str = Field(
        "twisted_cases", description="Qdrant collection name"
    )
    CHROMA_PERSIST_DIR: str = Field(
        "./chroma_db", description="Legacy ChromaDB directory (unused)"
    )

    # File Handling
    UPLOAD_DIR: str = Field("./uploads", description="Temporary file storage")
    MAX_FILE_SIZE: int = Field(
        100 * 1024 * 1024, description="Max file size in bytes (100MB)"
    )
    ALLOWED_EXTENSIONS: list = Field(
        [
            "txt",
            "md",
            "pdf",
            "docx",
            "rtf",
            "jpg",
            "jpeg",
            "png",
            "gif",
            "tiff",
            "mp4",
            "mov",
            "avi",
            "mkv",
            "mp3",
            "wav",
            "m4a",
            "flac",
            "eml",
            "msg",
        ]
    )

    # Server
    HOST: str = Field("0.0.0.0", description="Server bind address")
    PORT: int = Field(8000, description="Server port")
    DEBUG: bool = Field(False, description="Debug mode")

    # Security
    ENCRYPTION_KEY: Optional[str] = Field(
        None, description="AES-256-GCM key for data at rest"
    )
    DATA_PRIVACY_STRICT: bool = Field(
        False, description="Force all processing to be local if True"
    )
    DISABLE_LOCAL_MLX: bool = Field(
        True, description="Disable local MLX processing for thermal relief"
    )
    MLX_MEMORY_LIMIT_MB: int = Field(4096, description="MLX memory limit in MB")
    ENABLE_DEEP_RESEARCH: bool = Field(False, description="Enable deep research stage")

    # Logging
    LOG_DIR: str = Field("./logs", description="Directory for structured debug logs")
    LOG_LEVEL: str = Field("DEBUG", description="Logging level (DEBUG, INFO, WARNING, ERROR)")

    # Memory Management
    EMBEDDING_CACHE_MAX_SIZE: int = Field(1000, description="Max entries in embedding LRU cache")
    AGENT_CONVERSATION_HISTORY_LIMIT: int = Field(50, description="Max messages per agent conversation")
    DEBATE_HISTORY_LIMIT: int = Field(20, description="Max debate rounds to keep in memory")

    # Local LLM (LM Studio / Ollama)
    LOCAL_LLM_ENABLED: bool = Field(True, description="Enable local LLM fallback")
    LOCAL_LLM_URL: str = Field(
        "http://172.20.10.3:1234", description="Local LLM server URL"
    )
    LOCAL_LLM_MODEL: str = Field(
        "llama-3.2-8x3b-moe-dark-champion-instruct-uncensored-abliterated-18.4b",
        description="Local LLM model name",
    )
    LOCAL_LLM_TIMEOUT: float = Field(120.0, description="Local LLM request timeout")

    CORS_ORIGINS: list = Field(
        ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    )

    # NotebookLM MCP
    NOTEBOOKLM_MCP_ENABLED: bool = Field(
        True, description="Enable NotebookLM MCP integration"
    )
    NOTEBOOKLM_MCP_COMMAND: str = Field(
        "notebooklm-mcp", description="Path to notebooklm-mcp command"
    )

    @property
    def upload_path(self) -> Path:
        return Path(self.UPLOAD_DIR)

    @property
    def chroma_path(self) -> Path:
        return Path(self.CHROMA_PERSIST_DIR)


# Global settings instance
settings = Settings()
