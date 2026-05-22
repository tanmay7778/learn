import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-change-this"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///dell_store.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== LLM PROVIDER SELECTION =====
    # Options: "databricks", "gemini", or "groq"
    # Use "databricks" on corporate network (not blocked by proxy)
    # Use "groq" on personal laptop (free, fast, no billing needed)
    # Use "gemini" as backup (quota issues)
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER") or "groq"

    # ===== DATABRICKS FOUNDATION MODEL API =====
    # Works on corporate network! Uses your workspace's serving endpoints.
    DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST") or "https://adb-4246498347041546.6.azuredatabricks.net"
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN") or ""
    DATABRICKS_MODEL = os.environ.get("DATABRICKS_MODEL") or "databricks-meta-llama-3-3-70b-instruct"

    # ===== GROQ API (primary for personal laptop) =====
    # Free tier: 30 RPM, 14,400 RPD — very generous!
    # Get key: https://console.groq.com/keys
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY") or ""
    GROQ_MODEL = os.environ.get("GROQ_MODEL") or "llama-3.3-70b-versatile"

    # ===== GOOGLE GEMINI API (backup) =====
    # Free tier: https://aistudio.google.com/apikey
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ""
