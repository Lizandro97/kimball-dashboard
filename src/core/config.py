"""Central configuration via pydantic-settings."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://lizandro:148256@localhost/superstore")
    CSV_PATH: str = os.getenv("CSV_PATH", "data/super-store.csv")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    CORS_ORIGINS: list[str] = ["*"]
    APP_TITLE: str = "Superstore BI Dashboard"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
