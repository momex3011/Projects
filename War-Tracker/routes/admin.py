from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.war import War
from models.event import Event
from models.category import Category
from models.faction import Faction, SubFaction, TerritorySnapshot, FactionCapital
from extensions import db
from datetime import datetime, date
import json

admin_bp = Blueprint("admin", __name__, template_folder="templates")

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return wrapped

@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    wars = War.query.order_by(War.created_at.desc()).all()
    events = Event.query.order_by(Event.created_at.desc()).limit(50).all()
    return render_template("admin_dashboard.html", wars=wars, events=events)

@admin_bp.route("/wars/add", methods=["GET","POST"])
@login_required
@admin_required
def add_war():
    if request.method == "POST":
        # Convert string date "2011-03-15" to Python Date Object
        date_str = request.form.get("start_date")
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

        w = War(
            name=request.form["name"],
            description=request.form["description"],
            start_date=date_obj,
            default_lat=float(request.form.get("default_lat") or 0.0),
            default_lng=float(request.form.get("default_lng") or 0.0),
            default_zoom=int(request.form.get("default_zoom") or 6)
        )
        db.session.add(w)
        db.session.commit()
        flash("War created", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_add_war.html")

@admin_bp.route("/events/add", methods=["GET","POST"])
@login_required
@admin_required
def add_event():
    cats = Category.query.all()
    wars = War.query.all()
    if request.method == "POST":
        # Convert string date to Python Date Object
        date_str = request.form.get("event_date")
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None

        ev = Event(
            war_id = int(request.form["war_id"]),
            category_id = int(request.form["category_id"]) if request.form.get("category_id") else None,
            title = request.form.get("title"),
            description = request.form.get("description"),
            event_date = date_obj,
            lat = float(request.form["lat"]),
            lng = float(request.form["lng"]),
            source_url = request.form.get("source_url")
        )
        db.session.add(ev)
        db.session.commit()
        flash("Event added", "success")
        return redirect(url_for("admin.dashboard"))
    return render_template("admin_add_event.html", cats=cats, wars=wars)


# ============================================================
# FACTION MANAGEMENT
# ============================================================

@admin_bp.route("/wars/<int:war_id>/factions")
@login_required
@admin_required
def manage_factions(war_id):
    """View and manage factions for a war"""
    war = War.query.get_or_404(war_id)
    factions = Faction.query.filter_by(war_id=war_id).all()
    return render_template("admin_factions.html", war=war, factions=factions)


@admin_bp.route("/wars/<int:war_id>/factions/add", methods=["POST"])
@login_required
@admin_required
def add_faction(war_id):
    """Add a new faction"""
    war = War.query.get_or_404(war_id)
    
    faction = Faction(
        war_id=war_id,
        name=request.form.get("name", "New Faction"),
        short_name=request.form.get("short_name", "NEW"),
        color=request.form.get("color", "#808080")
    )
    db.session.add(faction)
    db.session.commit()
    flash(f"Faction '{faction.name}' created", "success")
    return redirect(url_for("admin.manage_factions", war_id=war_id))


@admin_bp.route("/factions/<int:faction_id>/update", methods=["POST"])
@login_required
@admin_required
def update_faction(faction_id):
    """Update faction name/color"""
    faction = Faction.query.get_or_404(faction_id)
    
    faction.name = request.form.get("name", faction.name)
    faction.short_name = request.form.get("short_name", faction.short_name)
    faction.color = request.form.get("color", faction.color)
    
    db.session.commit()
    flash(f"Faction '{faction.name}' updated", "success")
    return redirect(url_for("admin.manage_factions", war_id=faction.war_id))


@admin_bp.route("/factions/<int:faction_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_faction(faction_id):
    """Delete a faction and all related data"""
    faction = Faction.query.get_or_404(faction_id)
    war_id = faction.war_id
    name = faction.name
    
    # Delete related records first to avoid integrity errors
    from models.faction import FactionCapital, TerritorySnapshot, SubFaction
    
    # Delete all capitals for this faction
    FactionCapital.query.filter_by(faction_id=faction_id).delete()
    
    # Delete all territory snapshots for this faction
    TerritorySnapshot.query.filter_by(faction_id=faction_id).delete()
    
    # Delete all sub-factions for this faction
    SubFaction.query.filter_by(faction_id=faction_id).delete()
    
    # Now delete the faction itself
    db.session.delete(faction)
    db.session.commit()
    flash(f"Faction '{name}' deleted", "warning")
    return redirect(url_for("admin.manage_factions", war_id=war_id))


# ============================================================
# SUB-FACTION MANAGEMENT  
# ============================================================

@admin_bp.route("/factions/<int:faction_id>/subfactions/add", methods=["POST"])
@login_required
@admin_required
def add_subfaction(faction_id):
    """Add a new sub-faction to a faction"""
    faction = Faction.query.get_or_404(faction_id)
    
    sf = SubFaction(
        faction_id=faction_id,
        name=request.form.get("name", "New Sub-Faction"),
        short_name=request.form.get("short_name", ""),
        color=request.form.get("color", faction.color),
        subfaction_type=request.form.get("subfaction_type", "notable"),
        description=request.form.get("description", "")
    )
    db.session.add(sf)
    db.session.commit()
    flash(f"Sub-faction '{sf.name}' added to {faction.name}", "success")
    return redirect(url_for("admin.manage_factions", war_id=faction.war_id))


@admin_bp.route("/subfactions/<int:subfaction_id>/update", methods=["POST"])
@login_required
@admin_required
def update_subfaction(subfaction_id):
    """Update a sub-faction"""
    sf = SubFaction.query.get_or_404(subfaction_id)
    
    sf.name = request.form.get("name", sf.name)
    sf.short_name = request.form.get("short_name", sf.short_name)
    sf.color = request.form.get("color", sf.color)
    sf.subfaction_type = request.form.get("subfaction_type", sf.subfaction_type)
    sf.description = request.form.get("description", sf.description)
    
    db.session.commit()
    flash(f"Sub-faction '{sf.name}' updated", "success")
    return redirect(url_for("admin.manage_factions", war_id=sf.parent_faction.war_id))


@admin_bp.route("/subfactions/<int:subfaction_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_subfaction(subfaction_id):
    """Delete a sub-faction"""
    sf = SubFaction.query.get_or_404(subfaction_id)
    war_id = sf.parent_faction.war_id
    name = sf.name
    
    # Clear any territory snapshot references to this sub-faction
    TerritorySnapshot.query.filter_by(sub_faction_id=subfaction_id).update({"sub_faction_id": None})
    
    db.session.delete(sf)
    db.session.commit()
    flash(f"Sub-faction '{name}' deleted", "warning")
    return redirect(url_for("admin.manage_factions", war_id=war_id))


# ============================================================
# TERRITORY EDITOR - Interactive Map
# ============================================================

@admin_bp.route("/wars/<int:war_id>/territory-editor")
@login_required
@admin_required
def territory_editor(war_id):
    """Interactive map for drawing faction territories"""
    war = War.query.get_or_404(war_id)
    factions = Faction.query.filter_by(war_id=war_id).all()
    today = date.today().isoformat()
    return render_template("admin_territory_editor.html", war=war, factions=factions, today=today)


@admin_bp.route("/factions/<int:faction_id>/territory", methods=["POST"])
@login_required
@admin_required
def save_faction_territory(faction_id):
    """Save GeoJSON territory for a faction (AJAX endpoint)"""
    faction = Faction.query.get_or_404(faction_id)
    
    data = request.get_json()
    if data and "geojson" in data:
        faction.territory_geojson = json.dumps(data["geojson"])
        db.session.commit()
        return jsonify({"success": True, "message": f"Territory saved for {faction.name}"})
    
    return jsonify({"success": False, "message": "Invalid data"}), 400


@admin_bp.route("/api/wars/<int:war_id>/factions")
@login_required
@admin_required
def api_get_factions(war_id):
    """Get all factions with their territories as GeoJSON"""
    factions = Faction.query.filter_by(war_id=war_id).all()
    
    features = []
    for f in factions:
        feature = {
            "id": f.id,
            "name": f.name,
            "short_name": f.short_name,
            "color": f.color,
            "territory": json.loads(f.territory_geojson) if f.territory_geojson else None,
            "subfactions": [{
                "id": sf.id,
                "name": sf.name,
                "short_name": sf.short_name,
                "color": sf.color,
                "subfaction_type": sf.subfaction_type,
                "controls_land": sf.controls_land(),
                "territory": json.loads(sf.territory_geojson) if sf.territory_geojson else None
            } for sf in f.subfactions]
        }
        features.append(feature)
    
    return jsonify(features)


# ============================================================
# TERRITORY SNAPSHOTS - Date-based territory tracking
# ============================================================

@admin_bp.route("/factions/<int:faction_id>/territory/snapshot", methods=["POST"])
@login_required
@admin_required
def save_territory_snapshot(faction_id):
    """Save territory as a dated snapshot (AJAX endpoint)"""
    faction = Faction.query.get_or_404(faction_id)
    
    data = request.get_json()
    if not data or "geojson" not in data:
        return jsonify({"success": False, "message": "Invalid data"}), 400
    
    # Parse date or use today
    effective_date_str = data.get("effective_date")
    if effective_date_str:
        effective_date = datetime.strptime(effective_date_str, "%Y-%m-%d").date()
    else:
        effective_date = date.today()
    
    # Parse end date if provided
    end_date_str = data.get("end_date")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
    
    is_permanent = data.get("is_permanent", True)
    notes = data.get("notes", "")
    
    # Create snapshot
    snapshot = TerritorySnapshot(
        faction_id=faction_id,
        effective_date=effective_date,
        end_date=end_date,
        is_permanent=is_permanent,
        territory_geojson=json.dumps(data["geojson"]),
        source="manual",
        notes=notes
    )
    db.session.add(snapshot)
    
    # Also update the current territory on the faction
    faction.territory_geojson = json.dumps(data["geojson"])
    
    db.session.commit()
    
    return jsonify({
        "success": True, 
        "message": f"Territory snapshot saved for {faction.name}",
        "snapshot_id": snapshot.id
    })


@admin_bp.route("/factions/<int:faction_id>/territory/history")
@login_required
@admin_required
def get_territory_history(faction_id):
    """Get territory history for a faction"""
    faction = Faction.query.get_or_404(faction_id)
    snapshots = TerritorySnapshot.query.filter_by(faction_id=faction_id)\
        .order_by(TerritorySnapshot.effective_date.desc()).all()
    
    return jsonify({
        "faction": faction.to_dict(),
        "snapshots": [s.to_dict() for s in snapshots]
    })


@admin_bp.route("/wars/<int:war_id>/territory/at-date")
@login_required
@admin_required  
def get_territory_at_date(war_id):
    """Get all faction territories as they were on a specific date"""
    date_str = request.args.get("date")
    if date_str:
        query_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        query_date = date.today()
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    
    result = []
    for faction in factions:
        # Find the most recent snapshot that was effective on or before the query date
        snapshot = TerritorySnapshot.query.filter(
            TerritorySnapshot.faction_id == faction.id,
            TerritorySnapshot.effective_date <= query_date
        ).filter(
            # Either no end date, or end date is after query date
            db.or_(
                TerritorySnapshot.end_date.is_(None),
                TerritorySnapshot.end_date >= query_date
            )
        ).order_by(TerritorySnapshot.effective_date.desc()).first()
        
        territory_data = None
        if snapshot:
            territory_data = json.loads(snapshot.territory_geojson) if snapshot.territory_geojson else None
        elif faction.territory_geojson:
            # Fall back to current territory
            territory_data = json.loads(faction.territory_geojson)
        
        result.append({
            "faction": faction.to_dict(),
            "territory": territory_data,
            "snapshot_date": snapshot.effective_date.isoformat() if snapshot else None
        })
    
    return jsonify({
        "query_date": query_date.isoformat(),
        "territories": result
    })


# ============================================================
# FACTION CAPITALS - Anchor points for news
# ============================================================

@admin_bp.route("/factions/<int:faction_id>/capitals")
@login_required
@admin_required
def get_faction_capitals(faction_id):
    """Get all capitals for a faction"""
    faction = Faction.query.get_or_404(faction_id)
    capitals = FactionCapital.query.filter_by(faction_id=faction_id).all()
    
    return jsonify({
        "faction": faction.to_dict(),
        "capitals": [c.to_dict() for c in capitals]
    })


@admin_bp.route("/factions/<int:faction_id>/capitals/add", methods=["POST"])
@login_required
@admin_required
def add_faction_capital(faction_id):
    """Add a capital/anchor point for a faction (AJAX)"""
    faction = Faction.query.get_or_404(faction_id)
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    # If this is set as primary, unset other primaries (for overlapping dates)
    if data.get("is_primary"):
        FactionCapital.query.filter_by(faction_id=faction_id, is_primary=True)\
            .update({"is_primary": False})
    
    # Parse dates
    effective_date = None
    end_date = None
    if data.get("effective_date"):
        effective_date = datetime.strptime(data["effective_date"], "%Y-%m-%d").date()
    if data.get("end_date"):
        end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
    
    capital = FactionCapital(
        faction_id=faction_id,
        name=data.get("name", "Capital"),
        lat=float(data.get("lat", 0)),
        lng=float(data.get("lng", 0)),
        is_primary=data.get("is_primary", False),
        sector_name=data.get("sector_name", ""),
        effective_date=effective_date,
        end_date=end_date
    )
    db.session.add(capital)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"Capital '{capital.name}' added",
        "capital": capital.to_dict()
    })


@admin_bp.route("/capitals/<int:capital_id>/update", methods=["POST"])
@login_required
@admin_required
def update_faction_capital(capital_id):
    """Update a capital"""
    capital = FactionCapital.query.get_or_404(capital_id)
    
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "No data provided"}), 400
    
    if "name" in data:
        capital.name = data["name"]
    if "lat" in data:
        capital.lat = float(data["lat"])
    if "lng" in data:
        capital.lng = float(data["lng"])
    if "sector_name" in data:
        capital.sector_name = data["sector_name"]
    if "is_primary" in data:
        if data["is_primary"]:
            # Unset other primaries first
            FactionCapital.query.filter_by(faction_id=capital.faction_id, is_primary=True)\
                .update({"is_primary": False})
        capital.is_primary = data["is_primary"]
    
    # Handle date updates
    if "effective_date" in data:
        if data["effective_date"]:
            capital.effective_date = datetime.strptime(data["effective_date"], "%Y-%m-%d").date()
        else:
            capital.effective_date = None
    if "end_date" in data:
        if data["end_date"]:
            capital.end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
        else:
            capital.end_date = None
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"Capital '{capital.name}' updated",
        "capital": capital.to_dict()
    })


