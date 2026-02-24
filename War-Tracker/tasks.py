from celery_app import celery
from ingest_utils import save_event, heuristic_parse
import logging
from curl_cffi import requests
import feedparser
import urllib.parse
import yt_dlp
import random
from deep_translator import GoogleTranslator
from deep_translator.exceptions import TooManyRequests
from datetime import datetime, timedelta, timezone
from extensions import db
from bs4 import BeautifulSoup


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
]

CRAWL_INTERVAL_HOURS = {
    "trusted": 6,     # crawl often
    "probation": 24,  # crawl daily
    "banned": 999999  # never
}


try:
    from ai_agent import ask_brain
except ImportError:
    ask_brain = None

# --- HELPERS ---


def stealth_get(url, headers=None, timeout=15, allow_redirects=True):
    return requests.get(
        url,
        headers=headers,
        timeout=timeout,
        allow_redirects=allow_redirects,
        impersonate="chrome120",
    )



def should_crawl_source(src, now_utc: datetime) -> bool:
    """Cooldown gate: prevents over-crawling a source."""
    status = (src.status or "probation").lower()
    interval_h = CRAWL_INTERVAL_HOURS.get(status, 24)

    if status == "banned":
        return False

    if not src.last_crawled_at:
        return True

    return (now_utc - src.last_crawled_at) >= timedelta(hours=interval_h)

def source_weight(src) -> float:
    """
    Convert reliability_score into a crawl weight.
    Higher score => more likely to be crawled when scheduling.
    """
    score = float(src.reliability_score or 50.0)

    # Hard stop
    if (src.status or "").lower() == "banned":
        return 0.0

    # Base weight by status
    status = (src.status or "probation").lower()
    base = 1.0
    if status == "trusted":
        base = 2.5
    elif status == "probation":
        base = 1.0

    # Score curve (keeps low-scorers from dominating)
    # 0..100 => 0.2..3.0
    score_factor = 0.2 + (score / 100.0) * 2.8
    return base * score_factor


def _clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def update_source_reliability(source_id: int, date_str: str, *, saved: bool, evidence_score: int | None):
    """
    Part B:
    - writes/updates a SourceObservation for the day
    - adjusts Source.reliability_score + Source.status
    """
    from models.source import Source, SourceObservation

    day = datetime.strptime(date_str, "%Y-%m-%d").date()

    src = Source.query.get(source_id)
    if not src:
        return

    # --- 1) Update daily observation ---
    obs = SourceObservation.query.filter_by(source_id=source_id, date_observed=day).first()
    if not obs:
        obs = SourceObservation(source_id=source_id, date_observed=day, items_found=0, items_accepted=0)
        db.session.add(obs)

    obs.items_found += 1
    if saved:
        obs.items_accepted += 1

    # --- 2) Compute recent acceptance trend (last 7 days) ---
    start_day = day - timedelta(days=6)
    recent = SourceObservation.query.filter(
        SourceObservation.source_id == source_id,
        SourceObservation.date_observed >= start_day,
        SourceObservation.date_observed <= day,
    ).all()

    found_7d = sum(o.items_found for o in recent) or 0
    accepted_7d = sum(o.items_accepted for o in recent) or 0
    accept_rate_7d = (accepted_7d / found_7d) if found_7d > 0 else 0.0

    # --- 3) Per-item score delta ---
    ev = int(evidence_score or 5)
    ev = _clamp(ev, 1, 10)

    delta = 0.0
    if saved:
        # reward accepted content (stronger reward if high evidence)
        delta += 1.5 + (ev - 5) * 0.30
    else:
        # punish rejected content
        delta -= 1.0

    # Trend bonus/penalty (keeps behavior stable)
    if found_7d >= 10:
        if accept_rate_7d >= 0.60:
            delta += 0.6
        elif accept_rate_7d <= 0.20:
            delta -= 0.6

    # Clamp delta so one post can’t swing score too hard
    delta = _clamp(delta, -3.0, 3.0)

    # --- 4) Apply and update status ---
    src.reliability_score = _clamp((src.reliability_score or 50.0) + delta, 0.0, 100.0)

    # status logic (simple + effective)
    if src.reliability_score >= 75:
        src.status = "trusted"
    elif src.reliability_score <= 10 and found_7d >= 25:
        # only hard-ban if it keeps being trash at scale
        src.status = "banned"
    else:
        src.status = "probation"

    db.session.commit()


