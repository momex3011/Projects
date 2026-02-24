"""
Load Simulation Events (2011-2013) into the War Tracker database.
=================================================================
This script:
  1. Finds (or creates) the Syrian Civil War entry
  2. Inserts each simulation event as an Event row
  3. Creates/updates Location rows with controller info
  4. Creates TerritoryHistory rows so the time-machine slider works
  5. Skips duplicates (safe to re-run)

Usage:
    python simulation/load_simulation.py          # Load all events
    python simulation/load_simulation.py --clear   # Wipe simulation data first, then reload
    python simulation/load_simulation.py --dry-run  # Preview without writing to DB
"""

import sys, os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app import create_app
from extensions import db
from models.war import War
from models.event import Event
from models.location import Location
from models.history import TerritoryHistory

# Import simulation data
from simulation.events_2011_2013 import SIMULATION_EVENTS


def find_or_create_war(app):
    """Find the Syrian Civil War or create it."""
    with app.app_context():
        war = War.query.filter(War.name.ilike("%syria%")).first()
        if not war:
            war = War.query.first()  # Fall back to the first war
        if not war:
            print("⚠️  No war found. Creating 'Syrian Civil War'...")
            war = War(
                name="Syrian Civil War",
                description="The Syrian Civil War (2011-present)",
                start_date=datetime(2011, 3, 15).date(),
                default_lat=35.0,
                default_lng=38.0,
                default_zoom=7
            )
            db.session.add(war)
            db.session.commit()
            print(f"✅ Created war: {war.name} (id={war.id})")
        else:
            print(f"📌 Using war: {war.name} (id={war.id})")
        return war.id


def clear_simulation_data(app, war_id):
    """Remove all simulation-tagged data."""
    with app.app_context():
        # Delete events that match our simulation headlines
        sim_headlines = [e["headline"] for e in SIMULATION_EVENTS]
        deleted_events = Event.query.filter(
            Event.war_id == war_id,
            Event.title.in_(sim_headlines)
        ).delete(synchronize_session='fetch')
        
        # Delete locations created by simulation
        sim_locations = list(set(e["location"] for e in SIMULATION_EVENTS))
        # Don't delete locations that might have been created by other means
        # Just reset their controllers
        locs = Location.query.filter(
            Location.war_id == war_id,
            Location.name.in_(sim_locations)
        ).all()
        
        deleted_history = 0
        for loc in locs:
            h_count = TerritoryHistory.query.filter_by(location_id=loc.id).delete()
            deleted_history += h_count
        
        deleted_locations = Location.query.filter(
            Location.war_id == war_id,
            Location.name.in_(sim_locations)
        ).delete(synchronize_session='fetch')
        
        db.session.commit()
        print(f"🗑️  Cleared: {deleted_events} events, {deleted_locations} locations, {deleted_history} history entries")


def load_events(app, war_id, dry_run=False):
    """Insert simulation events, locations, and territory history."""
    with app.app_context():
        stats = {"events_added": 0, "events_skipped": 0, 
                 "locations_created": 0, "locations_updated": 0,
                 "history_added": 0}
        
        # Sort events by date
        sorted_events = sorted(SIMULATION_EVENTS, key=lambda e: e["date"])
        
        for entry in sorted_events:
            event_date = datetime.strptime(entry["date"], "%Y-%m-%d").date()
            headline = entry["headline"]
            lat = entry["lat"]
            lng = entry["lng"]
            location_name = entry["location"]
            controller_after = entry["controller_after"]
            importance = entry.get("importance", 5)
            
            # --- 1. Create Event ---
            existing_event = Event.query.filter_by(
                war_id=war_id,
                title=headline,
                event_date=event_date
            ).first()
            
            if existing_event:
                stats["events_skipped"] += 1
            else:
                if not dry_run:
                    # Build unique source_url using date + location slug
                    loc_slug = location_name.lower().replace(" ", "-").replace("'", "")
                    event = Event(
                        war_id=war_id,
                        title=headline,
                        description=f"[SIM] {headline}",
                        event_date=event_date,
                        lat=lat,
                        lng=lng,
                        source_url=f"simulation://2011-2013/{entry['date']}/{loc_slug}",
                        evidence_score=8  # High score so they always show
                    )
                    db.session.add(event)
                stats["events_added"] += 1
            
            # --- 2. Create/Update Location ---
            loc = Location.query.filter_by(
                war_id=war_id,
                name=location_name
            ).first()
            
            if loc:
                if loc.controller != controller_after:
                    if not dry_run:
                        loc.controller = controller_after
                        loc.importance = max(loc.importance or 1, importance)
                    stats["locations_updated"] += 1
            else:
                if not dry_run:
                    loc = Location(
                        war_id=war_id,
                        name=location_name,
                        lat=lat,
                        lng=lng,
                        controller=controller_after,
                        importance=importance
                    )
                    db.session.add(loc)
                    db.session.flush()  # Get the ID
                stats["locations_created"] += 1
            
            # --- 3. Create TerritoryHistory entry ---
            if loc and not dry_run:
                # Check if this exact history entry exists
                existing_history = TerritoryHistory.query.filter_by(
                    location_id=loc.id,
                    controller=controller_after,
                    valid_from=event_date
                ).first()
                
                if not existing_history:
                    history = TerritoryHistory(
                        location_id=loc.id,
                        controller=controller_after,
                        valid_from=event_date
                    )
                    db.session.add(history)
                    stats["history_added"] += 1
        
        if not dry_run:
            db.session.commit()
            print("✅ Database committed successfully!")
        
        return stats


def print_summary(stats, dry_run=False):
    prefix = "🔍 [DRY RUN] " if dry_run else "✅ "
    print(f"\n{'='*60}")
    print(f"{prefix}SIMULATION LOAD COMPLETE")
    print(f"{'='*60}")
    print(f"  Events added:      {stats['events_added']}")
    print(f"  Events skipped:    {stats['events_skipped']}")
    print(f"  Locations created: {stats['locations_created']}")
    print(f"  Locations updated: {stats['locations_updated']}")
    print(f"  History entries:   {stats['history_added']}")
    print(f"{'='*60}")
    
    if dry_run:
        print("  ℹ️  No changes were written. Run without --dry-run to commit.")


def main():
    dry_run = "--dry-run" in sys.argv
    clear = "--clear" in sys.argv
    
    app = create_app()
    war_id = find_or_create_war(app)
    
    if clear:
        print("\n🗑️  Clearing previous simulation data...")
        clear_simulation_data(app, war_id)
    
    print(f"\n📦 Loading {len(SIMULATION_EVENTS)} simulation events (2011-2013)...")
    stats = load_events(app, war_id, dry_run=dry_run)
    print_summary(stats, dry_run=dry_run)
    
    if not dry_run:
        print(f"\n🎯 Test it: Open the war map → slide the date picker to 2011-2013")
        print(f"   Expected: Red (Gov) should dominate in 2011")
        print(f"            Green (Rebel) starts appearing mid-2012")
        print(f"            Yellow (SDF) appears in northeast mid-2012")
        print(f"            Black (ISIS) appears in Raqqa late 2013")


if __name__ == "__main__":
    main()
