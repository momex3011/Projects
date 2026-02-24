import spacy
import re
from smart_geocoder import get_coordinates # <--- The massive dictionary lookup
from extensions import db
from models.location import Location

# Load the NLP Brain
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("⚠️ Spacy model missing. Run: python -m spacy download en_core_web_sm")
    nlp = None

def analyze_news(war_id, title, description, date_obj):
    """
    1. Extracts locations using Spacy + Regex.
    2. Looks them up in the LOCAL Syria Data (No internet required).
    3. Updates Control Map.
    """
    text = f"{title}. {description}"
    detected_places = []

    # 1. NLP EXTRACTION (Spacy)
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["GPE", "FAC", "LOC"]:
                # Clean up name (remove "The", "City of")
                clean_name = ent.text.replace("The ", "").replace("City of ", "").strip()
                
                # Filter out generic country names causing the "Center of Map" bug
                blacklist = ["syria", "russian", "american", "turkish", "israeli", "middle east", "northern", "southern"]
                if len(clean_name) > 2 and clean_name.lower() not in blacklist:
                    detected_places.append(clean_name)

    # 2. REGEX FALLBACK (For Crossings/Bases that Spacy often misses)
    if "Crossing" in title or "Base" in title or "Airport" in title:
        matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Crossing|Base|Airport))', title)
        detected_places.extend(matches)

    if not detected_places:
        return None, None 

    # 3. PROCESS LOCATIONS
    best_lat, best_lng = None, None
    
    # We do NOT open a new app_context() here. 
    # The parent script (scraper) already has one. This prevents crashes.
    
    for place_name in detected_places:
        # A. Check Database first (Has this location flipped before?)
        loc = Location.query.filter_by(war_id=war_id, name=place_name).first()
        
        if not loc:
            # B. Smart Geocoder Lookup (Instant & Local)
            # This handles "Al-Bab" vs "Bab" and "Aleppo Countryside" automatically
            geo_data = get_coordinates(place_name)
            
            if geo_data:
                loc = Location(
                    war_id=war_id,
                    name=place_name,
                    lat=geo_data['lat'],
                    lng=geo_data['lng'],
                    controller="Unknown" # Will be updated below
                )
                db.session.add(loc)
                db.session.commit()
                print(f"   🧠 Mapped: {place_name} -> {loc.lat}, {loc.lng}")
            else:
                continue # Skip if not found in our massive list

        if loc:
            best_lat, best_lng = loc.lat, loc.lng
            
            # 4. DETERMINE CONTROLLER (Territory Flip Logic)
            lower_text = text.lower()
            new_controller = None
            
            # Logic: Action + Actor
            # Only update control if explicitly stated
            if "capture" in lower_text or "seize" in lower_text or "control of" in lower_text or "liberated" in lower_text:
                if "rebel" in lower_text or "opposition" in lower_text or "fsa" in lower_text or "turk" in lower_text:
                    new_controller = "Rebel"
                elif "army" in lower_text or "government" in lower_text or "assad" in lower_text or "regime" in lower_text:
                    new_controller = "Government"
                elif "isis" in lower_text or "daesh" in lower_text:
                    new_controller = "ISIS"
                elif "kurd" in lower_text or "sdf" in lower_text or "ypg" in lower_text:
                    new_controller = "SDF"

            # Update Database if ownership changed
            if new_controller and loc.controller != new_controller:
                loc.controller = new_controller
                loc.last_updated = date_obj.strftime("%Y-%m-%d")
                db.session.commit()
                print(f"   ⚔️ TERRITORY FLIP: {place_name} is now {new_controller.upper()}")

    return best_lat, best_lng