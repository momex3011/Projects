from flask import Blueprint, jsonify, request
from extensions import db
from models.war import War
from models.event import Event
from models.category import Category
from models.territory import Territory
from models.location import Location
from models.history import TerritoryHistory
from models.faction import Faction, SubFaction, TerritorySnapshot, FactionCapital
import json
from datetime import datetime, date
from sqlalchemy import func

api_bp = Blueprint("api", __name__)

@api_bp.route("/wars")
def api_wars():
    wars = War.query.all()
    return jsonify([{
        "id": w.id, "name": w.name, 
        "start_date": w.start_date.isoformat() if w.start_date else None,
        "default_lat": w.default_lat, "default_lng": w.default_lng, "default_zoom": w.default_zoom
    } for w in wars])

@api_bp.route("/wars/<int:war_id>/events")
def api_war_events(war_id):
    # Base query
    dt = request.args.get("date")
    
    if not dt:
        # Live Mode: Show latest 100 events
        evs = Event.query.filter_by(war_id=war_id).order_by(Event.event_date.desc()).limit(100).all()
        return jsonify([e.to_dict() for e in evs])

    # TIME MACHINE MODE
    target_date = dt # Expecting YYYY-MM-DD
    
    # 1. Query only events for that specific day
    # Order by Evidence Score (Crucial for Map Clarity)
    query = Event.query.filter(
        Event.war_id == war_id,
        db.func.date(Event.event_date) == target_date
    ).order_by(Event.evidence_score.desc())
    
    # 2. The 50-Item Limit (Antigravity Protocol)
    events = query.limit(50).all()
    
    # 3. The "Surplus" Logic (Temporal Overflow)
    # If the day is quiet (less than 50 news items), show high-priority items from yesterday.
    if len(events) < 50:
        try:
            from datetime import timedelta, date
            current_dt = datetime.strptime(target_date, "%Y-%m-%d").date()
            previous_day = current_dt - timedelta(days=1)
            
            surplus_limit = 50 - len(events)
            
            surplus_events = Event.query.filter(
                Event.war_id == war_id,
                db.func.date(Event.event_date) == previous_day,
                Event.evidence_score >= 3 # Only show MAJOR events from previous day
            ).order_by(Event.evidence_score.desc()).limit(surplus_limit).all()
            
            # Add them to the map (User sees context from yesterday)
            events.extend(surplus_events)
        except Exception as e:
            print(f"Surplus Logic Error: {e}")

    return jsonify([{
        "id": e.id,
        "title": e.title,
        "description": e.description,
        "event_date": e.event_date.isoformat(),
        "lat": e.lat,
        "lng": e.lng,
        "source_url": e.source_url,
        "image_url": e.image_url,      
        "category_id": e.category_id,
        "evidence_score": e.evidence_score
    } for e in events])

@api_bp.route("/wars/<int:war_id>/locations")
def api_war_locations(war_id):
    # Returns the AI's learned territory points
    # Optional: ?date=YYYY-MM-DD
    date_str = request.args.get("date")
    
    if not date_str:
        # LIVE MODE: Return current controller
        locs = Location.query.filter_by(war_id=war_id).all()
        return jsonify([l.to_dict() for l in locs])
    else:
        # TIME MACHINE MODE
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Let's do the SQL way for performance
            subquery = db.session.query(TerritoryHistory.controller).\
                filter(TerritoryHistory.location_id == Location.id).\
                filter(TerritoryHistory.valid_from <= target_date).\
                order_by(TerritoryHistory.valid_from.desc()).\
                limit(1).correlate(Location)

            query = db.session.query(
                Location.name, Location.lat, Location.lng, 
                Location.importance,
                subquery.label("history_controller")
            ).filter(Location.war_id == war_id)
            
            rows = query.all()
            results = []
            
            for r in rows:
                controller = r.history_controller or "Government Control" # Default to Gov if no history (start of war)
                # Importance determines influence radius: small=3km, medium=8km, large=15km
                importance = r.importance or 5
                results.append({
                    "name": r.name,
                    "lat": r.lat,
                    "lng": r.lng,
                    "controller": controller,
                    "importance": importance
                })
                
            return jsonify(results)

        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

@api_bp.route("/categories")
def api_categories():
    cats = Category.query.all()
    return jsonify([{"id": c.id, "name": c.name, "icon": c.icon, "color": c.color} for c in cats])

@api_bp.route("/wars/<int:war_id>/territories")
def api_war_territories(war_id):
    # Returns the static map shapes (Country borders)
    territories = Territory.query.filter_by(war_id=war_id).all()
    features = []
    for t in territories:
        try:
            geometry = json.loads(t.geojson)
            features.append({
                "type": "Feature",
                "properties": {
                    "name": t.name,
                    "color": t.color
                },
                "geometry": geometry
            })
        except Exception as e:
            print(f"Error parsing geometry for territory {t.id}: {e}")

    return jsonify({
        "type": "FeatureCollection",
        "features": features
    })

