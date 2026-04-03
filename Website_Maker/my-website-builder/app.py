from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for
from flask_cors import CORS
from sqlalchemy.exc import IntegrityError

from models import Project, ProjectVersion, User, db
from published_site import build_published_context

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("PROJECT_DATA_DIR", BASE_DIR / "data")).resolve()
FRONTEND_DIR = Path(os.environ.get("FRONTEND_DIR", BASE_DIR / "out")).resolve()
DATABASE_PATH = Path(
    os.environ.get("DATABASE_PATH", DATA_DIR / "website_builder.db")
).resolve()
CLIENT_ERROR_LOG = Path(
    os.environ.get("CLIENT_ERROR_LOG", DATA_DIR / "client_errors.log")
).resolve()
DEFAULT_USERNAME = os.environ.get("DEFAULT_USERNAME", "local-builder").strip() or "local-builder"

app = Flask(
    __name__,
    static_folder=None,
    template_folder=str(BASE_DIR / "templates"),
)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _ensure_database() -> None:
    _ensure_data_dir()

    with app.app_context():
        db.create_all()
        _get_or_create_user(DEFAULT_USERNAME)


def _frontend_ready() -> bool:
    return FRONTEND_DIR.exists() and FRONTEND_DIR.is_dir()


def _parse_project_json(raw_json: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _project_counts(payload: dict[str, Any]) -> dict[str, int]:
    pages = payload.get("pages")
    elements = payload.get("elements")

    return {
        "pageCount": len(pages) if isinstance(pages, list) else 0,
        "elementCount": len(elements) if isinstance(elements, dict) else 0,
    }


def _project_theme_id(payload: dict[str, Any]) -> str | None:
    theme_id = payload.get("themeId")
    return theme_id if isinstance(theme_id, str) and theme_id.strip() else None


def _serialize_project_version(
    version: ProjectVersion,
    *,
    include_payload: bool = False,
) -> dict[str, Any]:
    payload = _parse_project_json(version.json_data)
    serialized = {
        "id": version.id,
        "projectId": version.project_id,
        "label": version.label,
        "createdAt": version.created_at.isoformat(),
        **_project_counts(payload),
    }

    if include_payload:
        serialized["project"] = payload

    return serialized


def _serialize_project(project: Project, *, include_payload: bool = True) -> dict[str, Any]:
    payload = _parse_project_json(project.json_data)
    latest_version = project.versions[0] if project.versions else None

    serialized = {
        "id": project.id,
        "userId": project.user_id,
        "username": project.user.username if project.user else None,
        "name": project.name,
        "publishedUrl": project.published_url,
        "themeId": _project_theme_id(payload),
        **_project_counts(payload),
        "versionCount": len(project.versions),
        "latestVersion": _serialize_project_version(latest_version)
        if latest_version
        else None,
    }

    if include_payload:
        serialized["project"] = payload

    return serialized


def _get_or_create_user(username: str) -> User:
    normalized_username = username.strip() or DEFAULT_USERNAME
    user = User.query.filter_by(username=normalized_username).one_or_none()

    if user:
        return user

    user = User(username=normalized_username)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing_user = User.query.filter_by(username=normalized_username).one_or_none()
        if existing_user:
            return existing_user
        raise

    return user


def _extract_project_payload(
    payload: dict[str, Any],
) -> tuple[str, str, dict[str, Any], int | None, str | None, str | None, bool]:
    username = str(payload.get("username") or DEFAULT_USERNAME).strip() or DEFAULT_USERNAME

    raw_project = payload.get("project")
    project_data = raw_project if isinstance(raw_project, dict) else payload

    project_id_value = payload.get("projectId") or payload.get("project_id") or payload.get("id")
    project_id = int(project_id_value) if project_id_value is not None else None

    project_name = str(
        payload.get("name")
        or project_data.get("projectName")
        or project_data.get("name")
        or f"Project {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    ).strip()

    published_url = payload.get("publishedUrl") or payload.get("published_url")
    published_url_provided = "publishedUrl" in payload or "published_url" in payload
    if published_url is not None:
        published_url = str(published_url).strip() or None

    version_label = payload.get("versionLabel") or payload.get("version_label")
    if version_label is not None:
        version_label = str(version_label).strip() or None

    return (
        username,
        project_name,
        project_data,
        project_id,
        published_url,
        version_label,
        published_url_provided,
    )


def _get_project_for_user(user: User, project_id: int) -> Project | None:
    return Project.query.filter_by(id=project_id, user_id=user.id).one_or_none()


def _create_project_version(
    project: Project,
    project_data: dict[str, Any],
    version_label: str | None = None,
) -> ProjectVersion:
    label = version_label

    if not label:
        label = "Initial save" if not project.versions else f"Version {len(project.versions) + 1}"

    version = ProjectVersion(
        project=project,
        label=label,
        json_data=json.dumps(project_data),
    )
    db.session.add(version)
    return version


def _serve_exported_path(asset_path: str):
    if not _frontend_ready():
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Frontend export not found. Run `npm run build` first.",
                    "frontendDir": str(FRONTEND_DIR),
                }
            ),
            503,
        )

    direct_file = FRONTEND_DIR / asset_path
    if asset_path and direct_file.is_file():
        return send_from_directory(FRONTEND_DIR, asset_path)

    directory_index = FRONTEND_DIR / asset_path / "index.html"
    if asset_path and directory_index.is_file():
        return send_from_directory(directory_index.parent, "index.html")

    html_file = FRONTEND_DIR / f"{asset_path}.html"
    if asset_path and html_file.is_file():
        return send_from_directory(FRONTEND_DIR, f"{asset_path}.html")

    root_index = FRONTEND_DIR / "index.html"
    if not asset_path and root_index.is_file():
        return send_from_directory(FRONTEND_DIR, "index.html")

    not_found = FRONTEND_DIR / "404.html"
    if not_found.is_file():
        return send_from_directory(FRONTEND_DIR, "404.html"), 404

    abort(404)


