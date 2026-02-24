

import requests
import time
import random
import sys
import hashlib
import re
import traceback
from datetime import datetime
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim

# --- APP IMPORTS (Assumed from your structure) ---
from app import create_app
from extensions import db
from models.event import Event
from models.war import War
from ai_agent import ask_brain  # Your AI logic

# --- CONFIGURATION ---
WAR_NAME = "Syria"
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# --- GEOLOCATOR SETUP ---
app = create_app()
app.app_context().push()
geolocator = Nominatim(user_agent="wartracker_arabic_hist_v2", timeout=10)

# --- TARGETS ---
TARGET_HANDLES = [
    "OrientNews", "ShamNetwork", "UgaritNews", "LccSy", 
    "SNHR", "SyriaMubasher", "HalabNow", "HoranFreeMedia", "AlArabiya_Brk"
]

# --- KEYWORD PRE-FILTER (Save AI Tokens) ---
# Only process text containing at least one of these
RELEVANT_KEYWORDS = [
    "قصف", "مقتل", "شهيد", "اشتباك", "انفجار", "مظاهرة", "إطلاق نار", 
    "جيش", "حرية", "اعتقال", "جرحى", "اقتحام", "مجلس", "تنسيقية", "كتائب",
    "shelling", "killed", "martyr", "clashes", "explosion", "protest"
]

# --- CACHE ---
EVENT_MEMORY = {}

# --- LOCATION MAPPING ---
# Expanded mapping to catch common variations
ARABIC_LOCATIONS = {
    "دمشق": "Damascus", "الشام": "Damascus", "المزة": "Damascus", "برزة": "Damascus", "جوبر": "Damascus", "الميدان": "Damascus",
    "حلب": "Aleppo", "الشهباء": "Aleppo", "صلاح الدين": "Aleppo", "الصاخور": "Aleppo",
    "حمص": "Homs", "بابا عمرو": "Homs", "الخالدية": "Homs", "الرستن": "Ar Rastan", "القصير": "Al Qusayr", "تدمر": "Tadmur", "الحولة": "Homs",
    "حماة": "Hama", "العاصي": "Hama", "قلعة المضيق": "Hama",
    "إدلب": "Idlib", "جسر الشغور": "Jisr ash Shughur", "معرة النعمان": "Ma`arrat an Nu`man", "سرمين": "Idlib",
    "درعا": "Daraa", "حوران": "Daraa", "الصنمين": "As Sanamayn", "طفس": "Daraa",
    "الرقة": "Ar Raqqah", "الطبقة": "Ath Thawrah",
    "دير الزور": "Deir ez-Zor", "البوكمال": "Abu Kamal", "الميادين": "Al Mayadin",
    "اللاذقية": "Latakia", "جبلة": "Jableh", "بانياس": "Baniyas", "طرطوس": "Tartus",
    "الحسكة": "Al Hasakah", "القامشلي": "Qamishli", "عامودا": "Al Hasakah",
    "دوما": "Douma", "الغوطة": "Damascus", "حرستا": "Harasta", "داريا": "Darayya", "الزبداني": "Zabadani"
}

# Try to import existing locations if available
try:
    from syria_data import SYRIA_LOCATIONS
except ImportError:
    SYRIA_LOCATIONS = {} # Fallback if file missing

# --- CORE FUNCTIONS ---

def get_snapshots(handle, year):
    """Fetches unique daily snapshots from Wayback Machine CDX API."""
    cdx_api = (
        f"http://web.archive.org/cdx/search/cdx?url=twitter.com/{handle}*"
        f"&from={year}0101&to={year}1231"
        f"&output=json&fl=timestamp,original&filter=statuscode:200&collapse=digest"
    )
    
    for attempt in range(3):
        try:
            r = requests.get(cdx_api, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if not data: return []
                
                # Deduplicate by day to avoid scraping the same content too often
                snapshots = []
                seen_days = set()
                for row in data[1:]: # Skip header
                    ts = row[0]
                    day = ts[:8]
                    if day in seen_days: continue
                    seen_days.add(day)
                    snapshots.append(ts)
                return sorted(snapshots)
        except Exception as e:
            print(f"   ⚠️ CDX Error (Attempt {attempt+1}): {e}")
            time.sleep(2)
    return []

def scrape_wayback_page(handle, timestamp):
    """
    Scrapes tweets AND their specific timestamps from archived HTML.
    Returns list of dicts: [{'text': str, 'date': datetime object}]
    """
    url = f"https://web.archive.org/web/{timestamp}/https://twitter.com/{handle}"
    extracted_data = []
    
    try:
        r = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=20)
        if r.status_code != 200: return []
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Selectors covering 2011-2015 layouts
        # We look for the tweet container to keep text and date linked
        tweet_containers = soup.select('div.original-tweet, div.tweet, div.stream-item, div.content')
        
        for div in tweet_containers:
            # 1. Extract Text
            text_elem = div.select_one('p.js-tweet-text, div.tweet-text, span.entry-content, p.tweet-text')
            if not text_elem: continue
            text = text_elem.get_text().strip()
            
            # 2. Extract Date (Crucial for History)
            tweet_date = None
            time_elem = div.select_one('span._timestamp, span.timestamp, a.tweet-timestamp, span.js-short-timestamp')
            
            if time_elem and time_elem.has_attr('data-time'):
                try:
                    # Twitter usually stores Unix timestamp in data-time
                    ts_int = int(time_elem['data-time'])
                    tweet_date = datetime.fromtimestamp(ts_int)
                except: pass
            
            if text:
                extracted_data.append({
                    'text': text,
                    'date': tweet_date # Might be None, handled in main loop
                })
                
        return extracted_data
    except Exception as e:
        print(f"   ⚠️ Scraping Error: {e}")
        return []