@api_bp.route("/wars/<int:war_id>/hotspots")
def api_war_hotspots(war_id):
    """
    Returns locations that changed hands recently (within ±3 days of target date).
    These are 'frontline hotspots' where active fighting is happening.
    """
    from datetime import timedelta
    
    date_str = request.args.get("date")
    if not date_str:
        return jsonify([])
    
    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        start_date = target_date - timedelta(days=3)
        end_date = target_date + timedelta(days=3)
        
        # Find all locations that had control changes in this window
        recent_changes = db.session.query(
            TerritoryHistory.location_id,
            Location.name,
            Location.lat,
            Location.lng,
            TerritoryHistory.controller,
            TerritoryHistory.valid_from
        ).join(Location, TerritoryHistory.location_id == Location.id).filter(
            TerritoryHistory.valid_from.between(start_date, end_date)
        ).order_by(TerritoryHistory.valid_from.desc()).all()
        
        hotspots = []
        seen = set()
        for row in recent_changes:
            if row.location_id not in seen:
                seen.add(row.location_id)
                hotspots.append({
                    "name": row.name,
                    "lat": row.lat,
                    "lng": row.lng,
                    "new_controller": row.controller,
                    "change_date": row.valid_from.isoformat()
                })
        
        return jsonify(hotspots)
    except Exception as e:
        print(f"Hotspots API Error: {e}")
        return jsonify([])


@api_bp.route("/wars/<int:war_id>/factions")
def api_war_factions(war_id):
    """
    Returns all factions with their territory GeoJSON for the public map.
    This is what powers the faction control visualization.
    
    Now includes sub-faction data:
    - land_controlling sub-factions have their own territory/color
    - notable sub-factions are listed for reference but territory defaults to faction
    
    Optional: ?date=YYYY-MM-DD to get territory as of a specific date
    """
    date_str = request.args.get("date")
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    
    result = []
    for f in factions:
        # Build sub-faction list
        subfactions_data = []
        for sf in f.subfactions:
            sf_data = {
                "id": sf.id,
                "name": sf.name,
                "short_name": sf.short_name,
                "color": sf.color,
                "subfaction_type": sf.subfaction_type,
                "controls_land": sf.controls_land(),
                "territory": None
            }
            
            # Only land-controlling sub-factions carry their own territory
            if sf.controls_land() and sf.territory_geojson:
                try:
                    sf_data["territory"] = json.loads(sf.territory_geojson)
                except:
                    pass
            
            subfactions_data.append(sf_data)
        
        faction_data = {
            "id": f.id,
            "name": f.name,
            "short_name": f.short_name,
            "color": f.color,
            "territory": None,
            "snapshot_date": None,
            "subfactions": subfactions_data
        }
        
        if date_str:
            # TIME MACHINE MODE: Get territory as of specific date
            try:
                query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                # Find the most recent snapshot effective on or before query date
                snapshot = TerritorySnapshot.query.filter(
                    TerritorySnapshot.faction_id == f.id,
                    TerritorySnapshot.effective_date <= query_date
                ).filter(
                    db.or_(
                        TerritorySnapshot.end_date.is_(None),
                        TerritorySnapshot.end_date >= query_date
                    )
                ).order_by(TerritorySnapshot.effective_date.desc()).first()
                
                if snapshot and snapshot.territory_geojson:
                    faction_data["territory"] = json.loads(snapshot.territory_geojson)
                    faction_data["snapshot_date"] = snapshot.effective_date.isoformat()
                elif f.territory_geojson:
                    # Fall back to current territory
                    faction_data["territory"] = json.loads(f.territory_geojson)
            except:
                pass
        else:
            # LIVE MODE: Get current territory
            if f.territory_geojson:
                try:
                    faction_data["territory"] = json.loads(f.territory_geojson)
                except:
                    pass
        
        result.append(faction_data)
    
    return jsonify(result)


@api_bp.route("/wars/<int:war_id>/capitals")
def api_war_capitals(war_id):
    """
    Returns all faction capitals/anchor points for the public map.
    These are used to anchor news that doesn't have specific geolocation.
    
    Optional: ?date=YYYY-MM-DD to get capitals active on that date
    """
    date_str = request.args.get("date")
    query_date = None
    
    if date_str:
        try:
            query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            pass
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    
    result = []
    for f in factions:
        # Get all capitals for this faction
        capitals_query = FactionCapital.query.filter_by(faction_id=f.id)
        
        # If date specified, filter to capitals active on that date
        if query_date:
            capitals_query = capitals_query.filter(
                db.or_(
                    FactionCapital.effective_date.is_(None),
                    FactionCapital.effective_date <= query_date
                )
            ).filter(
                db.or_(
                    FactionCapital.end_date.is_(None),
                    FactionCapital.end_date >= query_date
                )
            )
        
        capitals = capitals_query.all()
        
        for c in capitals:
            result.append({
                "id": c.id,
                "faction_id": f.id,
                "faction_name": f.name,
                "faction_color": f.color,
                "name": c.name,
                "lat": c.lat,
                "lng": c.lng,
                "is_primary": c.is_primary,
                "sector_name": c.sector_name,
                "effective_date": c.effective_date.isoformat() if c.effective_date else None,
                "end_date": c.end_date.isoformat() if c.end_date else None
            })
    
    return jsonify(result)


@api_bp.route("/factions/<int:faction_id>/capital")
def api_faction_primary_capital(faction_id):
    """
    Returns the primary capital for a faction.
    Used to anchor news without specific geolocation.
    """
    capital = FactionCapital.query.filter_by(
        faction_id=faction_id, 
        is_primary=True
    ).first()
    
    if not capital:
        # Fall back to any capital
        capital = FactionCapital.query.filter_by(faction_id=faction_id).first()
    
    if capital:
        return jsonify(capital.to_dict())
    
    return jsonify({"error": "No capital found"}), 404


# ==================== TERRITORY SNAPSHOT MANAGEMENT ====================

@api_bp.route("/wars/<int:war_id>/territory-snapshots")
def api_territory_snapshots(war_id):
    """
    Returns available territory snapshot dates for a war.
    Used for the time machine date picker.
    """
    from sqlalchemy import distinct
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    faction_ids = [f.id for f in factions]
    
    # Get all unique snapshot dates
    dates = db.session.query(
        distinct(TerritorySnapshot.effective_date)
    ).filter(
        TerritorySnapshot.faction_id.in_(faction_ids)
    ).order_by(TerritorySnapshot.effective_date.desc()).all()
    
    return jsonify({
        "war_id": war_id,
        "snapshot_dates": [d[0].isoformat() for d in dates if d[0]]
    })


@api_bp.route("/wars/<int:war_id>/territory-history")
def api_territory_history(war_id):
    """
    Returns territory changes over time for visualization.
    Shows how the map evolved day by day.
    
    Optional: ?start=YYYY-MM-DD&end=YYYY-MM-DD
    """
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    faction_ids = [f.id for f in factions]
    
    query = TerritorySnapshot.query.filter(
        TerritorySnapshot.faction_id.in_(faction_ids)
    )
    
    if start_str:
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            query = query.filter(TerritorySnapshot.effective_date >= start_date)
        except:
            pass
    
    if end_str:
        try:
            end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
            query = query.filter(TerritorySnapshot.effective_date <= end_date)
        except:
            pass
    
    snapshots = query.order_by(TerritorySnapshot.effective_date).all()
    
    # Group by date
    by_date = {}
    for snap in snapshots:
        date_key = snap.effective_date.isoformat()
        if date_key not in by_date:
            by_date[date_key] = []
        
        faction = next((f for f in factions if f.id == snap.faction_id), None)
        by_date[date_key].append({
            "faction_id": snap.faction_id,
            "faction_name": faction.name if faction else "Unknown",
            "faction_color": faction.color if faction else "#808080",
            "source": snap.source,
            "notes": snap.notes
        })
    
    return jsonify({
        "war_id": war_id,
        "history": by_date
    })


@api_bp.route("/wars/<int:war_id>/create-snapshot", methods=["POST"])
def api_create_snapshot(war_id):
    """
    Manually trigger creation of territory snapshots for a specific date.
    Used by admin or automated processes.
    
    POST body: {"date": "YYYY-MM-DD"} or empty for today
    """
    from tasks import create_daily_territory_snapshots
    
    data = request.get_json() or {}
    snapshot_date = data.get("date")
    
    # Trigger the Celery task
    result = create_daily_territory_snapshots.delay(war_id=war_id, snapshot_date=snapshot_date)
    
    return jsonify({
        "status": "queued",
        "task_id": result.id,
        "war_id": war_id,
        "date": snapshot_date or "today"
    })


@api_bp.route("/wars/<int:war_id>/territory-on-date")
def api_territory_on_date(war_id):
    """
    Get complete territory state for a specific date.
    Returns all factions with their territory as of that date.
    
    Required: ?date=YYYY-MM-DD
    """
    date_str = request.args.get("date")
    
    if not date_str:
        return jsonify({"error": "date parameter required"}), 400
    
    try:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    
    result = {
        "war_id": war_id,
        "date": date_str,
        "factions": []
    }
    
    for f in factions:
        # Get snapshot for this date
        snapshot = TerritorySnapshot.query.filter(
            TerritorySnapshot.faction_id == f.id,
            TerritorySnapshot.effective_date <= query_date
        ).order_by(TerritorySnapshot.effective_date.desc()).first()
        
        faction_data = {
            "id": f.id,
            "name": f.name,
            "short_name": f.short_name,
            "color": f.color,
            "territory": None,
            "snapshot_date": None,
            "source": None
        }
        
        if snapshot and snapshot.territory_geojson:
            try:
                faction_data["territory"] = json.loads(snapshot.territory_geojson)
                faction_data["snapshot_date"] = snapshot.effective_date.isoformat()
                faction_data["source"] = snapshot.source
            except:
                pass
        elif f.territory_geojson:
            # Fall back to current territory
            try:
                faction_data["territory"] = json.loads(f.territory_geojson)
                faction_data["snapshot_date"] = "current"
                faction_data["source"] = "live"
            except:
                pass
        
        result["factions"].append(faction_data)
    
    return jsonify(result)