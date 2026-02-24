import requests
import time
import random
import sys
import hashlib
import re
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup
from app import create_app
from extensions import db
from models.event import Event
from models.war import War
from geopy.geocoders import Nominatim
import google.generativeai as genai
from func_timeout import func_timeout, FunctionTimedOut
from youtube_transcript_api import YouTubeTranscriptApi
from newspaper import Article, Config
from data_locations import SYRIA_LOCATIONS, ARABIC_LOCATIONS

# --- CONFIGURATION ---
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, val = line.strip().split('=', 1)
                    os.environ[key] = val

load_env()
API_KEY = os.getenv("GOOGLE_API_KEY")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
WAR_NAME = "Syria"

# --- SETUP ---
try:
    genai.configure(api_key=API_KEY)
except: pass

app = create_app()
app.app_context().push()
geolocator = Nominatim(user_agent="wartracker_smart_ingest", timeout=10)

TARGET_HANDLES = [
    "OrientNews", "ShamNetwork", "UgaritNews", "LccSy", "SNHR", 
    "SyriaMubasher", "HalabNow", "HoranFreeMedia", "AlArabiya_Brk"
]

# --- PERSISTENT CACHE ---
CACHE_DIR = "cache"
if not os.path.exists(CACHE_DIR): os.makedirs(CACHE_DIR)

class PersistentCache:
    def __init__(self, filename):
        self.path = os.path.join(CACHE_DIR, filename)
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            except: self.data = {}

    def save(self):
        try:
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False)
        except: pass

    def get(self, key): return self.data.get(key)
    def set(self, key, value):
        self.data[key] = value
        self.save()

geo_cache = PersistentCache("geocode.json")
event_cache = PersistentCache("events.json")

# --- HELPER FUNCTIONS ---
def clean_json_response(text):
    try:
        text = text.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match: return json.loads(match.group(0))
    except: pass
    return None

def generate_with_retry(prompt, model_name="models/gemini-2.0-flash"):
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return clean_json_response(response.text)
    except Exception as e:
        if "429" in str(e):
            print(f"      ⏳ Quota Exceeded. Sleeping 60s...")
            time.sleep(60)
            return generate_with_retry(prompt, model_name)
        print(f"      ⚠️ AI Error: {e}")
    return None

def _get_article_data(title, url):
    text_to_analyze = title
    image_url = None
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    if url and len(title) < 100:
        try:
            # Newspaper3k
            config = Config()
            config.browser_user_agent = headers['User-Agent']
            config.request_timeout = 5
            article = Article(url, config=config)
            article.download()
            article.parse()
            if len(article.text) > 50: text_to_analyze = f"{title}\n\n{article.text[:1500]}"
            if article.top_image and "http" in article.top_image: image_url = article.top_image

            # Fallback / YouTube
            if not image_url or "youtube.com" in url:
                r = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(r.content, 'html.parser')
                
                if "youtube.com" in url or "youtu.be" in url:
                    desc = ""
                    meta = soup.find("meta", property="og:description")
                    if meta: desc = meta['content']
                    
                    transcript = ""
                    try:
                        vid = url.split("v=")[1].split("&")[0] if "v=" in url else url.split("/")[-1]
                        ts = YouTubeTranscriptApi.get_transcript(vid)
                        transcript = " ".join([t['text'] for t in ts[:100]])
                    except: pass
                    text_to_analyze = f"TITLE: {title}\nDESC: {desc[:500]}\nTRANSCRIPT: {transcript[:1500]}"

                if not image_url:
                    og = soup.find("meta", property="og:image")
                    if og: image_url = og['content']
        except: pass
    return text_to_analyze, image_url

# --- 2-STAGE AI PIPELINE ---

def ai_stage1_classify(text):
    """
    Stage 1: Fast classification
    - Is it Syrian war related?
    - What category?
    - Language?
    - Side?
    """
    prompt = f"""
    Classify the following post. Output ONLY JSON, no commentary.

    TEXT:
    {text}

    Respond with:
    {{
        "relevant": true/false,
        "category": "COMBAT" | "CASUALTIES" | "PROTEST" | "POLITICAL" | "HUMANITARIAN" | "UNKNOWN",
        "side": "GOV" | "REBEL" | "ISIS" | "KURD" | "ISRAEL" | "TURKEY" | "NEUTRAL",
        "lang": "ar" | "en" | "other"
    }}
    """
    return generate_with_retry(prompt)

