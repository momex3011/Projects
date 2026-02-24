from extensions import db

class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    war_id = db.Column(db.Integer, db.ForeignKey("wars.id"), nullable=False)
    
    # Fix: Re-added category_id to prevent the AttributeError crash
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=True)

    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    
    source_url = db.Column(db.Text)
    
    # Fix: Added image_url for the visual upgrade
    image_url = db.Column(db.Text) 
    
    # Antigravity Phase 1: Deduplication
    hash_key = db.Column(db.String(64), index=True) # SHA-256 hash of (date + title/url)
    video_url = db.Column(db.Text)
    evidence_score = db.Column(db.Integer, default=0)
    
    __table_args__ = (
        db.UniqueConstraint('source_url', name='_source_url_uc'),
    )
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships
    category = db.relationship("Category", backref="events")