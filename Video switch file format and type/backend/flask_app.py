"""
Flask entrypoint that keeps the FastAPI backend mounted for API routes while
serving the frontend from the same host and port.

Behavior:
- `/api`, `/docs`, `/redoc`, `/openapi.json`, and `/health` stay on FastAPI.
- `/` and other non-API routes serve the exported Next.js frontend if present.
- If no exported frontend exists, Flask falls back to proxying a live Next.js
  dev server on `http://127.0.0.1:3000`.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from a2wsgi import ASGIMiddleware
from flask import Flask, Response, request, send_from_directory

from backend.app_factory import create_fastapi_app


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
FRONTEND_EXPORT_DIR = FRONTEND_ROOT / "out"
FRONTEND_DEV_SERVER = os.getenv("FRONTEND_DEV_SERVER", "http://127.0.0.1:3000").rstrip("/")
FASTAPI_PATH_PREFIXES = ("/api", "/docs", "/redoc", "/openapi.json", "/health")
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


def _is_fastapi_path(path: str) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in FASTAPI_PATH_PREFIXES)


def _frontend_export_response(path: str) -> Response | None:
    if not FRONTEND_EXPORT_DIR.exists():
        return None

    normalized_path = path.strip("/")
    if normalized_path:
        file_candidate = FRONTEND_EXPORT_DIR / normalized_path
        if file_candidate.is_file():
            return send_from_directory(FRONTEND_EXPORT_DIR, normalized_path)

        route_index = FRONTEND_EXPORT_DIR / normalized_path / "index.html"
        if route_index.is_file():
            return send_from_directory(route_index.parent, route_index.name)

    index_file = FRONTEND_EXPORT_DIR / "index.html"
    if index_file.is_file():
        return send_from_directory(FRONTEND_EXPORT_DIR, "index.html")

    return None


def _proxy_frontend_request(path: str) -> Response | None:
    target = f"{FRONTEND_DEV_SERVER}/{path.lstrip('/')}" if path else FRONTEND_DEV_SERVER
    if request.args:
        target = f"{target}?{urlencode(request.args, doseq=True)}"

    forwarded_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
    }

    proxied_request = Request(target, headers=forwarded_headers, method=request.method)

    try:
        with urlopen(proxied_request, timeout=3) as upstream:
            response_headers = [
                (key, value)
                for key, value in upstream.getheaders()
                if key.lower() not in HOP_BY_HOP_HEADERS
            ]
            return Response(upstream.read(), status=upstream.status, headers=response_headers)
    except HTTPError as exc:
        response_headers = [
            (key, value)
            for key, value in exc.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS
        ]
        return Response(exc.read(), status=exc.code, headers=response_headers)
    except URLError:
        return None


def _frontend_unavailable_response() -> Response:
    html = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>RetroScale Frontend</title>
        <style>
          body {{
            margin: 0;
            min-height: 100vh;
            display: grid;
            place-items: center;
            background: linear-gradient(180deg, #17121f, #221b2f);
            color: #f8f4ff;
            font-family: Segoe UI, sans-serif;
          }}
          .card {{
            width: min(720px, calc(100vw - 48px));
            border-radius: 28px;
            padding: 32px;
            background: linear-gradient(180deg, rgba(65, 50, 84, 0.98), rgba(42, 34, 56, 0.98));
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 28px 28px 60px rgba(10, 8, 18, 0.42), -16px -16px 36px rgba(255,255,255,0.06);
          }}
          code {{
            display: block;
            margin-top: 12px;
            padding: 12px 14px;
            border-radius: 16px;
            background: rgba(0, 0, 0, 0.22);
            color: #ffdfcb;
          }}
        </style>
      </head>
      <body>
        <div class="card">
          <h1>Frontend Not Running Yet</h1>
          <p>Flask is up, but there is no exported frontend to serve and no live Next.js dev server responding at <strong>{FRONTEND_DEV_SERVER}</strong>.</p>
          <p>Use one of these options:</p>
          <code>cd frontend && npm.cmd run dev</code>
          <code>cd frontend && npm.cmd run build</code>
          <p>The first option enables live frontend development. The second creates a static frontend that Flask can serve directly on port 5000.</p>
        </div>
      </body>
    </html>
    """
    return Response(html, status=503, mimetype="text/html")


def create_flask_bridge() -> Flask:
    flask_app = Flask(__name__, static_folder=None)

    @flask_app.route("/", defaults={"path": ""}, methods=["GET", "HEAD"])
    @flask_app.route("/<path:path>", methods=["GET", "HEAD"])
    def serve_frontend(path: str) -> Response:
        if _is_fastapi_path(f"/{path}" if path else "/"):
            return Response(status=404)

        static_response = _frontend_export_response(path)
        if static_response is not None:
            return static_response

        proxy_response = _proxy_frontend_request(path)
        if proxy_response is not None:
            return proxy_response

        return _frontend_unavailable_response()

    fastapi_wsgi = ASGIMiddleware(create_fastapi_app())
    original_flask_wsgi = flask_app.wsgi_app

    def composite_app(environ, start_response):
        path = environ.get("PATH_INFO", "") or "/"
        if _is_fastapi_path(path):
            return fastapi_wsgi(environ, start_response)
        return original_flask_wsgi(environ, start_response)

    flask_app.wsgi_app = composite_app
    return flask_app


flask_app = create_flask_bridge()
