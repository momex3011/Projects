import requests
import time
import random
import hashlib
import re
import sys
import json
from datetime import datetime
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

# --- APP IMPORTS ---
from app import create_app
from extensions import db
from models.event import Event
from models.war import War

# --- DEPENDENCIES ---
import google.generativeai as genai

try:
    from ai_border_bot import update_border
except ImportError:
    def update_border(f, l): pass

# ===============================
# CONFIGURATION
# ===============================
WAR_NAME = "Syria"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
GEMINI_API_KEY = "AIzaSyBO5dHsp53nOKeeEWLZ51V0KBJz4Jvq9rM"
HF_MODEL = "google/flan-t5-base"

try:
    from syria_data import SYRIA_LOCATIONS
except ImportError:
    SYRIA_LOCATIONS = {}

try:
    from data_locations import SYRIA_LOCATIONS as MANUAL_LOCATIONS
    SYRIA_LOCATIONS.update(MANUAL_LOCATIONS)
    print(f"   ✅ Loaded {len(MANUAL_LOCATIONS)} manual locations from data_locations.py")
except ImportError:
    pass

# ===============================
# UNIFIED FREE LLM WRAPPER
# ===============================

def ask_gemini(prompt: str) -> str:
    """Call Google Gemini Flash (free tier)"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"      ⚠️ Gemini Error: {e}")
        return None

def ask_huggingface(prompt: str) -> str:
    """Call HuggingFace FLAN-T5 (free, no key)"""
    try:
        url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        res = requests.post(url, json={"inputs": prompt}, timeout=30)

        data = res.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()

        return None
    except Exception as e:
        print(f"      ⚠️ HF Error: {e}")
        return None

def ask_model(prompt: str, model: str = "gemini") -> str:
    """
    Unified interface:
    ask_model("hello", model="gemini")
    ask_model("hello", model="hf")
    """
    model = model.lower()

    if model == "gemini":
        return ask_gemini(prompt)
    elif model in ("hf", "huggingface"):
        return ask_huggingface(prompt)
    else:
        return None

def clean_json_response(text):
    try:
        if not text: return None
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except: pass
    return None

def construct_prompt(text):
    return f"""
    You are a Professional War Analyst covering the Syrian Civil War (2011-Present). 
    Analyze this text (which may be in ARABIC): 
    "{text}"
    
    1. RELEVANT: boolean. Is this related to the Syrian War/Revolution? 
       - YES: "Security forces", "Shabiha", "Protest", "Killed", "Wounded", "Shooting", "Shelling", "Arrest", "Demonstration".
       - YES: Any mention of Syrian cities (Homs, Daraa, Aleppo, Damascus, Idlib, etc.).
       - NO: Egypt, Libya, Yemen, Bahrain, or general religious quotes without context.
    2. CATEGORY: "COMBAT", "POLITICAL", "CASUALTIES", "PROTEST", "HUMANITARIAN".
    3. LOCATIONS: List of SPECIFIC neighborhoods, towns, or landmarks. 
       - CRITICAL: "Aleppo" is too vague. Find the neighborhood (e.g., "Sakhour", "Salah al-Din").
       - If a city is divided/contested, specify the exact area mentioned.
    4. CAPTURED: true ONLY if territory definitively changed hands.
    5. VICTOR: Government, Rebel, ISIS, Kurds, or None.
    6. SUMMARY: Write a professional, journalistic sentence describing the event.
       - Style: Objective, concise, historical record.
       - Do NOT use phrases like "Video shows", "Footage of", "A tweet about".
       - BAD: "Video of shelling in Homs."
       - GOOD: "Government forces shelled the Khalidiya district of Homs, causing structural damage."
       - GOOD: "Protesters in Douma demanded the fall of the regime."
    7. EVIDENCE_SCORE: 0-10 (10=video/footage/eyewitness, 0=rumor/unverified).
    8. KEY: A short, unique semantic string (e.g. "gov shelling homs khalidiya").

    Output JSON (in ENGLISH): {{ "relevant": true, "category": "COMBAT", "locations": ["Sakhour, Aleppo"], "captured": false, "victor": "None", "summary": "Government forces shelled the Sakhour neighborhood.", "evidence_score": 9, "key": "gov captures sakhour" }}
    """

# These are the most active accounts during 2011-2014
TARGET_HANDLES = [
    # -- Grassroots / Activists --
    "LccSy",          # Local Coordination Committees (The backbone of 2011 intel)
    "ShamNetwork",    # Shaam News Network (Very active field reports)
    "UgaritNews",     # Ugarit (Homs/Hama focus)
    "SNHR",           # Syrian Network for Human Rights (Casualty data)
    "SRGC_Syria",     # Syrian Revolution General Commission
    
    # -- City Specific --
    "HalabNow",       # Aleppo Now
    "AleppoAMC",      # Aleppo Media Center (Started 2012, very reliable)
    "HoranFreeMedia", # Daraa / South Syria
    "DeirEzzor24",    # Eastern Syria (ISIS/Gov/Rebel clashes)
    "Raqqa_SL",       # Raqqa is Being Slaughtered Silently (Anti-ISIS intel)

    # -- Major Media Breaking News --
    "OrientNews",     # Major pro-opposition TV channel
    "AJABreaking",    # Al Jazeera Arabic Breaking (Instant updates)
    "AlArabiya_Brk",  # Al Arabiya Breaking (Regional view)
    "syriahr",        # Syrian Observatory (SOHR) - Essential for death tolls
    
    # -- Military / Official --
    "SyrianCoalition",# Official Opposition political arm
    "FreeSyrianArmy"  # FSA Official (Historical archive)
]

# Arabic Combat Keywords
RELEVANT_KEYWORDS = [
    "قصف",       # Shelling/Bombing
    "مقتل",      # Killing/Death of
    "شهيد",      # Martyr
    "اشتباك",    # Clashes
    "انفجار",    # Explosion
    "مظاهرة",    # Protest
    "إطلاق نار", # Gunfire
    "جيش",       # Army
    "حرية",      # Freedom
    "اعتقال",    # Arrest
    "جرحى",      # Wounded
    "اقتحام",    # Storming/Raid
    "مجلس",      # Council
    "تنسيقية",   # Coordination Committee
    "كتائب",     # Battalions
    "سيطر",      # Captured/Controlled
    "تحرير",     # Liberation
    "سقوط"       # Fall of (town/regime)
]

SEEN_HASHES = set()

# --- SETUP ---
app = create_app()
app.app_context().push()
geolocator = Nominatim(user_agent="wartracker_arabic_v5", timeout=10)

def get_snapshots(handle, year):
    """Fetch unique daily snapshots from Wayback Machine"""
    print(f"   ⏳ Fetching archive list for @{handle} ({year})...")
    url = f"http://web.archive.org/cdx/search/cdx?url=twitter.com/{handle}*&from={year}0101&to={year}1231&output=json&fl=timestamp,original&filter=statuscode:200&collapse=digest"
    
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if not data: return []
            
            snapshots = []
            seen_days = set()
            
            # Header row is [0], data is [1:]
            for row in data[1:]:
                ts = row[0]
                day = ts[:8] # YYYYMMDD
                if day not in seen_days:
                    seen_days.add(day)
                    snapshots.append(ts)
            
            # Optimization: Take every 4th snapshot to cover the year faster
            # (Twitter archives often have duplicates on same day)
            return sorted(snapshots)[::4] 
from extensions import db
from models.event import Event
from models.war import War

# --- DEPENDENCIES ---
import google.generativeai as genai

try:
    from ai_border_bot import update_border
except ImportError:
    def update_border(f, l): pass

# ===============================
# CONFIGURATION
# ===============================
WAR_NAME = "Syria"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
GEMINI_API_KEY = "AIzaSyBO5dHsp53nOKeeEWLZ51V0KBJz4Jvq9rM"
HF_MODEL = "google/flan-t5-base"

try:
    from syria_data import SYRIA_LOCATIONS
except ImportError:
    SYRIA_LOCATIONS = {}

try:
    from data_locations import SYRIA_LOCATIONS as MANUAL_LOCATIONS
    SYRIA_LOCATIONS.update(MANUAL_LOCATIONS)
    print(f"   ✅ Loaded {len(MANUAL_LOCATIONS)} manual locations from data_locations.py")
except ImportError:
    pass

# ===============================
# UNIFIED FREE LLM WRAPPER
# ===============================

def ask_gemini(prompt: str) -> str:
    """Call Google Gemini Flash (free tier)"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"      ⚠️ Gemini Error: {e}")
        return None

