import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-change-this"
    SQLALCHEMY_DATABASE_URI = "sqlite:///dell_store.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ===== LLM PROVIDER SELECTION =====
    # Options: "databricks" or "gemini"
    # Use "databricks" on corporate network (not blocked by proxy)
    # Use "gemini" on personal network (blocked by Capgemini proxy)
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER") or "databricks"

    # ===== DATABRICKS FOUNDATION MODEL API =====
    # Works on corporate network! Uses your workspace's serving endpoints.
    # Get token: Databricks → User Settings → Developer → Access Tokens → Generate
    DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST") or "https://adb-4246498347041546.6.azuredatabricks.net"
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN") or "YOUR_DATABRICKS_TOKEN_HERE"
    # Free pay-per-token models (no endpoint deployment needed):
    # "databricks-meta-llama-3-3-70b-instruct" (best quality, free)
    # "databricks-claude-sonnet-4" (premium, may need enablement)
    DATABRICKS_MODEL = os.environ.get("DATABRICKS_MODEL") or "databricks-meta-llama-3-3-70b-instruct"

    # ===== GOOGLE GEMINI API (backup) =====
    # Free tier: https://aistudio.google.com/apikey
    # Blocked on Capgemini corporate network
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "AIzaSyBzD5kmSrOYGzRuQhqs9iUDLOjtKhK1Bdc"
