import random
try:
    from syria_data import SYRIA_LOCATIONS
except ImportError:
    print("❌ CRITICAL: 'syria_data.py' not found. Run fetch_all_towns.py first.")
    SYRIA_LOCATIONS = {}

# --- 1. INDEXING ---
print(f"⚡ Indexing {len(SYRIA_LOCATIONS)} locations...")
LOCATION_INDEX = {name.lower().strip(): coords for name, coords in SYRIA_LOCATIONS.items()}

# --- 2. INTERNATIONAL / DIPLOMATIC HUBS (NEW) ---
# These are mapped to their real-world capitals, not Syria.
DIPLOMATIC_HUBS = {
    "united nations": (40.7489, -73.9680),
    "un": (40.7489, -73.9680),
    "security council": (40.7489, -73.9680),
    "unsc": (40.7489, -73.9680),
    "new york": (40.7489, -73.9680),
    "geneva": (46.2044, 6.1432),
    "paris": (48.8566, 2.3522),
    "france": (48.8566, 2.3522),
    "washington": (38.9072, -77.0369),
    "usa": (38.9072, -77.0369),
    "white house": (38.9072, -77.0369),
    "moscow": (55.7558, 37.6173),
    "russia": (55.7558, 37.6173),
    "kremlin": (55.7558, 37.6173),
    "ankara": (39.9334, 32.8597),
    "turkey": (39.9334, 32.8597),
    "istanbul": (41.0082, 28.9784),
    "tehran": (35.6892, 51.3890),
    "iran": (35.6892, 51.3890),
    "london": (51.5074, -0.1278),
    "uk": (51.5074, -0.1278),
    "beirut": (33.8938, 35.5018),
    "lebanon": (33.8938, 35.5018),
    "amman": (31.9454, 35.9284),
    "jordan": (31.9454, 35.9284)
}

# --- 3. SYRIAN PROVINCE CAPITALS ---
GOVERNORATES = {
    "aleppo": (36.2012, 37.1612), "idlib": (35.9306, 36.6339), "homs": (34.7324, 36.7137),
    "hama": (35.1318, 36.7578), "latakia": (35.5317, 35.7901), "tartus": (34.8890, 35.8866),
    "damascus": (33.5138, 36.2765), "rif dimashq": (33.5138, 36.2765), "daraa": (32.6184, 36.1014),
    "sweida": (32.7089, 36.5695), "quneitra": (33.1250, 35.8250), "deir ez-zor": (35.3359, 40.1409),
    "raqqa": (35.9500, 39.0167), "hasakah": (36.5000, 40.7500)
}

def add_jitter(lat, lng):
    return lat + random.uniform(-0.005, 0.005), lng + random.uniform(-0.005, 0.005)

def get_coordinates(location_name):
    if not location_name: return None
    search_term = location_name.lower().strip()

    # 1. CHECK INTERNATIONAL HUBS (UN, Moscow, etc.)
    if search_term in DIPLOMATIC_HUBS:
        return {'lat': DIPLOMATIC_HUBS[search_term][0], 'lng': DIPLOMATIC_HUBS[search_term][1]}

    # 2. CHECK GOVERNORATES (Manual Override for generic regions)
    for gov, coords in GOVERNORATES.items():
        if search_term == gov or search_term == f"{gov} countryside" or search_term == f"{gov} province":
            j_lat, j_lng = add_jitter(coords[0], coords[1])
            return {'lat': j_lat, 'lng': j_lng}

    # 3. CHECK EXACT MATCH IN DICTIONARY
    if search_term in LOCATION_INDEX:
        lat, lng = LOCATION_INDEX[search_term]
        j_lat, j_lng = add_jitter(lat, lng)
        return {'lat': j_lat, 'lng': j_lng}

    # 4. FUZZY MATCH: Remove "Al-" or "El-" prefix
    if "al-" in search_term or "al " in search_term or "el-" in search_term:
        cleaned = search_term.replace("al-", "").replace("al ", "").replace("el-", "").strip()
        if cleaned in LOCATION_INDEX:
            lat, lng = LOCATION_INDEX[cleaned]
            j_lat, j_lng = add_jitter(lat, lng)
            return {'lat': j_lat, 'lng': j_lng}

    # 5. FUZZY MATCH: Add "Al-" prefix
    variations = [f"al-{search_term}", f"al {search_term}", f"el-{search_term}"]
    for v in variations:
        if v in LOCATION_INDEX:
            lat, lng = LOCATION_INDEX[v]
            j_lat, j_lng = add_jitter(lat, lng)
            return {'lat': j_lat, 'lng': j_lng}

    return None