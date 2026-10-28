
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_api_key: str = "cd40ae9012274bb1be691cd205d7ab22.O4pWNZ5OhqUd644IOxzKddLy"
    ollama_model: str = "beam:cloud"
    ollama_chat_url: str = "https://ollama.com/api/chat"
    llm_timeout_seconds: int = 120

    voyage_api_key: str = "pa-WWHD8aBr1Gi-bf9_AagTmaZNN6Cd0MEXIbgyr3vDUy_"
    embedding_model: str = "voyage-4-lite"

    database_url: str = ""
    policy_directory: str = "policies"
    retrieval_top_k: int = 5
    retrieval_backend: str = "tfidf"
    classification_confidence_threshold: float = 0.70

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
