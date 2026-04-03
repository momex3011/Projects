from __future__ import annotations

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    projects = db.relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True,
    )


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    json_data = db.Column(db.Text, nullable=False)
    published_url = db.Column(db.String(255), nullable=True)
    user = db.relationship("User", back_populates="projects")
    versions = db.relationship(
        "ProjectVersion",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="desc(ProjectVersion.id)",
    )


class ProjectVersion(db.Model):
    __tablename__ = "project_versions"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer,
        db.ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    label = db.Column(db.String(160), nullable=False)
    json_data = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    project = db.relationship("Project", back_populates="versions")
