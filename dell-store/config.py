import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-change-this"
    SQLALCHEMY_DATABASE_URI = "sqlite:///dell_store.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini API (free tier: https://aistudio.google.com/apikey)
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or "YOUR_GEMINI_API_KEY_HERE"
