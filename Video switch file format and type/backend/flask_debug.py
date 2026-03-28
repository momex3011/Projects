"""
Development-only runner that exposes the FastAPI app through the
Werkzeug debugger used by Flask.

This is a compatibility bridge, not a native Flask application.
"""

from werkzeug.serving import run_simple

from backend.flask_app import flask_app


if __name__ == "__main__":
    run_simple(
        hostname="127.0.0.1",
        port=8000,
        application=flask_app,
        use_reloader=True,
        use_debugger=True,
        use_evalex=True,
        threaded=True,
    )
