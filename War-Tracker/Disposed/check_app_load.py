from app import create_app
from models.event import Event
from extensions import db

try:
    app = create_app()
    with app.app_context():
        print("App loaded successfully.")
        # Try to query to ensure models are registered correctly
        count = Event.query.count()
        print(f"Event count: {count}")
except Exception as e:
    print(f"FAILED to load app: {e}")