def save_event(war_id, text, date_obj, original_url, handle):
    # 1. Deduplication
    dup_key = hashlib.md5(text.encode('utf-8')).hexdigest()
    if dup_key in EVENT_MEMORY: return
    EVENT_MEMORY[dup_key] = True

    # 2. Keyword Pre-filter (Save AI tokens)
    if not any(k in text for k in RELEVANT_KEYWORDS):
        return # Skip irrelevant stuff invisibly

    # 3. Extract External Links (e.g. YouTube)
    external_url = None
    url_match = re.search(r'(https?://\S+)', text)
    if url_match: external_url = url_match.group(0)

    # 4. AI Processing
    print(f"      🧠 Asking Brain: {text[:40]}...")
    intel = ask_brain(text, external_url)
    
    if not intel or not intel.get('relevant', False): return
    if not intel.get('locations'): return

    # 5. Geocoding
    primary_loc = intel["locations"][0]
    lat, lng = None, None
    
    # Strategy A: Hardcoded Maps
    if primary_loc in SYRIA_LOCATIONS:
        lat, lng = SYRIA_LOCATIONS[primary_loc]
    elif primary_loc in ARABIC_LOCATIONS:
        en_loc = ARABIC_LOCATIONS[primary_loc]
        if en_loc in SYRIA_LOCATIONS:
            lat, lng = SYRIA_LOCATIONS[en_loc]
        else:
            primary_loc = en_loc # Use English for Nominatim

    # Strategy B: Nominatim
    if not lat and primary_loc != "Syria":
        try:
            # Full specific search
            geo = geolocator.geocode(f"{primary_loc}, Syria", timeout=5)
            if geo:
                lat, lng = geo.latitude, geo.longitude
            else:
                # Fallback: Strip neighborhood (e.g. "Mallah, Aleppo" -> "Aleppo")
                if "," in primary_loc:
                    city = primary_loc.split(",")[-1].strip()
                    geo = geolocator.geocode(f"{city}, Syria", timeout=5)
                    if geo: lat, lng = geo.latitude, geo.longitude
            
            time.sleep(1.1) # Respect Rate Limits
        except Exception as e:
            print(f"      ⚠️ Geo Error: {e}")

    # 6. Integrity Check (No Fake Data)
    if not lat:
        print(f"      ❌ SKIPPED: Location '{primary_loc}' not found. No fake data added.")
        return

    # 7. Save to DB
    try:
        ev = Event(
            war_id=war_id,
            title=f"[{intel.get('category', 'News')}] {intel.get('summary', text[:50])}",
            description=f"Source: @{handle} | {text}",
            event_date=date_obj,
            lat=lat, lng=lng,
            source_url=original_url,
            image_url=intel.get('image')
        )
        db.session.add(ev)
        db.session.commit()
        print(f"      ✅ SAVED: {intel['summary'][:50]}... ({date_obj.date()})")
    except Exception as e:
        db.session.rollback()
        print(f"      ⚠️ DB Error: {e}")

def run_arabic_scraper(year=2011):
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war:
        print(f"❌ Database entry for '{WAR_NAME}' not found.")
        return

    print(f"--- 🌍 INTELLIGENT HISTORY INGESTION ({year}) ---")
    
    for handle in TARGET_HANDLES:
        print(f"\n🔎 Scanning: @{handle} ...")
        snapshots = get_snapshots(handle, year)
        print(f"   Found {len(snapshots)} snapshots.")
        
        for ts in snapshots:
            snapshot_date = datetime.strptime(ts[:8], "%Y%m%d")
            print(f"   ⏳ Processing snapshot: {ts[:8]} ...")
            
            tweets_data = scrape_wayback_page(handle, ts)
            
            for item in tweets_data:
                text = item['text']
                # USE EXACT DATE IF FOUND, ELSE APPROXIMATE (Snapshot date)
                final_date = item['date'] if item['date'] else snapshot_date
                
                valid_url = f"https://web.archive.org/web/{ts}/https://twitter.com/{handle}"
                
                save_event(war.id, text, final_date, valid_url, handle)

if __name__ == "__main__":
    # Start the scraper
    run_arabic_scraper(2011)