def _youtube_source_url_from_handle(handle: str) -> str:
    """
    Build a channel/videos URL from a Source.handle.
    Accepts:
      - UCxxxx channel_id  -> https://www.youtube.com/channel/UCxxxx/videos
      - @handle            -> https://www.youtube.com/@handle/videos
      - full URL           -> returned as-is
      - anything else      -> treated as a channel name search URL (fallback)
    """
    h = (handle or "").strip()

    if not h:
        raise ValueError("Empty YouTube handle")

    if "youtube.com" in h or "youtu.be" in h:
        return h

    if h.startswith("UC"):
        return f"https://www.youtube.com/channel/{h}/videos"

    if h.startswith("@"):
        return f"https://www.youtube.com/{h}/videos"

    # Fallback: channel name search (less ideal, but still no Google)
    # NOTE: best practice is to store UC channel_id or @handle in Source.handle.
    return f"https://www.youtube.com/results?search_query={h}"

def _collect_youtube_video_items_for_date(source_handle: str, target_date_str: str, limit: int = 30):
    """
    Returns a list of items: [{"title": ..., "link": ...}, ...]
    
    ROLLING WINDOW STRATEGY:
    Instead of trying to find videos from a specific date (which requires scrolling
    through thousands of videos), we ingest the LATEST N videos from each source.
    
    - extract_flat=True: Bypasses age gates
    - No date filtering: Accept latest content
    - AI brain: Filters for relevance
    - Hash dedup: Prevents repeat ingestion
    """
    url = _youtube_source_url_from_handle(source_handle)

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,     # ENABLED: Bypass age-gate
        "skip_download": True,
        "playlistend": limit,     # Take latest N videos
        "ignoreerrors": True,
        **YT_AGE_BYPASS_OPTS,     # Age-gate bypass for war content
    }

    items = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # Normalize to entries list
    entries = []
    if isinstance(info, dict):
        if "entries" in info and info["entries"]:
            entries = list(info["entries"])
        elif info.get("webpage_url") or info.get("url"):
            entries = [info]

    for e in entries:
        if not e:
            continue

        title = e.get("title") or e.get("fulltitle") or "YouTube video"
        link = e.get("url") or e.get("webpage_url")

        # Flat entries sometimes give relative urls like "watch?v=..."
        if link and link.startswith("watch?v="):
            link = "https://www.youtube.com/" + link

        if link:
            items.append({"title": title, "link": link})

    print(f"      ✅ Found {len(items)} videos from {source_handle}")
    return items


