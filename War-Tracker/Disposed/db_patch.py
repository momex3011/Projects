import sqlite3
import datetime

DB_PATH = "wartracker.db"

def patch_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("Checking 'sources' table for 'created_at' column...")
        cursor.execute("PRAGMA table_info(sources)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "created_at" not in columns:
            print("   ⚠️ 'created_at' missing. Adding it now...")
            cursor.execute("ALTER TABLE sources ADD COLUMN created_at DATETIME")
            # Update existing rows to have a default timestamp
            now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE sources SET created_at = ? WHERE created_at IS NULL", (now,))
            conn.commit()
            print("   ✅ Column added and populated.")
        else:
            print("   ✅ 'created_at' already exists.")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Patch Error: {e}")

if __name__ == "__main__":
    patch_db()
