import time
import ssl
import urllib.parse
import sys
import random
from datetime import datetime, timedelta
from tasks import schedule_source_crawls
# App imports
from app import create_app
from extensions import db
from models.event import Event
from models.war import War
from models.scraper_state import ScraperState
from zoneinfo import ZoneInfo 
import redis



# SSL Fix for Windows environments
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

app = create_app()
app.app_context().push()

WAR_NAME = "Syria"
SY_TZ = ZoneInfo("Asia/Damascus")

# --- THE PURE SOCIAL CONFIG ---
TARGET_PLATFORMS = ["youtube.com", "facebook.com", "twitter.com", "youtu.be"]

CITIES = [
    "Daraa", "Homs", "Damascus", "Aleppo", "Hama", "Baniyas", "Idlib", "Deir Ezzor",
    "Raqqa", "Douma", "Zabadani", "Inkhil", "Jassem", "Nawa", "Da'el"
]

# --- ERA-SPECIFIC DORKS (Post-2025 Autonomy Logic) ---
# This ensures we search for "Graffiti" in 2011 and "Drones" in 2025.
ERA_DORKS = {
    "2011": ["protest", "Daraa children", "Ugarit News", "Shaam News", "SNN", "LCC Syria", "graffiti", "demonstration"],
    "2012": ["FSA", "Free Syrian Army", "Defection", "Baba Amr", "barrel bomb", "siege", "shelling"],
    "2013": ["Chemical attack", "Ghouta", "Hezbollah", "Qusayr"],
    "2014": ["ISIS", "Daesh", "Kobani", "Coalition strike", "YPG", "SDF"],
    "2015": ["Russian airforce", "Palmyra", "Tiger Forces", "Iranian militia"],
    "2020": ["HTS", "Turkish drone", "Suwayda protests", "Economic collapse"],
    "2025": ["Drone strike", "Frozen lines", "HTS consolidation", "Autonomous monitoring"]
}


def run_source_ingest(target_date):
    # 1. Get all trusted sources
    sources = Source.query.filter(Source.status != "banned").all()
    
    for source in sources:
        # Dispatch a mission for this specific source
        ingest_from_source.delay(source.id, target_date.strftime('%Y-%m-%d'))

def get_dorks_for_year(year):
    """Selects the best keywords for the specific year being scanned."""
    year_str = str(year)
    
    # 1. Base Historical Dorks
    if year_str in ERA_DORKS:
        base_dorks = ERA_DORKS[year_str]
    else:
        base_dorks = ERA_DORKS["2025"]
        
    # 2. Adaptive Trends (The Learning Layer)
    try:
        from models.trend import Trend
        # We only want trends that are active
        active_trends = [t.keyword for t in Trend.query.filter_by(is_active=True).all()]
        if active_trends:
            print(f"   🧠 Intelligence: Injecting {len(active_trends)} learned keywords.")
            # Combine unique
            return list(set(base_dorks + active_trends))
    except Exception as e:
        print(f"   ⚠️ Trend Error: {e}")

    return base_dorks

def check_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=1)
        r.ping()
        print("   ✅ Redis Connection: OK")
        return True
    except Exception as e:
        print(f"\n❌ REDIS ERROR: {e}\n👉 Start Redis/Memurai first!")
        return False

def run_scraper(target_year=2011):
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war:
        raise RuntimeError(f"War '{WAR_NAME}' not found in database")

    state = ScraperState.query.filter_by(war_id=war.id).first()

    now_sy = datetime.now(SY_TZ)
    current = datetime(target_year, 3, 6, 0, 0, 0, tzinfo=SY_TZ)

    if state and state.last_date_processed:
        resume_day = state.last_date_processed + timedelta(days=1)
        current = datetime(
            resume_day.year,
            resume_day.month,
            resume_day.day,
            0, 0, 0,
            tzinfo=SY_TZ
        )

