"""NER-GRID Configuration Module

Loads environment variables with strict type validation using pydantic-settings.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    APP_PORT: int = Field(default=8000)
    APP_HOST: str = Field(default="0.0.0.0")

    # Provenance & Data Integrity
    ALLOW_SIMULATED_DATA: bool = Field(default=False)
    ENFORCE_DATA_PROVENANCE: bool = Field(default=True)

    # Database
    # Default to SQLite for local development; supports PostgreSQL/PostGIS via postgresql://
    DATABASE_URL: str = Field(default="sqlite:///./data/ner_grid.db")

    # External APIs
    OSRM_BACKEND_URL: str = Field(default="https://router.project-osrm.org")
    OPEN_METEO_BASE_URL: str = Field(default="https://api.open-meteo.com/v1")
    OVERPASS_API_URL: str = Field(default="https://overpass-api.de/api/interpreter")
    NOMINATIM_BASE_URL: str = Field(default="https://nominatim.openstreetmap.org")
    IMD_API_BASE_URL: str = Field(default="https://mausam.imd.gov.in/api")
    BHUVAN_WMS_BASE_URL: str = Field(default="https://bhuvan-vec2.nrsc.gov.in/bhuvan/wms")
    DATA_GOV_IN_BASE_URL: str = Field(default="https://api.data.gov.in")
    DATA_GOV_IN_API_KEY: Optional[str] = Field(default=None)

    # Caching
    CACHE_DIR: str = Field(default="./data/cached")
    CACHE_DEFAULT_TTL_SECONDS: int = Field(default=3600)  # 1 hour

    # Geographic Bounding Box for North Eastern Region (NER)
    NER_BBOX_MIN_LAT: float = Field(default=21.5)
    NER_BBOX_MAX_LAT: float = Field(default=29.5)
    NER_BBOX_MIN_LON: float = Field(default=88.0)
    NER_BBOX_MAX_LON: float = Field(default=97.5)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
