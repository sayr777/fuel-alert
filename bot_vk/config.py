from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    vk_group_token: str
    api_base_url: str = "http://127.0.0.1:8000/api/v1"
    redis_url: str = "redis://localhost:6379/3"


@lru_cache
def get_settings() -> Settings:
    return Settings()
