
import base64
import re

import sqlite3
import base64
import re

def get_url_from_db():
    conn = sqlite3.connect('wartracker.db')
def get_url_from_db():
    conn = sqlite3.connect('wartracker.db')
    cursor = conn.cursor()
    cursor.execute("SELECT video_url, source_url FROM events WHERE video_url LIKE '%news.google.com%' OR source_url LIKE '%news.google.com%' LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0] if row[0] and 'news.google.com' in row[0] else row[1]
    return None

url = get_url_from_db()
print(f"URL Found: {url}")
if not url:
    print("No URL found in DB")
    exit()

print(f"Full URL Length: {len(url)}")
print(f"Full URL: {url}")

try:
    # Extract the base64 part
    match = re.search(r'articles/([^?]+)', url)
    if match:
        b64_str = match.group(1)
        # Fix padding
        padded = b64_str + '=' * (-len(b64_str) % 4)
        # Decode - standard b64 or urlsafe b64
        decoded_bytes = base64.urlsafe_b64decode(padded)
        
        print("--- DECODED RAW ---")
        # Try to print as latin1 to preserve bytes, or just find http strings
        print(decoded_bytes)
        
        # Searching for URLs in the bytes
        # URLs usually start with http
        print("\n--- EXTRACTED URLS ---")
        import string
        printable = set(string.printable.encode('ascii'))
        # Simple extraction of "http..." strings
        
        text = decoded_bytes.decode('latin1', errors='ignore')
        urls = re.findall(r'(https?://[^\s\x00-\x1f\x7f-\xff]+)', text)
        for u in urls:
            print(u)
            
        # Refined protobuf search (often starts with a length byte then the string)
        # But grep for https? is usually good enough for inspection
            
    else:
        print("No match found")
except Exception as e:
    print(f"Error: {e}")
