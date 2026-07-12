from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "polibot"

    postgres_dsn: str = "postgresql://polibot:polibot@localhost:5432/polibot"

    rustfs_endpoint: str = "http://localhost:9000"
    rustfs_access_key: str = ""
    rustfs_secret_key: str = ""
    rustfs_bucket: str = "polibot-materials"

    ollama_base_url: str = "http://localhost:11434"
    ollama_reformulation_model: str = "gemma4:e2b"
    ollama_vlm_model: str = "gemma4:e4b"
    ollama_lesson_model: str = "gemma4:e4b"

    ollama_embedding_model: str = "bge-m3"
    sparse_model_name: str = "Qdrant/bm25"
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
