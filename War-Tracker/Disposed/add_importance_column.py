"""Add importance column to locations table"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'wartracker.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(locations)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'importance' not in columns:
        print("Adding 'importance' column to locations table...")
        cursor.execute("ALTER TABLE locations ADD COLUMN importance INTEGER DEFAULT 5")
        conn.commit()
        print("✅ Column added successfully!")
    else:
        print("✅ 'importance' column already exists")
    
    conn.close()

if __name__ == "__main__":
    migrate()