@celery.task(bind=True)
def schedule_source_crawls(self, war_id: int, target_date_str: str, max_sources: int = 50):
    """
    STEP C:
    - For HISTORICAL dates (> 2 days ago): Use YouTube date-filtered search
    - For LIVE dates (recent): Crawl sources normally
    """
    from models.source import Source

    now_utc = datetime.utcnow()
    today = datetime.utcnow().date()
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    
    # HISTORY MODE CHECK:
    # If target_date is older than 2 days ago, use HISTORICAL SEARCH
    is_history_mode = (today - target_date).days > 2
    
    print(f"   [SCHEDULER] Target: {target_date_str}, History Mode: {is_history_mode}")

    # === HISTORY MODE: Date-filtered YouTube Search ===
    if is_history_mode:
        # Get era-specific keywords - include channel names & Arabic terms
        year = target_date.year
        era_keywords = {
            2011: [
                "Ugarit News Syria",      # Key citizen journalism channel
                "Shaam News Network",     # SNN - major opposition outlet
                "سوريا مظاهرة درعا",        # "Syria demonstration Daraa" in Arabic
                "syria daraa protest",
                "syria homs demonstration",
            ],
            2012: [
                "Syria FSA attack",
                "Baba Amr Homs",
                "syria army defection",
                "syria barrel bomb",
                "Ugarit homs",
            ],
            2013: [
                "syria chemical ghouta",
                "syria sarin attack",
                "qusayr hezbollah",
                "syria damascus bomb",
            ],
            2014: [
                "isis raqqa syria",
                "kobani isis",
                "syria coalition airstrike",
            ],
            2015: [
                "russia syria airstrike",
                "palmyra isis",
                "syria iranian militia",
            ],
        }
        keywords = era_keywords.get(year, ["syria war footage", "syrian conflict"])
        
        print(f"   [HISTORICAL] Searching YouTube for {year} content...")
        
        items = search_youtube_historical(keywords, target_date_str, limit=30)
        
        dispatched = 0
        for item in items:
            # Use the video's actual upload date
            actual_date = item.get("upload_date", target_date_str)
            process_event_task.delay(item, war_id, actual_date)
            dispatched += 1
        
        return f"✅ Historical search: Dispatched {dispatched} videos from {target_date_str} era"

    # === LIVE MODE: Crawl sources normally ===
    sources = Source.query.filter(Source.status != "banned").all()
    if not sources:
        return "No sources to schedule"

    eligible = [s for s in sources if should_crawl_source(s, now_utc)]
    print(f"   [SCHEDULER] Eligible sources: {len(eligible)}")
    
    if not eligible:
        return "No eligible sources (cooldowns active)"

    # Weighted pick
    picks = []
    pool = eligible[:]

    for _ in range(min(max_sources, len(pool))):
        weights = [source_weight(s) for s in pool]
        total = sum(weights)
        if total <= 0:
            break

        r = random.uniform(0, total)
        upto = 0.0
        chosen_idx = None
        for i, w in enumerate(weights):
            upto += w
            if upto >= r:
                chosen_idx = i
                break

        if chosen_idx is None:
            break

        chosen = pool.pop(chosen_idx)
        picks.append(chosen)

    print(f"   [SCHEDULER] Selected {len(picks)} sources for ingestion")

    dispatched = 0
    for src in picks:
        ingest_from_source.delay(src.id, target_date_str, war_id)
        dispatched += 1

    return f"✅ Scheduled {dispatched} source crawls for {target_date_str}"


# === AGE-GATE & BOT-DETECTION BYPASS CONFIG ===
# YouTube is blocking requests with "Sign in to confirm you're not a bot"
# 
# OPTION 1: Export cookies to a file (RECOMMENDED FOR WINDOWS):
#   1. Install browser extension: "Get cookies.txt LOCALLY" 
#   2. Go to youtube.com (logged in)
#   3. Click extension → Export → Save as "cookies.txt" in War-Tracker folder
#
# OPTION 2: Use browser cookies directly (Linux/Mac only - DPAPI issues on Windows)
#
import os
COOKIES_FILE = os.path.join(os.path.dirname(__file__), "cookies.txt")

YT_AGE_BYPASS_OPTS = {
    "age_limit": None,  # Ignore age restrictions
    "extractor_args": {
        "youtube": {
            # Android/iOS clients often bypass age verification
            "player_client": ["android", "ios", "web"],
            "player_skip": ["webpage"],  # Skip webpage check
        }
    },
}

# Add cookies file if it exists
if os.path.exists(COOKIES_FILE):
    YT_AGE_BYPASS_OPTS["cookiefile"] = COOKIES_FILE
    print(f"   🍪 Using cookies from: {COOKIES_FILE}")


