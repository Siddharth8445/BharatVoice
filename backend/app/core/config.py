import os
from functools import lru_cache
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # Server settings
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "development"
    APP_NAME: str = "BharatVoice"
    APP_VERSION: str = "0.1.0"

    # CORS origins
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # Database
    DATABASE_URL: str = "sqlite:///./bharatvoice.db"

    # Gnani AI configuration
    GNANI_API_KEY: Optional[str] = None
    USE_MOCK_GNANI: bool = True

    # Gnani STT parameters
    GNANI_STT_ENDPOINT: str = "https://api.vachana.ai/stt/v3"
    GNANI_STT_MODEL: str = "prisma-v3.0"
    GNANI_STT_LANGUAGE_CODE: str = "indic-auto"

    # Gnani TTS parameters
    GNANI_TTS_ENDPOINT: str = "https://api.vachana.ai/api/v1/tts/inference"
    GNANI_TTS_MODEL: str = "timbre-v2.5"
    GNANI_TTS_VOICE: str = "Nalini"
    GNANI_TTS_LANGUAGE: str = "hi-IN"
    GNANI_TTS_SPEED: float = 1.0
    GNANI_TTS_TIMEOUT_SECONDS: float = 30.0

    # Audio limitations
    MAX_AUDIO_DURATION_SECONDS: int = 30
    MAX_AUDIO_FILE_SIZE_BYTES: int = 10485760  # 10 MB

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Union[List[str], str]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_gnani_mock_enabled(self) -> bool:
        """Report the explicitly selected provider mode.

        Real mode without an API key is a configuration error; it must not
        silently fall back to mock responses.
        """
        return self.USE_MOCK_GNANI


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
