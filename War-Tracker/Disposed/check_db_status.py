from app import create_app
from models.event import Event
from extensions import db
from sqlalchemy import func

app = create_app()
with app.app_context():
    total = Event.query.count()
    print(f"Total Events: {total}")
    
    # Check date distribution
    dates = db.session.query(Event.event_date, func.count(Event.id)).group_by(Event.event_date).all()
    print("Events by Date:")
    for d, c in dates:
        print(f"  {d}: {c}")

from extensions import db
