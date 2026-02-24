
import sqlite3

def fix_db():
    conn = sqlite3.connect('wartracker.db')
    cursor = conn.cursor()
    
    # 1. Clear malformed video_urls (not starting with http)
    print("Checking for malformed video URLs...")
    cursor.execute("SELECT id, video_url FROM events WHERE video_url IS NOT NULL AND video_url NOT LIKE 'http%'")
    rows = cursor.fetchall()
    for r in rows:
        print(f"Fixing ID {r[0]}: Bad video_url '{r[1]}'")
        cursor.execute("UPDATE events SET video_url = NULL WHERE id = ?", (r[0],))
        
    # 2. Promote source_url to video_url if source is YouTube and video is missing
    print("Promoting YouTube source links...")
    cursor.execute("""
        SELECT id, source_url FROM events 
        WHERE (video_url IS NULL OR video_url = '') 
        AND (source_url LIKE '%youtube.com%' OR source_url LIKE '%youtu.be%')
    """)
    rows = cursor.fetchall()
    for r in rows:
        print(f"Promoting ID {r[0]}: Source '{r[1]}' -> Video")
        cursor.execute("UPDATE events SET video_url = ? WHERE id = ?", (r[1], r[0]))

    # 3. Clean titles (remove ' - YouTube', ' - Al Jazeera', etc.)
    print("Cleaning titles...")
    cursor.execute("SELECT id, title FROM events WHERE title LIKE '% - YouTube%' OR title LIKE '% - Al Jazeera%'")
    rows = cursor.fetchall()
    for r in rows:
        old_title = r[1]
        new_title = old_title.replace(' - YouTube', '').replace(' - Al Jazeera', '').strip()
        print(f"Cleaning ID {r[0]}: '{old_title}' -> '{new_title}'")
        cursor.execute("UPDATE events SET title = ? WHERE id = ?", (new_title, r[0]))

    conn.commit()
    conn.close()
    print("Database repair complete.")

if __name__ == "__main__":
    fix_db()
