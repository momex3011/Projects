from app import create_app
from extensions import db
from models.scraper_state import ScraperState

app = create_app()

with app.app_context():
    print("--- 🛠️ UPDATING DATABASE SCHEMA ---")
    db.create_all()
    print("   ✅ Created 'scraper_state' table (if it didn't exist).")
