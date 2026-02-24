from geopy.geocoders import Nominatim
from syria_data import SYRIA_LOCATIONS
import difflib

geolocator = Nominatim(user_agent="wartracker_test_v1")

def test_geocode(name):
    print(f"--- Testing: {name} ---")
    
    # 1. Exact Match
    if name in SYRIA_LOCATIONS:
        print(f"✅ Exact match found: {SYRIA_LOCATIONS[name]}")
        return

    # 2. Fuzzy Match
    matches = difflib.get_close_matches(name, SYRIA_LOCATIONS.keys(), n=1, cutoff=0.8)
    if matches:
        print(f"✅ Fuzzy match found: {matches[0]} -> {SYRIA_LOCATIONS[matches[0]]}")
        return

    # 3. Nominatim
    try:
        print("🌍 Querying Nominatim...")
        loc = geolocator.geocode(f"{name}, Syria", timeout=10)
        if loc:
            print(f"✅ Nominatim found: {loc.address} ({loc.latitude}, {loc.longitude})")
        else:
            print("❌ Nominatim failed.")
    except Exception as e:
        print(f"❌ Nominatim error: {e}")

if __name__ == "__main__":
    test_cases = [
        "Aleppo", "Damascus", "Idlib", "Raqqa", # Major cities (English)
        "Al-Raqqa", "Ar Raqqah", # Variations
        "Qusayr", "Al-Qusayr", # Towns
        "RandomVillageThatDoesntExist", # Failure case
        "Homs", "Hama", "Deir ez-Zor"
    ]
    
    for t in test_cases:
        test_geocode(t)
