from app import create_app
from extensions import db
from models.source import Source
import json
import os

app = create_app()

def import_sources():
    file_path = "trusted_sources.json"
    if not os.path.exists(file_path):
        print(f"❌ '{file_path}' not found.")
        return

    with app.app_context():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"📚 Found {len(data)} sources in file.")
            added = 0
            
            # OPTIONAL: Clear old sources if 'strict' mode is desired?
            # Uncomment next line to wipe existing sources before import
            # Source.query.delete(); db.session.commit()

            for item in data:
                exists = Source.query.filter_by(handle=item['handle']).first()
                if not exists:
                    src = Source(
                        name=item['name'],
                        platform=item['platform'],
                        handle=item['handle'],
                        status='trusted', # Auto-trust these
                        reliability_score=100.0
                    )
                    db.session.add(src)
                    added += 1
                else:
                    # Update to trusted if existed
                    exists.status = 'trusted'
                    exists.reliability_score = 100.0
            
            db.session.commit()
            print(f"✅ Successfully imported {added} new sources. All marked 'trusted'.")
            
        except Exception as e:
            print(f"❌ Error importing sources: {e}")

if __name__ == "__main__":
    import_sources()