@admin_bp.route("/capitals/<int:capital_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_faction_capital(capital_id):
    """Delete a capital"""
    capital = FactionCapital.query.get_or_404(capital_id)
    name = capital.name
    
    db.session.delete(capital)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"Capital '{name}' deleted"
    })


# ============================================================
# TERRITORY SNAPSHOT MANAGEMENT - Daily map versioning
# ============================================================

@admin_bp.route("/wars/<int:war_id>/snapshots/create", methods=["POST"])
@login_required
@admin_required
def create_war_snapshots(war_id):
    """
    Manually create territory snapshots for all factions in a war.
    This captures the current map state for a specific date.
    """
    war = War.query.get_or_404(war_id)
    data = request.get_json() or {}
    
    # Get target date (default to today)
    date_str = data.get("date")
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        target_date = date.today()
    
    notes = data.get("notes", f"Manual snapshot created on {datetime.now().isoformat()}")
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    created = []
    skipped = []
    
    for faction in factions:
        # Check if snapshot already exists
        existing = TerritorySnapshot.query.filter_by(
            faction_id=faction.id,
            effective_date=target_date
        ).first()
        
        if existing:
            skipped.append(faction.name)
            continue
        
        if not faction.territory_geojson:
            skipped.append(f"{faction.name} (no territory)")
            continue
        
        # Create snapshot
        snapshot = TerritorySnapshot(
            faction_id=faction.id,
            effective_date=target_date,
            territory_geojson=faction.territory_geojson,
            source="manual",
            notes=notes
        )
        db.session.add(snapshot)
        created.append(faction.name)
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "date": target_date.isoformat(),
        "created": created,
        "skipped": skipped,
        "message": f"Created {len(created)} snapshots for {target_date}"
    })


