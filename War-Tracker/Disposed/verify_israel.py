from app import create_app
from extensions import db
from models.territory import Territory
from models.location import Location

app = create_app()

with app.app_context():
    israel = Territory.query.filter_by(name="Israel").first()
    if israel:
        print(f"✅ Israel Territory Found: ID={israel.id}")
        points = Location.query.filter_by(controller="Israel").count()
        print(f"✅ Israel Control Points: {points}")
        if points > 0:
            print("🚀 SUCCESS: Israel is on the map!")
        else:
            print("⚠️ WARNING: Israel exists but has NO points.")
    else:
        print("❌ ERROR: Israel Territory NOT found.")
