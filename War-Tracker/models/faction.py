from extensions import db
from datetime import date

class Faction(db.Model):
    __tablename__ = "factions"
    id = db.Column(db.Integer, primary_key=True)
    war_id = db.Column(db.Integer, db.ForeignKey("wars.id"), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)  # e.g. "Syrian Government", "Rebels"
    short_name = db.Column(db.String(20))             # e.g. "GOV", "REB" 
    color = db.Column(db.String(20), default="#808080")  # Hex color
    
    # Territory GeoJSON - stores the faction's current control polygon
    territory_geojson = db.Column(db.Text)  # GeoJSON MultiPolygon
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    war = db.relationship("War", backref=db.backref("factions", lazy=True))
    subfactions = db.relationship("SubFaction", backref="parent_faction", lazy=True, cascade="all, delete-orphan", order_by="SubFaction.name")
    
    def to_dict(self):
        return {
            "id": self.id,
            "war_id": self.war_id,
            "name": self.name,
            "short_name": self.short_name,
            "color": self.color,
            "territory_geojson": self.territory_geojson,
            "subfactions": [sf.to_dict() for sf in self.subfactions]
        }


class SubFaction(db.Model):
    """
    Sub-factions within a main faction.
    
    Types:
      - 'land_controlling': Can independently control territory (e.g. HTS, SNA in Syria).
        When they capture land, the map shows the faction's thick outer border with
        their own color as a thinner inner fill.
      - 'notable': Important fighting force that doesn't hold territory independently
        (e.g. Wagner in Ukraine). Highlighted for importance but captures default
        to the parent faction's color.
    
    A typical war has 3-4 factions but ~20 sub-factions.
    If a sub-faction type is 'notable' or unrecognized, territory defaults to parent faction.
    """
    __tablename__ = "subfactions"
    id = db.Column(db.Integer, primary_key=True)
    faction_id = db.Column(db.Integer, db.ForeignKey("factions.id"), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)  # e.g. "HTS", "Wagner", "SNA"
    short_name = db.Column(db.String(20))             # e.g. "HTS", "WAG"
    color = db.Column(db.String(20), default="#808080")  # Inner color for territory
    
    # 'land_controlling' = can hold territory, 'notable' = important but no land control
    subfaction_type = db.Column(db.String(20), default="notable")
    
    # Description / notes about what this group is
    description = db.Column(db.Text)
    
    # Territory GeoJSON - only for land_controlling sub-factions
    territory_geojson = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def controls_land(self):
        """Returns True if this sub-faction can independently control territory."""
        return self.subfaction_type == "land_controlling"
    
    def to_dict(self):
        return {
            "id": self.id,
            "faction_id": self.faction_id,
            "name": self.name,
            "short_name": self.short_name,
            "color": self.color,
            "subfaction_type": self.subfaction_type,
            "description": self.description,
            "controls_land": self.controls_land(),
            "territory_geojson": self.territory_geojson
        }


class TerritorySnapshot(db.Model):
    """
    Stores territory state for a specific date range.
    Allows historical tracking of territory changes over time.
    """
    __tablename__ = "territory_snapshots"
    id = db.Column(db.Integer, primary_key=True)
    faction_id = db.Column(db.Integer, db.ForeignKey("factions.id"), nullable=False)
    
    # Date this territory starts being valid
    effective_date = db.Column(db.Date, nullable=False, default=date.today)
    
    # If null, this territory applies indefinitely (until a new snapshot exists)
    # If set, territory only applies until this date
    end_date = db.Column(db.Date, nullable=True)
    
    # Is this a permanent change or temporary?
    is_permanent = db.Column(db.Boolean, default=True)
    
    # The territory GeoJSON for this snapshot
    territory_geojson = db.Column(db.Text)
    
    # Optional: which sub-faction controls this specific territory piece
    # If null, territory is attributed to the parent faction directly
    sub_faction_id = db.Column(db.Integer, db.ForeignKey("subfactions.id"), nullable=True)
    
    # Who/what created this snapshot
    source = db.Column(db.String(50), default="manual")  # "manual", "ai_ingest", "event"
    source_event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=True)
    
    # Notes about the change
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    faction = db.relationship("Faction", backref=db.backref("territory_snapshots", lazy=True, order_by="TerritorySnapshot.effective_date.desc()", cascade="all, delete-orphan"))
    sub_faction = db.relationship("SubFaction", backref=db.backref("territory_snapshots", lazy=True))
    source_event = db.relationship("Event", backref=db.backref("territory_changes", lazy=True))
    
    def to_dict(self):
        return {
            "id": self.id,
            "faction_id": self.faction_id,
            "sub_faction_id": self.sub_faction_id,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_permanent": self.is_permanent,
            "territory_geojson": self.territory_geojson,
            "source": self.source,
            "notes": self.notes
        }


class FactionCapital(db.Model):
    """
    Capital/anchor points for factions.
    Used to anchor news that doesn't have specific geolocation.
    Supports date ranges for historical tracking.
    """
    __tablename__ = "faction_capitals"
    id = db.Column(db.Integer, primary_key=True)
    faction_id = db.Column(db.Integer, db.ForeignKey("factions.id"), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)  # e.g. "Damascus", "Idlib"
    
    # Location
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    
    # Is this the primary capital? (used as default anchor point)
    is_primary = db.Column(db.Boolean, default=False)
    
    # Optional region/sector this capital represents
    sector_name = db.Column(db.String(100))  # e.g. "Northern Syria", "Damascus Region"
    
    # Date range - when this capital was active
    effective_date = db.Column(db.Date, nullable=True)  # When this became capital (null = from start)
    end_date = db.Column(db.Date, nullable=True)  # When it stopped being capital (null = still active)
    
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    faction = db.relationship("Faction", backref=db.backref("capitals", lazy=True, cascade="all, delete-orphan"))
    
    def to_dict(self):
        return {
            "id": self.id,
            "faction_id": self.faction_id,
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
            "is_primary": self.is_primary,
            "sector_name": self.sector_name,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }
