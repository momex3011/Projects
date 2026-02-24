from app import create_app
from extensions import db
from models.trend import Trend
from models.source import Source, SourceObservation

app = create_app()

def fix_db():
    with app.app_context():
        print("Creating missing tables...")
        # This will create tables if they don't exist, safely ignoring existing ones usually
        db.create_all()
        print("Database schema updated.")

if __name__ == "__main__":
    fix_db()
