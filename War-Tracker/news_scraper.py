"""
Google News RSS Scraper for Syria War Events
Scrapes Google News RSS feeds for Syria-related keywords
Discovers sources automatically and tracks reliability
"""

import feedparser
import requests
from datetime import datetime, timedelta
from urllib.parse import quote_plus

# Syria War Keywords - Combat, Political, Humanitarian
SYRIA_KEYWORDS = [
    "Syria combat",
    "Syria offensive",
    "Syria airstrike",
    "Syria rebel",
    "Syria army",
    "Syria Assad",
    "Syria protest",
    "Syria Damascus",
    "Syria Aleppo",
    "Syria Idlib",
    "Syria Homs",
    "Syria ceasefire",
    "Syria humanitarian",
    "Syria refugees",
]

def scrape_google_news_rss(keyword, max_results=20):
    """
    Scrape Google News RSS for a specific keyword.
    Returns list of articles: [{"title": ..., "link": ..., "published": ..., "source": ...}]
    """
    try:
        # Google News RSS URL
        encoded_keyword = quote_plus(keyword)
        rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=en-US&gl=US&ceid=US:en"
        
        # Parse RSS feed
        feed = feedparser.parse(rss_url)
        
        articles = []
        for entry in feed.entries[:max_results]:
            # Extract source from title (format: "Title - Source")
            title = entry.get("title", "")
            source_name = "Unknown"
            if " - " in title:
                title, source_name = title.rsplit(" - ", 1)
            
            articles.append({
                "title": title,
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "source": source_name,
                "description": entry.get("summary", ""),
            })
        
        return articles
        
    except Exception as e:
        print(f"   ❌ RSS Error for '{keyword}': {e}")
        return []


def ingest_news_for_date(war_id, target_date_str):
    """
    Scrape Google News for Syria keywords and dispatch to Celery.
    This is the news-based replacement for schedule_source_crawls.
    """
    from tasks import process_event_task
    
    print(f"   📰 Scraping Google News for: {target_date_str}")
    
    all_articles = []
    for keyword in SYRIA_KEYWORDS:
        articles = scrape_google_news_rss(keyword, max_results=10)
        all_articles.extend(articles)
        print(f"      - {keyword}: {len(articles)} articles")
    
    # Deduplicate by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        if article["link"] not in seen_urls:
            seen_urls.add(article["link"])
            unique_articles.append(article)
    
    print(f"   ✅ Found {len(unique_articles)} unique articles")
    
    # Dispatch to Celery
    dispatched = 0
    for article in unique_articles:
        # Auto-discover source (extract domain from URL)
        from urllib.parse import urlparse
        parsed = urlparse(article["link"])
        source_domain = parsed.netloc
        
        # Dispatch to process_event_task
        process_event_task.delay(
            war_id=war_id,
            title=article["title"],
            url=article["link"],
            description=article["description"],
            current_date_str=target_date_str,
            thumbnail=None,
            channel_or_uploader=article["source"],
            source_id=None,  # Will be auto-discovered
        )
        dispatched += 1
    
    print(f"   ✅ Dispatched {dispatched} articles for AI filtering")
    return dispatched
