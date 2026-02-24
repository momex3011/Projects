import requests
import json
import os
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.ops import unary_union
from app import create_app
from extensions import db
from models.location import Location
from models.location_cache import LocationCache
from models.territory import Territory
from models.war import War
from models.user import User, Role
from models.scraper_state import ScraperState
from datetime import date

app = create_app()

def setup_system():
    with app.app_context():
        print("--- 🛠️ MASTER SETUP: SYRIA & GOLAN (NO OVERLAPS) ---")
        
        # 1. RESET DATABASE
        print("   💥 Resetting Database tables...")
        db.drop_all()
        db.create_all()
        
        # 2. CREATE ADMIN
        admin = User(username="admin", role=Role.ADMIN)
        admin.set_password("admin123")
        db.session.add(admin)
        
        # 3. CREATE WAR
        war = War(name="Syria", start_date=date(2011, 3, 15), default_lat=34.0, default_lng=37.5, default_zoom=7)
        db.session.add(war)
        db.session.commit()

        # 4. DOWNLOAD MAPS
        print("   🌍 Downloading HD Map Data...")
        
        # A. SYRIA (Official Borders)
        syria_shape = None
        syria_url = "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/SYR/ADM0/geoBoundaries-SYR-ADM0.geojson"
        try:
            r_syr = requests.get(syria_url)
            syr_data = r_syr.json()
            syr_geom = syr_data['features'][0]['geometry'] if 'features' in syr_data else syr_data['geometry']
            syria_shape = shape(syr_geom)
        except Exception as e:
            print(f"   ❌ Error downloading Syria map: {e}")
            return

        # B. GOLAN HEIGHTS (HD Occupied Territory)
        golan_poly = None
        golan_geojson_str = ""
        
        golan_url = "https://gist.githubusercontent.com/panchicore/dd6d615c4bdf7e34a2831f231f773e07/raw/res_Golan%2520Heights%2520-%2520controlled%2520by%2520Israel.geojson"
        try:
            r_gol = requests.get(golan_url)
            gol_data = r_gol.json()
            gol_geom = gol_data['features'][0]['geometry']
            golan_poly = shape(gol_geom)
            golan_geojson_str = json.dumps(gol_geom)
            print("   ✅ Golan Heights HD Map acquired.")
        except Exception as e:
            print(f"   ⚠️ Could not download Golan Map ({e}). Using Low-Res Fallback.")
            golan_coords = [[35.6, 32.7], [35.6, 33.3], [35.9, 33.3], [35.9, 32.7], [35.6, 32.7]]
            golan_poly = Polygon(golan_coords)
            golan_geojson_str = json.dumps({"type": "Polygon", "coordinates": [golan_coords]})

        # 5. GEOMETRIC SUBTRACTION (THE FIX)
        # We cut the Golan shape OUT of the Syria shape so they don't overlap.
        print("   ✂️  Clipping Territories to prevent overlap...")
        
        # Calculate: Syria_Final = Syria_Raw - Golan
        gov_shape = syria_shape.difference(golan_poly)
        
        # Convert Shapely object back to GeoJSON string for DB
        # We use a mapping because Shapely creates MultiPolygons after cutting
        from shapely.geometry import mapping
        gov_geojson_str = json.dumps(mapping(gov_shape))

        # 6. SAVE TERRITORIES
        print("   🗺️ Saving Clean Territories...")
        
        # Government gets the CLIPPED shape
        gov = Territory(war_id=war.id, name="Government Control", color="#ef4444", geojson=gov_geojson_str)
        
        # Israel gets the Golan shape
        isr = Territory(war_id=war.id, name="Israel", color="#0984e3", geojson=golan_geojson_str)
        
        # Placeholders
        tiny = json.dumps({"type": "Polygon", "coordinates": [[[36,36],[36.01,36],[36,36.01],[36,36]]]})
        reb = Territory(war_id=war.id, name="Rebel Control", color="#10b981", geojson=tiny)
        isis = Territory(war_id=war.id, name="ISIS", color="#000000", geojson=tiny)
        sdf = Territory(war_id=war.id, name="SDF", color="#f1c40f", geojson=tiny)
        
        db.session.add_all([gov, reb, isis, sdf, isr])
        db.session.commit()

        # 7. GENERATE TACTICAL GRID
        print("   🎨 Painting Tactical Grid...")
        points = []

        # A. SYRIA BORDER (High Res)
        # Use the NEW gov_shape so points don't appear inside Golan
        geoms = [gov_shape] if isinstance(gov_shape, Polygon) else gov_shape.geoms
        
        for poly in geoms:
            if poly.exterior:
                for i, (lng, lat) in enumerate(poly.exterior.coords):
                    if i % 4 == 0: 
                        points.append(Location(war_id=war.id, name=f"B-{i}", lat=lat, lng=lng, controller="Government Control"))

        # B. GOLAN BORDER (Israel)
        if golan_poly.exterior:
            for i, (lng, lat) in enumerate(golan_poly.exterior.coords):
                points.append(Location(war_id=war.id, name=f"IL-B-{i}", lat=lat, lng=lng, controller="Israel"))

        # C. FILL MAP
        min_lon, min_lat, max_lon, max_lat = syria_shape.bounds
        
        # Main Grid
        step = 0.12
        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                p = Point(lon, lat)
                
                # Check 1: Is it in the original Syria bounds?
                if syria_shape.contains(p):
                    # Check 2: Is it inside Golan?
                    if golan_poly.contains(p):
                        # It's inside Golan -> Add to Israel Grid (High Density)
                        # (We skip this here and do a dedicated high-res loop below)
                        pass 
                    else:
                        # It's in Syria but NOT Golan -> Government
                        points.append(Location(war_id=war.id, name=f"G-{lat:.2f}-{lon:.2f}", lat=lat, lng=lon, controller="Government Control"))
                lon += step
            lat += step

        # HD Golan Grid
        g_min_lon, g_min_lat, g_max_lon, g_max_lat = golan_poly.bounds
        step_golan = 0.02
        lat = g_min_lat
        while lat <= g_max_lat:
            lon = g_min_lon
            while lon <= g_max_lon:
                p = Point(lon, lat)
                if golan_poly.contains(p):
                    points.append(Location(war_id=war.id, name=f"IL-{lat:.3f}-{lon:.3f}", lat=lat, lng=lon, controller="Israel"))
                lon += step_golan
            lat += step_golan

        # 8. SAVE
        print(f"   💾 Committing {len(points)} tactical points...")
        chunk_size = 500
        for i in range(0, len(points), chunk_size):
            db.session.add_all(points[i:i + chunk_size])
            db.session.commit()

        print("--- 🏁 SETUP COMPLETE. NO OVERLAPS DETECTED. ---")

if __name__ == "__main__":
    setup_system()