# --- ANALYST LOGIC (INTEGRATED) ---
import re
import sqlite3
import os
from collections import Counter

DB_PATH = "wartracker.db"
STOP_WORDS = {
    "video", "report", "news", "syria", "breaking", "exclusive", "live", "coverage",
    "footage", "update", "analysis", "watch", "today", "yesterday", "daily", "weekly",
    "killed", "injured", "dead", "attack", "clash", "fighting", "battle", "force", "army",
    "rebel", "regime", "assad", "isis", "group", "militia", "control", "village", "town",
    "city", "near", "north", "south", "east", "west", "central", "province", "rural",
    "media", "channel", "network", "agency", "source", "via", "confirmed", "official",
    "statement", "announced", "claimed", "reported", "said", "says", "claims", "reports",
    "about", "this", "that", "with", "from", "after", "before", "during", "while", "when",
    "where", "what", "which", "who", "whom", "whose", "why", "how", "and", "but", "or",
    "nor", "for", "yet", "so", "the", "a", "an", "in", "on", "at", "to", "of", "by", "is", "are"
}

def analyze_trends():
    """Runs frequency analysis on recent events to populate the 'trends' table."""
    if not os.path.exists(DB_PATH): return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Look back 24h
        since_time = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Fetch Trusted Content
        cursor.execute("SELECT count(*) FROM sources WHERE status='trusted'")
        trusted_count = cursor.fetchone()[0]
        
        query = "SELECT title, description FROM events WHERE created_at >= ?"
        if trusted_count == 0:
            print("   ⚠️ Analyst: No trusted sources. scanning ALL recent events.")
        
        cursor.execute(query, (since_time,))
        rows = cursor.fetchall()
        
        if not rows: return

        # building corpus
        text_corpus = []
        for r in rows:
            title, description = r
            if title: text_corpus.append(title.lower())
            if description: text_corpus.append(description.lower())

        # frequency analysis
        words = []
        for text in text_corpus:
            cleaned = re.findall(r'\b[a-z]{3,}\b', text)
            words.extend(cleaned)
            
        filtered_words = [w for w in words if w not in STOP_WORDS]
        counts = Counter(filtered_words)
        
        # upsert trends
        active_trends = []
        now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        found_count = 0
        for word, count in counts.most_common(20):
            if count < 3: continue
            active_trends.append(word)
            found_count += 1
            
            cursor.execute("""
                INSERT INTO trends (keyword, score, last_seen, is_active) 
                VALUES (?, ?, ?, 1)
                ON CONFLICT(keyword) DO UPDATE SET
                    score = ?, last_seen = ?, is_active = 1
            """, (word, float(count), now_str, float(count), now_str))
            
        # Optional: Deactivate old trends
        if active_trends:
            placeholders = ','.join('?' for _ in active_trends)
            cursor.execute(f"UPDATE trends SET is_active=0 WHERE keyword NOT IN ({placeholders})", active_trends)
            
        conn.commit()
        conn.close()
        
        if found_count > 0:
            print(f"   🧠 Analyst: Learned {found_count} keywords.")
            
    except Exception as e:
        print(f"   ❌ Analyst Error: {e}")

