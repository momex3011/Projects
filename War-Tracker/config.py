import os

class Config:
    # We use SQLite for local testing (no installation needed)
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'wartracker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "supersecretkey"