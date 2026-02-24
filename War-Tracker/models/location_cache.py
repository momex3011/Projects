from extensions import db

class LocationCache(db.Model):
    """
    Antigravity Phase 1: Geocode Cache
    Stores the result of Nominatim lookups to prevent hitting the API 
    for the same city 1,000 times.
    """
    __tablename__ = "location_cache"
    id = db.Column(db.Integer, primary_key=True)
    
    # SEARCH KEY (Normalized)
    search_term = db.Column(db.String(255), unique=True, nullable=False, index=True)
    
    # RESULT
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    
    # Metadata
    display_name = db.Column(db.String(500)) # The full name returned by API
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "search_term": self.search_term,
            "lat": self.lat,
            "lng": self.lng
        }