def run_scraper(target_year=2011):
    war = War.query.filter_by(name=WAR_NAME).first()
    if not war: raise RuntimeError(f"War '{WAR_NAME}' not found in database")

    state = ScraperState.query.filter_by(war_id=war.id).first()
    now_sy = datetime.now(SY_TZ)
    current = datetime(target_year, 3, 6, 0, 0, 0, tzinfo=SY_TZ)

    if state and state.last_date_processed:
        resume_day = state.last_date_processed + timedelta(days=1)
        current = datetime(resume_day.year, resume_day.month, resume_day.day, 0,0,0, tzinfo=SY_TZ)

    loop_count = 0

    while current.date() <= now_sy.date():
        d_str = current.date().isoformat()
        print(f"\n⚡ [PULSE] {WAR_NAME} | {d_str} (Syria TZ)")

        # 1. Run Analyst
        analyze_trends()

        # 2. Schedule YouTube Sources (SYNCHRONOUS FOR DEBUGGING)
        from tasks import schedule_source_crawls as ssc_func
        result = ssc_func(war.id, d_str, max_sources=50)
        print(f"   [INGESTION] Scheduler result: {result}")

        # 3. Checkpoint
        if not state:
            state = ScraperState(war_id=war.id, last_date_processed=current.date())
            db.session.add(state)

        state.last_date_processed = current.date()
        db.session.commit()

        loop_count += 1
        
        # DYNAMIC SLEEP:
        # If we are in the past (> 2 days ago), run at a pace that matches AI rate limits.
        # Groq free tier: 30 RPM = ~1 request every 2 seconds
        # With 147 videos per day, we need ~300 seconds (5 min) to process them all
        days_diff = (now_sy.date() - current.date()).days
        
        if days_diff > 2:
            # Wait for the current batch to process before queuing more
            # Each video takes ~3-5 seconds with retries, so 147 videos = ~10 minutes
            print(f"   ⏩ History Mode: Sleeping 600s (letting AI process batch)...")
            time.sleep(600)  # 10 minutes - let the batch process
        else:
            print(f"   💤 Live Mode: Sleeping 600s (monitoring)...")
            time.sleep(600)
            
        current += timedelta(days=1)

def reset_all_data():
    """Wipes DB events, scraper state, text ledger, and Celery queue."""
    print("\n   💥 STARTING FULL SYSTEM RESET...")
    
    # 1. Clear Database
    try:
        from models.source import Source # Lazy import to avoid circular issues
        num_events = db.session.query(Event).delete()
        db.session.query(ScraperState).delete()
        
        # RESET SOURCES COOLDOWNS
        # Use bulk update to reset last_crawled_at so they fire immediately
        db.session.query(Source).update({Source.last_crawled_at: None})
        
        db.session.commit()
        print(f"      ✅ Database: Deleted {num_events} events, reset state, & cleared source cooldowns.")
    except Exception as e:
        db.session.rollback()
        print(f"      ❌ Database Error: {e}")

    # 2. Clear Ledger
    try:
        with open("accepted_events.md", "w", encoding="utf-8") as f:
            f.write("# 📂 The Daily Ledger\n**Status**: Real-time Sync Active\n**Filtered By**: Strong Acceptance Criteria (Combats, Protests, Crimes)\n\n---\n")
        print("      ✅ Ledger: Cleared 'accepted_events.md'.")
    except Exception as e:
        print(f"      ⚠️ Ledger Error: {e}")

    # 3. Flush Celery/Redis
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.flushdb()
        print("      ✅ Queue: Flushed Redis (Deleted all pending tasks).")
    except Exception as e:
        print(f"      ⚠️ Redis Error: {e}")
        
    print("   ✨ SYSTEM CLEAN. Starting fresh from Day 1.\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "RESET":
         reset_all_data()
         run_scraper(2011)
    else:
        print("\n\n#################################################")
        print("#    WAR TRACKER - INGESTION CONTROL CENTER     #")
        print("#################################################")
        print("1. [C]ONTINUE  : Resume scraping from last saved date.")
        print("2. [R]ESET     : DELETE ALL DATA and start fresh from 2011.")
        print("3. [Q]UIT      : Exit.")
        
        choice = input("\n👉 Select Option (c/r/q): ").strip().lower()
        
        if choice == 'r':
            confirm = input("⚠️  ARE YOU SURE? THIS CANNOT BE UNDONE. (type 'yes'): ")
            if confirm == 'yes':
                with app.app_context():
                    reset_all_data()
                run_scraper(2011)
            else:
                print("ABORTED.")
        elif choice == 'c':
            print("   ▶️ Resuming...")
            run_scraper(2011)
        else:
            print("   👋 Bye.")