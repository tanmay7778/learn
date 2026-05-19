import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "your-secret-key-change-this"
    SQLALCHEMY_DATABASE_URI = "sqlite:///dell_store.db"  # SQLite for dev, PostgreSQL for prod
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Dell scraping settings
    DELL_BASE_URL = "https://www.dell.com/en-in"  # Change country as needed
    SCRAPE_INTERVAL_HOURS = 24  # Refresh product data daily

    # Categories to scrape
    DELL_CATEGORIES = {
        "laptops": "/shop/laptops/new",
        "desktops": "/shop/desktops-all-in-one/new",
        "all-in-ones": "/shop/desktops-all-in-one/all-in-one",
    }
