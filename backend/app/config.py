from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "WindScope — UK Wind Forecast Intelligence"
    API_V1_STR: str = "/api"
    
    # Elexon BMRS API
    ELEXON_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1"
    HTTP_TIMEOUT_SECONDS: float = 25.0
    HTTP_MAX_RETRIES: int = 3
    
    # Decision Time & Market Defaults
    DEFAULT_CUTOFF_TIME: str = "09:30"
    DEFAULT_TIMEZONE: str = "Europe/London"
    
    # Caching
    CACHE_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "cache")
    CACHE_ENABLED: bool = True
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://*.vercel.app",
    ]
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
