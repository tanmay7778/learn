import os
from dotenv import load_dotenv

# Load .env file if it exists (local dev). In production, env vars are set by the platform.
load_dotenv()

# Detect production environment (Render sets RENDER=true automatically)
_is_production = os.environ.get("RENDER") or os.environ.get("PRODUCTION")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        if _is_production:
            raise RuntimeError("SECRET_KEY must be set in production!")
        SECRET_KEY = "dev-only-insecure-key"

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

    # ===== CLOUDINARY (All Image Storage — Products + Series) =====
    # Free tier: 25GB storage, 25GB bandwidth/month
    # Sign up: https://cloudinary.com/users/register_free
    # Dashboard: https://console.cloudinary.com/settings/api-keys
    CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME") or ""
    CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY") or ""
    CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET") or ""
    CLOUDINARY_UPLOAD_FOLDER = "dell-store/products"  # Product images folder

    # Series images base URL (hero.png, feature1-3.png for each series)
    # Upload series images to Cloudinary under: dell-store/series/<series_name>/
    # Example: dell-store/series/inspiron/hero.png
    # URL pattern: https://res.cloudinary.com/<cloud_name>/image/upload/dell-store/series/
    if CLOUDINARY_CLOUD_NAME:
        CLOUDINARY_SERIES_BASE_URL = f"https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/image/upload/dell-store/series"
    else:
        # Fallback for local dev — uses local static folder
        CLOUDINARY_SERIES_BASE_URL = ""
