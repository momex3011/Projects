from extensions import db

class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    war_id = db.Column(db.Integer, db.ForeignKey("wars.id"), nullable=False)
    
    name = db.Column(db.String(255), nullable=False) # e.g. "Nasib Crossing"
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    
    # Who currently owns it?
    controller = db.Column(db.String(50), default="Unknown") # e.g. "Rebel", "Gov"
    last_updated = db.Column(db.DateTime, server_default=db.func.now())
    
    # Importance determines influence radius (km): 
    # 1-3 = small (checkpoint, building), 4-6 = medium (town), 7-10 = large (city, governorate)
    importance = db.Column(db.Integer, default=5)
    
    # To prevent duplicate API calls
    def to_dict(self):
        return {
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
            "controller": self.controller,
            "importance": self.importance or 5
        }