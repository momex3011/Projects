from extensions import db
from datetime import datetime

class Source(db.Model):
    __tablename__ = 'sources'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False) # youtube, twitter, facebook
    handle = db.Column(db.String(100), nullable=False)  # @channel_name or ID
    name = db.Column(db.String(200)) # Human readable name
    
    # Trust System
    status = db.Column(db.String(20), default='probation') # trusted, probation, banned
    reliability_score = db.Column(db.Float, default=50.0) # 0 to 100
    
    # Stats
    last_crawled_at = db.Column(db.DateTime)
    total_events_found = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Source {self.platform}:{self.handle} ({self.status})>"

class SourceObservation(db.Model):
    """Daily stats for a source to track performance trends"""
    __tablename__ = 'source_observations'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id'), nullable=False)
    date_observed = db.Column(db.Date, nullable=False)
    
    items_found = db.Column(db.Integer, default=0)
    items_accepted = db.Column(db.Integer, default=0)
    
    source = db.relationship(Source, backref=db.backref('observations', lazy=True))