def ask_huggingface(prompt: str) -> str:
    """Call HuggingFace FLAN-T5 (free, no key)"""
    try:
        url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        res = requests.post(url, json={"inputs": prompt}, timeout=30)

        data = res.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"].strip()

        return None
    except Exception as e:
        print(f"      ⚠️ HF Error: {e}")
        return None

def ask_model(prompt: str, model: str = "gemini") -> str:
    """
    Unified interface:
    ask_model("hello", model="gemini")
    ask_model("hello", model="hf")
    """
    model = model.lower()

    if model == "gemini":
        return ask_gemini(prompt)
    elif model in ("hf", "huggingface"):
        return ask_huggingface(prompt)
    else:
        return None

def clean_json_response(text):
    try:
        if not text: return None
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except: pass
    return None

def construct_prompt(text):
    return f"""
    You are a Professional War Analyst covering the Syrian Civil War (2011-Present). 
    Analyze this text (which may be in ARABIC): 
    "{text}"
    
    1. RELEVANT: boolean. Is this related to the Syrian War/Revolution? 
       - YES: "Security forces", "Shabiha", "Protest", "Killed", "Wounded", "Shooting", "Shelling", "Arrest", "Demonstration".
       - YES: Any mention of Syrian cities (Homs, Daraa, Aleppo, Damascus, Idlib, etc.).
       - NO: Egypt, Libya, Yemen, Bahrain, or general religious quotes without context.
    2. CATEGORY: "COMBAT", "POLITICAL", "CASUALTIES", "PROTEST", "HUMANITARIAN".
    3. LOCATIONS: List of SPECIFIC neighborhoods, towns, or landmarks. 
       - CRITICAL: "Aleppo" is too vague. Find the neighborhood (e.g., "Sakhour", "Salah al-Din").
       - If a city is divided/contested, specify the exact area mentioned.
    4. CAPTURED: true ONLY if territory definitively changed hands.
    5. VICTOR: Government, Rebel, ISIS, Kurds, or None.
    6. SUMMARY: Write a professional, journalistic sentence describing the event.
       - Style: Objective, concise, historical record.
       - Do NOT use phrases like "Video shows", "Footage of", "A tweet about".
       - BAD: "Video of shelling in Homs."
       - GOOD: "Government forces shelled the Khalidiya district of Homs, causing structural damage."
       - GOOD: "Protesters in Douma demanded the fall of the regime."
    7. EVIDENCE_SCORE: 0-10 (10=video/footage/eyewitness, 0=rumor/unverified).
    8. KEY: A short, unique semantic string (e.g. "gov shelling homs khalidiya").

    Output JSON (in ENGLISH): {{ "relevant": true, "category": "COMBAT", "locations": ["Sakhour, Aleppo"], "captured": false, "victor": "None", "summary": "Government forces shelled the Sakhour neighborhood.", "evidence_score": 9, "key": "gov captures sakhour" }}
    """

