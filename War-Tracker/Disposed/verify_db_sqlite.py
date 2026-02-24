import sqlite3

try:
    conn = sqlite3.connect('wartracker.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(events)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'video_url' in columns:
        print("SUCCESS: video_url column exists.")
    else:
        print("FAILURE: video_url column MISSING.")
        print("Attempting to add video_url column...")
        try:
            cursor.execute("ALTER TABLE events ADD COLUMN video_url TEXT")
            conn.commit()
            print("SUCCESS: video_url column added successfully.")
        except Exception as e:
            print(f"ERROR: Could not add column: {e}")
            
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
