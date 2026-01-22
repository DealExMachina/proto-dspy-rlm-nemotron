"""Application settings and configuration."""

from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Nemotron on Koyeb (H100 - expensive!)
    nemotron_api_url: str = "https://nemotron-3-inference-dealexmachina-53d19e1c.koyeb.app"
    nemotron_timeout: int = 120

    # Ollama for local testing
    ollama_api_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b-instruct"  # Use full model name with -instruct suffix
    ollama_timeout: int = 60

    # Database
    duckdb_path: str = "./data/regulatory.duckdb"

    # Document cache
    document_cache_dir: str = "./data/documents"

    # Logging
    log_level: str = "INFO"

    # Testing mode (use Ollama instead of Nemotron)
    use_ollama: bool = False

    @property
    def duckdb_path_obj(self) -> Path:
        """Get DuckDB path as Path object."""
        path = Path(self.duckdb_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def document_cache_dir_obj(self) -> Path:
        """Get document cache directory as Path object."""
        path = Path(self.document_cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
