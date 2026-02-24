from models.source import Source
from app import create_app

app = create_app()
with app.app_context():
    sources = Source.query.all()
    print(f"Total sources in DB: {len(sources)}")
    for s in sources:
        print(f"  - {s.platform}/{s.handle} | status={s.status} | last_crawled={s.last_crawled_at}")
