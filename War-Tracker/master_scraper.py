import requests
import feedparser
import ssl
import time
import re
import random
from datetime import datetime
from app import create_app
from extensions import db
from models.event import Event
from models.war import War
from geopy.geocoders import Nominatim

# Import massive town list
try:
    from syria_data import SYRIA_LOCATIONS
except ImportError:
    SYRIA_LOCATIONS = {} # Fallback

try:
    from ai_border_bot import update_border
except ImportError:
    def update_border(f, l): pass

app = create_app()
app.app_context().push()
geolocator = Nominatim(user_agent="wartracker_master_v3")

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

WAR_NAME = "Syria"
ACLED_API_URL = "https://api.acleddata.com/acled/read?terms=accept&country=Syria&limit=100"

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=Syria+Civil+War+when:1d&hl=en-US&gl=US&ceid=US:en",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://english.alarabiya.net/.mrss/en.xml",
    "https://www.rudaw.net/rss/english",
    "https://www.middleeasteye.net/rss",
    "https://www.reddit.com/r/SyrianCivilWar/new/.rss",
    "https://www.reddit.com/r/CombatFootage/search.rss?q=Syria&sort=new&restrict_sr=on"
]

def save_event_to_db(war_id, title, description, date_obj, lat, lng, source_url, location_name=None):
    if Event.query.filter_by(war_id=war_id, title=title).first(): return False

    ev = Event(
        war_id=war_id,
        title=title,
        description=description[:500],
        event_date=date_obj,
        lat=lat, lng=lng,
        source_url=source_url
    )
    db.session.add(ev)
    db.session.commit()
    print(f"   ✅ Added: {title[:50]}...")

    if location_name and ("captured" in title.lower() or "seized" in title.lower()):
        faction = None
        txt = (title + " " + description).lower()
        if "government" in txt or "army" in txt or "assad" in txt: faction = "Government Control"
        elif "rebel" in txt or "opposition" in txt or "fsa" in txt: faction = "Rebel Control"
        
        if faction: update_border(faction, location_name)    
    return True

def scrape_acled(war_id):
    print("\n--- 🛡️ Phase 1: ACLED Military Database ---")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(ACLED_API_URL, headers=headers, timeout=5)
        data = r.json()
        if not data.get('success'): return
        count = 0
        for item in data['data']:
            evt_date = datetime.strptime(item['event_date'], "%Y-%m-%d").date()
            title = f"{item['event_type']} in {item['location']}"
            save_event_to_db(war_id, title, item['notes'], evt_date, float(item['latitude']), float(item['longitude']), "https://acleddata.com", item['location'])
            count += 1
        print(f"   -> Imported {count} military events.")
    except Exception as e:
        print(f"   ⚠️ ACLED unavailable: {e}")

def scrape_media(war_id, war_obj):
    print("\n--- 📰 Phase 2: Global Media (Massive Geocode) ---")
    
    action_keywords = ["killed", "attack", "captured", "seized", "bombing", "airstrike", "clash", "army", "rebel", "tank", "drone", "strike"]
    
    # IMPORTANT: General context keywords to ensure we are talking about Syria
    context_keywords = ["syria", "damascus", "assad", "kurds", "sdf", "aleppo", "idlib", "isis", "isil"]

    for url in RSS_FEEDS:
        print(f"   📡 Scanning: {url[:30]}...")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title
                desc = entry.summary if hasattr(entry, 'summary') else ""
                full_text = (title + " " + desc).lower()
                
                # 1. Must be violent/relevant
                if not any(k in full_text for k in action_keywords): continue
                
                # 2. Must be about Syria context
                if not any(k in full_text for k in context_keywords): continue

                evt_date = datetime.now().date()
                if hasattr(entry, 'published_parsed'):
                    try: evt_date = datetime.fromtimestamp(time.mktime(entry.published_parsed)).date()
                    except: pass

                # 3. MASSIVE GEOCODING
                lat, lng = war_obj.default_lat, war_obj.default_lng
                found_loc = None
                
                # Loop through 6,000 towns
                # Optimization: Check if string length of article is short, scan all.
                # If long, scan only headers.
                
                for city_name, coords in SYRIA_LOCATIONS.items():
                    # Skip very short names to avoid false positives (e.g. "Al")
                    if len(city_name) < 3: continue
                    
                    # Use Regex for exact word match
                    if re.search(r'\b' + re.escape(city_name) + r'\b', title, re.IGNORECASE):
                        found_loc = city_name
                        c_lat, c_lng = coords
                        lat = c_lat + random.uniform(-0.01, 0.01)
                        lng = c_lng + random.uniform(-0.01, 0.01)
                        break 
                
                save_event_to_db(war_id, title, desc, evt_date, lat, lng, entry.link, found_loc)

        except Exception as e:
            print(f"   ⚠️ Feed Error: {e}")

def run_master_scraper():
    print(f"=== 🚀 STARTING MASTER INTEL SCRAPER ({len(SYRIA_LOCATIONS)} LOCATIONS) ===")
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war: return
    scrape_acled(war.id)
    scrape_media(war.id, war)
    print("=== 🏁 DONE ===")

if __name__ == "__main__":
    run_master_scraper()