# These are the most active accounts during 2011-2014
TARGET_HANDLES = [
    # -- Grassroots / Activists --
    "LccSy",          # Local Coordination Committees (The backbone of 2011 intel)
    "ShamNetwork",    # Shaam News Network (Very active field reports)
    "UgaritNews",     # Ugarit (Homs/Hama focus)
    "SNHR",           # Syrian Network for Human Rights (Casualty data)
    "SRGC_Syria",     # Syrian Revolution General Commission
    
    # -- City Specific --
    "HalabNow",       # Aleppo Now
    "AleppoAMC",      # Aleppo Media Center (Started 2012, very reliable)
    "HoranFreeMedia", # Daraa / South Syria
    "DeirEzzor24",    # Eastern Syria (ISIS/Gov/Rebel clashes)
    "Raqqa_SL",       # Raqqa is Being Slaughtered Silently (Anti-ISIS intel)

    # -- Major Media Breaking News --
    "OrientNews",     # Major pro-opposition TV channel
    "AJABreaking",    # Al Jazeera Arabic Breaking (Instant updates)
    "AlArabiya_Brk",  # Al Arabiya Breaking (Regional view)
    "syriahr",        # Syrian Observatory (SOHR) - Essential for death tolls
    
    # -- Military / Official --
    "SyrianCoalition",# Official Opposition political arm
    "FreeSyrianArmy"  # FSA Official (Historical archive)
]

