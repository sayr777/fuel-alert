from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    admin_bot_token: str
    admin_chat_id: int
    api_base_url: str = "http://127.0.0.1:8000/api/v1"
    moderator_token: str
    redis_url: str = "redis://localhost:6379/2"
    health_interval: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
