from app import create_app
from extensions import db
from models.event import Event

app = create_app()
with app.app_context():
    events = Event.query.all()
    print(f"--- DUMPING {len(events)} URLs ---")
    for e in events:
        print(f"ID {e.id}: {e.source_url}")
