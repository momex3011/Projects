import requests
import feedparser
import time
import random
import ssl
import urllib.parse
import sys
import re
import hashlib
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from urllib.parse import urlparse
from app import create_app
from extensions import db
from models.event import Event
from models.war import War
from models.location import Location
from models.history import TerritoryHistory
from geopy.geocoders import Nominatim
from duckduckgo_search import DDGS

# --- DEPENDENCIES ---
try:
    from syria_data import SYRIA_LOCATIONS
except ImportError:
    SYRIA_LOCATIONS = {}

# SSL Fix
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

app = create_app()
app.app_context().push()
geolocator = Nominatim(user_agent="wartracker_ingest_no_ai", timeout=10)

# --- CONFIG ---
WAR_NAME = "Syria"

# SOCIAL ONLY
SOCIAL_SITES = ["twitter.com", "facebook.com", "youtube.com"]

# PRIMARY SOURCES (For extraction)
PRIMARY_SOURCES = ["SOHR", "Observatory", "SNHR", "VDC", "United Nations", "UN", "Human Rights Watch", "LCC", "Local Coordination Committees"]

# STRICTER KEYWORDS (Must imply conflict/event)
SEARCH_TERMS = [
    "Syria protest", "Syria clash", "Syria shelling", "Syria killed", 
    "Syria massacre", "Free Syrian Army", "Syria defect", "Syria arrest", 
    "Syria funeral", "Syria explosion",
    "مظاهرات سوريا", "اشتباكات سوريا", "قصف سوريا", "قتلى سوريا", 
    "الجيش الحر", "انشقاق جيش", "مجزرة سوريا", "اقتحام جيش", 
    "اعتقالات سوريا", "تشييع شهيد", "الشبيحة"
]

# EXCLUSION TERMS (To remove noise)
EXCLUDE_TERMS = [
    "-song", "-music", "-mp3", "-lyrics", "-match", "-goal", "-vs", "-football", 
    "-movie", "-trailer", "-episode", "-series", "-recipe", "-cooking", "-weather",
    "-أغنية", "-موسيقى", "-مباراة", "-هدف", "-فيلم", "-مسلسل", "-طبخ", "-وصفة", "-طقس"
]

# NEIGHBOR TERMS (For negative scoring if Syria not present)
NEIGHBOR_TERMS = ["Lebanon", "Israel", "Turkey", "Jordan", "Iraq", "Beirut", "Amman", "Ankara", "Tel Aviv"]

SEEN_TITLES = set()
EVENT_MEMORY = {} 

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

# Map Arabic names to English keys in SYRIA_LOCATIONS
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

# --- KEYWORD MATCHING LOGIC ---
KEYWORDS = {
    "PROTEST": [
        "protest", "demonstration", "march", "rally", "sit-in", "uprising", "revolution", "funeral",
        "مظاهرة", "احتجاج", "اعتصام", "ثورة", "انتفاضة", "مسيرة", "تشييع", "حرية"
    ],
    "COMBAT": [
        "clash", "battle", "attack", "kill", "bomb", "strike", "shelling", "fire", "shot", "explosion", "massacre",
        "اشتباك", "معركة", "قصف", "قتلى", "هجوم", "انفجار", "إطلاق نار", "مجزرة", "شهيد", "تدمير", "استهداف"
    ],
    "POLITICAL": [
        "regime", "assad", "opposition", "un", "council", "meeting", "sanction", "defect",
        "نظام", "أسد", "معارضة", "مجلس", "اجتماع", "عقوبات", "انشقاق", "بيان"
    ],
    "ARREST": [
        "arrest", "detain", "kidnap", "prison", "torture",
        "اعتقال", "سجن", "تعذيب", "خطف", "مداهمة"
    ],
    "DEFECT": [
        "defect", "desert", "officer", "general",
        "انشقاق", "ضباط", "هروب"
    ]
}

