import sqlite3
import os

DB_PATH = "wartracker.db"

def force_create():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"🔌 Connected to {DB_PATH}")

    # 1. Create Trends Table
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword VARCHAR(100) NOT NULL UNIQUE,
            score FLOAT DEFAULT 0.0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        );
        """)
        print("✅ 'trends' table ensured.")
    except Exception as e:
        print(f"❌ Error creating trends: {e}")

    # 2. Create Sources Table
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform VARCHAR(50) NOT NULL,
            handle VARCHAR(100) NOT NULL,
            name VARCHAR(200),
            status VARCHAR(20) DEFAULT 'probation',
            reliability_score FLOAT DEFAULT 50.0,
            last_crawled_at DATETIME,
            total_events_found INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        print("✅ 'sources' table ensured.")
    except Exception as e:
        print(f"❌ Error creating sources: {e}")

    # 3. Create SourceObservations Table
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS source_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER NOT NULL,
            date_observed DATE NOT NULL,
            items_found INTEGER DEFAULT 0,
            items_accepted INTEGER DEFAULT 0,
            FOREIGN KEY(source_id) REFERENCES sources(id)
        );
        """)
        print("✅ 'source_observations' table ensured.")
    except Exception as e:
        print(f"❌ Error creating source_observations: {e}")

    conn.commit()
    conn.close()
    print("🏁 Done.")

if __name__ == "__main__":
    force_create()
