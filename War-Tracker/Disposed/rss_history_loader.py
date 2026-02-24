import feedparser
import time
import random
import ssl
import urllib.parse
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from app import create_app
from extensions import db
from models.event import Event
from models.war import War
from geopy.geocoders import Nominatim

try:
    from syria_data import SYRIA_LOCATIONS
except ImportError:
    SYRIA_LOCATIONS = {}

try:
    from ai_border_bot import update_border
except ImportError:
    def update_border(f, l): pass

try:
    from ai_agent import ask_brain
except ImportError:
    print("❌ Error: ai_agent.py not found.")
    exit()

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

app = create_app()
app.app_context().push()
geolocator = Nominatim(user_agent="wartracker_rss_v6", timeout=10)

WAR_NAME = "Syria"

# We check these MANUALLY now, instead of forcing them in the Google Query
# This fixes the "0 Results" bug caused by complex URLs
TARGET_SITES = [
    "aljazeera.com", "reuters.com", "bbc.co.uk", "cnn.com", 
    "france24.com", "dailystar.com.lb", "hurriyetdailynews.com",
    "timesofisrael.com", "middleeasteye.net"
]

# --- GLOBAL MEMORY ---
SEEN_TITLES = set()

def load_memory(war_id):
    events = db.session.query(Event.title).filter_by(war_id=war_id).all()
    for t in events:
        if t.title: SEEN_TITLES.add(t.title.lower().strip())

def parse_rss_date(entry):
    if hasattr(entry, 'published_parsed') and entry.published_parsed:
        return datetime.fromtimestamp(time.mktime(entry.published_parsed)).date()
    date_str = entry.get('published', entry.get('updated', ''))
    if date_str:
        try: return date_parser.parse(date_str).date()
        except: pass
    return None

def run_rss_history():
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war: return

    load_memory(war.id)
    print(f"--- 📡 GOOGLE RSS LOADER (OPTIMIZED) ---")
    
    start_date = datetime(2013, 1, 1)
    end_date = datetime(2014, 1, 1)
    current = start_date
    
    while current < end_date:
        next_step = current + timedelta(days=2)
        d_after = current.strftime("%Y-%m-%d")
        d_before = next_step.strftime("%Y-%m-%d")
        
        print(f"\n📅 Scanning: {d_after} ...")
        
        # SIMPLER QUERY (More likely to get results)
        # We search broadly, then filter in Python
        raw_query = f"Syria (battle OR captured OR killed OR shelling) after:{d_after} before:{d_before}"
        encoded_query = urllib.parse.quote(raw_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                print("   (No news found)")
                current = next_step
                time.sleep(1)
                continue

            count = 0
            for entry in feed.entries:
                title = entry.title.strip()
                link = entry.link
                
                # 1. MEMORY CHECK
                if title.lower() in SEEN_TITLES: continue

                # 2. DATE CHECK
                real_date = parse_rss_date(entry)
                if not real_date: continue
                if abs((real_date - current.date()).days) > 60: continue 

                # 3. SOURCE CHECK (Optional: Enable if you want strictly these sites)
                # if not any(s in link for s in TARGET_SITES): continue

                # 4. AI CHECK
                intel = ask_brain(title, link)
                if not intel: continue
                if intel.get("category") == "IRRELEVANT": continue

                # 5. SAVE
                loc_name = intel.get("location")
                captured = intel.get("captured", False)
                victor = intel.get("victor")
                summary = intel.get("summary", title)
                img_url = intel.get("image")
                category = intel.get("category", "GENERAL")

                if save_event(war.id, title, summary, loc_name, real_date, link, captured, victor, category, img_url):
                    count += 1
                    SEEN_TITLES.add(title.lower())
                    print(f"      ✅ SAVED: {title[:50]}...")

            print(f"   🏁 Batch Complete. {count} new events.")

        except Exception as e:
            print(f"   ❌ RSS Error: {e}")
            time.sleep(5)

        current = next_step
        time.sleep(2)

def save_event(war_id, title, summary, loc_name, date_obj, url, is_capture, victor, category, img_url):
    try:
        lat, lng = 34.8, 39.0
        found = False

        # --- FIX: BLOCK GENERIC NAMES ---
        if loc_name and loc_name.lower() in ["syria", "middle east", "border"]:
            loc_name = None # Treat as unknown location

        if loc_name:
            if loc_name in SYRIA_LOCATIONS:
                lat, lng = SYRIA_LOCATIONS[loc_name]
                found = True
            else:
                try:
                    geo = geolocator.geocode(f"{loc_name}, Syria", timeout=5)
                    if geo:
                        lat, lng = geo.latitude, geo.longitude
                        found = True
                except: pass

        if not found:
            if category == "POLITICAL":
                lat, lng = 33.5138, 36.2765 
            else:
                import random
                lat = 35.0 + random.uniform(-1.5, 1.5)
                lng = 38.0 + random.uniform(-1.5, 1.5)
        
        import random
        lat += random.uniform(-0.01, 0.01)
        lng += random.uniform(-0.01, 0.01)

        ev = Event(
            war_id=war_id,
            title=f"[{category}] {title[:200]}",
            description=f"{summary}",
            event_date=date_obj,
            lat=lat, lng=lng,
            source_url=url,
            image_url=img_url
        )
        db.session.add(ev)
        db.session.commit()
        
        if found and is_capture and victor:
            faction = None
            v = victor.lower()
            if "gov" in v or "assad" in v: faction = "Government Control"
            elif "rebel" in v or "opposition" in v: faction = "Rebel Control"
            elif "isis" in v: faction = "ISIS"
            elif "kurd" in v: faction = "SDF"
            if faction: update_border(faction, loc_name)

        return True
    except Exception:
        return False

if __name__ == "__main__":
    run_rss_history()