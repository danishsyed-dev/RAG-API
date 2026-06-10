"""Centralized configuration for the RAG-API application.

All settings are configurable via environment variables or a `.env` file.
See `.env.example` for a full list of available settings.
"""

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Database ---
    chromadb_path: str = "./db"
    collection_name: str = "docs"

    # --- LLM ---
    llm_model: str = "tinyllama"
    ollama_host: str = "http://localhost:11434"
    use_mock_llm: bool = False

    # --- API ---
    cors_origins: list[str] = ["*"]
    max_query_length: int = 1000
    default_n_results: int = 3

    # --- Ingestion ---
    chunk_size: int = 500
    chunk_overlap: int = 50

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Accept comma-separated string for CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


settings = Settings()
