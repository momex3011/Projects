from geopy.geocoders import Nominatim
import time

geolocator = Nominatim(user_agent="wartracker_test", timeout=10)

def test_loc(loc_name):
    print(f"\nTesting: {loc_name}", flush=True)
    try:
        geo = geolocator.geocode(f"{loc_name}, Syria", timeout=5)
        if geo:
            print(f"✅ Found: {geo.address} ({geo.latitude}, {geo.longitude})")
        else:
            print(f"❌ Failed to geocode: {loc_name}")
            if "," in loc_name:
                city = loc_name.split(",")[-1].strip()
                print(f"   🔄 Trying fallback city: {city}")
                geo = geolocator.geocode(f"{city}, Syria", timeout=5)
                if geo:
                    print(f"   ✅ Found Fallback: {geo.address}")
                else:
                    print(f"   ❌ Fallback Failed")
    except Exception as e:
        print(f"⚠️ Error: {e}")

locations = [
    "Hama",
    "Sakhour, Aleppo",
    "Khalidiya, Homs",
    "Douma",
    "Al-Arbaeen, Hama", # Tricky one
    "RandomPlaceThatDoesntExist"
]

for l in locations:
    test_loc(l)
    time.sleep(1)