def parse_date_from_text(text):
    """
    Tries to extract a date from video title/description.
    Many Syrian Revolution videos have dates like:
    - "27 Mar 2011", "March 27, 2011", "2011-03-27", "27/3/2011", "3-27-2011"
    """
    import re
    from datetime import datetime
    
    if not text:
        return None
    
    # Common date patterns in video titles
    patterns = [
        # YYYY-MM-DD or YYYY/MM/DD
        (r'(20\d{2})[-/](\d{1,2})[-/](\d{1,2})', lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
        # DD-MM-YYYY or DD/MM/YYYY
        (r'(\d{1,2})[-/](\d{1,2})[-/](20\d{2})', lambda m: f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"),
        # "27 Mar 2011" or "Mar 27, 2011"
        (r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(20\d{2})', 
         lambda m: _month_day_year(m.group(2), m.group(1), m.group(3))),
        (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+(\d{1,2}),?\s+(20\d{2})', 
         lambda m: _month_day_year(m.group(1), m.group(2), m.group(3))),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                date_str = formatter(match)
                # Validate it's a real date
                datetime.strptime(date_str, "%Y-%m-%d")
                return date_str
            except:
                continue
    
    return None


def _month_day_year(month_str, day, year):
    """Helper to convert month name to number."""
    months = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    month_num = months.get(month_str[:3].lower(), '01')
    return f"{year}-{month_num}-{str(day).zfill(2)}"


def extract_metadata(url, timeout=30):
    """Extracts YouTube description, thumbnail, channel key, and UPLOAD DATE."""
    if "youtube.com" in url or "youtu.be" in url:
        ydl_opts = {
            "quiet": True, 
            "no_warnings": True, 
            "noplaylist": True,
            "socket_timeout": timeout,  # Network timeout
            "extractor_retries": 1,     # Don't retry forever
            **YT_AGE_BYPASS_OPTS,       # Age-gate bypass
        }
        try:
            from func_timeout import func_timeout, FunctionTimedOut
            
            def _extract():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = func_timeout(timeout, _extract)
            
            channel_key = (
                info.get("channel_id")
                or info.get("uploader_id")
                or ""
            )
            
            # Extract actual upload date (format: YYYYMMDD)
            upload_date_raw = info.get("upload_date")  # e.g., "20110325"
            upload_date = None
            if upload_date_raw and len(upload_date_raw) == 8:
                try:
                    upload_date = f"{upload_date_raw[:4]}-{upload_date_raw[4:6]}-{upload_date_raw[6:8]}"
                    print(f"      📅 YouTube metadata upload_date: {upload_date}")
                except:
                    pass
            
            # FALLBACK: Try parsing date from title/description if no upload_date
            if not upload_date:
                title = info.get("title", "")
                desc = info.get("description", "")
                upload_date = parse_date_from_text(title) or parse_date_from_text(desc)
                if upload_date:
                    print(f"      📅 Parsed date from title/desc: {upload_date}")
                else:
                    print(f"      ⚠️ No upload date found in metadata or title")

            return (
                info.get("description", ""),
                info.get("thumbnail", ""),
                channel_key,
                upload_date,  # Actual upload date (or parsed from title)
            )
        except FunctionTimedOut:
            print(f"      ⏰ TIMEOUT: Metadata extraction took too long for {url[:50]}...")
        except Exception as e:
            print(f"      ❌ Metadata extraction error: {type(e).__name__}: {str(e)[:50]}")
            pass

    return None, None, None, None


# --- HISTORICAL YOUTUBE SEARCH ---
def search_youtube_historical(keywords: list, target_date_str: str, limit: int = 30):
    """
    Search YouTube for historical Syria war content.
    
    REALITY CHECK: YouTube search doesn't support date filtering.
    So we search for era-specific terms and let the AI + metadata extraction
    filter out irrelevant modern content later.
    
    The key is using SPECIFIC historical terms that won't return modern content:
    - "Daraa 2011" instead of just "Syria protest"
    - Channel names that only existed back then (Ugarit News, Shaam News)
    """
    from datetime import datetime
    
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    year = target_date.year
    month = target_date.strftime("%B")  # e.g., "March"
    
    all_items = []
    
    for keyword in keywords[:5]:  # Limit to avoid rate limits
        # Add year to make search more specific
        search_query = f"ytsearch{limit}:{keyword} {year}"
        
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,  # Fast mode - just get URLs
            "skip_download": True,
            "ignoreerrors": True,
            "socket_timeout": 30,
            **YT_AGE_BYPASS_OPTS,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
            if not info or "entries" not in info:
                continue
            
            found_count = 0
            for e in info.get("entries", []):
                if not e:
                    continue
                
                title = e.get("title") or "YouTube video"
                link = e.get("url") or e.get("webpage_url")
                
                # Flat mode gives relative URLs sometimes
                if link and link.startswith("watch?v="):
                    link = "https://www.youtube.com/" + link
                
                if link:
                    all_items.append({
                        "title": title,
                        "link": link,
                    })
                    found_count += 1
                    
            print(f"      🔍 Search '{keyword} {year}': Found {found_count} videos")
            
        except Exception as e:
            print(f"      ⚠️ Search error for '{keyword}': {e}")
            continue
    
    # Deduplicate by URL
    seen = set()
    unique_items = []
    for item in all_items:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique_items.append(item)
    
    print(f"      ✅ Historical search total: {len(unique_items)} unique videos")
    return unique_items


# --- TASK 1: THE SOURCE HUNTER ---

@celery.task(bind=True, max_retries=3)
def ingest_from_source(self, source_id: int, target_date_str: str, war_id: int):
    from models.source import Source

    source = Source.query.get(source_id)
    if not source:
        return "Source not found"

    if source.platform == "youtube":
        try:
            items = _collect_youtube_video_items_for_date(source.handle, target_date_str, limit=80)
        except Exception as e:
            raise self.retry(exc=e, countdown=120)
            
    elif source.platform == "facebook":
        # Jump to mobile loophole
        text, img = scrape_facebook_mobile(source.handle) # We assume handle is a URL for now
        if text:
             items = [{
                 "title": text[:100] + "...", 
                 "link": source.handle, 
                 "summary": text, 
                 "source_url": source.handle,
                 "image": img
             }]
        else:
            items = []
            
    else:
        return f"Platform '{source.platform}' not implemented"

    dispatched = 0
    for it in items:
        it["source_id"] = source_id
        process_event_task.delay(it, war_id, target_date_str)
        dispatched += 1

    try:
        source.last_crawled_at = datetime.utcnow()
        source.total_events_found = (source.total_events_found or 0) + dispatched
        db.session.commit()
    except:
        db.session.rollback()

    return f"✅ YouTube source-first: dispatched={dispatched} for {source.handle} on {target_date_str}"

@celery.task(bind=True, max_retries=3)
def platform_discovery_task(self, platform: str, query: str, war_id: int, date_str: str):
    """
    Google-free discovery.
    Uses platform-native search endpoints.
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
    }

    found = 0

    try:
        if platform == "twitter":
            # Guest-access Twitter search (no Google, no RSS)
            url = "https://twitter.com/i/api/2/search/adaptive.json"
            params = {
                "q": query,
                "count": 20,
                "query_source": "typed_query",
            }

            resp = requests.get(
                url,
                headers=headers,
                params=params,
                impersonate="chrome120",
                timeout=15,
            )

            if resp.status_code != 200:
                raise self.retry(countdown=120)

            data = resp.json()
            tweets = data.get("globalObjects", {}).get("tweets", {})

            for t in tweets.values():
                text = t.get("full_text", "")
                tweet_id = t.get("id_str")
                if not tweet_id:
                    continue

                link = f"https://twitter.com/i/status/{tweet_id}"
                process_event_task.delay(
                    {"title": text[:120], "link": link},
                    war_id,
                    date_str,
                )
                found += 1

        elif platform == "facebook":
            # Public page search (limited but real)
            url = f"https://www.facebook.com/search/top/"
            params = {"q": query}

            resp = stealth_get(url, headers=headers)
            if resp.status_code != 200:
                raise self.retry(countdown=120)

            # FB parsing is HTML-based (intentionally crude)
            # Extract links manually
            for line in resp.text.splitlines():
                if "/videos/" in line or "/posts/" in line:
                    link = "https://www.facebook.com" + line.split('"')[1]
                    process_event_task.delay(
                        {"title": query, "link": link},
                        war_id,
                        date_str,
                    )
                    found += 1

        return f"✅ {platform} discovery: {found} items"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# --- TASK 3: THE VALIDATOR & SOURCE DISCOVERER ---

def scrape_facebook_mobile(url):
    """
    Force the 'basic' mobile version (God-tier for scraping).
    """
    if "facebook.com" not in url:
        # Handle is just "LCCSy" -> transform to URL
        url = f"https://mbasic.facebook.com/{url}"
    elif "https://" not in url: 
        url = f"https://{url}"
        
    mobile_url = url.replace("www.facebook.com", "mbasic.facebook.com").replace("web.facebook.com", "mbasic.facebook.com")
    
    try:
        # Use curl_cffi to look like a real phone
        resp = requests.get(mobile_url, impersonate="chrome120", timeout=15)
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Structure is messy in mbasic, but usually the first div with text is the post
        # Better heuristic: look for <p> tags
        paragraphs = soup.find_all('p')
        post_content = "\n".join([p.get_text() for p in paragraphs])
        
        # Get the raw image (End Product)
        image = soup.find("a", string="View Full Size")
        image_url = image["href"] if image else None
        
        return post_content, image_url
    except Exception as e:
        print(f"FB Error: {e}")
        return None, None

@celery.task(bind=True, max_retries=3)
def process_event_task(self, entry_data, war_id, current_date_str):
    from models.source import Source

    try:
        url = entry_data["link"]
        title = entry_data["title"]
        source_id = entry_data.get("source_id")  # <-- NEW

        description, thumbnail, channel_or_uploader, actual_upload_date = extract_metadata(url)
        
        # USE THE ACTUAL UPLOAD DATE if available, otherwise fall back to current_date_str
        event_date_str = actual_upload_date if actual_upload_date else current_date_str
        
        # Log when we have to use fallback date (indicates metadata extraction failed)
        if not actual_upload_date:
            # LAST RESORT: Try to parse date from the search result title
            parsed_from_title = parse_date_from_text(title)
            if parsed_from_title:
                event_date_str = parsed_from_title
                print(f"      📅 Parsed date from search title: {parsed_from_title}")
            else:
                print(f"      ⚠️ Using fallback date: {current_date_str} (no upload date from metadata or title)")
        
        # === YEAR FILTER: Skip videos from wrong era ===
        # If we're trying to ingest 2011 content, reject 2025/2026 uploads
        try:
            target_year = int(current_date_str[:4])
            actual_year = int(event_date_str[:4]) if event_date_str else target_year
            
            # Allow some flexibility: target year +/- 2 years for documentaries
            # But reject anything from 2020+ when ingesting 2011-2015
            if target_year <= 2015 and actual_year >= 2020:
                print(f"      🚫 YEAR FILTER: Skipping {actual_year} video (wanted {target_year} era)")
                return "🗑️ Wrong Era"
        except:
            pass
        
        # Log when dates differ (helps debug)
        if actual_upload_date and actual_upload_date != current_date_str:
            print(f"      📅 Date corrected: {current_date_str} → {actual_upload_date}")
        
        full_context = f"{title}\nDescription: {description[:500]}" if description else title

        if not ask_brain:
            return "❌ AI Brain Offline"

        intel = ask_brain(full_context, url)
        if not intel or not intel.get("relevant"):
            # Part B: count rejection (if we know source)
            if source_id:
                update_source_reliability(source_id, event_date_str, saved=False, evidence_score=0)
            return "🗑️ Rejected"

        save_success = save_event(
            war_id=war_id,
            title=intel.get("summary", title),
            summary=description if description else title,
            locations=intel.get("locations", []),
            date_obj=datetime.strptime(event_date_str, "%Y-%m-%d").date(),
            url=url,
            is_capture=intel.get("captured", False),
            victor=intel.get("victor"),
            category=intel.get("category", "SOCIAL"),
            img_url=thumbnail,
            evidence_score=intel.get("evidence_score", 5),
            dup_key=intel.get("key"),
        )
        
        # --- NEW: Readable Ledger ---
        try:
            if save_success:
                with open("accepted_events.md", "a", encoding="utf-8") as f:
                    f.write(f"## Date: {event_date_str}\n")
                    f.write(f"- **Title**: {intel.get('summary', title)}\n")
                    f.write(f"- **Published By**: {channel_or_uploader or 'Unknown'}\n")
                    f.write(f"- **Upload Date**: {event_date_str}\n")
                    f.write(f"- **URL**: {url}\n")
                    f.write(f"---\n\n")
        except: pass
        # ----------------------------

        # Part B: update reliability based on whether it actually saved
        if source_id:
            update_source_reliability(
                source_id,
                current_date_str,
                saved=bool(save_success),
                evidence_score=intel.get("evidence_score", 5),
            )

        # Auto-source discovery (YouTube only)
        if save_success and channel_or_uploader:
            existing = Source.query.filter_by(platform="youtube", handle=channel_or_uploader).first()
            if not existing:
                new_src = Source(platform="youtube", handle=channel_or_uploader, name=channel_or_uploader, status="probation")
                db.session.add(new_src)
                db.session.commit()
                print(f"      📡 SOURCE DISCOVERED: Added {channel_or_uploader}")

        return "🏆 SUCCESS"

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ==================== TERRITORY MANAGEMENT TASKS ====================

@celery.task(bind=True)
def create_daily_territory_snapshots(self, war_id: int = None, snapshot_date: str = None):
    """
    Creates daily territory snapshots for all factions.
    This preserves the map state for each day, allowing historical playback.
    
    Args:
        war_id: Specific war to snapshot, or None for all wars
        snapshot_date: Date string (YYYY-MM-DD), or None for today
    
    This task should be run daily via Celery Beat or cron.
    """
    from models.war import War
    from models.faction import Faction, TerritorySnapshot
    from datetime import date
    
    target_date = date.fromisoformat(snapshot_date) if snapshot_date else date.today()
    
    # Get wars to process
    if war_id:
        wars = War.query.filter_by(id=war_id).all()
    else:
        wars = War.query.all()
    
    results = []
    
    for war in wars:
        factions = Faction.query.filter_by(war_id=war.id).all()
        
        for faction in factions:
            # Check if snapshot already exists for this date
            existing = TerritorySnapshot.query.filter_by(
                faction_id=faction.id,
                effective_date=target_date
            ).first()
            
            if existing:
                print(f"  ⏭️ Snapshot already exists for {faction.name} on {target_date}")
                continue
            
            # Only create snapshot if faction has territory
            if not faction.territory_geojson:
                print(f"  ⚠️ No territory for {faction.name}, skipping")
                continue
            
            # Create new snapshot from current territory
            snapshot = TerritorySnapshot(
                faction_id=faction.id,
                effective_date=target_date,
                territory_geojson=faction.territory_geojson,
                source="daily_snapshot",
                notes=f"Automatic daily snapshot for {target_date.isoformat()}"
            )
            
            db.session.add(snapshot)
            results.append({
                "war": war.name,
                "faction": faction.name,
                "date": target_date.isoformat(),
                "status": "created"
            })
            print(f"  ✅ Created snapshot for {faction.name} ({war.name}) on {target_date}")
    
    db.session.commit()
    
    print(f"\n📸 TERRITORY SNAPSHOT COMPLETE: Created {len(results)} snapshots for {target_date}")
    return {"date": target_date.isoformat(), "snapshots": results}


@celery.task(bind=True)
def get_territory_for_date(self, war_id: int, target_date: str):
    """
    Retrieves the territory map state for a specific date.
    
    Returns the most recent snapshot on or before the target date for each faction.
    This allows viewing historical maps.
    """
    from models.war import War
    from models.faction import Faction, TerritorySnapshot
    from datetime import date
    
    query_date = date.fromisoformat(target_date)
    
    war = War.query.get(war_id)
    if not war:
        return {"error": f"War {war_id} not found"}
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    
    result = {
        "war_id": war_id,
        "war_name": war.name,
        "date": target_date,
        "factions": []
    }
    
    for faction in factions:
        # Get the most recent snapshot on or before target date
        snapshot = TerritorySnapshot.query.filter(
            TerritorySnapshot.faction_id == faction.id,
            TerritorySnapshot.effective_date <= query_date
        ).order_by(TerritorySnapshot.effective_date.desc()).first()
        
        faction_data = {
            "id": faction.id,
            "name": faction.name,
            "color": faction.color,
            "territory_geojson": None,
            "snapshot_date": None,
            "source": None
        }
        
        if snapshot:
            faction_data["territory_geojson"] = snapshot.territory_geojson
            faction_data["snapshot_date"] = snapshot.effective_date.isoformat()
            faction_data["source"] = snapshot.source
        elif faction.territory_geojson:
            # Fall back to current territory if no historical snapshot
            faction_data["territory_geojson"] = faction.territory_geojson
            faction_data["snapshot_date"] = "current"
            faction_data["source"] = "live"
        
        result["factions"].append(faction_data)
    
    return result


@celery.task(bind=True)
def cleanup_old_snapshots(self, days_to_keep: int = 365, war_id: int = None):
    """
    Cleans up old territory snapshots to prevent database bloat.
    Keeps one snapshot per week for data older than days_to_keep.
    
    Args:
        days_to_keep: Number of days to keep daily snapshots (default 365)
        war_id: Specific war to clean, or None for all
    """
    from models.faction import Faction, TerritorySnapshot
    from datetime import date, timedelta
    from sqlalchemy import func
    
    cutoff_date = date.today() - timedelta(days=days_to_keep)
    
    # Get all factions
    query = Faction.query
    if war_id:
        query = query.filter_by(war_id=war_id)
    factions = query.all()
    
    deleted_count = 0
    
    for faction in factions:
        # Get old snapshots grouped by week
        old_snapshots = TerritorySnapshot.query.filter(
            TerritorySnapshot.faction_id == faction.id,
            TerritorySnapshot.effective_date < cutoff_date
        ).order_by(TerritorySnapshot.effective_date).all()
        
        # Group by week and keep only one per week
        weeks = {}
        for snap in old_snapshots:
            week_key = snap.effective_date.isocalendar()[:2]  # (year, week)
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(snap)
        
        # For each week, keep the first snapshot and delete the rest
        for week_key, snaps in weeks.items():
            if len(snaps) > 1:
                for snap_to_delete in snaps[1:]:
                    db.session.delete(snap_to_delete)
                    deleted_count += 1
    
    db.session.commit()
    print(f"🧹 Cleaned up {deleted_count} old territory snapshots")
    return {"deleted": deleted_count}


def get_faction_territory_on_date(faction_id: int, query_date: date):
    """
    Helper function to get territory GeoJSON for a faction on a specific date.
    Can be used by other parts of the app (ingest, AI, etc.)
    
    Returns:
        str: GeoJSON string or None
    """
    from models.faction import Faction, TerritorySnapshot
    
    # Try to get historical snapshot first
    snapshot = TerritorySnapshot.query.filter(
        TerritorySnapshot.faction_id == faction_id,
        TerritorySnapshot.effective_date <= query_date
    ).order_by(TerritorySnapshot.effective_date.desc()).first()
    
    if snapshot:
        return snapshot.territory_geojson
    
    # Fall back to current territory
    faction = Faction.query.get(faction_id)
    if faction:
        return faction.territory_geojson
    
    return None


def get_all_territories_for_war(war_id: int, query_date: date = None):
    """
    Get all faction territories for a war on a specific date.
    Used by map display and ingest processes.
    
    Returns:
        dict: {faction_id: {"name": str, "color": str, "geojson": str}}
    """
    from models.faction import Faction
    from datetime import date as date_type
    
    if query_date is None:
        query_date = date_type.today()
    
    factions = Faction.query.filter_by(war_id=war_id).all()
    
    result = {}
    for faction in factions:
        geojson = get_faction_territory_on_date(faction.id, query_date)
        result[faction.id] = {
            "name": faction.name,
            "short_name": faction.short_name,
            "color": faction.color,
            "geojson": geojson
        }
    
    return result