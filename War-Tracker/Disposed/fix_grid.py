import json
from shapely.geometry import shape, Point, Polygon
from app import create_app
from extensions import db
from models.location import Location
from models.territory import Territory
from models.war import War

app = create_app()

def fix_grid():
    with app.app_context():
        print("--- 🛠️ FIXING MAP GRID ---")
        
        # 1. Get War and Territory
        war = War.query.filter_by(name="Syria").first()
        if not war:
            print("❌ War 'Syria' not found.")
            return

        gov = Territory.query.filter_by(war_id=war.id, name="Government Control").first()
        if not gov:
            print("❌ 'Government Control' territory not found.")
            return

        # 2. Verify GeoJSON
        try:
            geo_data = json.loads(gov.geojson)
            if 'features' in geo_data: geo_data = geo_data['features'][0]['geometry']
            elif 'geometry' in geo_data: geo_data = geo_data['geometry']
            
            syria_shape = shape(geo_data)
            print(f"   ✅ Loaded Syria Shape. Type: {syria_shape.geom_type}")
            print(f"   📏 Bounds: {syria_shape.bounds}")
        except Exception as e:
            print(f"   ❌ Invalid GeoJSON: {e}")
            return

        # 3. Check Existing Points
        count = Location.query.filter_by(war_id=war.id, controller="Government Control").count()
        print(f"   📊 Current Government Points: {count}")
        
        if count > 1000:
            print("   ✅ Grid seems populated. Skipping regeneration.")
            # Uncomment to force regeneration
            # return 
        
        # 4. Regenerate Grid
        print("   🎨 Regenerating Grid Points...")
        
        # Delete old Gov points (be careful not to delete historical ones if we had them, but for now we assume static grid)
        # We only delete points starting with "G-" (Grid) or "B-" (Border)
        deleted_g = Location.query.filter(Location.war_id == war.id, Location.name.like("G-%")).delete(synchronize_session=False)
        deleted_b = Location.query.filter(Location.war_id == war.id, Location.name.like("B-%")).delete(synchronize_session=False)
        print(f"   🗑️ Deleted {deleted_g} grid points and {deleted_b} border points.")
        
        points = []
        
        # A. Stitch Border (High precision)
        print("   📍 Generating Border Points...")
        if isinstance(syria_shape, Polygon): exteriors = [syria_shape.exterior]
        else: exteriors = [p.exterior for p in syria_shape.geoms]
        
        for line in exteriors:
            coords = list(line.coords)
            step = 2 # Every 2nd point
            for i, (lng, lat) in enumerate(coords):
                if i % step == 0: 
                    points.append(Location(war_id=war.id, name=f"B-{i}", lat=lat, lng=lng, controller="Government Control"))

        # B. Fill Center (Grid)
        print("   ▦ Generating Interior Grid...")
        min_lon, min_lat, max_lon, max_lat = syria_shape.bounds
        step = 0.08 # Higher density than before (was 0.12)
        lat = min_lat
        while lat <= max_lat:
            lon = min_lon
            while lon <= max_lon:
                if syria_shape.contains(Point(lon, lat)):
                    points.append(Location(war_id=war.id, name=f"G-{lat}-{lon}", lat=lat, lng=lon, controller="Government Control"))
                lon += step
            lat += step

        # Batch save
        print(f"   💾 Saving {len(points)} points...")
        for i in range(0, len(points), 500):
            db.session.add_all(points[i:i+500])
            db.session.commit()

        print("--- 🏁 GRID FIXED. ---")

if __name__ == "__main__":
    fix_grid()