def ai_stage2_extract(text, article_data=None):
    """
    Stage 2: Full war-event extraction.
    Includes location, victor, capture status, summary, evidence, and side.
    Only used for complex or ambiguous tweets.
    """
    combined = text
    if article_data:
        combined = f"{text}\n\nARTICLE/TRANSCRIPT:\n{article_data[:2000]}"

    prompt = f"""
    You are a professional military conflict analyst covering the Syrian Civil War (2011–present).

    Analyze the event described below and output ONLY JSON.

    TEXT:
    {combined}

    Respond with:
    {{
        "locations": ["Town, District"],
        "captured": true/false,
        "victor": "Government" | "Rebel" | "ISIS" | "Kurds" | "None",
        "side": "GOV" | "REBEL" | "ISIS" | "KURD" | "ISRAEL" | "TURKEY" | "NEUTRAL",
        "summary": "Professional one-sentence journalistic summary.",
        "evidence_score": 0-10,
        "key": "unique event semantic key"
    }}
    """
    return generate_with_retry(prompt)

# --- HYBRID LOGIC ---

def is_hard_case(text, url):
    # 1. Media URLs -> HARD (Need to read content)
    if url and ("youtube" in url or "youtu.be" in url or "news" in url or "report" in url):
        return True
    
    # 2. Check for Keywords (If present, it's likely EASY if location is also present)
    keywords = ["قصف", "شهيد", "مظاهرة", "اشتباك", "قتلى", "جرحى", "اعتقال", "أمن", "جيش"]
    has_keyword = any(k in text for k in keywords)
    
    # 3. Check for Location
    has_loc = False
    for loc in ARABIC_LOCATIONS:
        if loc in text:
            has_loc = True
            break
            
    # If we have a keyword AND a location, it's EASY (Regex can handle it)
    if has_keyword and has_loc:
        return False
        
    # If we have no location, it's HARD (AI needs to infer)
    if not has_loc:
        return True
        
    # If text is very long/complex, it might be HARD
    if len(text) > 250:
        return True
    
    return False # Default to EASY

def process_easy_case(text):
    # Extract location
    found_locs = []
    for ar_loc, en_loc in ARABIC_LOCATIONS.items():
        if ar_loc in text:
            found_locs.append(en_loc)
    
    primary_loc = found_locs[0] if found_locs else "Syria"
    
    # Simple Category & Side Heuristics
    cat = "NEWS"
    side = "NEUTRAL"
    
    if "قتلى" in text or "شهيد" in text: cat = "CASUALTIES"
    elif "مظاهرة" in text or "حرية" in text: 
        cat = "PROTEST"
        side = "REBEL" # Protests are usually anti-gov
    elif "قصف" in text or "اشتباك" in text: cat = "COMBAT"
    
    # Simple Side Keywords
    if "جيش حر" in text or "ثوار" in text or "الجيش الحر" in text: side = "REBEL"
    elif "جيش نظامي" in text or "عصابات الأسد" in text or "شبيحة" in text or "الجيش النظامي" in text or "قوات الأسد" in text: side = "GOV"
    
    return {
        "relevant": True,
        "category": cat,
        "locations": [primary_loc],
        "summary": text, # Use raw text for easy cases
        "side": side,
        "image": None
    }

def ask_brain(text, url=None):
    print(f"   🤖 Stage 1: Classifying: {text[:40]}...")

    # Stage 1
    s1 = ai_stage1_classify(text)
    if not s1 or not s1.get("relevant", False):
        return None

    # If it's easy (Arabic keywords + known Syrian location), fast path
    if not is_hard_case(text, url):
        print("      ⚡ Regex fast path.")
        res = process_easy_case(text)
        if res['category'] == "NEWS" and s1.get('category'):
            res['category'] = s1['category']
        # Trust AI side if regex didn't find one
        if res['side'] == "NEUTRAL" and s1.get('side'):
            res['side'] = s1['side']
        return res

    # Otherwise Stage 2
    print("      🤖 Stage 2: Extracting details...")
    article_data, image = _get_article_data(text, url)
    s2 = ai_stage2_extract(text, article_data)

    if not s2:
        return None

    # Merge Stage 1 + Stage 2 + image
    s2["category"] = s1.get("category", "COMBAT")
    if image: s2["image"] = image
    
    # Ensure relevant is set
    s2["relevant"] = True

    return s2

