import urllib.parse
import requests
import feedparser
import time
from datetime import datetime
from tasks import process_event_task

import random

# Specific targets for "Real Footage"
SOCIAL_PLATFORMS = [
    "youtube.com", 
    "twitter.com", 
    "facebook.com",
    "liveleak.com" # Historical footage often ended up here
]

ACTIVIST_GROUPS = [
    "Ugarit News", "Shaam News Network", "SNN", "LCC Syria", 
    "VDC Syria", "Flash News Network", "Syrian Revolution", 
    "تنسيقية", "شبكة شام", "أوغاريت"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15"
]

def ingest_social_archive(war_id, start_date, end_date, locations):
    """
    Specifically targets raw footage and social reports.
    Uses Google Search Index as a proxy to find archived social links.
    """
    total_queued = 0
    
    # Powerful Dorks to find footage
    FOOTAGE_KEYWORDS = [
        "footage", "protest", "clash", "shooting", 
        "demonstration", "raw", "video", "shabiha"
    ]
    # Merge activist groups into keywords for maximum coverage
    FOOTAGE_KEYWORDS.extend(ACTIVIST_GROUPS)

    for loc in locations:
        for keyword in FOOTAGE_KEYWORDS:
            # We treat all platforms as a single query to save requests if possible, 
            # BUT the user requested specifics. Let's do a combined site: OR query to be efficient
            # otherwise 192 queries/day will ban us instantly.
            # Strategy: site:youtube.com OR site:twitter.com ...
            


            headers = {'User-Agent': random.choice(USER_AGENTS)}

            platforms_dork = " OR ".join([f"site:{p}" for p in SOCIAL_PLATFORMS])
            query = f'({platforms_dork}) "{loc}" {keyword}'
            
            # Friday Logic (3. Fixing the "0 Tasks" on Friday Protests)
            try:
                date_obj = datetime.strptime(start_date, "%Y-%m-%d")
                if date_obj.weekday() == 4: # Friday
                    query = f'site:youtube.com "سوريا" "جمعة" "{loc}"'
            except: pass

            raw_query = f"{query} after:{start_date} before:{end_date}"
            
            # We use the Google Search RSS feed (most stable way to get URLs)
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(raw_query)}&hl=en-US&gl=US&ceid=US:en"
            
            try:
                # Slight delay to avoid hammering
                time.sleep(1.0) 
                
                # Retry logic for robustness
                resp = None
                for attempt in range(2):
                    try:
                        resp = requests.get(rss_url, headers=headers, timeout=15)
                        if resp.status_code == 200:
                            break
                    except requests.exceptions.RequestException:
                        time.sleep(2)
                        continue
                
                if not resp or resp.status_code != 200:
                    continue

                feed = feedparser.parse(resp.content)
                
                if not feed.entries:
                    continue
                
                print(f"      🔎 Found {len(feed.entries)} raw links for {loc} + {keyword}")

                for entry in feed.entries:
                    # Dispatch to worker
                    # The worker will handle 'translating' these URLs into actual data
                    process_event_task.delay(
                        {'title': entry.title, 'link': entry.link}, 
                        war_id, 
                        start_date
                    )
                    total_queued += 1
            except Exception as e:
                print(f"      ⚠️ Social Ingest Error ({loc}): {e}")
                continue 
                    
    return total_queued
