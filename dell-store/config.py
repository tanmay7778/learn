import os
from dotenv import load_dotenv

# Load .env file if it exists (local dev). In production, env vars are set by the platform.
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-change-this"

    # Database: PostgreSQL in production, SQLite locally
    # Render uses 'postgres://' but SQLAlchemy requires 'postgresql://'
    _db_url = os.environ.get("DATABASE_URL") or "sqlite:///dell_store.db"
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Debug mode (False in production)
    DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")

    # ===== GROQ LLM API =====
    # Free tier: 30 RPM, 14,400 RPD
    # Get key: https://console.groq.com/keys
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or ""
    GROQ_MODEL = os.environ.get("GROQ_MODEL") or "llama-3.3-70b-versatile"
