from extensions import db
from datetime import datetime

class Trend(db.Model):
    __tablename__ = 'trends'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), unique=True, nullable=False)
    
    # "Heat" score: How often it's mentioned by trusted sources recently
    score = db.Column(db.Float, default=0.0)
    
    # Tracking lifecycle
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # If True, the scraper will use this keyword
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<Trend {self.keyword} (Score: {self.score})>"
