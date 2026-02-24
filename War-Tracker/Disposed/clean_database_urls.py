from app import create_app
from extensions import db
from models.event import Event
import urllib.parse

import requests

def clean_google_url(url):
    """Unwraps google.com/url?q=... AND resolves news.google.com redirects"""
    # 1. Standard Google Redirect (URL params)
    if "google.com/url" in url or "url?q=" in url:
        try:
            parsed = urllib.parse.urlparse(url)
            q_params = urllib.parse.parse_qs(parsed.query)
            if 'q' in q_params:
                return q_params['q'][0]
            if 'url' in q_params:
                return q_params['url'][0]
        except:
            pass
            
    # 2. Google News Opaque Redirect (Resolver)
    if "news.google.com" in url or "google.com" in url:
        try:
            # We must follow the redirect to get the real link
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            
            # HEAD request often fails on Google, so prioritized GET if HEAD fails check
            resp = requests.head(url, headers=headers, allow_redirects=True, timeout=5)
            
            final_url = resp.url
            if resp.status_code != 200 or "google.com" in final_url:
                 # Try GET
                 resp = requests.get(url, headers=headers, allow_redirects=True, timeout=5)
                 final_url = resp.url
                 
            if "google.com" not in final_url:
                print(f"   Resolved: {url[:30]}... -> {final_url[:30]}...")
                return final_url
        except Exception as e:
            print(f"   Resolution failed: {e}")
            
    return url

app = create_app()
with app.app_context():
    # Find candidates
    dirty_events = Event.query.filter(Event.source_url.like('%google.com%')).all()
    print(f"Found {len(dirty_events)} potentially dirty URLs.")
    
    count = 0
    for e in dirty_events:
        clean = clean_google_url(e.source_url)
        if clean != e.source_url:
            print(f"Cleaning: {e.source_url[:30]}... -> {clean[:30]}...")
            e.source_url = clean
            
            # Also fix video_url if it matches
            if e.video_url and "google.com" in e.video_url:
                e.video_url = clean_google_url(e.video_url)
                
            # Attempt to fix thumbnail if it was broken
            if "youtube.com" in clean or "youtu.be" in clean:
                try:
                    video_id = ""
                    if "v=" in clean: video_id = clean.split("v=")[1].split("&")[0]
                    elif "youtu.be" in clean: video_id = clean.split("/")[-1]
                    if video_id:
                        e.image_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
                except: pass
                
            count += 1
            
    if count > 0:
        db.session.commit()
        print(f"✅ Successfully cleaned {count} events.")
    else:
        print("db is already clean.")
