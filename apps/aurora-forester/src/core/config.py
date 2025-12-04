"""
Aurora Forester Configuration
Loads settings from environment and secrets

Supports two modes:
1. Kubernetes: Environment variables injected via secretKeyRef
2. Local: Reads from ~/.aurora-forester/secrets/secrets.env
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


def get_env_file_path() -> Optional[str]:
    """Get the env file path if it exists, otherwise None."""
    path = Path.home() / ".aurora-forester" / "secrets" / "secrets.env"
    return str(path) if path.exists() else None


class Settings(BaseSettings):
    """Aurora Forester configuration settings."""

    # Identity
    agent_name: str = "Aurora Forester"
    agent_version: str = "0.1.0"
    owner: str = "Graydon"

    # Discord - reads from DISCORD_BOT_TOKEN env var
    discord_token: str = Field(default="", validation_alias="DISCORD_BOT_TOKEN")
    discord_channel_id: Optional[int] = Field(default=None, validation_alias="DISCORD_CHANNEL_ID")

    # Database
    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="aurora_db", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="aurora_forester", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="", validation_alias="POSTGRES_PASSWORD")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    # Ollama
    ollama_host: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_HOST")
    ollama_model: str = Field(default="mistral", validation_alias="OLLAMA_MODEL")
    ollama_model_fast: str = Field(default="llama3.2", validation_alias="OLLAMA_MODEL_FAST")

    # Hugging Face
    hf_token: Optional[str] = Field(default=None, validation_alias="HF_TOKEN")

    # Paths (with defaults that work in container)
    secrets_path: Path = Field(
        default=Path.home() / ".aurora-forester" / "secrets" / "secrets.env"
    )
    context_path: Path = Field(
        default=Path.home() / "sector7-infrastructure" / ".context" / "aurora-forester"
    )
    learning_path: Path = Field(
        default=Path.home() / ".aurora-forester" / "learning"
    )

    # Learning
    learning_enabled: bool = True
    feedback_required: bool = True  # Must have explicit feedback to learn

    # Self-care monitoring
    meal_reminder_hours: float = 4.0
    break_reminder_hours: float = 6.0

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
        # Allow both field name and validation_alias to work
        populate_by_name=True,
    )


# Global settings instance
settings = Settings()


def load_secrets():
    """
    Load secrets from the secrets file if available.
    In Kubernetes, secrets are already in environment variables.
    """
    secrets_path = Path.home() / ".aurora-forester" / "secrets" / "secrets.env"
    if secrets_path.exists():
        from dotenv import load_dotenv
        load_dotenv(secrets_path, override=True)
        # Reload settings to pick up new values
        global settings
        settings = Settings()
    # In K8s, env vars are already set, just ensure settings are loaded
    return settings
