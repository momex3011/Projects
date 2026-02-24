from app import create_app
from extensions import db
from models.event import Event
from models.scraper_state import ScraperState

app = create_app()

def clear_news():
    with app.app_context():
        print("⚠️  WARNING: This will delete ALL scraped news events.")
        confirm = input("Type 'DELETE' to confirm: ")
        
        if confirm == "DELETE":
            try:
                num_events = db.session.query(Event).delete()
                # Also reset scraper state so it starts over from 2011/target date
                db.session.query(ScraperState).delete()
                
                db.session.commit()
                
                # Clear the text ledger
                with open("accepted_events.md", "w", encoding="utf-8") as f:
                    f.write("# 📂 The Daily Ledger\n**Status**: Real-time Sync Active\n**Filtered By**: Strong Acceptance Criteria (Combats, Protests, Crimes)\n\n---\n")

                print(f"✅ Deleted {num_events} events.")
                print("✅ Reset Scraper Progress (Back to Day 1: Mar 06 2011).")
                print("✅ Cleared 'accepted_events.md'.")
                print("   (Sources and Trends were PRESERVED).")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Error: {e}")
        else:
            print("❌ Operation cancelled.")

if __name__ == "__main__":
    clear_news()
