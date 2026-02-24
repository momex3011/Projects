
import requests
import sqlite3
import time

def unwrap_url(url):
    try:
        print(f"Unwrapping: {url[:50]}...")
        # Google news links often need a user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response Content Preview: {response.text[:500]}")
        return response.url
    except Exception as e:
        print(f"Error: {e}")
        return None

conn = sqlite3.connect('wartracker.db')
cursor = conn.cursor()

cursor.execute("SELECT id, video_url FROM events WHERE video_url LIKE '%news.google.com%' LIMIT 1")
row = cursor.fetchone()

if row:
    original_url = row[1]
    final_url = unwrap_url(original_url)
    print(f"Original: {original_url}")
    print(f"Final: {final_url}")
else:
    print("No Google News links found in video_url")
    
    # Try source_url
    cursor.execute("SELECT id, source_url FROM events WHERE source_url LIKE '%news.google.com%' LIMIT 1")
    row = cursor.fetchone()
    if row:
        original_url = row[1]
        final_url = unwrap_url(original_url)
        print(f"Original (Source): {original_url}")
        print(f"Final: {final_url}")

conn.close()
