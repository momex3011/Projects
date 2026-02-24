import google.generativeai as genai
import requests
import json
import re
import os
from dotenv import load_dotenv
import time
from newspaper import Article, Config
from bs4 import BeautifulSoup
from func_timeout import func_timeout, FunctionTimedOut
from youtube_transcript_api import YouTubeTranscriptApi
from extensions import db
import redis

# === REDIS RATE LIMITER ===
# Ensures only 1 AI call every 2 seconds across ALL Celery workers
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    redis_client = None
    REDIS_AVAILABLE = False
    print("   ⚠️ Redis not available for rate limiting")

def acquire_ai_lock(timeout=60):
    """Acquire a distributed lock for AI calls. Returns True if acquired."""
    if not REDIS_AVAILABLE:
        return True
    
    lock_key = "ai_rate_lock"
    # Try to acquire lock with 2 second minimum gap
    for _ in range(timeout * 2):  # Check every 0.5s
        # SETNX returns True if key didn't exist (we got the lock)
        if redis_client.set(lock_key, "1", nx=True, ex=3):
            return True
        # Check how long until we can retry
        ttl = redis_client.ttl(lock_key)
        if ttl > 0:
            time.sleep(min(ttl, 0.5))
        else:
            time.sleep(0.5)
    return False

def release_ai_lock():
    """Release the AI lock after a delay to enforce rate limit."""
    if REDIS_AVAILABLE:
        # Keep lock for 2 more seconds to enforce rate limit
        redis_client.expire("ai_rate_lock", 2)


load_dotenv("APIs.env") 
GRAD_API_KEY = os.getenv("GRAD_API_KEY")
OLLAMA_URL   = os.getenv("OLLAMA_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GRAD_API_KEY or not GROQ_API_KEY:
    raise RuntimeError("API keys not loaded")

try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("   🚀 Groq Client Initialized (Llama 3.3 Speed Mode)")
except ImportError:
    groq_client = None
    print("   ⚠️ Groq not found, falling back to slow mode.")

try:
    genai.configure(api_key=GRAD_API_KEY)
except: pass

def clean_json_response(text):
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1]
            
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except: pass
    return None

def try_groq_brain(prompt):
    """The Speedster (Llama 3.3 on Groq)"""
    if not groq_client: return None
    
    # Retry up to 3 times with longer exponential backoff
    # Groq rate limit window is ~60 seconds
    for attempt in range(3):
        try:
            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[
                    {"role": "system", "content": "You are a Professional War Intelligence API. You output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1024,
                response_format={"type": "json_object"} 
            )
            return clean_json_response(completion.choices[0].message.content)
        except Exception as e:
            if "429" in str(e):
                wait_time = 20 * (attempt + 1)  # 20s, 40s, 60s
                print(f"      ⏳ Groq 429, retry {attempt+1}/3 in {wait_time}s...")
                time.sleep(wait_time)
                continue
            print(f"      ⚠️ Groq Error: {e}")
            return None
    
    print(f"      ❌ Groq failed after 3 retries, trying Gemini...")
    return None

def try_google_brain(prompt):
    """The Heavyweight (Gemini 2.0) - Fallback when Groq is rate limited"""
    model_name = 'models/gemini-2.0-flash'
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        if response.text:
            result = clean_json_response(response.text)
            if result:
                print(f"      ✅ Gemini success (Groq fallback)")
            return result
    except Exception as e:
        print(f"      ⚠️ Gemini Error: {e}")
    return None
    return None

def try_local_brain(prompt):
    """The Backup (Ollama)"""
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }, timeout=30)
        if response.status_code == 200:
            return json.loads(response.json()['response'])
    except Exception as e:
        if "HTTPConnectionPool" not in str(e):
             print(f"      ⚠️ Local Brain Error: {e}")
    return None

def _get_article_data(title, url):
    """Extracts raw metadata from the source link for the AI to analyze."""
    text_to_analyze = title
    image_url = None
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    if not url: return text_to_analyze, None

    try:
        if "youtube.com" in url or "youtu.be" in url:
            video_id = ""
            if "v=" in url: video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be" in url: video_id = url.split("/")[-1].split("?")[0]
            
            # FIXED: Correct YouTube Thumbnail URL
            image_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            
            try:
                ts = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = " ".join([t['text'] for t in ts[:60]]) 
                text_to_analyze = f"TITLE: {title}\nTRANSCRIPT: {transcript_text}"
            except: 
                r = requests.get(url, headers=headers, timeout=5)
                soup = BeautifulSoup(r.content, 'html.parser')
                desc_meta = soup.find("meta", property="og:description")
                if desc_meta: text_to_analyze = f"TITLE: {title}\nDESC: {desc_meta['content']}"

        else:
            config = Config()
            config.request_timeout = 5
            article = Article(url, config=config)
            article.download()
            article.parse()
            text_to_analyze = f"{title}\n\n{article.text[:1200]}"
            image_url = article.top_image
    except: pass
            
    return text_to_analyze, image_url

def _unsafe_ask_brain(title, url):
    text, img = title, None
    try:
        text, img = func_timeout(15, _get_article_data, args=(title, url))
    except: pass

    prompt = f"""
    You are a Professional War Analyst covering the 2011 Syrian Revolution.
    DATA: "{text}"
    
    IMPORTANT INSTRUCTIONS:
    1. locations: List ALL distinct geographic locations mentioned (cities, neighborhoods, towns). If fighting spans multiple areas, list each one.
    2. captured: TRUE if territory control changed hands (one side took/seized/captured an area from another)
    3. For clashes/battles where control is contested but not captured, captured=false
    
    RETURN JSON ONLY:
    {{ 
      "relevant": bool, 
      "category": "COMBAT|CLASH|POLITICAL|CASUALTIES|PROTEST", 
      "locations": ["Location1, City1", "Location2, City2"], 
      "captured": bool, 
      "victor": "Government|Rebel|ISIS|SDF|None", 
      "summary": "Concise journalistic sentence", 
      "evidence_score": 1-10, 
      "key": "unique_semantic_key" 
    }}
    """

    data = try_groq_brain(prompt)
    if not data: data = try_google_brain(prompt)
    if not data: data = try_local_brain(prompt)

    if data:
        data['image'] = img
        if data.get('locations'): data['location'] = data['locations'][0]
        return data
    return None

