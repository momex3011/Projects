from app import create_app
from extensions import db
from models.event import Event
from datetime import datetime
import hashlib
import sys

app = create_app()

def test_insertion():
    with app.app_context():
        print("--- 🧪 TESTING ANTIGRAVITY PHASE 1 (DEDUPLICATION) ---")
        
        # 1. Prepare Test Data
        title = "TEST EVENT: Deduplication Verification"
        date_obj = datetime.now()
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        # 2. Generate Hash
        hash_input = f"{date_obj.date().isoformat()}-{title}".encode('utf-8') # Using date() to match ingest logic
        event_hash = hashlib.sha256(hash_input).hexdigest()
        
        # 3. Insert First Event
        print("   🔹 Inserting Event #1...")
        ev1 = Event(
            war_id=1,
            title=title,
            description="First insertion.",
            event_date=date_obj,
            lat=33.5, lng=36.2,
            source_url=url,
            hash_key=event_hash,
            image_url="https://img.youtube.com/vi/dQw4w9WgXcQ/0.jpg",
            category_id=1
        )
        try:
            db.session.add(ev1)
            db.session.commit()
            print("      ✅ Success.")
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            db.session.rollback()

        # 4. Attempt Duplicate Insert (Constraint Check)
        print("   🔹 Inserting Duplicate Event (Should Fail)...")
        ev2 = Event(
            war_id=1,
            title=title,
            description="This is a duplicate.",
            event_date=date_obj,
            lat=33.5, lng=36.2,
            source_url=url, # Constraint!
            hash_key=event_hash, 
            category_id=1
        )
        try:
            db.session.add(ev2)
            db.session.commit()
            print("      ❌ ERROR: Duplicate was allowed!")
        except Exception as e:
            print("      ✅ Success: Duplicate blocked by Database Constraint.")
            # print(f"      (Error: {e})")
            db.session.rollback()

if __name__ == "__main__":
    test_insertion()
