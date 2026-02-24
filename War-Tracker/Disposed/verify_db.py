from app import create_app, db
from models.event import Event
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if column exists
        result = db.session.execute(text("PRAGMA table_info(events)")).fetchall()
        columns = [row[1] for row in result]
        
        if 'video_url' in columns:
            print("SUCCESS: video_url column exists.")
        else:
            print("FAILURE: video_url column MISSING.")
            
            # Attempt to add it
            print("Attempting to add video_url column...")
            try:
                db.session.execute(text("ALTER TABLE events ADD COLUMN video_url TEXT"))
                db.session.commit()
                print("SUCCESS: video_url column added successfully.")
            except Exception as e:
                print(f"ERROR: Could not add column: {e}")

    except Exception as e:
        print(f"ERROR: {e}")
