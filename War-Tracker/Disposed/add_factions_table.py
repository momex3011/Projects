"""
Migration script to add the factions table to the database.
Run this once to create the table.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models.faction import Faction

app = create_app()

with app.app_context():
    # Check if table exists
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'factions' not in tables:
        print("Creating 'factions' table...")
        Faction.__table__.create(db.engine)
        print("✓ 'factions' table created successfully!")
    else:
        print("✓ 'factions' table already exists.")
    
    print("\nDone! You can now manage factions from the admin panel.")
