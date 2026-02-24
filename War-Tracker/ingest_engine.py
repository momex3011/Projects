import asyncio
import aiohttp
import json
import os
import sys
import time
import random
import hashlib
import re
from datetime import datetime
from tqdm.asyncio import tqdm
from bs4 import BeautifulSoup
from app import create_app
from extensions import db
from models.event import Event
from models.war import War
from ai_agent import ask_brain
from data_locations import SYRIA_LOCATIONS, ARABIC_LOCATIONS
from geopy.geocoders import Nominatim

# --- CONFIGURATION ---
WAR_NAME = "Syria"
YEAR = 2011
CONCURRENCY_LIMIT = 3  # Low to be safe with Archive.org
STATE_FILE = "ingest_state.json"
CACHE_DIR = "cache"
TARGET_HANDLES = [
    "OrientNews", "ShamNetwork", "UgaritNews", "LccSy", 
    "SNHR", "SyriaMubasher", "HalabNow", "HoranFreeMedia", "AlArabiya_Brk"
]

# --- SETUP ---
if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR)
app = create_app()
app.app_context().push()
geolocator = Nominatim(user_agent="wartracker_engine_v1", timeout=10)

# --- STATE MANAGEMENT ---
def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f: return json.load(f)
        except: pass
    return {"processed_snapshots": {}}

def save_state(state):
    with open(STATE_FILE, 'w') as f: json.dump(state, f)

