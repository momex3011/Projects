import sys
from app import app, db, War, Event, Location
from war_brain import analyze_intel
import feedparser

def run_diagnostic():
    print("============== SYSTEM DIAGNOSTIC ==============")
    
    with app.app_context():
        # --- CHECK 1: Database Connection & War Existence ---
        print("\n[1] CHECKING DATABASE...")
        wars = War.query.all()
        if not wars:
            print("❌ CRITICAL FAIL: No Wars found in database.")
            print("   -> SOLUTION: Run 'python setup.py' or add a war via /admin.")
            return
        
        print(f"✅ Found {len(wars)} Active Wars:")
        target_war = None
        for w in wars:
            print(f"   - ID: {w.id} | Name: '{w.name}'")
            # We are looking for a match for our scraper
            if "syria" in w.name.lower():
                target_war = w

        if not target_war:
            print("❌ CRITICAL FAIL: Scraper is looking for 'Syria', but no matching war was found.")
            return
        
        print(f"🎯 TARGET LOCKED: Using War ID {target_war.id} ('{target_war.name}') for data injection.")

        # --- CHECK 2: AI Brain Connection ---
        print("\n[2] CHECKING AI BRAIN...")
        test_headline = "Government forces capture the village of Al-Dana from rebels."
        print(f"   -> Sending Test Intel: '{test_headline}'")
        
        try:
            intel = analyze_intel(test_headline)
            print(f"   -> AI Response: {intel}")
            
            if not intel:
                print("❌ CRITICAL FAIL: AI returned None. Check your OpenAI API Key in config.py.")
                return
            if intel.get('controller') != "Government":
                print("⚠️  WARNING: AI logic might be weak. Expected 'Government', got:", intel.get('controller'))
            else:
                print("✅ AI BRAIN FUNCTIONAL.")
                
        except Exception as e:
            print(f"❌ AI ERROR: {e}")
            return

        # --- CHECK 3: Save Permission ---
        print("\n[3] ATTEMPTING DRY-RUN SAVE...")
        try:
            # Check for duplicates first to avoid crashing
            exists = Event.query.filter_by(title="DIAGNOSTIC TEST EVENT").first()
            if exists:
                print("   -> Diagnostic event already exists. Deleting it...")
                db.session.delete(exists)
                db.session.commit()

            # Create dummy event
            test_event = Event(
                war_id=target_war.id,
                title="DIAGNOSTIC TEST EVENT",
                description="System check. Ignore.",
                event_date="2025-01-01",
                lat=33.5138, 
                lng=36.2765, # Damascus
                source_url="http://localhost",
                image_url=None
            )
            
            db.session.add(test_event)
            db.session.commit()
            print("✅ SAVE SUCCESSFUL: Wrote test event to DB.")
            print("   -> Deleting test event now...")
            db.session.delete(test_event)
            db.session.commit()
            print("✅ CLEANUP COMPLETE.")
            
        except Exception as e:
            print(f"❌ DATABASE WRITE ERROR: {e}")
            return

    print("\n============== DIAGNOSTIC COMPLETE ==============")
    print("If all checks passed, your Scraper is working but likely deduplicating old news.")
    print("If check [1] failed: You need to rename your war in the DB to match the scraper.")
    print("If check [2] failed: Your API Key is wrong.")

if __name__ == "__main__":
    run_diagnostic()