def ask_brain(title, url=None):
    print(f"   🤖 AI Analyzing: {title[:40]}...")
    
    # DISTRIBUTED RATE LIMIT: Only 1 AI call every 2 seconds across all workers
    # This prevents 429 errors when multiple Celery tasks run in parallel
    if not acquire_ai_lock(timeout=120):  # Wait up to 2 minutes for lock
        print("   ⏳ Timeout waiting for AI rate limit lock")
        return None
    
    try:
        result = func_timeout(45, _unsafe_ask_brain, args=(title, url))
        return result
    except FunctionTimedOut:
        print("   ⏳ AI Timed Out")
    except Exception as e:
        print(f"   ❌ AI Agent Error: {e}")
    finally:
        release_ai_lock()  # Ensure lock is released with 2s delay
    return None

def auto_update_territory(lat, lng, faction, radius=0.15):
    """
    Physically changes the controller of map points around an event.
    This allows the map to 'evolve' without human intervention.
    """
    from models.location import Location
    try:
        # Find all map points within the conflict radius
        points = Location.query.filter(
            Location.lat.between(lat - radius, lat + radius),
            Location.lng.between(lng - radius, lng + radius)
        ).all()

        for p in points:
            p.controller = faction # e.g., "Rebel Control"
        
        db.session.commit()
        print(f"      🖌️ PAINTED: Updated territory around {lat}, {lng} to {faction}")
    except Exception as e:
        db.session.rollback()
        print(f"      ⚠️ Territory Update Failed: {e}")


def update_faction_territory_from_event(event_id, war_id, lat, lng, victor, event_summary=""):
    """
    Creates a territory snapshot when AI detects a capture event.
    This allows automatic territory updates based on news.
    
    Args:
        event_id: The event that triggered this change
        war_id: The war this territory belongs to
        lat, lng: Approximate location of the capture
        victor: Who captured it (e.g., "Government", "Rebel", "SDF")
        event_summary: Description for the snapshot notes
    """
    from models.faction import Faction, TerritorySnapshot
    from datetime import date
    import json
    
    try:
        # Map victor names to faction short names
        victor_map = {
            "Government": ["GOV", "SAA", "Syrian Government", "Assad"],
            "Rebel": ["REB", "FSA", "Rebels", "Opposition", "HTS"],
            "SDF": ["SDF", "Kurdish", "YPG"],
            "ISIS": ["ISIS", "IS", "ISIL", "Daesh"],
            "Turkey": ["TUR", "TSK", "Turkish"]
        }
        
        # Find matching faction
        faction = None
        for key, aliases in victor_map.items():
            if victor in aliases or victor == key:
                faction = Faction.query.filter(
                    Faction.war_id == war_id,
                    db.or_(
                        Faction.short_name.in_(aliases),
                        Faction.name.ilike(f"%{key}%")
                    )
                ).first()
                break
        
        if not faction:
            print(f"      ⚠️ Faction not found for victor: {victor}")
            return False
        
        # Check if faction already has territory containing this point
        # If so, we might need to expand it
        current_territory = json.loads(faction.territory_geojson) if faction.territory_geojson else None
        
        # Create a small buffer polygon around the capture point
        # This represents the approximate area captured
        buffer_radius = 0.05  # ~5km radius
        new_polygon = {
            "type": "Feature",
            "properties": {"source": "ai_capture"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [lng - buffer_radius, lat - buffer_radius],
                    [lng + buffer_radius, lat - buffer_radius],
                    [lng + buffer_radius, lat + buffer_radius],
                    [lng - buffer_radius, lat + buffer_radius],
                    [lng - buffer_radius, lat - buffer_radius]
                ]]
            }
        }
        
        # If faction has existing territory, add to it
        if current_territory and current_territory.get('features'):
            current_territory['features'].append(new_polygon)
            new_geojson = current_territory
        else:
            new_geojson = {
                "type": "FeatureCollection",
                "features": [new_polygon]
            }
        
        # Create snapshot
        snapshot = TerritorySnapshot(
            faction_id=faction.id,
            effective_date=date.today(),
            is_permanent=True,
            territory_geojson=json.dumps(new_geojson),
            source="ai_ingest",
            source_event_id=event_id,
            notes=f"AI-detected capture: {event_summary[:100]}"
        )
        db.session.add(snapshot)
        
        # Update faction's current territory
        faction.territory_geojson = json.dumps(new_geojson)
        
        db.session.commit()
        print(f"      🗺️ AI TERRITORY: Added capture zone for {faction.name} at {lat:.4f}, {lng:.4f}")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"      ⚠️ AI Territory Update Failed: {e}")
        return False


def get_ai_coordinates(location_name, context_text):
    """
    Asks the AI to estimate coordinates for specific neighborhoods.
    """
    prompt = f"Find the Latitude and Longitude for '{location_name}' in Syria. Context: {context_text}. Return JSON: {{\"lat\": float, \"lng\": float}}"
    data = try_groq_brain(prompt)
    if data and 'lat' in data:
        return data['lat'], data['lng']
    return None, None