# --- ASYNC HELPERS ---
async def fetch_with_retry(session, url, retries=5):
    print(f"      🌐 Fetching: {url[:60]}...")
    for attempt in range(retries):
        try:
            async with session.get(url, timeout=60) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    wait = (attempt + 1) * 5
                    print(f"      ⚠️ 429 Rate Limit. Sleeping {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    print(f"      ⚠️ Status {response.status}")
                    return None
        except Exception as e:
            wait = (attempt + 1) * 2
            print(f"      ⚠️ Network Error: {e}. Retrying in {wait}s...")
            await asyncio.sleep(wait)
    return None

async def get_snapshots_async(session, handle, year):
    api = f"http://web.archive.org/cdx/search/cdx?url=twitter.com/{handle}*&from={year}0101&to={year}1231&output=json&fl=timestamp,original&filter=statuscode:200&collapse=digest"
    text = await fetch_with_retry(session, api)
    if not text: return []
    try:
        data = json.loads(text)
        if not data: return []
        # Deduplicate by day
        snapshots = []
        seen_days = set()
        for row in data[1:]:
            ts = row[0]
            day = ts[:8]
            if day in seen_days: continue
            seen_days.add(day)
            snapshots.append(ts)
        return sorted(snapshots)
    except: return []

# --- PROCESSING LOGIC (SYNC WRAPPER) ---
def process_content(text, date_obj, handle, url, war_id):
    # 1. Deduplication
    dup_key = hashlib.md5(text.encode('utf-8')).hexdigest()
    # (Simple in-memory check for this run, ideally DB check)
    if Event.query.filter(Event.description.contains(text[:50])).first():
        return

    # 2. AI/Regex Pipeline
    # We reuse the logic from ingest_smart.py but simplified here for the engine
    
    # Fast Path: Keywords
    keywords = [
        "قصف", "شهيد", "مظاهرة", "اشتباك", "قتلى", "جرحى", "اعتقال", "أمن", "جيش",
        "shelling", "killed", "martyr", "clashes", "explosion", "protest", "arrest"
    ]
    if not any(k in text for k in keywords): return

    print(f"   🧠 Analyzing: {text[:40]}...")
    
    # Call AI (Synchronous for now, as it's CPU/API bound)
    try:
        intel = ask_brain(text)
        if not intel or not intel.get('relevant', False): return
        
        # Geocoding
        lat, lng = None, None
        locs = intel.get('locations', [])
        if locs:
            primary = locs[0]
            if primary in SYRIA_LOCATIONS:
                lat, lng = SYRIA_LOCATIONS[primary]
            elif "," in primary:
                candidate = primary.split(",")[0].strip()
                if candidate in SYRIA_LOCATIONS:
                    lat, lng = SYRIA_LOCATIONS[candidate]
            elif primary in ARABIC_LOCATIONS:
                en = ARABIC_LOCATIONS[primary]
                if en in SYRIA_LOCATIONS: lat, lng = SYRIA_LOCATIONS[en]
            
            if not lat and primary != "Syria":
                try:
                    geo = geolocator.geocode(f"{primary}, Syria", timeout=5)
                    if geo: lat, lng = geo.latitude, geo.longitude
                    time.sleep(1) # Rate limit geocoding
                except: pass
        
        if not lat: return # Skip if no location

        # Save
        side_tag = f"Side: {intel.get('side', 'NEUTRAL')}"
        ev = Event(
            war_id=war_id,
            title=f"[{intel.get('category', 'News')}] {intel.get('summary', text[:50])}",
            description=f"Source: @{handle} | {text} | {side_tag}",
            event_date=date_obj,
            lat=lat, lng=lng,
            source_url=url,
            image_url=intel.get('image')
        )
        db.session.add(ev)
        db.session.commit()
        print(f"   ✅ SAVED: {intel['summary'][:40]}...")
        
    except Exception as e:
        print(f"   ❌ Error processing: {e}")
        db.session.rollback()

# --- WORKER ---
async def process_handle(session, handle, war_id, state):
    print(f"\n🔎 Scanning @{handle}...")
    snapshots = await get_snapshots_async(session, handle, YEAR)
    print(f"   Found {len(snapshots)} snapshots.")
    
    # Filter already processed
    processed = state['processed_snapshots'].get(handle, [])
    to_process = [s for s in snapshots if s not in processed]
    
    if not to_process:
        print("   ✨ All caught up.")
        return

    for ts in tqdm(to_process, desc=f"@{handle}"):
        url = f"https://web.archive.org/web/{ts}/https://twitter.com/{handle}"
        html = await fetch_with_retry(session, url)
        if not html: continue
        
        # Parse HTML (Lightweight)
        soup = BeautifulSoup(html, 'html.parser')
        tweets = []
        # Expanded selectors for 2011-2015 Twitter layouts
        selectors = [
            'div.tweet-text', 'p.js-tweet-text', 'div.content', 
            'span.entry-content', 'div.stream-item-header', 'p.tweet-text'
        ]
        for sel in selectors:
            for el in soup.select(sel):
                t = el.get_text().strip()
                if t and t not in tweets: tweets.append(t)
        
        if not tweets:
            # Debug: Warn if snapshot was empty (helps identify bad selectors)
            # print(f"      ⚠️ No tweets found in {ts}") 
            pass
            
        # Process Tweets
        date_obj = datetime.strptime(ts[:8], "%Y%m%d")
        for text in tweets:
            # Run sync processing in thread pool to not block async loop
            await asyncio.to_thread(process_content, text, date_obj, handle, url, war_id)
            
        # Update State
        state['processed_snapshots'].setdefault(handle, []).append(ts)
        save_state(state)
        
        # Be nice to Archive.org
        await asyncio.sleep(1.5)

# --- MAIN ---
async def main():
    print(f"=== 🚀 UNIFIED INGESTION ENGINE ({YEAR}) ===")
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war:
        print("❌ War not found in DB.")
        return
        
    state = load_state()
    
    async with aiohttp.ClientSession() as session:
        # Process handles sequentially to avoid overwhelming Archive.org globally
        # (Parallelism is handled within fetch_with_retry for retries, but we limit handle concurrency)
        for handle in TARGET_HANDLES:
            await process_handle(session, handle, war.id, state)

if __name__ == "__main__":
    # Windows AsyncIO Fix
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())
