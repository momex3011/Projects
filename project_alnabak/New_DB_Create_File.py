from app import app, db
from app import User, Project, Vote, Volunteer, ProjectMember

with app.app_context():
    db.create_all()

print("Database tables created!")