def analyze_text_advanced(text, url=""):
    """
    Analyzes text using advanced scoring and regex.
    """
    text_lower = text.lower()
    
    # 0. Hard Filter for Noise
    noise_words = ["song", "music", "lyrics", "match", "football", "movie", "episode", "recipe", "أغنية", "موسيقى", "مباراة", "فيلم", "مسلسل"]
    for w in noise_words:
        if w in text_lower:
            return None 

    # 1. Relevance Scoring
    score = 0
    if "syria" in text_lower or "سوريا" in text_lower: score += 5
    
    # Check domain relevance
    domain = urlparse(url).netloc.lower()
    if "facebook.com" in domain or "youtube.com" in domain or "twitter.com" in domain: score += 10 # High score for social
    
    # Check neighbors (Negative if Syria not mentioned)
    for n in NEIGHBOR_TERMS:
        if n.lower() in text_lower and "syria" not in text_lower and "border" not in text_lower:
            score -= 20
            
    # Check primary sources
    for ps in PRIMARY_SOURCES:
        if ps.lower() in text_lower:
            score += 10
            break
            
    if score < 5: return None # Discard low relevance

    # 2. Determine Category
    category = "GENERAL"
    for cat, words in KEYWORDS.items():
        for w in words:
            if w in text_lower:
                category = cat
                break
        if category != "GENERAL": break
    
    # 3. Extract Locations (Regex + Aliases)
    locations = []
    
    # A. Check English Aliases (Regex for word boundaries)
    for alias, formal in COMMON_ALIASES.items():
        if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
            locations.append(formal)
            
    # B. Check Arabic Aliases
    for arabic, formal in ARABIC_ALIASES.items():
        if arabic in text: 
            locations.append(formal)
    
    # C. Check SYRIA_LOCATIONS (The Big List)
    if not locations:
        for loc in SYRIA_LOCATIONS:
            if loc.lower() in text_lower:
                locations.append(loc)
                break 
    
    if not locations:
        locations = ["Syria"]

    return {
        "category": category,
        "locations": locations,
        "captured": False, 
        "victor": None,
        "summary": text, 
        "evidence_score": score,
        "image": None
    }

def save_event(war_id, title, summary, locations, date_obj, url, is_capture, victor, category, img_url, evidence_score, dup_key):
    try:
        if dup_key and dup_key in EVENT_MEMORY:
            return False

        primary_loc = locations[0] if locations else "Syria"
        lat, lng = None, None
        found = False

        # 1. Try Local Database (Exact Match)
        if primary_loc in SYRIA_LOCATIONS:
            lat, lng = SYRIA_LOCATIONS[primary_loc]
            found = True
        
        # 2. Try Local Database (Normalized Match)
        if not found:
            norm_loc = primary_loc.replace("-", " ").title()
            if norm_loc in SYRIA_LOCATIONS:
                lat, lng = SYRIA_LOCATIONS[norm_loc]
                found = True

        # 3. Try Geocoding (Nominatim)
        if not found and primary_loc.lower() != "syria":
            try:
                # Rate limit (cached if possible, but we sleep here)
                time.sleep(1.1) 
                query = f"{primary_loc}, Syria"
                geo = geolocator.geocode(query, timeout=5)
                if geo:
                    lat, lng = geo.latitude, geo.longitude
                    found = True
            except: pass

        # 4. Default Fallback (Damascus)
        if not found:
            lat, lng = 33.5138, 36.2765 
        
        lat += random.uniform(-0.0005, 0.0005)
        lng += random.uniform(-0.0005, 0.0005)

        ev = Event(
            war_id=war_id, title=f"[{category}] {title[:200]}",
            description=summary, event_date=date_obj,
            lat=lat, lng=lng, source_url=url, image_url=img_url
        )
        db.session.add(ev)
        db.session.commit()
        
        if dup_key:
            EVENT_MEMORY[dup_key] = {'evidence_score': evidence_score, 'event_id': ev.id}
        
        return True
    except Exception as e: 
        print(f"Error saving event: {e}")
        return False

