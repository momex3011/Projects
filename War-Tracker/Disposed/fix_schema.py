from app import create_app
from extensions import db
# Import ALL models to ensure they are registered with SQLAlchemy
from models.event import Event
from models.war import War
from models.category import Category
from models.location_cache import LocationCache
# Add others if needed:
from models.history import TerritoryHistory
from models.location import Location

app = create_app()
with app.app_context():
    print("Creating all tables...")
    db.create_all()
    print("✅ Schema fixed. LocationCache should exist now.")