# Arabic Combat Keywords
RELEVANT_KEYWORDS = [
    "قصف",       # Shelling/Bombing
    "مقتل",      # Killing/Death of
    "شهيد",      # Martyr
    "اشتباك",    # Clashes
    "انفجار",    # Explosion
    "مظاهرة",    # Protest
    "إطلاق نار", # Gunfire
    "جيش",       # Army
    "حرية",      # Freedom
    "اعتقال",    # Arrest
    "جرحى",      # Wounded
    "اقتحام",    # Storming/Raid
    "مجلس",      # Council
    "تنسيقية",   # Coordination Committee
    "كتائب",     # Battalions
    "سيطر",      # Captured/Controlled
    "تحرير",     # Liberation
    "سقوط"       # Fall of (town/regime)
]

SEEN_HASHES = set()

# --- SETUP ---
app = create_app()
app.app_context().push()
geolocator = Nominatim(user_agent="wartracker_arabic_v5", timeout=10)

def get_snapshots(handle, year):
    """Fetch unique daily snapshots from Wayback Machine"""
    print(f"   ⏳ Fetching archive list for @{handle} ({year})...")
    url = f"http://web.archive.org/cdx/search/cdx?url=twitter.com/{handle}*&from={year}0101&to={year}1231&output=json&fl=timestamp,original&filter=statuscode:200&collapse=digest"
    
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if not data: return []
            
            snapshots = []
            seen_days = set()
            
            # Header row is [0], data is [1:]
            for row in data[1:]:
                ts = row[0]
                day = ts[:8] # YYYYMMDD
                if day not in seen_days:
                    seen_days.add(day)
                    snapshots.append(ts)
            
            # Optimization: Take every 4th snapshot to cover the year faster
            # (Twitter archives often have duplicates on same day)
            return sorted(snapshots)[::4] 
    except Exception as e:
        print(f"      ⚠️ CDX Error: {e}")
    
    return []

