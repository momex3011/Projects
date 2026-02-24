import requests
import json
import time
import random
import sys
import urllib.parse
from datetime import datetime
from dateutil import parser as date_parser

# App Imports
from app import create_app
from extensions import db
from models.event import Event
from models.war import War
from data_locations import SYRIA_LOCATIONS, ARABIC_LOCATIONS

# --- CONFIG ---
WAR_NAME = "Syria"
ACCOUNTS_FILE = "twitter_accounts.json"
# SearchTimeline Query ID (Rotates occasionally, verified working Dec 2025)
QUERY_ID = "nK1dw4oV3k4w5TdtcAdSww" 

# Keywords from ingest.py (Arabic + English subset)
# MAX INGESTION: Broad terms requested
KEYWORDS = [
    '"Syria"', '"Syrian"', '"Damascus"', '"Aleppo"', '"Idlib"',
    '"Syria clash"', '"Syria shelling"', '"Syria explosion"',
    '"مظاهرات سوريا"', '"اشتباكات سوريا"', '"قصف سوريا"', 
    '"انشقاق جيش"', '"الجيش الحر"', '"مجزرة سوريا"',
    '"سوريا"', '"دمشق"', '"حلب"', '"إدلب"', '"درعا"'
]

class TwitterClient:
    def __init__(self):
        self.accounts = self.load_accounts()
        self.current_index = 0
        self.session = requests.Session()
    
    def load_accounts(self):
        try:
            with open(ACCOUNTS_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading {ACCOUNTS_FILE}: {e}")
            sys.exit(1)

    def get_current_account(self):
        return self.accounts[self.current_index]

    def rotate_account(self):
        self.current_index = (self.current_index + 1) % len(self.accounts)
        print(f"   🔄 Rotating to account #{self.current_index + 1}: {self.get_current_account()['username']}")
        time.sleep(2) # Brief cooldown

    def get_headers(self):
        acc = self.get_current_account()
        return {
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "x-csrf-token": acc["ct0"],
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "en",
            "x-twitter-active-user": "yes",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": f"auth_token={acc['auth_token']}; ct0={acc['ct0']}"
        }

    def search_graphql(self, query, cursor=None):
        url = f"https://twitter.com/i/api/graphql/{QUERY_ID}/SearchTimeline"
        
        variables = {
            "rawQuery": query,
            "count": 20,
            "querySource": "typed_query",
            "product": "Top"
        }
        if cursor: variables["cursor"] = cursor

        features = {
            "responsive_web_graphql_exclude_directive_enabled": True,
            "verified_phone_label_enabled": False,
            "creator_subscriptions_tweet_preview_api_enabled": True,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "view_counts_everywhere_api_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "responsive_web_twitter_article_tweet_consumption_enabled": False,
            "tweet_awards_web_tipping_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": True,
            "standardized_nudges_misinfo": True,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "responsive_web_media_download_video_enabled": False,
            "responsive_web_enhance_cards_enabled": False
        }

        max_global_attempts = len(self.accounts)
        if max_global_attempts == 1: max_global_attempts = 5 # Allow retries for single account

        attempts = 0
        while attempts < max_global_attempts:
            try:
                headers = self.get_headers()
                resp = self.session.get(url, headers=headers, params={
                    "variables": json.dumps(variables),
                    "features": json.dumps(features)
                }, timeout=10)

                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    print(f"      ⚠️ Rate Limit (429). Sleeping 30s...")
                    time.sleep(30)
                    if len(self.accounts) > 1:
                        self.rotate_account()
                    # If single account, just loop again (retry)
                    attempts += 1
                elif resp.status_code in [401, 403]:
                    print(f"      ⚠️ Auth Error ({resp.status_code}). Rotating...")
                    self.rotate_account()
                    attempts += 1
                else:
                    print(f"      ❌ API Error: {resp.status_code} | {resp.text[:100]}")
                    return None
            except Exception as e:
                print(f"      ❌ Connection Error: {e}")
                self.rotate_account()
                attempts += 1
        
        print("      ❌ All accounts failed.")
        return None

def parse_tweets(data):
    tweets = []
    try:
        # Navigate complex GraphQL response
        instructions = data['data']['search_by_raw_query']['search_timeline']['timeline']['instructions']
        entries = []
        for i in instructions:
            if i['type'] == 'TimelineAddEntries':
                entries = i['entries']
                break
        
        for entry in entries:
            try:
                if 'tweet' not in entry['entryId']: continue
                result = entry['content']['itemContent']['tweet_results']['result']
                
                # Handle retweets/quotes sometimes wrapped differently
                if 'tweet' in result: result = result['tweet']
                
                legacy = result['legacy']
                user = result['core']['user_results']['result']['legacy']
                
                # Basic Data
                tweet_id = legacy['id_str']
                text = legacy['full_text']
                date_str = legacy['created_at'] # "Sun Dec 22 19:48:00 +0000 2025"
                screen_name = user['screen_name']
                
                # Media
                img = None
                if 'entities' in legacy and 'media' in legacy['entities']:
                    img = legacy['entities']['media'][0]['media_url_https']

                tweets.append({
                    'id': tweet_id,
                    'text': text,
                    'user': screen_name,
                    'date': date_parser.parse(date_str),
                    'link': f"https://twitter.com/{screen_name}/status/{tweet_id}",
                    'img': img
                })
            except KeyError:
                continue # Skip promo tweets or malformed entries
    except Exception as e:
        print(f"      ⚠️ Parse Error: {e}")
    
    return tweets

def geocode_simple(text):
    # Reuse valid locations logic simply
    text_lower = text.lower()
    
    # Check English
    for loc, coords in SYRIA_LOCATIONS.items():
        if loc.lower() in text_lower:
            return coords[0], coords[1]
    
    # Check Arabic
    for arabic, english in ARABIC_LOCATIONS.items():
        if arabic in text_lower:
            if english in SYRIA_LOCATIONS:
                return SYRIA_LOCATIONS[english]
            
    # Default Fallback (Damascus-ish)
    return 33.5138 + random.uniform(-0.1, 0.1), 36.2765 + random.uniform(-0.1, 0.1)

def ingest_twitter(war_id, start_date=None, end_date=None):
    client = TwitterClient()
    
    # Date logic
    date_query_part = ""
    if start_date and end_date:
        date_query_part = f" since:{start_date} until:{end_date}"
    
    total_saved = 0
    
    for term in KEYWORDS:
        # print(f"      🐦 Searching: {term} {date_query_part} ...")
        
        query = f"{term}{date_query_part}"
        
        data = client.search_graphql(query)
        if not data: 
            print("      ⚠️ All accounts failed. Skipping remaining keywords.")
            break # Stop trying other keywords if we can't search at all
        
        tweets = parse_tweets(data)
        if not tweets: continue
        # print(f"      found {len(tweets)} raw tweets.")
        
        count = 0
        for t in tweets:
            # check exists
            exists = Event.query.filter(Event.source_url == t['link']).first()
            if exists: continue
            
            lat, lng = geocode_simple(t['text'])
            
            # Create Event
            ev_title = f"@{t['user']}: {t['text'][:50]}..."
            
            event = Event(
                war_id=war_id,
                title=ev_title,
                description=t['text'],
                event_date=t['date'],
                lat=lat, lng=lng,
                source_url=t['link'],
                image_url=t['img']
            )
            # Default category/faction
            event.category = "SOCIAL" 
            
            db.session.add(event)
            count += 1
        
        db.session.commit()
        if count > 0:
            print(f"      ✅ SAVED (Twitter): {count} new tweets for '{term}'")
        total_saved += count
        time.sleep(1) # Fast pace

    return total_saved

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        war = War.query.filter_by(name=WAR_NAME).first()
        if war:
            ingest_twitter(war.id)
        else:
            print(f"War '{WAR_NAME}' not found.")
