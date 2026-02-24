
import sqlite3
import json

conn = sqlite3.connect('wartracker.db')
cursor = conn.cursor()
cursor.execute("SELECT id, source_url FROM events WHERE source_url LIKE '%news.google.com%'")
rows = cursor.fetchall()
conn.close()

urls = [{"id": r[0], "url": r[1]} for r in rows]
with open('google_urls.json', 'w') as f:
    json.dump(urls, f, indent=2)

print(f"Exported {len(urls)} URLs")