def normalize_text(text):
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def save_event_hybrid(war_id, text, date_obj, original_url, handle):
    # Semantic Deduplication
    norm_text = normalize_text(text)
    dup_key = hashlib.md5(norm_text.encode()).hexdigest()
    
    if event_cache.get(dup_key): return
    event_cache.set(dup_key, True)

    # Check for URL
    external_url = None
    url_match = re.search(r'(https?://\S+)', text)
    if url_match: external_url = url_match.group(0)

    # ORCHESTRATION VIA ASK_BRAIN
    intel = ask_brain(text, external_url)

    if not intel or not intel.get('relevant', True): return
    if not intel.get('locations'): return

    # Geolocation (Shared Logic with Cache)
    primary_loc = intel["locations"][0]
    lat, lng = None, None
    
    # 1. Map Lookup
    if primary_loc in SYRIA_LOCATIONS:
        lat, lng = SYRIA_LOCATIONS[primary_loc]
    elif primary_loc in ARABIC_LOCATIONS:
        en = ARABIC_LOCATIONS[primary_loc]
        if en in SYRIA_LOCATIONS: lat, lng = SYRIA_LOCATIONS[en]
        else: primary_loc = en

    # 2. Geocoding with Cache
    if not lat and primary_loc != "Syria":
        cached_geo = geo_cache.get(primary_loc)
        if cached_geo:
            lat, lng = cached_geo
        else:
            try:
                geo = geolocator.geocode(f"{primary_loc}, Syria", timeout=5)
                if geo: 
                    lat, lng = geo.latitude, geo.longitude
                    geo_cache.set(primary_loc, (lat, lng))
                else:
                    if "," in primary_loc:
                        city = primary_loc.split(",")[-1].strip()
                        cached_city = geo_cache.get(city)
                        if cached_city:
                            lat, lng = cached_city
                        else:
                            geo = geolocator.geocode(f"{city}, Syria", timeout=5)
                            if geo: 
                                lat, lng = geo.latitude, geo.longitude
                                geo_cache.set(city, (lat, lng))
            except: pass
            time.sleep(1.1)

    if not lat:
        lat, lng = 33.5138, 36.2765
        lat += random.uniform(-0.02, 0.02)

    side_tag = f"Side: {intel.get('side', 'NEUTRAL')}"
    print(f"      ✅ SAVED: {intel['summary'][:50]}... [{intel['category']}] ({side_tag})")

    ev = Event(
        war_id=war_id,
        title=f"[{intel['category']}] {intel['summary']}",
        description=f"Source: @{handle} | {text} | {side_tag}",
        event_date=date_obj,
        lat=lat, lng=lng,
        source_url=original_url,
        image_url=intel.get('image')
    )
    db.session.add(ev)
    db.session.commit()

# --- WAYBACK ENGINE ---
def get_snapshots(handle, year):
    api = f"http://web.archive.org/cdx/search/cdx?url=twitter.com/{handle}*&from={year}0315&to={year}1231&output=json&fl=timestamp,original&filter=statuscode:200&collapse=digest"
    
    for attempt in range(5):
        try:
            r = requests.get(api, timeout=60)
            if r.status_code == 200:
                data = r.json()
                if data: return sorted([row[0] for row in data[1:]])
            elif r.status_code == 429:
                print(f"   ⚠️ CDX Rate Limit (429). Sleeping...")
                time.sleep(10)
        except Exception as e:
            wait_time = 5 * (attempt + 1)
            print(f"   ⚠️ CDX Error (Attempt {attempt+1}): {e}. Sleeping {wait_time}s...")
            time.sleep(wait_time)
    return []

def scrape_page(handle, ts):
    url = f"https://web.archive.org/web/{ts}/https://twitter.com/{handle}"
    try:
        r = requests.get(url, headers={'User-Agent': 'WT-Smart/1.0'}, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        tweets = []
        selectors = [
            'div.tweet-text', 
            'div.js-tweet-text-container p', 
            'article div[data-testid="tweetText"]',
            'span.entry-content',
            'p.js-tweet-text'
        ]
        for sel in selectors:
            for item in soup.select(sel):
                t = item.get_text().strip()
                if t: tweets.append(t)
        return tweets
    except: return []

def run_smart_scraper(year=2011):
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war: return
    print(f"--- 🧠 SMART HYBRID INGESTION (API + AI): {year} ---")
    
    for handle in TARGET_HANDLES:
        print(f"\n🔎 Scanning: @{handle} ...")
        snaps = get_snapshots(handle, year)
        print(f"   Found {len(snaps)} snapshots.")
        
        for ts in snaps:
            print(f"   ⏳ Parsing: {ts[:8]} ...")
            tweets = scrape_page(handle, ts)
            for text in tweets:
                url = f"https://web.archive.org/web/{ts}/https://twitter.com/{handle}"
                save_event_hybrid(war.id, text, datetime.strptime(ts[:8], "%Y%m%d"), url, handle)
            time.sleep(1)

if __name__ == "__main__":
    run_smart_scraper(2011)