def scrape_twitter_via_ddg(war_id, current_date):
    print(f"   🦆 DuckDuckGo (Twitter) Scan: {current_date} ...")
    
    d_start = current_date.strftime('%Y-%m-%d')
    d_end = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Dork: site:twitter.com "Syria" ("protest" OR "clash") after:2011-03-01 before:2011-03-02
    query = f'site:twitter.com "Syria" ("protest" OR "clash" OR "killed" OR "shelling") after:{d_start} before:{d_end}'
    
    try:
        results = DDGS().text(query, max_results=20)
        count = 0
        if results:
            for r in results:
                title = r['title']
                link = r['href']
                snippet = r['body']
                full_text = f"{title} {snippet}"
                
                unique_str = f"{title[:50]}_{current_date.strftime('%Y-%m-%d')}"
                dup_key = hashlib.md5(unique_str.encode()).hexdigest()
                if dup_key in EVENT_MEMORY: continue

                intel = analyze_text_advanced(full_text, link)
                if not intel: continue
                
                if save_event(war_id, title, snippet, intel["locations"], current_date, link, False, None, intel["category"], None, intel["evidence_score"], dup_key):
                    count += 1
                    print(f"      ✅ SAVED (DDG-Twitter): {title[:50]}... [{intel['category']}]")
        return count
    except Exception as e:
        print(f"      ❌ DDG Error: {e}")
        return 0

def scrape_social_google(war_id, d_after, d_before, current_date):
    print(f"   👥 Social Media Scan (FB/YouTube): {d_after} ...")
    
    # TARGET SPECIFIC SITES: Facebook, YouTube
    # We exclude Twitter here because we have DDG
    site_query = " OR ".join([f"site:{s}" for s in SOCIAL_SITES if "twitter" not in s])
    
    terms_part = " OR ".join(SEARCH_TERMS[10:]) 
    exclude_part = " ".join(EXCLUDE_TERMS)
    
    raw_query = f"{site_query} ({terms_part}) {exclude_part} after:{d_after} before:{d_before}"
    rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(raw_query)}&hl=en-US&gl=US&ceid=US:en"
    
    try:
        feed = feedparser.parse(rss_url)
        count = 0
        for entry in feed.entries:
            title = entry.title.strip()
            link = entry.link
            summary = entry.get("summary", "")
            full_text = f"{title} {summary}"
            
            # RELAXED DATE CHECK (Buffer +/- 1 day for RSS)
            pub_date_str = entry.get('published', '')
            try:
                pub_date = date_parser.parse(pub_date_str).date()
                # Allow +/- 1 day buffer
                if not (current_date - timedelta(days=1) <= pub_date <= current_date + timedelta(days=1)):
                    continue
            except: continue

            # Deduplication
            unique_str = f"{title}_{current_date.strftime('%Y-%m-%d')}"
            dup_key = hashlib.md5(unique_str.encode()).hexdigest()
            if dup_key in EVENT_MEMORY: continue
            
            intel = analyze_text_advanced(full_text, link)
            if not intel: continue 

            if save_event(war_id, title, summary, intel["locations"], current_date, link, False, None, intel["category"], None, intel["evidence_score"], dup_key):
                count += 1
                print(f"      ✅ SAVED (Social): {title[:50]}... [{intel['category']}]")
        return count
    except Exception as e:
        print(f"      ❌ Social Error: {e}")
        return 0

def run_scraper(year=2011):
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war: 
        print("❌ Run setup.py first!")
        return

    print(f"--- 🦅 SOCIAL-ONLY INGESTION (DDG + Google) STARTING {year} ---")
    
    current = datetime(year, 3, 1)
    end_date = datetime(year, 12, 31)
    
    while current <= end_date:
        next_step = current + timedelta(days=1)
        d_after = current.strftime("%Y-%m-%d")
        d_before = next_step.strftime("%Y-%m-%d")
        
        print(f"\n📅 Scanning: {d_after} ...")
        
        # 1. Twitter (DuckDuckGo)
        count_t = scrape_twitter_via_ddg(war.id, current.date())
        
        # 2. Facebook & YouTube (Google RSS)
        count_s = scrape_social_google(war.id, d_after, d_before, current.date())
        
        print(f"   🏁 Batch: {count_t + count_s} events")
        current = next_step
        
        # RATE LIMITING: Random sleep to avoid DDG bans
        sleep_time = random.uniform(5, 10)
        print(f"   💤 Sleeping {sleep_time:.1f}s ...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    target_year = 2011
    if len(sys.argv) > 1: target_year = int(sys.argv[1])
    run_scraper(target_year)