def save_event(war_id, text, date_obj, url, image_url=None, video_url=None):
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    if text_hash in SEEN_HASHES: return
    SEEN_HASHES.add(text_hash)

    if Event.query.filter_by(war_id=war_id, description=text[:100]).first(): return

    # AI Analysis
    print(f"   🤖 AI Analyzing: {text[:40]}...")
    prompt = construct_prompt(text)
    
    # Try Gemini First
    raw_response = ask_model(prompt, model="gemini")
    
    # Fallback to HF if Gemini fails
    if not raw_response:
        print("      ⚠️ Gemini failed, trying HuggingFace...")
        raw_response = ask_model(prompt, model="hf")

    intel = clean_json_response(raw_response)
    
    if not intel: 
        print("      ⚠️ AI Parsing Failed (Skipping)")
        return

    if intel.get("category") == "IRRELEVANT": return

    # Geocode
    lat, lng = 34.8, 39.0
    found_loc = None
    loc_name = intel.get("location")
    
    if loc_name:
        # 1. Exact Match
        if loc_name in SYRIA_LOCATIONS:
            lat, lng = SYRIA_LOCATIONS[loc_name]
            found_loc = loc_name
        
        # 2. Comma Split (e.g. "Talbiseh, Homs" -> "Talbiseh")
        elif "," in loc_name:
            candidate = loc_name.split(",")[0].strip()
            if candidate in SYRIA_LOCATIONS:
                lat, lng = SYRIA_LOCATIONS[candidate]
                found_loc = candidate

        if not found_loc:
            try:
                geo = geolocator.geocode(f"{loc_name}, Syria", timeout=5)
                if geo:
                    lat, lng = geo.latitude, geo.longitude
                    found_loc = loc_name
            except: pass

    # Jitter
    lat += random.uniform(-0.01, 0.01)
    lng += random.uniform(-0.01, 0.01)

    # Use AI image if scraper didn't find one, otherwise prefer scraper image
    final_image = image_url if image_url else intel.get("image")

    try:
        ev = Event(
            war_id=war_id,
            title=f"[{intel.get('category', 'INTEL')}] {intel.get('summary', text[:50])}",
            description=f"{text}\n\n(Source: @{url.split('twitter.com/')[1].split('/')[0]})",
            event_date=date_obj,
            lat=lat, lng=lng,
            source_url=url,
            image_url=final_image,
            video_url=video_url
        )
        db.session.add(ev)
        db.session.commit()
        
        print(f"      ✅ SAVED ({date_obj}): {intel.get('summary')[:60]}...")

        if found_loc and intel.get("captured") and intel.get("victor"):
            faction = None
            v = intel.get("victor").lower()
            if "gov" in v or "assad" in v or "army" in v: faction = "Government Control"
            elif "rebel" in v or "opposition" in v or "fsa" in v: faction = "Rebel Control"
            elif "isis" in v or "daesh" in v: faction = "ISIS"
            elif "kurd" in v or "sdf" in v: faction = "SDF"
            
            if faction:
                update_border(faction, found_loc)
                print(f"      ⚔️ MAP UPDATE: {faction} took {found_loc}")

    except Exception as e:
        pass

def run_arabic_scraper():
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war: return

    print(f"--- 🌍 EXPANDED ARABIC HISTORY INGESTION (15+ SOURCES) ---")
    
    # Iterate through years
    for year in [2011, 2012, 2013]:
        print(f"\n📅 PROCESSING YEAR: {year}")
        
        for handle in TARGET_HANDLES:
            print(f"   🔎 Scanning Handle: @{handle}")
            snapshots = get_snapshots(handle, year)
            
            if not snapshots:
                print("      (No snapshots found)")
                continue

            for ts in snapshots:
                try:
                    archive_url = f"https://web.archive.org/web/{ts}/https://twitter.com/{handle}"
                    time.sleep(1.5) # Archive.org rate limit
                    
                    r = requests.get(archive_url, headers={'User-Agent': USER_AGENT}, timeout=15)
                    if r.status_code != 200: continue

                    soup = BeautifulSoup(r.content, 'html.parser')
                    tweets = soup.select('.tweet-text, .js-tweet-text, .entry-content, .ms-tweet-text')
                    
                    if not tweets:
                        tweets = soup.find_all('div', class_='dir-ltr')

                    count = 0
                    snapshot_date = datetime.strptime(ts[:8], "%Y%m%d").date()

                    for t in tweets:
                        text = t.get_text().strip()
                        
                        # --- MEDIA EXTRACTION ---
                        media_img = None
                        media_video = None
                        
                        # Parent container (tweet div)
                        tweet_container = t.find_parent('div', class_='tweet') or t.find_parent('li')
                        
                        if tweet_container:
                            # 1. Extract Image
                            img_tag = tweet_container.find('div', class_='AdaptiveMedia-photoContainer')
                            if img_tag:
                                media_img = img_tag.get('data-image-url')
                            
                            if not media_img:
                                # Fallback: Look for any large image in the tweet
                                imgs = tweet_container.find_all('img')
                                for img in imgs:
                                    src = img.get('src', '')
                    if count > 0:
                        print(f"      Found {count} events in snapshot.")
                    
                except Exception:
                    pass

if __name__ == "__main__":
    run_arabic_scraper()