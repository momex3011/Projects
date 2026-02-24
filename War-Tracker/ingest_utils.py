import hashlib
import time
import random
import re
import json
from datetime import datetime, date
from geopy.geocoders import Nominatim
from app import create_app
from extensions import db
from models.event import Event
from models.location import Location
from models.location_cache import LocationCache
from models.history import TerritoryHistory
from dateutil import parser as date_parser

# Setup
# Setup
from geopy.geocoders import Nominatim
# UNIQUE USER AGENT TO AVOID BLOCKING
geolocator = Nominatim(user_agent="wartracker_pro_v3_ahmed_research", timeout=10)

try:
    from syria_data import SYRIA_LOCATIONS
except ImportError:
    SYRIA_LOCATIONS = {}


# ============================================================
# TERRITORY POLYGON UTILITIES
# Used to check faction control based on drawn map territories
# ============================================================

def point_in_polygon(lat, lng, polygon_coords):
    """
    Ray-casting algorithm to check if a point is inside a polygon.
    polygon_coords: list of [lng, lat] pairs (GeoJSON format)
    """
    x, y = lng, lat
    n = len(polygon_coords)
    inside = False
    
    p1x, p1y = polygon_coords[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon_coords[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside


def point_in_geojson(lat, lng, geojson_str):
    """
    Check if a point is inside a GeoJSON geometry.
    Supports Polygon and MultiPolygon.
    """
    if not geojson_str:
        return False
    
    try:
        geom = json.loads(geojson_str) if isinstance(geojson_str, str) else geojson_str
        
        # Handle GeoJSON structure variations
        if geom.get('type') == 'Feature':
            geom = geom.get('geometry', {})
        elif geom.get('type') == 'FeatureCollection':
            # Check all features
            for feature in geom.get('features', []):
                if point_in_geojson(lat, lng, feature):
                    return True
            return False
        elif geom.get('type') == 'GeometryCollection':
            for g in geom.get('geometries', []):
                if point_in_geojson(lat, lng, g):
                    return True
            return False
        
        geom_type = geom.get('type')
        coords = geom.get('coordinates', [])
        
        if geom_type == 'Polygon':
            # First ring is exterior, rest are holes
            if coords and len(coords) > 0:
                exterior = coords[0]
                if point_in_polygon(lat, lng, exterior):
                    # Check if in any hole
                    for hole in coords[1:]:
                        if point_in_polygon(lat, lng, hole):
                            return False
                    return True
                    
        elif geom_type == 'MultiPolygon':
            for poly_coords in coords:
                if poly_coords and len(poly_coords) > 0:
                    exterior = poly_coords[0]
                    if point_in_polygon(lat, lng, exterior):
                        # Check holes
                        in_hole = False
                        for hole in poly_coords[1:]:
                            if point_in_polygon(lat, lng, hole):
                                in_hole = True
                                break
                        if not in_hole:
                            return True
    except Exception as e:
        print(f"      ⚠️ Error checking point in GeoJSON: {e}")
    
    return False


def get_controlling_faction(lat, lng, war_id, query_date=None):
    """
    Determine which faction controls a given point based on territory polygons.
    
    Args:
        lat: Latitude
        lng: Longitude
        war_id: War ID to check factions for
        query_date: Date to check (uses historical snapshots if available)
    
    Returns:
        dict: {"faction_id": int, "faction_name": str, "color": str} or None
    """
    from models.faction import Faction, TerritorySnapshot
    
    if query_date is None:
        query_date = date.today()
    elif isinstance(query_date, str):
        query_date = datetime.strptime(query_date, "%Y-%m-%d").date()
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    
    for faction in factions:
        # Try to get historical snapshot first
        snapshot = TerritorySnapshot.query.filter(
            TerritorySnapshot.faction_id == faction.id,
            TerritorySnapshot.effective_date <= query_date
        ).order_by(TerritorySnapshot.effective_date.desc()).first()
        
        territory_geojson = None
        if snapshot:
            territory_geojson = snapshot.territory_geojson
        elif faction.territory_geojson:
            territory_geojson = faction.territory_geojson
        
        if territory_geojson and point_in_geojson(lat, lng, territory_geojson):
            return {
                "faction_id": faction.id,
                "faction_name": faction.name,
                "short_name": faction.short_name,
                "color": faction.color
            }
    
    return None


def get_all_faction_territories(war_id, query_date=None):
    """
    Get all faction territories for a war as of a specific date.
    Used by map display and territory analysis.
    
    Returns:
        list: [{"faction_id", "name", "color", "geojson"}, ...]
    """
    from models.faction import Faction, TerritorySnapshot
    
    if query_date is None:
        query_date = date.today()
    elif isinstance(query_date, str):
        query_date = datetime.strptime(query_date, "%Y-%m-%d").date()
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    result = []
    
    for faction in factions:
        # Try historical snapshot first
        snapshot = TerritorySnapshot.query.filter(
            TerritorySnapshot.faction_id == faction.id,
            TerritorySnapshot.effective_date <= query_date
        ).order_by(TerritorySnapshot.effective_date.desc()).first()
        
        territory_geojson = None
        snapshot_date = None
        
        if snapshot:
            territory_geojson = snapshot.territory_geojson
            snapshot_date = snapshot.effective_date.isoformat()
        elif faction.territory_geojson:
            territory_geojson = faction.territory_geojson
            snapshot_date = "current"
        
        result.append({
            "faction_id": faction.id,
            "name": faction.name,
            "short_name": faction.short_name,
            "color": faction.color,
            "geojson": territory_geojson,
            "snapshot_date": snapshot_date
        })
    
    return result


# --- CONSTANTS ---
SOCIAL_SITES = ["facebook.com", "youtube.com", "twitter.com", "t.me"]

# STRICTER KEYWORDS
# ROBUST KEYWORDS (MAX INGESTION)
SEARCH_TERMS = [
    '(Syria OR Syrian) (protest OR revolution OR uprising OR "Arab Spring")',
    '(Syria OR Syrian) (clash OR shelling OR explosion OR "security forces")',
    '(Syria OR Syrian) (arrest OR detention OR "human rights" OR torture)',
    'site:reuters.com Syria',
    'site:aljazeera.com Syria',
    'site:bbc.co.uk Syria'
]

SEEN_TITLES = set()
EVENT_MEMORY = {} 

# Common Aliases
COMMON_ALIASES = {
    "raqqa": "Ar Raqqah", "al-raqqa": "Ar Raqqah", "idlib": "Idlib", 
    "qusayr": "Al Qusayr", "al-qusayr": "Al Qusayr", "palmyra": "Tadmur",
    "tadmur": "Tadmur", "deir ez-zor": "Dayr az Zawr", "deir ezzor": "Dayr az Zawr",
    "kobani": "`Ayn al `Arab", "kobane": "`Ayn al `Arab", "afrin": "`Afrin",
    "ghouta": "Damascus", "eastern ghouta": "Damascus", "daraa": "Dar`a", "dara'a": "Dar`a",
    "homs": "Hims", "hama": "Hamah", "aleppo": "Halab", "damascus": "Dimashq",
    "latakia": "Al Ladhiqiyah", "tartus": "Tartus", "kamishli": "Al Qamishli",
    "qamishli": "Al Qamishli", "hasakah": "Al Hasakah", "manbij": "Manbij",
    "jarabulus": "Jarabulus", "al-bab": "Al Bab", "azaz": "A`zaz",
    
    # Specific Villages/Towns requested or common
    "as-sahl": "As Sahl", "sahl": "As Sahl", "al-sahl": "As Sahl",
    "zabadani": "Az Zabadani", "madaya": "Madaya", "douma": "Duma",
    "harasta": "Harasta", "daraya": "Darayya"
}

ARABIC_ALIASES = {
    "السحل": "As Sahl", "دمشق": "Dimashq", "حلب": "Halab", "حمص": "Hims",
    "حماة": "Hamah", "إدلب": "Idlib", "درعا": "Dar`a", "الرقة": "Ar Raqqah",
    "دير الزور": "Dayr az Zawr", "اللاذقية": "Al Ladhiqiyah", "طرطوس": "Tartus",
    "الحسكة": "Al Hasakah", "القامشلي": "Al Qamishli", "عفرين": "`Afrin",
    "كوباني": "`Ayn al `Arab", "عين العرب": "`Ayn al `Arab", "منبج": "Manbij",
    "الباب": "Al Bab", "جرابلس": "Jarabulus", "اعزاز": "A`zaz",
    "الزبداني": "Az Zabadani", "مضايا": "Madaya", "دوما": "Duma",
    "حرستا": "Harasta", "داريا": "Darayya", "القصير": "Al Qusayr",
    "تدمر": "Tadmur", "الغوطة": "Damascus"
}

# Location importance mapping (determines influence radius in km)
MAJOR_CITIES = ["Damascus", "Aleppo", "Homs", "Hama", "Latakia", "Deir Ezzor", "Raqqa", "Idlib", "Daraa", "Tartus"]
MEDIUM_TOWNS = ["Douma", "Daraya", "Qusayr", "Palmyra", "Tadmur", "Manbij", "Al-Bab", "Jisr al-Shughur", "Saraqib", "Khan Shaykhun", "Maarat al-Numan"]

def get_location_importance(name):
    """Determines the influence radius based on location type"""
    clean = name.lower().strip()
    
    # Major cities = large influence (15km radius)
    for city in MAJOR_CITIES:
        if city.lower() in clean:
            return 12
    
    # Medium towns = medium influence (8km radius)  
    for town in MEDIUM_TOWNS:
        if town.lower() in clean:
            return 8
    
    # Small locations (neighborhoods, checkpoints) = small influence (4km)
    if any(kw in clean for kw in ["checkpoint", "crossing", "hospital", "airport", "base", "neighborhood"]):
        return 3
    
    # Default = medium-small (5km)
    return 5

def update_border_logic(faction, location_name, event_date, war_id=1):
    """Updates the map points (The 'Paint') when AI detects a capture"""
    print(f"      🖌️ PAINTING: {faction} captured {location_name} on {event_date}...")
    try:
        # 1. Find Coordinates (Dynamic Geocoding)
        target_lat, target_lng = None, None
        
        # Normalize name
        clean_name = location_name.lower().strip()
        if clean_name in COMMON_ALIASES:
            location_name = COMMON_ALIASES[clean_name]

        # Try specific query first
        try:
            loc = geolocator.geocode(f"{location_name}, Syria", timeout=5)
            if loc: 
                target_lat, target_lng = loc.latitude, loc.longitude
        except: pass
        
        # Fallback to general lookup if specific fails
        if not target_lat and location_name in SYRIA_LOCATIONS:
            target_lat, target_lng = SYRIA_LOCATIONS[location_name]
        
        if not target_lat: return
        
        # Get importance for this location type
        importance = get_location_importance(location_name)

        # 2. Check if this exact location exists, if not create it
        existing = Location.query.filter(
            Location.lat.between(target_lat - 0.01, target_lat + 0.01),
            Location.lng.between(target_lng - 0.01, target_lng + 0.01),
            Location.name == location_name
        ).first()
        
        if not existing:
            # Create new location point
            new_loc = Location(
                war_id=war_id,
                name=location_name,
                lat=target_lat,
                lng=target_lng,
                controller=faction,
                importance=importance
            )
            db.session.add(new_loc)
            db.session.flush()  # Get the ID
            
            # Add history
            h = TerritoryHistory(location_id=new_loc.id, controller=faction, valid_from=event_date)
            db.session.add(h)
            print(f"      ✨ NEW LOCATION: {location_name} (importance={importance})")
        else:
            # Update existing
            existing.controller = faction
            existing.importance = importance
            h = TerritoryHistory(location_id=existing.id, controller=faction, valid_from=event_date)
            db.session.add(h)

        # 3. Also flip nearby points within radius based on importance
        RADIUS = importance * 0.01  # Convert km to approximate degrees
        points = Location.query.filter(
            Location.lat.between(target_lat - RADIUS, target_lat + RADIUS),
            Location.lng.between(target_lng - RADIUS, target_lng + RADIUS),
            Location.name != location_name  # Don't double-update
        ).all()

        for p in points:
            # Only flip smaller locations (larger ones resist)
            if (p.importance or 5) <= importance:
                p.controller = faction
                h = TerritoryHistory(location_id=p.id, controller=faction, valid_from=event_date)
                db.session.add(h)
        
        db.session.commit()
    except Exception as e:
        print(f"      ⚠️ Map Update Error: {e}")

# Strict Aliases for Geocoding
GOVERNORATE_CENTERS = {
    "Daraa": (32.62, 36.10), "Idlib": (35.93, 36.63), "Homs": (34.73, 36.71),
    "Aleppo": (36.20, 37.13), "Hama": (35.13, 36.75), "Deir Ezzor": (35.33, 40.14),
    "Raqqa": (35.95, 39.01), "Latakia": (35.53, 35.78), "Tartus": (34.88, 35.88),
    "Damascus": (33.51, 36.29), "Rif Dimashq": (33.51, 36.31), 
    "Hasakah": (36.49, 40.74), "Quneitra": (33.12, 35.82), "Suwayda": (32.70, 36.57)
}

def smart_geocode(location_name):
    """
    Intelligent geocoding path:
    1. Exact Match (DB/Dict)
    2. Approximate Match (Normalized)
    3. Alias Match
    4. LIVE Nominatim (Address search)
    5. Governorate Center Fallback (The Cluster Fix)
    """
    # 0. Check Cache
    clean_name = location_name.strip()
    cache_hit = LocationCache.query.filter_by(search_term=clean_name.lower()).first()
    if cache_hit:
        return cache_hit.lat, cache_hit.lng

    lat, lng = None, None
    
    # 1. Local Lookup
    if location_name in SYRIA_LOCATIONS:
        return SYRIA_LOCATIONS[location_name]
        
    # 2. Heuristic Lookup (Check if it's a known city/governorate)
    for gov, coords in GOVERNORATE_CENTERS.items():
        if gov.lower() in location_name.lower():
             # Add massive jitter to distribute points across the province
             # We want a cloud, not a stack.
             lat = coords[0] + random.uniform(-0.15, 0.15)
             lng = coords[1] + random.uniform(-0.15, 0.15)
             return lat, lng
             
    # 3. Nominatim (Live)
    try:
         # Respect OSM Policy (1 request per second max)
         time.sleep(1.2)
         geo = geolocator.geocode(f"{location_name}, Syria", timeout=5)
         if geo:
             # Cache it
             try:
                 new_cache = LocationCache(
                     search_term=clean_name.lower(),
                     lat=geo.latitude, lng=geo.longitude,
                     display_name=location_name
                 )
                 db.session.add(new_cache)
                 db.session.commit()
             except Exception as db_err:
                 print(f"⚠️ Cache Save Error: {db_err}")
                 db.session.rollback()
                 
             return geo.latitude, geo.longitude
    except Exception as e:
        print(f"⚠️ Geocoding Error: {e}")
    
    return None, None

def save_event(war_id, title, summary, locations, date_obj, url, is_capture, victor, category, img_url, evidence_score, dup_key):
    try:
        # Antigravity Phase 1: Robust Deduplication
        hash_input = f"{date_obj.isoformat()}-{title}".encode('utf-8')
        event_hash = hashlib.sha256(hash_input).hexdigest()
        
        # Check DB for hash collision (or URL collision)
        existing_ev = Event.query.filter((Event.hash_key == event_hash) | (Event.source_url == url)).first()
        if existing_ev:
             return False

        # Multi-Location Event Processing
        # If AI detected multiple distinct locations, create a marker for each
        unique_locations = list(set(locations)) if locations else ["Syria"]
        events_created = 0
        
        for idx, loc in enumerate(unique_locations):
            # Geocode this location
            lat, lng = smart_geocode(loc)
            
            # Fallback to Damascus with jitter
            if not lat:
                lat, lng = 33.5138, 36.2765
                lat += random.uniform(-0.05, 0.05)
                lng += random.uniform(-0.05, 0.05)
            
            # Add tiny jitter to prevent perfect stacking
            lat += random.uniform(-0.0005, 0.0005)
            lng += random.uniform(-0.0005, 0.0005)
            
            # For secondary locations, modify hash to avoid collision
            loc_hash = event_hash if idx == 0 else hashlib.sha256(f"{event_hash}-{loc}".encode()).hexdigest()
            
            # Title modification for multi-location events
            if len(unique_locations) > 1:
                ev_title = f"[{category}] {title[:180]} ({loc})"
            else:
                ev_title = f"[{category}] {title[:200]}"

            ev = Event(
                war_id=war_id, title=ev_title,
                description=summary, event_date=date_obj,
                lat=lat, lng=lng, source_url=url, image_url=img_url,
                hash_key=loc_hash,
                evidence_score=evidence_score or 1
            )
            db.session.add(ev)
            events_created += 1
        
        db.session.commit()
        
        if events_created > 1:
            print(f"      🗺️ Multi-Point Event: {events_created} markers created for {len(unique_locations)} locations")
        
        # Multi-Point Capture Logic
        if is_capture and victor:
            faction = None
            v = victor.lower()
            if "gov" in v or "assad" in v: faction = "Government Control"
            elif "rebel" in v or "opposition" in v: faction = "Rebel Control"
            elif "isis" in v: faction = "ISIS Control"
            elif "kurd" in v or "sdf" in v: faction = "SDF Control"
            
            if faction:
                # Iterate ALL locations for capture
                for loc in unique_locations:
                    update_border_logic(faction, loc, date_obj)
            
            # Also update faction territory snapshots (new system)
            try:
                from ai_agent import update_faction_territory_from_event
                for loc in unique_locations:
                    lat_val, lng_val = SYRIA_LOCATIONS.get(loc, (None, None))
                    if lat_val and lng_val:
                        update_faction_territory_from_event(
                            event_id=ev.id if ev else None,
                            war_id=war_id,
                            lat=lat_val,
                            lng=lng_val,
                            victor=victor,
                            event_summary=summary or title
                        )
            except Exception as e:
                print(f"      ⚠️ Territory snapshot update skipped: {e}")

        return True
    except Exception as e: 
        print(f"Error saving event: {e}")
        return False

def heuristic_parse(text):
    """Simple keyword matching if AI fails"""
    text = text.lower()
    found_locs = []
    
    # Check English keys
    for loc in SYRIA_LOCATIONS.keys():
        if loc.lower() in text:
            found_locs.append(loc)
            
    # Check Arabic aliases
    for arabic, english in ARABIC_ALIASES.items():
        if arabic in text:
            found_locs.append(english)
            
    return list(set(found_locs))
