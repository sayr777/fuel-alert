from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://fuelwatch:fuelwatch@localhost:5432/fuelwatch"

    # Redis (FSM state for bot, rate limiting)
    redis_url: str = "redis://localhost:6379/0"

    # Object storage (photos)
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "fuelwatch"
    s3_secret_key: str = "fuelwatch123"
    s3_bucket: str = "fuel-watch-photos"
    s3_public_url: str = "http://localhost:9000/fuel-watch-photos"
    s3_use_ssl: bool = False

    # API
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]

    # Moderation
    moderator_token: str = "change-me-moderator-token"

    # Region coverage (European Russia approx bbox: min_lon, min_lat, max_lon, max_lat).
    # Excludes the Kaliningrad exclave (west of this box) to avoid also covering
    # Belarus/Baltic-state territory that shares the same longitude band.
    # NOTE: a real GeoJSON polygon should replace this bbox before production use —
    # a bbox lets through points in Belarus/Ukraine/Baltic states that share this box.
    region_bbox: tuple[float, float, float, float] = (27.0, 41.0, 60.0, 70.0)

    # Validation pipeline tunables
    rate_limit_per_hour: int = 5
    dedup_radius_m: float = 200.0
    dedup_window_minutes: int = 120
    station_match_radius_m: float = 150.0
    max_event_age_hours: int = 72
    exif_gps_mismatch_km: float = 5.0

    # Report constraints
    max_photos_per_report: int = 2
    max_description_length: int = 500


@lru_cache
def get_settings() -> Settings:
    return Settings()
