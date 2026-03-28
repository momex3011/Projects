"""
Root Flask starter for RetroScale AI.

Run with:

    flask --app app.py run --debug

The underlying API implementation remains FastAPI; this file provides a
Flask-discoverable app object for the debugger and reloader workflow.
"""

from backend.flask_app import create_flask_bridge


app = create_flask_bridge()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
