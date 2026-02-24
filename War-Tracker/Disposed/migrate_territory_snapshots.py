"""
Migration: Add TerritorySnapshot and FactionCapital tables
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "wartracker.db")

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create territory_snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS territory_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faction_id INTEGER NOT NULL,
            effective_date DATE NOT NULL DEFAULT (date('now')),
            end_date DATE,
            is_permanent BOOLEAN DEFAULT 1,
            territory_geojson TEXT,
            source VARCHAR(50) DEFAULT 'manual',
            source_event_id INTEGER,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (faction_id) REFERENCES factions(id),
            FOREIGN KEY (source_event_id) REFERENCES events(id)
        )
    """)
    print("✓ Created territory_snapshots table")
    
    # Create index for efficient date queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_territory_snapshots_date 
        ON territory_snapshots(faction_id, effective_date DESC)
    """)
    print("✓ Created index on territory_snapshots")
    
    # Create faction_capitals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faction_capitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            faction_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            lat FLOAT NOT NULL,
            lng FLOAT NOT NULL,
            is_primary BOOLEAN DEFAULT 0,
            sector_name VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (faction_id) REFERENCES factions(id)
        )
    """)
    print("✓ Created faction_capitals table")
    
    conn.commit()
    conn.close()
    print("\n✓ Migration complete!")

if __name__ == "__main__":
    migrate()
