import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-change-this"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///dell_store.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== GROQ LLM API =====
    # Free tier: 30 RPM, 14,400 RPD — very generous!
    # Get key: https://console.groq.com/keys
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or ""
    GROQ_MODEL = os.environ.get("GROQ_MODEL") or "llama-3.3-70b-versatile"
