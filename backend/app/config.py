"""Configuration loaded from environment / .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

# backend/ directory (this file lives in backend/app/config.py)
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Settings:
    PLEX_URL = os.getenv("PLEX_URL", "http://localhost:32400")
    PLEX_TOKEN = os.getenv("PLEX_TOKEN", "")
    PLEX_MOVIE_LIBRARY = os.getenv("PLEX_MOVIE_LIBRARY", "Movies")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    _db = os.getenv("DB_PATH", "moviepicker.db")
    DB_PATH = str(BASE_DIR / _db) if not os.path.isabs(_db) else _db

    @property
    def plex_configured(self) -> bool:
        return bool(self.PLEX_TOKEN and self.PLEX_URL)


settings = Settings()
