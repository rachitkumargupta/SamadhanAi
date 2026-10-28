from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "local"
    database_url: str
    jwt_secret: SecretStr
    jwt_issuer: str
    jwt_audience: str
    openai_api_key: SecretStr | None = None
    complaint_analyst_model: str = "gpt-6-luna"
    complaint_analyst_timeout_seconds: float = Field(default=30.0, gt=0, le=120)
    complaint_analyst_categories: str | None = None
    complaint_analyst_policy_file: str | None = None
    complaint_media_storage_dir: str = "./private_media"
    complaint_analysis_worker_poll_seconds: float = Field(default=2.0, gt=0, le=60)
    monitoring_escalation_model: str = "gpt-6-luna"
    monitoring_escalation_timeout_seconds: float = Field(default=20.0, gt=0, le=60)
    monitoring_worker_poll_seconds: float = Field(default=30.0, gt=0, le=300)
    citizen_verification_window_hours: int = Field(default=168, gt=0, le=720)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("jwt_secret")
    @classmethod
    def validate_jwt_secret(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if secret.startswith("replace-with-"):
            raise ValueError("Replace the JWT_SECRET placeholder before starting the API")
        if len(secret.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET must contain at least 32 bytes")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
