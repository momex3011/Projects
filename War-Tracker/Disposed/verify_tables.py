from app import create_app
from extensions import db
from sqlalchemy import inspect, text

app = create_app()

def check_tables():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Existing tables: {tables}")
        
        if 'trends' not in tables:
            print("❌ 'trends' table missing. Attempting raw SQL creation...")
            try:
                # Raw SQL for SQLite
                sql = """
                CREATE TABLE trends (
                    id INTEGER NOT NULL, 
                    keyword VARCHAR(100) NOT NULL, 
                    score FLOAT, 
                    created_at DATETIME, 
                    last_seen DATETIME, 
                    is_active BOOLEAN, 
                    PRIMARY KEY (id), 
                    UNIQUE (keyword)
                );
                """
                with db.engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()
                print("✅ 'trends' table created via SQL.")
            except Exception as e:
                print(f"Failed to create trends: {e}")
                
        if 'sources' not in tables:
            print("❌ 'sources' table missing. Attempting raw SQL creation...")
            try:
                sql = """
                CREATE TABLE sources (
                    id INTEGER NOT NULL, 
                    platform VARCHAR(50) NOT NULL, 
                    handle VARCHAR(100) NOT NULL, 
                    name VARCHAR(200), 
                    status VARCHAR(20), 
                    reliability_score FLOAT, 
                    last_crawled_at DATETIME, 
                    total_events_found INTEGER, 
                    created_at DATETIME, 
                    PRIMARY KEY (id)
                );
                """
                with db.engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()
                print("✅ 'sources' table created via SQL.")
            except Exception as e:
                print(f"Failed to create sources: {e}")

if __name__ == "__main__":
    check_tables()
