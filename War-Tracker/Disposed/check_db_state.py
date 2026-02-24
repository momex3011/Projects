from models.event import Event
from models.scraper_state import ScraperState
from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    # Check latest event
    latest = Event.query.order_by(Event.event_date.desc()).first()
    print(f"Latest event in DB: {latest.event_date if latest else 'No events'}")
    
    # Check scraper state
    state = ScraperState.query.first()
    print(f"Last scraped date: {state.last_date_processed if state else 'No state'}")
    
    # Count total events
    total = Event.query.count()
    print(f"Total events: {total}")
