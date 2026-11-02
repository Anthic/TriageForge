"""Application settings managed via Pydantic Settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = Field(default="", description="Groq API key")
    groq_model: str = Field(default="openai/gpt-oss-20b", description="Groq model name")
    llm_fallback_model: str | None = Field(default="openai/gpt-oss-120b", description="Optional Groq fallback model")
    cors_origins: str = Field(default="http://localhost:3001", description="Comma separated origins")
    max_tool_calls: int = Field(default=3, description="Max allowed tool calls per triage")
    llm_timeout_seconds: int = Field(default=30, description="Timeout for LLM invocation")
    llm_requests_per_minute: int = Field(default=60, description="Max LLM requests per minute for rate limiting")
    test_concurrency: int = Field(default=2, description="Max concurrent tickets in test runner")
    llm_max_retries: int = Field(default=1, description="Max SDK retries for LLM calls")
    triage_requests_per_minute: int = Field(default=10, description="Triage requests allowed per IP per minute")

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a clean list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