@admin_bp.route("/wars/<int:war_id>/snapshots/status")
@login_required
@admin_required
def snapshot_status(war_id):
    """
    Get snapshot status for a war - shows available dates and gaps.
    Useful for understanding map history coverage.
    """
    war = War.query.get_or_404(war_id)
    factions = Faction.query.filter_by(war_id=war_id).all()
    faction_ids = [f.id for f in factions]
    
    # Get all snapshot dates
    from sqlalchemy import distinct, func
    
    snapshot_counts = db.session.query(
        TerritorySnapshot.effective_date,
        func.count(TerritorySnapshot.id).label('count')
    ).filter(
        TerritorySnapshot.faction_id.in_(faction_ids)
    ).group_by(
        TerritorySnapshot.effective_date
    ).order_by(
        TerritorySnapshot.effective_date.desc()
    ).limit(100).all()
    
    # Get date range
    earliest = db.session.query(
        func.min(TerritorySnapshot.effective_date)
    ).filter(
        TerritorySnapshot.faction_id.in_(faction_ids)
    ).scalar()
    
    latest = db.session.query(
        func.max(TerritorySnapshot.effective_date)
    ).filter(
        TerritorySnapshot.faction_id.in_(faction_ids)
    ).scalar()
    
    return jsonify({
        "war_id": war_id,
        "war_name": war.name,
        "faction_count": len(factions),
        "earliest_snapshot": earliest.isoformat() if earliest else None,
        "latest_snapshot": latest.isoformat() if latest else None,
        "recent_snapshots": [
            {"date": s.effective_date.isoformat(), "faction_count": s.count}
            for s in snapshot_counts
        ]
    })


@admin_bp.route("/wars/<int:war_id>/snapshots/trigger-celery", methods=["POST"])
@login_required
@admin_required
def trigger_celery_snapshot(war_id):
    """
    Trigger the Celery task to create daily snapshots.
    Used to manually run the scheduled task.
    """
    from tasks import create_daily_territory_snapshots
    
    data = request.get_json() or {}
    target_date = data.get("date")
    
    # Queue the task
    result = create_daily_territory_snapshots.delay(
        war_id=war_id,
        snapshot_date=target_date
    )
    
    return jsonify({
        "success": True,
        "task_id": result.id,
        "message": f"Snapshot task queued for war {war_id}",
        "date": target_date or "today"
    })