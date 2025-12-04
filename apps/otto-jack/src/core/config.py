"""
Otto Configuration
Platform Guide for Hello World Co-Op
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


def get_env_file_path() -> Optional[str]:
    """Get the env file path if it exists, otherwise None."""
    path = Path.home() / ".otto-jack" / "secrets" / "secrets.env"
    return str(path) if path.exists() else None


class Settings(BaseSettings):
    """Otto configuration settings."""

    # Identity
    agent_name: str = "Otto"
    agent_version: str = "0.1.0"
    agent_title: str = "Platform Mascot & Digital Guide"

    # Discord - reads from environment variables
    discord_token: str = Field(default="", validation_alias="DISCORD_BOT_TOKEN")
    discord_guild_id: Optional[int] = Field(default=None, validation_alias="DISCORD_GUILD_ID")

    # Ollama for AI responses
    ollama_host: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_HOST")
    ollama_model: str = Field(default="mistral", validation_alias="OLLAMA_MODEL")

    # Knowledge base path
    docs_path: Path = Field(
        default=Path("/app/knowledge")
    )

    # Personality settings
    response_style: str = "playful"  # playful, helpful, informative
    max_response_length: int = 1800

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


# Global settings instance
settings = Settings()


def load_secrets():
    """Load secrets from file if available."""
    secrets_path = Path.home() / ".otto-jack" / "secrets" / "secrets.env"
    if secrets_path.exists():
        from dotenv import load_dotenv
        load_dotenv(secrets_path, override=True)
        global settings
        settings = Settings()
    return settings
