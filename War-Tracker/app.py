from flask import Flask, render_template
from flask_apscheduler import APScheduler
from config import Config
from extensions import db, migrate, bcrypt, login_manager
from extensions import db
from datetime import datetime
import time
import subprocess
import socket
import os
import sys



class Source(db.Model):
    __tablename__ = "sources"
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(32), nullable=False)  # 'youtube', 'telegram', 'facebook'
    handle = db.Column(db.String(255), nullable=False)   # Channel ID or Username
    name = db.Column(db.String(255))                     # Friendly name (e.g., 'Ugarit News')
    
    status = db.Column(db.String(24), default="probation") # trusted|probation|banned
    reliability_score = db.Column(db.Float, default=50.0)
    
    last_crawled_at = db.Column(db.DateTime)
    total_events_found = db.Column(db.Integer, default=0)

    # Unique constraint so we don't add the same channel twice
    __table_args__ = (db.UniqueConstraint('platform', 'handle', name='_platform_handle_uc'),)

class SourceObservation(db.Model):
    """Tracks how well a source performed during a specific scan."""
    __tablename__ = "source_observations"
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey("sources.id"))
    date_observed = db.Column(db.Date, default=datetime.utcnow().date())
    items_found = db.Column(db.Integer, default=0)
    items_accepted = db.Column(db.Integer, default=0)

# --- PHOTON MANAGER ---
def start_photon():
    """
    Ensures the local Geocoding server (Photon) is running.
    Bypasses rate limits and functions entirely offline.
    """
    # 1. Check if Photon is already running on its default port 2322
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(('127.0.0.1', 2322))
    sock.close()
    
    if result == 0:
        print("📍 Offline Geocoder: Already active on port 2322.")
        return

    # 2. Paths to files (Ensure these files are in your project folder)
    # Search for the latest JAR in your folder
    photon_jar = "photon-opensearch-0.7.4.jar"
    data_dir = "photon_data"

    if not os.path.exists(photon_jar):
        print(f"⚠️ Warning: {photon_jar} not found. Offline geocoding will be disabled.")
        return

    print("🚀 Offline Geocoder: Starting Syria Mapping Engine...")
    
    # 3. Launch Process
    try:
        # -Xmx2g allocates 2GB of RAM. If you have 16GB+ RAM, change to -Xmx4g for speed.
        subprocess.Popen(
            ["java", "-Xmx2g", "-jar", photon_jar, "-data", data_dir],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        print("✅ Offline Geocoder: Background process initiated.")
    except Exception as e:
        print(f"❌ Offline Geocoder Error: {e}")

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Register blueprints
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.wars import wars_bp
    from routes.events import events_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(wars_bp, url_prefix="/wars")
    app.register_blueprint(events_bp, url_prefix="/events")
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/")
    def index():
        from models.war import War
        wars = War.query.order_by(War.created_at.desc()).all()
        return render_template("index.html", wars=wars)

    return app

if __name__ == "__main__":
    # Standard Antigravity Boot
    create_app().run(debug=True, host="0.0.0.0")