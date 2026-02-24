from extensions import db

class Territory(db.Model):
    __tablename__ = "territories"
    id = db.Column(db.Integer, primary_key=True)
    war_id = db.Column(db.Integer, db.ForeignKey("wars.id"), nullable=False)
    name = db.Column(db.String(100))    # e.g. "Syrian Government"
    color = db.Column(db.String(20))    # e.g. "#ff0000"
    geojson = db.Column(db.Text, nullable=False) # Stores the actual shape data