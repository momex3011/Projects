from extensions import db
from datetime import datetime

class ScraperState(db.Model):
    __tablename__ = 'scraper_state'
    id = db.Column(db.Integer, primary_key=True)
    war_id = db.Column(db.Integer, db.ForeignKey('wars.id'), unique=True)
    last_date_processed = db.Column(db.Date, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
