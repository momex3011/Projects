# fix_db.py
from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    try:
        # We use a raw SQL command to add the missing column
        db.session.execute(db.text('ALTER TABLE events ADD COLUMN evidence_score INTEGER DEFAULT 0'))
        db.session.commit()
        print("✅ SUCCESS: 'evidence_score' column added to database.")
    except Exception as e:
        db.session.rollback()
        if "duplicate column name" in str(e).lower():
            print("ℹ️ INFO: Column 'evidence_score' already exists. You are good to go!")
        else:
            print(f"❌ ERROR: {e}")