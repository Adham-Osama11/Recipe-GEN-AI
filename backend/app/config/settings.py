from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Recipe Generator API"
    api_prefix: str = "/api/v1"
    environment: str = "development"

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL")
    groq_temperature: float = Field(default=0.85, alias="GROQ_TEMPERATURE")
    llm_max_retries: int = Field(default=2, alias="LLM_MAX_RETRIES")
    parser_max_retries: int = Field(default=2, alias="PARSER_MAX_RETRIES")

    request_timeout_seconds: int = Field(default=45, alias="REQUEST_TIMEOUT_SECONDS")
    allowed_origins: str = Field(default="*", alias="ALLOWED_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]
        return origins or ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
