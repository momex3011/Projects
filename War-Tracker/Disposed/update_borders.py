import requests
import json
import os
from shapely.geometry import shape, Point, Polygon
from app import create_app
from extensions import db
from models.location import Location
from models.territory import Territory
from models.war import War

app = create_app()

def update_borders():
    with app.app_context():
        print("--- 🌍 UPDATING SYRIA BORDERS ---")
        
        # 1. GET WAR
        war = War.query.filter_by(name="Syria").first()
        if not war:
            print("❌ War 'Syria' not found. Run setup.py first.")
            return

        # 2. DOWNLOAD HIGH-RES MAP
        print("   ⬇️ Downloading High-Res GeoJSON...")
        url = "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/SYR/ADM0/geoBoundaries-SYR-ADM0.geojson"
        try:
            r = requests.get(url)
            if r.status_code != 200:
                print(f"   ❌ Failed to download: Status {r.status_code}")
                return
            
            geo_data = r.json()
            # Handle FeatureCollection vs Geometry
            if 'features' in geo_data: 
                # geoBoundaries usually returns a FeatureCollection
                # We want the geometry of the first feature
                geo_data = geo_data['features'][0]['geometry']
            elif 'geometry' in geo_data:
                geo_data = geo_data['geometry']
                
            syria_shape = shape(geo_data)
            print("   ✅ Download successful.")
        except Exception as e:
            print(f"   ❌ Error downloading/parsing map: {e}")
            return

        # 3. DOWNLOAD & MERGE ISRAEL + GOLAN
        print("   ⬇️ Downloading Israel & Golan Data...")
        isr_url = "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/ISR/ADM0/geoBoundaries-ISR-ADM0.geojson"
        golan_url = "https://gist.githubusercontent.com/panchicore/dd6d615c4bdf7e34a2831f231f773e07/raw/res_Golan%20Heights%20-%20controlled%20by%20Israel.geojson"
        
        try:
            # Israel
            r_isr = requests.get(isr_url)
            if r_isr.status_code == 200:
                isr_data = r_isr.json()
                if 'features' in isr_data: isr_geom = shape(isr_data['features'][0]['geometry'])
                elif 'geometry' in isr_data: isr_geom = shape(isr_data['geometry'])
                else: isr_geom = None
            else:
                print("   ❌ Failed to download Israel map")
                isr_geom = None

            # Golan
            r_golan = requests.get(golan_url)
            if r_golan.status_code == 200:
                golan_data = r_golan.json()
                # Gist might return a FeatureCollection or just geometry
                if 'features' in golan_data: golan_geom = shape(golan_data['features'][0]['geometry'])
                elif 'geometry' in golan_data: golan_geom = shape(golan_data['geometry'])
                else: golan_geom = shape(golan_data)
            else:
                print("   ❌ Failed to download Golan map")
                golan_geom = None

            # Merge
            if isr_geom and golan_geom:
                israel_full = isr_geom.union(golan_geom)
            elif isr_geom:
                israel_full = isr_geom
            elif golan_geom:
                israel_full = golan_geom
            else:
                israel_full = None

            if israel_full:
                # Create/Update Israel Territory
                print("   📝 Updating Israel Territory Record...")
                isr_terr = Territory.query.filter_by(war_id=war.id, name="Israel").first()
                # Convert shapely geometry back to GeoJSON dict
                # shapely.geometry.mapping is useful here but we need to import it or just use json.dumps on __geo_interface__
                geo_interface = json.dumps(israel_full.__geo_interface__)
                
                if isr_terr:
                    isr_terr.geojson = geo_interface
                    db.session.commit()
                    print("   ✅ Israel territory updated.")
                else:
                    isr_terr = Territory(war_id=war.id, name="Israel", color="#0984e3", geojson=geo_interface)
                    db.session.add(isr_terr)
                    db.session.commit()
                    print("   ✅ Israel territory created.")
            
        except Exception as e:
            print(f"   ❌ Error processing Israel/Golan: {e}")


        # 4. UPDATE SYRIA TERRITORY RECORD
        print("   📝 Updating Syria Territory Record...")
        gov = Territory.query.filter_by(war_id=war.id, name="Government Control").first()
        if gov:
            gov.geojson = json.dumps(geo_data)
            db.session.commit()
            print("   ✅ Territory updated.")
        else:
            print("   ⚠️ 'Government Control' territory not found. Creating...")
            gov = Territory(war_id=war.id, name="Government Control", color="#d9534f", geojson=json.dumps(geo_data))
            db.session.add(gov)
            db.session.commit()

        # 5. REGENERATE BORDER POINTS
        print("   🎨 Regenerating Border Points (This may take a moment)...")
        
        # Delete existing border points (B-*)
        deleted = Location.query.filter(Location.war_id == war.id, Location.name.like("B-%")).delete(synchronize_session=False)
        print(f"   🗑️ Deleted {deleted} old border points.")
        
        points = []
        
        # Stitch Border (High precision edges)
        if isinstance(syria_shape, Polygon): exteriors = [syria_shape.exterior]
        else: exteriors = [p.exterior for p in syria_shape.geoms]
        
        for line in exteriors:
            coords = list(line.coords)
            # Use a slightly higher resolution for the border points since we have better data now
            # But don't go too crazy to avoid performance issues
            step = 2 # Take every 2nd point instead of 4th for better detail
            for i, (lng, lat) in enumerate(coords):
                if i % step == 0: 
                    points.append(Location(war_id=war.id, name=f"B-{i}", lat=lat, lng=lng, controller="Government Control"))

        # Batch save
        print(f"   💾 Saving {len(points)} new border points...")
        for i in range(0, len(points), 500):
            db.session.add_all(points[i:i+500])
            db.session.commit()

        print("--- 🏁 UPDATE COMPLETE. ---")

if __name__ == "__main__":
    update_borders()
