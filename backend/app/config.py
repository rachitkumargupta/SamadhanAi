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
    complaint_analyst_categories: str = (
        "roads_potholes,garbage_sanitation,drainage_sewage,water_leakage,"
        "streetlights_electrical,damaged_public_infrastructure,other_uncertain"
    )

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
