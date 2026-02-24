from extensions import db

class TerritoryHistory(db.Model):
    __tablename__ = "territory_history"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    
    # Who controlled it at this time?
    controller = db.Column(db.String(50), nullable=False) # e.g. "Rebel", "Gov"
    
    # When did this change happen?
    valid_from = db.Column(db.Date, nullable=False)
    
    # Relationship
    location = db.relationship("Location", backref=db.backref("history", lazy=True))
