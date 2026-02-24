import requests
import zipfile
import io
import csv
import re

def generate_variations(name):
    """
    Generates common variations of Syrian names to ensure we catch everything.
    Example: "Al-Qabun" -> ["Al-Qabun", "Al Qabun", "El-Qabun", "Qabun"]
    """
    variations = set()
    name = name.strip()
    variations.add(name)

    # 1. Handle "Al-" / "El-" prefixes (The #1 cause of missing locations)
    # Regex checks for Al, El, Ar, As, Az at the start (Sun/Moon letters)
    prefix_match = re.match(r"^(Al|El|Ar|As|Az|An|Ash|At)[-\s](.+)", name, re.IGNORECASE)
    
    if prefix_match:
        core_name = prefix_match.group(2) # The name without the prefix (e.g., "Qabun")
        variations.add(core_name)
        variations.add(f"Al-{core_name}")
        variations.add(f"Al {core_name}")
        variations.add(f"El-{core_name}")
        variations.add(f"El {core_name}")
    
    # 2. Handle specific character swaps common in news reports
    # "iy" vs "y" (e.g., "Qasiyun" vs "Qasioun")
    if "ou" in name: variations.add(name.replace("ou", "u"))
    if "u" in name: variations.add(name.replace("u", "ou"))
    
    return variations

def generate_massive_list():
    print("--- 🌍 STARTING 'NUCLEAR' DOWNLOAD OF SYRIAN LOCATIONS ---")
    print("Downloading raw data from geonames.org...")
    
    # Official GeoNames URL for Syria
    url = "http://download.geonames.org/export/dump/SY.zip"
    
    try:
        r = requests.get(url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        
        print("Extracting and parsing data (Including Hills, Neighborhoods, Farms, Ruins)...")
        
        locations = {}
        count = 0
        
        # Open the text file inside the zip (SY.txt)
        with z.open('SY.txt') as f:
            content = io.TextIOWrapper(f, encoding='utf-8')
            reader = csv.reader(content, delimiter='\t')
            
            for row in reader:
                try:
                    # GeoNames Format:
                    # 0:id, 1:name, 2:asciiname, 3:alternatenames, 4:lat, 5:lng, 6:feature_class, 7:feature_code
                    
                    name_utf8 = row[1]
                    name_ascii = row[2]
                    alternates = row[3]
                    lat = float(row[4])
                    lng = float(row[5])
                    f_class = row[6] # P=City, T=Hill, S=Building, L=Area, H=Water
                    
                    # --- THE "NUCLEAR" FILTER ---
                    # We accept almost everything relevant to war reporting:
                    # P = Cities, Towns, Villages
                    # T = Mountains, Hills (Crucial for "Tell ...")
                    # S = Spots, Buildings, Farms, Castles
                    # L = Parks, Areas (Neighborhoods often fall here)
                    # A = Administrative Regions
                    # R = Roads, Railroads (Crucial for supply lines)
                    # H = Hydrographic (Streams, Wadis, Lakes)
                    # V = Forests, Woods (Battlefields)
                    if f_class in ['P', 'T', 'S', 'L', 'A', 'R', 'H', 'V']:
                        
                        # 1. Add the main UTF8 name (often Arabic or official spelling)
                        locations[name_utf8] = (lat, lng)
                        
                        # 2. Add the ASCII name (English)
                        if name_ascii:
                            locations[name_ascii] = (lat, lng)
                            
                        # 3. Add ALL alternate names (Comma separated list of spellings)
                        if alternates:
                            alt_list = alternates.split(',')
                            for alt in alt_list:
                                alt = alt.strip()
                                if alt:
                                    locations[alt] = (lat, lng)
                        
                        count += 1
                        
                except IndexError:
                    continue

        print(f"✅ Extraction Complete.")
        print(f"   -> Raw entries processed: {count}")
        print(f"   -> Total unique searchable names: {len(locations)}")
        
        # Write to python file
        print("Writing to syria_data.py...")
        with open("syria_data.py", "w", encoding="utf-8") as f:
            f.write("# AUTO-GENERATED 'NUCLEAR' DATA FILE\n")
            f.write("# Includes: Cities, Towns, Hills (Tell), Farms, Neighborhoods, Ruins\n\n")
            f.write("SYRIA_LOCATIONS = {\n")
            
            # Sort for cleaner file structure
            for name in sorted(locations.keys()):
                # Clean name of any weird characters that might break Python syntax
                safe_name = name.replace("\\", "").replace("'", "\\'")
                coords = locations[name]
                f.write(f"    '{safe_name}': {coords},\n")
            
            f.write("}\n")
            
        print("--- 🏁 DONE. 'syria_data.py' is now massive! ---")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_massive_list()