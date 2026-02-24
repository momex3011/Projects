"""Add sub_faction_id column to territory_snapshots table."""
from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    # Check if column already exists
    cols = [c['name'] for c in db.inspect(db.engine).get_columns('territory_snapshots')]
    
    if 'sub_faction_id' not in cols:
        with db.engine.connect() as conn:
            conn.execute(db.text('ALTER TABLE territory_snapshots ADD COLUMN sub_faction_id INTEGER REFERENCES subfactions(id)'))
            conn.commit()
        print('Added sub_faction_id column to territory_snapshots')
    else:
        print('sub_faction_id column already exists')
    
    # Verify
    cols = [c['name'] for c in db.inspect(db.engine).get_columns('territory_snapshots')]
    print('territory_snapshots columns:', cols)
    
    cols2 = [c['name'] for c in db.inspect(db.engine).get_columns('subfactions')]
    print('subfactions columns:', cols2)
    
    print('Migration complete!')
