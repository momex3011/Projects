import requests
import zipfile
import io
import csv
import sqlite3
import os

# --- CONFIGURATION ---
# UNCOMMENT the one you want:

# OPTION A: NUCLEAR (Every farm, hill, & city on Earth - 12 Million+ entries)
# WARNING: huge download, takes 5-10 mins to process.
DOWNLOAD_URL = "http://download.geonames.org/export/dump/allCountries.zip"
FILE_NAME = "allCountries.txt"

# OPTION B: TACTICAL (All cities with pop > 1000 - 150k entries)
# Fast, covers 99% of reporting, misses tiny hamlets/hills.
# DOWNLOAD_URL = "http://download.geonames.org/export/dump/cities1000.zip"
# FILE_NAME = "cities1000.txt"

DB_NAME = "world.db"

def build_database():
    print(f"--- 🌍 INITIALIZING GLOBAL GEOSPATIAL DATABASE ---")
    
    # 1. Setup SQLite
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME) # Clean slate
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # We use a simple schema optimized for speed
    # We index 'name' so lookups are instant (0.001s)
    c.execute('''CREATE TABLE locations 
                 (name TEXT, lat REAL, lng REAL, population INTEGER, priority INTEGER)''')
    c.execute('CREATE INDEX idx_name ON locations(name)')
    
    print("⬇️  Downloading Global Data (This is a large file, please wait)...")
    try:
        r = requests.get(DOWNLOAD_URL, stream=True)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        
        print("⚡ Extracting and parsing data stream...")
        
        count = 0
        batch = []
        
        with z.open(FILE_NAME) as f:
            content = io.TextIOWrapper(f, encoding='utf-8')
            reader = csv.reader(content, delimiter='\t')
            
            for row in reader:
                try:
                    # GeoNames Columns:
                    # 1:name, 2:asciiname, 3:alternates, 4:lat, 5:lng, 6:class, 7:code, 14:pop
                    
                    # Filters for "Nuclear" relevance
                    # P=City, T=Hill, S=Spot/Building, L=Area/Park, A=Region
                    f_class = row[6]
                    if f_class not in ['P', 'T', 'S', 'L', 'A']:
                        continue

                    lat = float(row[4])
                    lng = float(row[5])
                    pop = int(row[14]) if row[14].isdigit() else 0
                    
                    # Priority Scoring (Capital > City > Hill > Farm)
                    priority = 1
                    if row[7] == 'PPLC': priority = 10 # Capital
                    elif row[7] == 'PPLA': priority = 8 # Major City
                    elif row[7] == 'PPLX': priority = 6 # Neighborhood
                    
                    # We add multiple entries for the same coordinates so any spelling works
                    names_to_add = set()
                    names_to_add.add(row[1]) # UTF8 Name
                    names_to_add.add(row[2]) # ASCII Name
                    
                    # Add Alternates (Arabic, French, etc)
                    # Limit to avoid database explosion if using allCountries
                    if row[3]:
                        alts = row[3].split(',')
                        # Only take first 5 alternates to save space, or remove slice [:] for ALL
                        for alt in alts[:5]: 
                            if alt: names_to_add.add(alt.strip())

                    for name in names_to_add:
                        if len(name) > 2:
                            # Batch insert for speed
                            batch.append((name.lower(), lat, lng, pop, priority))
                    
                    count += 1
                    if len(batch) > 50000:
                        c.executemany("INSERT INTO locations VALUES (?,?,?,?,?)", batch)
                        conn.commit()
                        batch = []
                        print(f"   -> Indexed {count} locations...")

                except IndexError:
                    continue
        
        # Insert remaining
        if batch:
            c.executemany("INSERT INTO locations VALUES (?,?,?,?,?)", batch)
            conn.commit()

        print("🔨 Optimizing Database Indices...")
        c.execute("ANALYZE")
        
        print(f"✅ SUCCESS: Database built with {count} unique physical locations.")
        print(f"   -> Saved to '{DB_NAME}'")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    build_database()