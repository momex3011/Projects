
import sqlite3
from urllib.parse import urlparse

def deduplicate():
    conn = sqlite3.connect('wartracker.db')
    cursor = conn.cursor()
    
    # 1. Deduplicate by video_url (if present)
    print("Deduplicating by matching video_url...")
    cursor.execute("""
        DELETE FROM events 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM events 
            WHERE video_url IS NOT NULL 
            GROUP BY video_url
        ) 
        AND video_url IS NOT NULL;
    """)
    print(f"Removed {cursor.rowcount} duplicates by video_url")
    
    # 2. Deduplicate by source_url (if video is null)
    print("Deduplicating by matching source_url...")
    cursor.execute("""
        DELETE FROM events 
        WHERE id NOT IN (
            SELECT MIN(id) 
            FROM events 
            GROUP BY source_url
        )
        AND source_url IS NOT NULL;
    """)
    print(f"Removed {cursor.rowcount} duplicates by source_url")

    # 3. Clean up titles - remove [TAGS] like [COMBAT] if redundant or just clean them
    # For now, just confirming deletions
    conn.commit()
    conn.close()

if __name__ == "__main__":
    deduplicate()