@app.get("/api/health")
def api_health():
    return jsonify(
        {
            "status": "ok",
            "frontendReady": _frontend_ready(),
            "frontendDir": str(FRONTEND_DIR),
            "databasePath": str(DATABASE_PATH),
            "defaultUsername": DEFAULT_USERNAME,
        }
    )


@app.post("/api/client-errors")
def log_client_error():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"status": "ignored"}), 202

    _ensure_data_dir()
    entry = {
        "receivedAt": datetime.now(timezone.utc).isoformat(),
        "path": request.headers.get("Referer"),
        "payload": payload,
    }

    with CLIENT_ERROR_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")

    return jsonify({"status": "ok"}), 202


@app.get("/api/projects")
def get_projects():
    username = request.args.get("username", DEFAULT_USERNAME).strip() or DEFAULT_USERNAME
    project_id = request.args.get("project_id", type=int) or request.args.get("id", type=int)

    user = _get_or_create_user(username)

    if project_id is not None:
        project = _get_project_for_user(user, project_id)

        if not project:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Project {project_id} was not found for user '{username}'.",
                    }
                ),
                404,
            )

        serialized = _serialize_project(project)
        return jsonify(
            {
                "status": "ok",
                "project": serialized,
                "projectId": project.id,
            }
        )

    projects = Project.query.filter_by(user_id=user.id).order_by(Project.id.desc()).all()

    if not projects:
        return jsonify(
            {
                "status": "empty",
                "message": f"No projects have been saved for '{username}' yet.",
                "username": username,
                "projectCount": 0,
                "projects": [],
                "latestProject": None,
            }
        )

    serialized_projects = [
        _serialize_project(project, include_payload=False) for project in projects
    ]

    return jsonify(
        {
            "status": "ok",
            "username": username,
            "projectCount": len(serialized_projects),
            "projects": serialized_projects,
            "latestProject": serialized_projects[0],
        }
    )


@app.post("/api/projects")
def save_project():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Expected a JSON object payload for the project snapshot.",
                }
            ),
            400,
        )

    try:
        (
            username,
            project_name,
            project_data,
            project_id,
            published_url,
            version_label,
            published_url_provided,
        ) = _extract_project_payload(payload)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Project id must be a valid integer when provided.",
                }
            ),
            400,
        )

    user = _get_or_create_user(username)
    project: Project | None = None

    if project_id is not None:
        project = _get_project_for_user(user, project_id)
        if project is None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Project {project_id} was not found for user '{username}'.",
                    }
                ),
                404,
            )

    if project is None:
        project = Project(
            user_id=user.id,
            name=project_name,
            json_data="{}",
            published_url=published_url,
        )
        db.session.add(project)

    project.name = project_name
    project.json_data = json.dumps(project_data)
    if published_url_provided:
        project.published_url = published_url
    version = _create_project_version(project, project_data, version_label)
    db.session.commit()

    serialized = _serialize_project(project)
    saved_at = version.created_at.isoformat()

    return jsonify(
        {
            "status": "ok",
            "savedAt": saved_at,
            "projectId": project.id,
            "project": serialized,
            "version": _serialize_project_version(version),
        }
    )


