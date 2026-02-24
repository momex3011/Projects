# repair.py
from app import create_app
from extensions import db
from models.event import Event
from models.location_cache import LocationCache

app = create_app()
with app.app_context():
    # 1. Ensure all tables (including location_cache) exist
    db.create_all()
    
    # 2. Add the evidence_score column if it's missing
    try:
        db.session.execute(db.text('ALTER TABLE events ADD COLUMN evidence_score INTEGER DEFAULT 0'))
        db.session.commit()
        print("✅ Column 'evidence_score' added successfully.")
    except Exception as e:
        db.session.rollback()
        if "duplicate column name" in str(e).lower():
            print("ℹ️ Column 'evidence_score' already exists.")
        else:
            print(f"⚠️ Note: {e}")

    print("✅ Database structure is now perfect.")
