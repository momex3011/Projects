from extensions import db

class War(db.Model):
    __tablename__ = "wars"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    default_lat = db.Column(db.Float, default=0.0)
    default_lng = db.Column(db.Float, default=0.0)
    default_zoom = db.Column(db.Integer, default=6)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Define relationship to events
    events = db.relationship("Event", backref="war", lazy="dynamic", cascade="all,delete")