@app.post("/api/projects/publish")
def publish_project():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Expected a JSON object payload for the project snapshot.",
                }
            ),
            400,
        )

    try:
        (
            username,
            project_name,
            project_data,
            project_id,
            _published_url,
            version_label,
            _published_url_provided,
        ) = _extract_project_payload(payload)
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Project id must be a valid integer when provided.",
                }
            ),
            400,
        )

    user = _get_or_create_user(username)
    project: Project | None = None

    if project_id is not None:
        project = _get_project_for_user(user, project_id)
        if project is None:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Project {project_id} was not found for user '{username}'.",
                    }
                ),
                404,
            )

    if project is None:
        project = Project(
            user_id=user.id,
            name=project_name,
            json_data="{}",
            published_url=None,
        )
        db.session.add(project)

    project.name = project_name
    project.json_data = json.dumps(project_data)
    db.session.flush()
    project.published_url = url_for(
        "serve_published_project",
        project_id=project.id,
        _external=True,
    )

    version = _create_project_version(
        project,
        project_data,
        version_label or "Published snapshot",
    )
    db.session.commit()

    serialized = _serialize_project(project)
    saved_at = version.created_at.isoformat()

    return jsonify(
        {
            "status": "ok",
            "savedAt": saved_at,
            "projectId": project.id,
            "publishedUrl": project.published_url,
            "project": serialized,
            "version": _serialize_project_version(version),
        }
    )


@app.get("/api/projects/<int:project_id>/versions")
def get_project_versions(project_id: int):
    username = request.args.get("username", DEFAULT_USERNAME).strip() or DEFAULT_USERNAME
    user = _get_or_create_user(username)
    project = _get_project_for_user(user, project_id)

    if project is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Project {project_id} was not found for user '{username}'.",
                }
            ),
            404,
        )

    return jsonify(
        {
            "status": "ok",
            "projectId": project.id,
            "versions": [_serialize_project_version(version) for version in project.versions],
        }
    )


@app.get("/api/projects/<int:project_id>/versions/<int:version_id>")
def get_project_version(project_id: int, version_id: int):
    username = request.args.get("username", DEFAULT_USERNAME).strip() or DEFAULT_USERNAME
    user = _get_or_create_user(username)
    project = _get_project_for_user(user, project_id)

    if project is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Project {project_id} was not found for user '{username}'.",
                }
            ),
            404,
        )

    version = ProjectVersion.query.filter_by(
        id=version_id,
        project_id=project.id,
    ).one_or_none()

    if version is None:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Version {version_id} was not found for project {project_id}.",
                }
            ),
            404,
        )

    return jsonify(
        {
            "status": "ok",
            "projectId": project.id,
            "version": _serialize_project_version(version, include_payload=True),
        }
    )


@app.get("/p/<int:project_id>")
def serve_published_project(project_id: int):
    project = Project.query.filter_by(id=project_id).one_or_none()

    if project is None:
        abort(404)

    payload = _parse_project_json(project.json_data)

    try:
        context = build_published_context(
            project_id=project.id,
            project_name=project.name,
            payload=payload,
            base_url=url_for("serve_published_project", project_id=project.id),
        )
    except ValueError as error:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": str(error),
                    "projectId": project.id,
                }
            ),
            422,
        )

    published_root_url = url_for(
        "serve_published_project",
        project_id=project.id,
        _external=True,
    )

    if project.published_url != published_root_url:
        project.published_url = published_root_url
        db.session.commit()

    if (
        context["has_multiple_pages"]
        and context["current_page"]["slug"] != context["page_links"][0]["slug"]
    ):
        return redirect(context["current_page"]["url"])

    return render_template("published_site.html", **context)


@app.get("/p/<int:project_id>/<page_slug>")
def serve_published_project_page(project_id: int, page_slug: str):
    project = Project.query.filter_by(id=project_id).one_or_none()

    if project is None:
        abort(404)

    payload = _parse_project_json(project.json_data)

    try:
        context = build_published_context(
            project_id=project.id,
            project_name=project.name,
            payload=payload,
            requested_page_slug=page_slug,
            base_url=url_for("serve_published_project", project_id=project.id),
        )
    except ValueError as error:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": str(error),
                    "projectId": project.id,
                }
            ),
            422,
        )

    return render_template("published_site.html", **context)


@app.get("/")
def serve_index():
    return _serve_exported_path("")


@app.get("/<path:asset_path>")
def serve_frontend(asset_path: str):
    if asset_path.startswith("api/"):
        abort(404)

    return _serve_exported_path(asset_path)


_ensure_database()


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"

    if debug:
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        try:
            from waitress import serve

            serve(app, host="0.0.0.0", port=port)
        except ImportError:
            app.run(host="0.0.0.0", port=port, debug=False)
