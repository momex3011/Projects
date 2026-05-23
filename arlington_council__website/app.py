from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
from html import escape, unescape
from html.parser import HTMLParser
import json
import os
import re
import secrets
from urllib.parse import urlparse, urlunparse

from markupsafe import Markup

from flask import (
    Flask,
    abort,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_admin import Admin, AdminIndexView, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_babel import Babel, format_datetime as babel_format_datetime, gettext, lazy_gettext as _l, refresh
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from wtforms import (
    BooleanField,
    DateTimeLocalField,
    DecimalField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, EqualTo, Length, NumberRange, Optional, ValidationError


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def load_secret_key():
    configured_secret = os.environ.get("SECRET_KEY")
    if configured_secret:
        return configured_secret
    instance_dir = os.path.join(BASE_DIR, "instance")
    os.makedirs(instance_dir, exist_ok=True)
    secret_path = os.path.join(instance_dir, "dev_secret_key.txt")
    if os.path.exists(secret_path):
        with open(secret_path, "r", encoding="utf-8") as secret_file:
            return secret_file.read().strip()
    generated_secret = secrets.token_urlsafe(48)
    with open(secret_path, "w", encoding="utf-8") as secret_file:
        secret_file.write(generated_secret)
    return generated_secret


def get_locale():
    view_args = getattr(request, "view_args", None) or {}
    locale = view_args.get("locale") or session.get("locale")
    path_locale = request.path.lstrip("/").split("/", 1)[0]
    if path_locale in app.config["BABEL_SUPPORTED_LANGUAGES"]:
        return path_locale
    if locale in app.config["BABEL_SUPPORTED_LANGUAGES"]:
        return locale
    return request.accept_languages.best_match(app.config["BABEL_SUPPORTED_LANGUAGES"]) or app.config["BABEL_DEFAULT_LOCALE"]


def choose_locale():
    session_locale = session.get("locale")
    if session_locale in app.config["BABEL_SUPPORTED_LANGUAGES"]:
        return session_locale
    return request.accept_languages.best_match(app.config["BABEL_SUPPORTED_LANGUAGES"]) or app.config["BABEL_DEFAULT_LOCALE"]


def is_safe_redirect(target):
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc and target.startswith("/") and not target.startswith("//")


app = Flask(__name__)
app.config["SECRET_KEY"] = load_secret_key()
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'site.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["BABEL_DEFAULT_LOCALE"] = "en"
app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"
app.config["BABEL_SUPPORTED_LANGUAGES"] = ["en", "es"]
app.config["WTF_CSRF_TIME_LIMIT"] = 7200

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
babel = Babel(app, locale_selector=get_locale)


class Role:
    ADMIN = "admin"
    COUNCIL_MEMBER = "council_member"
    TRACKER = "tracker"
    NEWS_EDITOR = "news_editor"

    CHOICES = [
        (ADMIN, _l("Admin")),
        (COUNCIL_MEMBER, _l("Council Member")),
        (TRACKER, _l("Project Tracker")),
        (NEWS_EDITOR, _l("News Editor")),
    ]


class Permission:
    CREATE_PROJECT = "create_project"
    EDIT_PROJECT = "edit_project"
    ASSIGN_TRACKER = "assign_tracker"
    TRACK_ASSIGNED_PROJECT = "track_assigned_project"
    TRACK_ANY_PROJECT = "track_any_project"
    UPDATE_PROJECT_STATUS = "update_project_status"
    ADD_PROJECT_COMMENT = "add_project_comment"
    VOTE_PROJECT = "vote_project"
    VIEW_VOTE_RESULTS = "view_vote_results"
    CREATE_PROPOSAL = "create_proposal"
    VOTE_PROPOSAL = "vote_proposal"
    MANAGE_HOME_CONTENT = "manage_home_content"


PERMISSION_DEFINITIONS = [
    {
        "key": Permission.CREATE_PROJECT,
        "label": _l("Create projects"),
        "description": _l("Create new public projects and set their core details."),
    },
    {
        "key": Permission.EDIT_PROJECT,
        "label": _l("Edit projects"),
        "description": _l("Change project descriptions, dates, categories, status, and voting deadlines."),
    },
    {
        "key": Permission.ASSIGN_TRACKER,
        "label": _l("Assign project trackers"),
        "description": _l("Choose which tracker is responsible for a project."),
    },
    {
        "key": Permission.TRACK_ASSIGNED_PROJECT,
        "label": _l("Track assigned projects"),
        "description": _l("Open the tracker workspace for projects assigned to this user."),
    },
    {
        "key": Permission.TRACK_ANY_PROJECT,
        "label": _l("Track any project"),
        "description": _l("Open the tracker workspace for any project, even if not assigned."),
    },
    {
        "key": Permission.UPDATE_PROJECT_STATUS,
        "label": _l("Update project status"),
        "description": _l("Move a project between pending, in progress, and completed."),
    },
    {
        "key": Permission.ADD_PROJECT_COMMENT,
        "label": _l("Add project updates"),
        "description": _l("Post field updates, blockers, and notes on project activity."),
    },
    {
        "key": Permission.VOTE_PROJECT,
        "label": _l("Vote on projects"),
        "description": _l("Submit or update votes on project decisions before the deadline."),
    },
    {
        "key": Permission.VIEW_VOTE_RESULTS,
        "label": _l("View vote results"),
        "description": _l("See project voting results and decision totals."),
    },
    {
        "key": Permission.CREATE_PROPOSAL,
        "label": _l("Create proposals"),
        "description": _l("Create council proposals and choose who can see and vote on them."),
    },
    {
        "key": Permission.VOTE_PROPOSAL,
        "label": _l("Vote on proposals"),
        "description": _l("Vote on eligible council proposals."),
    },
    {
        "key": Permission.MANAGE_HOME_CONTENT,
        "label": _l("Manage home content"),
        "description": _l("Create and edit home page announcements and newspaper-style news posts."),
    },
]


ROLE_DEFAULT_PERMISSIONS = {
    Role.ADMIN: {item["key"] for item in PERMISSION_DEFINITIONS},
    Role.COUNCIL_MEMBER: {
        Permission.VOTE_PROJECT,
        Permission.VIEW_VOTE_RESULTS,
        Permission.CREATE_PROPOSAL,
        Permission.VOTE_PROPOSAL,
        Permission.MANAGE_HOME_CONTENT,
    },
    Role.TRACKER: {
        Permission.TRACK_ASSIGNED_PROJECT,
        Permission.UPDATE_PROJECT_STATUS,
        Permission.ADD_PROJECT_COMMENT,
    },
    Role.NEWS_EDITOR: {
        Permission.MANAGE_HOME_CONTENT,
    },
}


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.COUNCIL_MEMBER)
    contact_details = db.Column(db.Text)
    permissions = db.Column(db.Text)

    tracked_projects = db.relationship("Project", backref="tracker", lazy=True, foreign_keys="Project.tracker_id")
    created_projects = db.relationship("Project", backref="creator", lazy=True, foreign_keys="Project.created_by_id")
    votes = db.relationship("Vote", backref="user", lazy=True, cascade="all, delete-orphan")
    volunteering_projects = db.relationship("ProjectMember", backref="user", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("ProjectComment", backref="author", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"

    def has_permission(self, permission):
        if self.role == Role.ADMIN:
            return True
        config = parse_permission_config(self.permissions)
        default_permissions = ROLE_DEFAULT_PERMISSIONS.get(self.role, set())
        allowed_by_default = permission in default_permissions
        if config["use_defaults"]:
            return allowed_by_default
        if permission in config["deny"]:
            return False
        return allowed_by_default or permission in config["allow"]

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


def parse_permission_config(raw_permissions):
    raw_permissions = (raw_permissions or "").strip()
    if not raw_permissions:
        return {"use_defaults": True, "allow": set(), "deny": set()}
    try:
        config = json.loads(raw_permissions)
    except (TypeError, ValueError):
        legacy_permissions = {item.strip() for item in raw_permissions.split(",") if item.strip()}
        return {"use_defaults": False, "allow": legacy_permissions, "deny": set()}
    if not isinstance(config, dict):
        return {"use_defaults": True, "allow": set(), "deny": set()}
    use_defaults_value = config.get("use_defaults", True)
    if isinstance(use_defaults_value, bool):
        use_defaults = use_defaults_value
    elif isinstance(use_defaults_value, str):
        use_defaults = use_defaults_value.strip().lower() not in {"false", "0", "no", "off"}
    else:
        use_defaults = True
    return {
        "use_defaults": use_defaults,
        "allow": {item for item in config.get("allow", []) if item in permission_keys()},
        "deny": {item for item in config.get("deny", []) if item in permission_keys()},
    }


def serialize_permission_config(use_defaults, overrides):
    allow = []
    deny = []
    if not use_defaults:
        for permission in permission_keys():
            state = overrides.get(permission, "default")
            if state == "allow":
                allow.append(permission)
            elif state == "deny":
                deny.append(permission)
    return json.dumps({"use_defaults": use_defaults, "allow": allow, "deny": deny}, ensure_ascii=False)


def permission_keys():
    return [item["key"] for item in PERMISSION_DEFINITIONS]


def permission_label(permission):
    value = next((item["label"] for item in PERMISSION_DEFINITIONS if item["key"] == permission), permission)
    return str(value) if value != permission else gettext(permission)


def permission_description(permission):
    value = next((item["description"] for item in PERMISSION_DEFINITIONS if item["key"] == permission), permission)
    return str(value) if value != permission else gettext(permission)


def role_label(role):
    return {
        Role.ADMIN: gettext("Admin"),
        Role.COUNCIL_MEMBER: gettext("Council Member"),
        Role.TRACKER: gettext("Project Tracker"),
        Role.NEWS_EDITOR: gettext("News Editor"),
    }.get(role, role)


def role_description(role):
    descriptions = {
        Role.ADMIN: _l("Admins manage users, projects, donations, site links, and all council operations."),
        Role.COUNCIL_MEMBER: _l("Council members review projects, vote on decisions, and create or vote on proposals."),
        Role.TRACKER: _l("Project trackers report progress on assigned projects, update status, and add field notes."),
        Role.NEWS_EDITOR: _l("News editors prepare short public news posts with images for the home page."),
    }
    return str(descriptions.get(role, _l("This role uses the permissions selected below.")))


def role_description_items():
    return [
        {"role": Role.ADMIN, "label": role_label(Role.ADMIN), "description": role_description(Role.ADMIN)},
        {
            "role": Role.COUNCIL_MEMBER,
            "label": role_label(Role.COUNCIL_MEMBER),
            "description": role_description(Role.COUNCIL_MEMBER),
        },
        {"role": Role.TRACKER, "label": role_label(Role.TRACKER), "description": role_description(Role.TRACKER)},
        {"role": Role.NEWS_EDITOR, "label": role_label(Role.NEWS_EDITOR), "description": role_description(Role.NEWS_EDITOR)},
    ]


def permission_editor_rows(user):
    config = parse_permission_config(user.permissions)
    role_defaults = ROLE_DEFAULT_PERMISSIONS.get(user.role, set())
    rows = []
    for item in PERMISSION_DEFINITIONS:
        key = item["key"]
        role_default_map = {
            Role.ADMIN: key in ROLE_DEFAULT_PERMISSIONS.get(Role.ADMIN, set()),
            Role.COUNCIL_MEMBER: key in ROLE_DEFAULT_PERMISSIONS.get(Role.COUNCIL_MEMBER, set()),
            Role.TRACKER: key in ROLE_DEFAULT_PERMISSIONS.get(Role.TRACKER, set()),
            Role.NEWS_EDITOR: key in ROLE_DEFAULT_PERMISSIONS.get(Role.NEWS_EDITOR, set()),
        }
        if config["use_defaults"]:
            state = "default"
        elif key in config["allow"]:
            state = "allow"
        elif key in config["deny"]:
            state = "deny"
        else:
            state = "default"
        rows.append(
            {
                "key": key,
                "label": permission_label(key),
                "description": permission_description(key),
                "default_enabled": key in role_defaults,
                "defaults": role_default_map,
                "state": state,
            }
        )
    return rows


def tracker_assignable_users():
    return [
        user
        for user in User.query.order_by(User.role.asc(), User.username.asc()).all()
        if user.role != Role.ADMIN
        and (
            user.has_permission(Permission.TRACK_ASSIGNED_PROJECT)
            or user.has_permission(Permission.TRACK_ANY_PROJECT)
        )
    ]


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tracker_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    status = db.Column(db.String(20), default="Pending")
    category = db.Column(db.String(50))
    voting_deadline = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    vote_type = db.Column(db.String(50), default="simple_majority")

    votes = db.relationship("Vote", backref="project", lazy=True, cascade="all, delete-orphan")
    volunteers = db.relationship("ProjectMember", backref="project", lazy=True, cascade="all, delete-orphan")
    comments = db.relationship("ProjectComment", backref="project", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Project('{self.title}', '{self.status}')"

    @property
    def is_open_for_voting(self):
        return not self.voting_deadline or self.voting_deadline > datetime.utcnow()

    @property
    def is_active(self):
        return self.status in {"Pending", "In Progress"}

    def progress(self):
        if not self.start_date or not self.end_date:
            return 0
        now = datetime.utcnow()
        if now <= self.start_date:
            return 0
        if now >= self.end_date:
            return 100
        total_seconds = (self.end_date - self.start_date).total_seconds()
        if total_seconds <= 0:
            return 100
        return max(0, min(100, ((now - self.start_date).total_seconds() / total_seconds) * 100))

    def voting_progress(self):
        if not self.start_date or not self.voting_deadline:
            return 0
        now = datetime.utcnow()
        if self.voting_deadline <= self.start_date:
            return 0
        if now <= self.start_date:
            return 0
        if now >= self.voting_deadline:
            return 100
        total_seconds = (self.voting_deadline - self.start_date).total_seconds()
        if total_seconds <= 0:
            return 100
        return max(0, min(100, ((now - self.start_date).total_seconds() / total_seconds) * 100))

    def vote_counts(self):
        yes_votes = Vote.query.filter_by(project_id=self.id, vote=True).count()
        no_votes = Vote.query.filter_by(project_id=self.id, vote=False).count()
        return yes_votes, no_votes


class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    vote = db.Column(db.Boolean, nullable=False)
    vote_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "project_id", name="unique_vote"),)

    def __repr__(self):
        return f"Vote('{self.user_id}', '{self.project_id}', '{self.vote}')"


class CouncilProposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    summary = db.Column(db.String(240))
    body = db.Column(db.Text, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    visibility = db.Column(db.String(20), nullable=False, default="council")
    vote_visibility = db.Column(db.String(20), nullable=False, default="anonymous")
    status = db.Column(db.String(20), nullable=False, default="Open")
    voting_deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship("User", backref=db.backref("created_proposals", lazy=True))
    votes = db.relationship("CouncilProposalVote", backref="proposal", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"CouncilProposal('{self.title}', '{self.visibility}', '{self.status}')"

    @property
    def is_open_for_voting(self):
        if self.status != "Open":
            return False
        return not self.voting_deadline or self.voting_deadline > datetime.utcnow()

    def vote_counts(self):
        return {
            "Yes": CouncilProposalVote.query.filter_by(proposal_id=self.id, choice="Yes").count(),
            "No": CouncilProposalVote.query.filter_by(proposal_id=self.id, choice="No").count(),
            "Abstain": CouncilProposalVote.query.filter_by(proposal_id=self.id, choice="Abstain").count(),
        }


class CouncilProposalVote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("council_proposal.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    choice = db.Column(db.String(20), nullable=False)
    comment = db.Column(db.Text)
    vote_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("proposal_votes", lazy=True, cascade="all, delete-orphan"))

    __table_args__ = (db.UniqueConstraint("proposal_id", "user_id", name="unique_proposal_vote"),)

    def __repr__(self):
        return f"CouncilProposalVote('{self.proposal_id}', '{self.user_id}', '{self.choice}')"


class PublicSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_type = db.Column(db.String(30), nullable=False, default="council")
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"))
    submitted_by_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    name = db.Column(db.String(120))
    contact = db.Column(db.String(160))
    title = db.Column(db.String(140), nullable=False)
    body = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="New")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    project = db.relationship("Project", backref=db.backref("suggestions", lazy=True, cascade="all, delete-orphan"))
    submitter = db.relationship("User", backref=db.backref("submitted_suggestions", lazy=True))

    def __repr__(self):
        return f"PublicSuggestion('{self.title}', '{self.target_type}', '{self.status}')"


class HomePost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_type = db.Column(db.String(20), nullable=False, default="news")
    title = db.Column(db.String(160), nullable=False)
    summary = db.Column(db.String(260))
    body = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500))
    is_published = db.Column(db.Boolean, nullable=False, default=True)
    show_on_home = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship("User", backref=db.backref("home_posts", lazy=True))

    def __repr__(self):
        return f"HomePost('{self.title}', '{self.post_type}', '{self.is_published}')"


class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_name = db.Column(db.String(100), nullable=False)
    additional_info = db.Column(db.Text)

    def __repr__(self):
        return f"Volunteer('{self.name}', '{self.project_name}')"


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text)

    def __repr__(self):
        return f"<Setting {self.key}>"


DEFAULT_SITE_LINKS = {
    "instagram_url": "https://www.instagram.com/cityofarlington",
    "whatsapp_url": "#",
    "facebook_url": "https://www.facebook.com/CityofArlington",
    "twitter_url": "https://x.com/CityOfArlington",
    "telegram_url": "#",
}

DEFAULT_SITE_LINK_VISIBILITY = {
    "instagram_enabled": "1",
    "whatsapp_enabled": "0",
    "facebook_enabled": "1",
    "twitter_enabled": "1",
    "telegram_enabled": "0",
}

DEFAULT_SITE_LINK_DESCRIPTIONS = {
    "instagram_description_en": "Photos, announcements, and Arlington community updates.",
    "instagram_description_ar": "Fotos, anuncios y noticias comunitarias de Arlington.",
    "whatsapp_description_en": "Optional direct contact channel for urgent resident updates.",
    "whatsapp_description_ar": "Canal opcional para avisos urgentes y contacto directo con residentes.",
    "facebook_description_en": "Public posts, city news, events, and resident-facing updates.",
    "facebook_description_ar": "Publicaciones, noticias de la ciudad, eventos y avisos para residentes.",
    "twitter_description_en": "Short city notices, service reminders, and public announcements.",
    "twitter_description_ar": "Avisos breves de la ciudad, recordatorios de servicios y anuncios publicos.",
    "telegram_description_en": "Optional public broadcast channel for alerts and civic updates.",
    "telegram_description_ar": "Canal opcional de difusion para alertas y actualizaciones civicas.",
}

SOCIAL_LINK_PLATFORMS = [
    {
        "key": "instagram",
        "title": "Instagram",
        "icon": "fab fa-instagram",
        "enabled_key": "instagram_enabled",
        "url_key": "instagram_url",
        "description_en_key": "instagram_description_en",
        "description_ar_key": "instagram_description_ar",
        "placeholder": "https://www.instagram.com/cityofarlington",
    },
    {
        "key": "whatsapp",
        "title": "WhatsApp",
        "icon": "fab fa-whatsapp",
        "enabled_key": "whatsapp_enabled",
        "url_key": "whatsapp_url",
        "description_en_key": "whatsapp_description_en",
        "description_ar_key": "whatsapp_description_ar",
        "placeholder": "https://wa.me/0000000000",
    },
    {
        "key": "facebook",
        "title": "Facebook",
        "icon": "fab fa-facebook",
        "enabled_key": "facebook_enabled",
        "url_key": "facebook_url",
        "description_en_key": "facebook_description_en",
        "description_ar_key": "facebook_description_ar",
        "placeholder": "https://www.facebook.com/CityofArlington",
    },
    {
        "key": "twitter",
        "title": "Twitter/X",
        "icon": "fab fa-twitter",
        "enabled_key": "twitter_enabled",
        "url_key": "twitter_url",
        "description_en_key": "twitter_description_en",
        "description_ar_key": "twitter_description_ar",
        "placeholder": "https://x.com/CityOfArlington",
    },
    {
        "key": "telegram",
        "title": "Telegram",
        "icon": "fab fa-telegram",
        "enabled_key": "telegram_enabled",
        "url_key": "telegram_url",
        "description_en_key": "telegram_description_en",
        "description_ar_key": "telegram_description_ar",
        "placeholder": "https://t.me/arlingtoncivic",
    },
]

USEFUL_SITES_SETTING_KEY = "useful_sites"
MAX_USEFUL_SITES = 12
HOME_NEWS_ENABLED_KEY = "home_news_enabled"


def empty_useful_site():
    return {
        "enabled": True,
        "title_en": "",
        "title_ar": "",
        "url": "",
        "description_en": "",
        "description_ar": "",
    }


def get_setting(key, default=""):
    setting = Settings.query.filter_by(key=key).first()
    if setting is None:
        return default
    return setting.value or ""


def set_setting(key, value):
    setting = Settings.query.filter_by(key=key).first()
    if setting is None:
        setting = Settings(key=key)
        db.session.add(setting)
    setting.value = value


def is_allowed_link_value(value):
    value = (value or "").strip()
    if not value or value == "#":
        return True
    parsed = urlparse(value)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https", "mailto", "tel"}:
        return False
    if scheme in {"http", "https"} and not parsed.netloc:
        return False
    if scheme in {"mailto", "tel"} and not parsed.path:
        return False
    return True


def get_site_links():
    links = {}
    for key, default in DEFAULT_SITE_LINKS.items():
        value = get_setting(key, default).strip()
        links[key] = value if value != "#" and is_allowed_link_value(value) else ""
    links.update({key: get_setting(key, default) == "1" for key, default in DEFAULT_SITE_LINK_VISIBILITY.items()})
    links.update({key: get_setting(key, default).strip() for key, default in DEFAULT_SITE_LINK_DESCRIPTIONS.items()})
    return links


def get_social_site_items():
    site_links = get_site_links()
    locale = get_locale()
    sites = []
    for platform in SOCIAL_LINK_PLATFORMS:
        url = site_links.get(platform["url_key"], "")
        if not site_links.get(platform["enabled_key"]) or not url:
            continue
        description = (
            site_links.get(platform["description_ar_key"])
            if locale == "es"
            else site_links.get(platform["description_en_key"])
        )
        fallback_description = (
            site_links.get(platform["description_en_key"])
            if locale == "es"
            else site_links.get(platform["description_ar_key"])
        )
        sites.append(
            {
                "title": gettext(platform["title"]),
                "url": url,
                "description": description or fallback_description,
                "icon": platform["icon"],
            }
        )
    return sites


def normalize_useful_site(site):
    cleaned = empty_useful_site()
    if not isinstance(site, dict):
        return cleaned
    cleaned["enabled"] = site.get("enabled") in {True, "1", "true", "True", "on", "yes"}
    cleaned["title_en"] = str(site.get("title_en") or site.get("title") or "").strip()[:120]
    cleaned["title_ar"] = str(site.get("title_ar") or "").strip()[:120]
    cleaned["url"] = str(site.get("url") or "").strip()[:500]
    cleaned["description_en"] = str(site.get("description_en") or site.get("description") or "").strip()[:500]
    cleaned["description_ar"] = str(site.get("description_ar") or "").strip()[:500]
    return cleaned


def get_useful_sites(include_disabled=False):
    raw_sites = get_setting(USEFUL_SITES_SETTING_KEY, "[]")
    try:
        stored_sites = json.loads(raw_sites)
    except (TypeError, ValueError):
        stored_sites = []
    if not isinstance(stored_sites, list):
        stored_sites = []

    sites = []
    locale = get_locale()
    for stored_site in stored_sites[:MAX_USEFUL_SITES]:
        site = normalize_useful_site(stored_site)
        if not any([site["title_en"], site["title_ar"], site["url"], site["description_en"], site["description_ar"]]):
            continue
        if not include_disabled and not site["enabled"]:
            continue
        if not is_allowed_link_value(site["url"]) or site["url"] == "#":
            continue

        if locale == "es":
            site["title"] = site["title_ar"] or site["title_en"]
            site["description"] = site["description_ar"] or site["description_en"]
        else:
            site["title"] = site["title_en"] or site["title_ar"]
            site["description"] = site["description_en"] or site["description_ar"]
        site["icon"] = "fa-solid fa-globe"
        if site["title"]:
            sites.append(site)
    return sites


def parse_useful_sites_form(form_data):
    sites = []
    errors = []
    indexes = form_data.getlist("custom_site_index")[:MAX_USEFUL_SITES]

    for index in indexes:
        index = str(index)
        site = {
            "enabled": form_data.get(f"custom_site_enabled_{index}") == "1",
            "title_en": (form_data.get(f"custom_site_title_en_{index}") or "").strip()[:120],
            "title_ar": (form_data.get(f"custom_site_title_ar_{index}") or "").strip()[:120],
            "url": (form_data.get(f"custom_site_url_{index}") or "").strip()[:500],
            "description_en": (form_data.get(f"custom_site_description_en_{index}") or "").strip()[:500],
            "description_ar": (form_data.get(f"custom_site_description_ar_{index}") or "").strip()[:500],
        }
        has_content = any(
            [
                site["title_en"],
                site["title_ar"],
                site["url"],
                site["description_en"],
                site["description_ar"],
            ]
        )
        if not has_content:
            continue
        if not site["title_en"] and not site["title_ar"]:
            errors.append(gettext("Each useful site needs a name."))
        if not site["url"]:
            errors.append(gettext("Each useful site needs a link."))
        elif not is_allowed_link_value(site["url"]) or site["url"] == "#":
            errors.append(gettext("Use a valid http, https, mailto, or tel link for each useful site."))
        sites.append(site)

    return sites, errors


RICH_TEXT_ALLOWED_TAGS = {
    "blockquote",
    "br",
    "em",
    "h2",
    "h3",
    "li",
    "ol",
    "p",
    "span",
    "strong",
    "u",
    "ul",
}
RICH_TEXT_TAG_ALIASES = {"b": "strong", "i": "em", "font": "span", "div": "p"}
RICH_TEXT_ALLOWED_COLORS = {"#006c35", "#00843d", "#ce1126", "#1f2a24", "#52665c"}
RICH_TEXT_ALLOWED_FONT_SIZES = {
    "0.95rem",
    "1rem",
    "1.12rem",
    "1.28rem",
    "1.55rem",
    "13px",
    "16px",
    "18px",
    "22px",
    "28px",
}
RICH_TEXT_FONT_SIZE_MAP = {"1": "0.95rem", "2": "0.95rem", "3": "1rem", "4": "1.28rem", "5": "1.55rem"}
RICH_TEXT_ALLOWED_FONTS = {
    "arial": "Arial, sans-serif",
    "georgia": "Georgia, serif",
    "tahoma": "Tahoma, sans-serif",
    "courier new": "'Courier New', monospace",
}
RICH_TEXT_ALLOWED_ALIGNMENTS = {"left", "center", "right"}


def normalize_rich_text_tag(tag):
    tag = (tag or "").lower()
    return RICH_TEXT_TAG_ALIASES.get(tag, tag)


def clean_rich_text_style(style_value):
    if not style_value:
        return ""
    cleaned = []
    for declaration in style_value.split(";"):
        if ":" not in declaration:
            continue
        name, value = declaration.split(":", 1)
        name = name.strip().lower()
        value = value.strip().strip('"').strip("'")
        value_lower = value.lower()
        if name == "font-size" and value_lower in RICH_TEXT_ALLOWED_FONT_SIZES:
            cleaned.append(f"font-size: {value_lower}")
        elif name == "font-family":
            first_family = value_lower.split(",", 1)[0].strip().strip('"').strip("'")
            if first_family in RICH_TEXT_ALLOWED_FONTS:
                cleaned.append(f"font-family: {RICH_TEXT_ALLOWED_FONTS[first_family]}")
        elif name == "text-align" and value_lower in RICH_TEXT_ALLOWED_ALIGNMENTS:
            cleaned.append(f"text-align: {value_lower}")
        elif name == "color" and value_lower in RICH_TEXT_ALLOWED_COLORS:
            cleaned.append(f"color: {value_lower}")
    return "; ".join(cleaned)


class RichTextSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.open_tags = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        normalized_tag = normalize_rich_text_tag(tag)
        if normalized_tag not in RICH_TEXT_ALLOWED_TAGS:
            return
        if normalized_tag == "br":
            self.parts.append("<br>")
            return

        attr_map = {name.lower(): value for name, value in attrs if name and value is not None}
        styles = []
        inline_style = clean_rich_text_style(attr_map.get("style"))
        if inline_style:
            styles.append(inline_style)

        if tag.lower() == "font":
            face = attr_map.get("face", "").lower()
            size = attr_map.get("size", "")
            color = attr_map.get("color", "").lower()
            if face in RICH_TEXT_ALLOWED_FONTS:
                styles.append(f"font-family: {RICH_TEXT_ALLOWED_FONTS[face]}")
            if size in RICH_TEXT_FONT_SIZE_MAP:
                styles.append(f"font-size: {RICH_TEXT_FONT_SIZE_MAP[size]}")
            if color in RICH_TEXT_ALLOWED_COLORS:
                styles.append(f"color: {color}")

        style_attribute = f' style="{escape("; ".join(styles), quote=True)}"' if styles else ""
        self.parts.append(f"<{normalized_tag}{style_attribute}>")
        self.open_tags.append(normalized_tag)

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        normalized_tag = normalize_rich_text_tag(tag)
        if normalized_tag not in self.open_tags:
            return
        while self.open_tags:
            current = self.open_tags.pop()
            self.parts.append(f"</{current}>")
            if current == normalized_tag:
                break

    def handle_data(self, data):
        if self.skip_depth:
            return
        self.parts.append(escape(data))

    def handle_entityref(self, name):
        if self.skip_depth:
            return
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        if self.skip_depth:
            return
        self.parts.append(f"&#{name};")

    def clean(self, html_value):
        self.feed(html_value or "")
        while self.open_tags:
            self.parts.append(f"</{self.open_tags.pop()}>")
        return "".join(self.parts).strip()


def sanitize_rich_text(value):
    return RichTextSanitizer().clean(value or "")


def rich_text_to_plain_text(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


@app.template_filter("rich_text")
def rich_text_filter(value):
    return Markup(sanitize_rich_text(value))


def validate_email_format(form, field):
    value = (field.data or "").strip()
    if not value:
        return
    if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
        raise ValidationError(_l("Enter a valid email address."))


def validate_safe_link(form, field):
    value = (field.data or "").strip()
    if not value or value == "#":
        return
    parsed = urlparse(value)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https", "mailto", "tel"}:
        raise ValidationError(_l("Use a valid http, https, mailto, or tel link."))
    if scheme in {"http", "https"} and not parsed.netloc:
        raise ValidationError(_l("Use a complete link, including the website address."))
    if scheme in {"mailto", "tel"} and not parsed.path:
        raise ValidationError(_l("Use a complete link target."))


def validate_image_link(form, field):
    value = (field.data or "").strip()
    if not value:
        return
    if value.startswith("/static/uploads/home_posts/"):
        return
    parsed = urlparse(value)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError(_l("Use a complete http or https image link, or upload a picture."))


class ProjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    volunteer_name = db.Column(db.String(100))

    def __repr__(self):
        return f"ProjectMember('{self.user_id}', '{self.project_id}')"


class ProjectComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"ProjectComment('{self.project_id}', '{self.user_id}')"


class DonationCampaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    currency = db.Column(db.String(10), nullable=False, default="USD")
    beneficiary = db.Column(db.String(140))
    payment_instructions = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="Active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    groups = db.relationship("DonationGroup", backref="campaign", lazy=True, cascade="all, delete-orphan")
    donations = db.relationship("Donation", backref="campaign", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"DonationCampaign('{self.title}', '{self.status}')"

    def confirmed_total(self):
        total = (
            db.session.query(db.func.coalesce(db.func.sum(Donation.amount), 0))
            .filter_by(campaign_id=self.id, payment_status="Confirmed")
            .scalar()
        )
        return Decimal(total or 0)

    def pledged_total(self):
        total = (
            db.session.query(db.func.coalesce(db.func.sum(Donation.amount), 0))
            .filter(Donation.campaign_id == self.id, Donation.payment_status.in_(["Pending", "Confirmed"]))
            .scalar()
        )
        return Decimal(total or 0)

    def progress(self):
        if not self.goal_amount:
            return 0
        return max(0, min(100, float((self.confirmed_total() / self.goal_amount) * 100)))


class DonationGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("donation_campaign.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    donations = db.relationship("Donation", backref="group", lazy=True)

    def __repr__(self):
        return f"DonationGroup('{self.name}', '{self.campaign_id}')"

    def confirmed_total(self):
        total = (
            db.session.query(db.func.coalesce(db.func.sum(Donation.amount), 0))
            .filter_by(group_id=self.id, payment_status="Confirmed")
            .scalar()
        )
        return Decimal(total or 0)


class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("donation_campaign.id"), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey("donation_group.id"))
    donor_name = db.Column(db.String(120), nullable=False)
    donor_email = db.Column(db.String(120))
    donor_phone = db.Column(db.String(50))
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    attribution_type = db.Column(db.String(20), nullable=False, default="independent")
    display_name = db.Column(db.Boolean, nullable=False, default=True)
    payment_method = db.Column(db.String(30), nullable=False, default="bank_transfer")
    payment_status = db.Column(db.String(20), nullable=False, default="Pending")
    payment_reference = db.Column(db.String(40), nullable=False, unique=True, index=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"Donation('{self.donor_name}', '{self.amount}', '{self.payment_status}')"

    def public_name(self):
        return self.donor_name if self.display_name else gettext("Anonymous donor")


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


class RegistrationForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField(_l("Email"), validators=[DataRequired(), Length(max=120), validate_email_format])
    password = PasswordField(_l("Password"), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(_l("Confirm Password"), validators=[DataRequired(), EqualTo("password")])
    role = SelectField(_l("Role"), choices=Role.CHOICES, default=Role.COUNCIL_MEMBER)
    submit = SubmitField(_l("Create User"))

    def validate_username(self, username):
        if User.query.filter_by(username=username.data.strip()).first():
            raise ValidationError(_l("That username is taken. Please choose a different one."))

    def validate_email(self, email):
        if User.query.filter(db.func.lower(User.email) == email.data.strip().lower()).first():
            raise ValidationError(_l("That email is taken. Please choose a different one."))


class UserEditForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField(_l("Email"), validators=[DataRequired(), Length(max=120), validate_email_format])
    role = SelectField(_l("Role"), choices=Role.CHOICES, validators=[DataRequired()])
    contact_details = TextAreaField(_l("Contact Details"), validators=[Optional()])
    permissions = StringField(_l("Permissions"), validators=[Optional()])
    password = PasswordField(_l("New Password"), validators=[Optional(), Length(min=6)])
    submit = SubmitField(_l("Save User"))

    def __init__(self, original_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_user = original_user

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.strip()).first()
        if user and user.id != self.original_user.id:
            raise ValidationError(_l("That username is taken. Please choose a different one."))

    def validate_email(self, email):
        user = User.query.filter(db.func.lower(User.email) == email.data.strip().lower()).first()
        if user and user.id != self.original_user.id:
            raise ValidationError(_l("That email is taken. Please choose a different one."))


class LoginForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired()])
    password = PasswordField(_l("Password"), validators=[DataRequired()])
    remember_me = BooleanField(_l("Remember me"))
    submit = SubmitField(_l("Login"))


class ProjectForm(FlaskForm):
    title = StringField(_l("Title"), validators=[DataRequired(), Length(max=100)])
    description = TextAreaField(_l("Description"), validators=[DataRequired()])
    category = StringField(_l("Category"), validators=[Optional(), Length(max=50)])
    voting_deadline = DateTimeLocalField(_l("Voting Deadline"), format="%Y-%m-%dT%H:%M", validators=[Optional()])
    start_date = DateTimeLocalField(_l("Start Date"), format="%Y-%m-%dT%H:%M", validators=[Optional()])
    end_date = DateTimeLocalField(_l("End Date"), format="%Y-%m-%dT%H:%M", validators=[Optional()])
    status = SelectField(
        _l("Status"),
        choices=[("Pending", _l("Pending")), ("In Progress", _l("In Progress")), ("Completed", _l("Completed"))],
        default="Pending",
        validators=[DataRequired()],
    )
    submit = SubmitField(_l("Save Project"))

    def validate_end_date(self, end_date):
        if self.start_date.data and end_date.data and end_date.data < self.start_date.data:
            raise ValidationError(_l("End date must be after the start date."))


class AssignTrackerForm(FlaskForm):
    tracker = SelectField(_l("Project Tracker"), coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l("Assign Project Tracker"))


class VoteForm(FlaskForm):
    vote = RadioField(_l("Vote"), choices=[("True", _l("Yes")), ("False", _l("No"))], validators=[DataRequired()])
    submit = SubmitField(_l("Submit Vote"))


class ProposalForm(FlaskForm):
    title = StringField(_l("Proposal Title"), validators=[DataRequired(), Length(max=140)])
    summary = StringField(_l("Short Summary"), validators=[Optional(), Length(max=240)])
    body = TextAreaField(_l("Proposal Details"), validators=[DataRequired()])
    visibility = SelectField(
        _l("Who can see and vote"),
        choices=[
            ("council", _l("Council members only")),
            ("internal", _l("Council members and trackers")),
            ("public", _l("Public page with internal voting")),
        ],
        default="council",
        validators=[DataRequired()],
    )
    vote_visibility = SelectField(
        _l("Vote transparency"),
        choices=[
            ("anonymous", _l("Anonymous results")),
            ("public", _l("Public accountability")),
        ],
        default="anonymous",
        validators=[DataRequired()],
    )
    status = SelectField(
        _l("Proposal Status"),
        choices=[("Open", _l("Open")), ("Closed", _l("Closed"))],
        default="Open",
        validators=[DataRequired()],
    )
    voting_deadline = DateTimeLocalField(_l("Voting Deadline"), format="%Y-%m-%dT%H:%M", validators=[Optional()])
    submit = SubmitField(_l("Save Proposal"))


class ProposalVoteForm(FlaskForm):
    choice = RadioField(
        _l("Your Vote"),
        choices=[("Yes", _l("Yes")), ("No", _l("No")), ("Abstain", _l("Abstain"))],
        validators=[DataRequired()],
    )
    comment = TextAreaField(_l("Optional Reason"), validators=[Optional(), Length(max=500)])
    submit = SubmitField(_l("Submit Proposal Vote"))


class EditProfileForm(FlaskForm):
    username = StringField(_l("Username"), validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField(_l("Email"), validators=[DataRequired(), Length(max=120), validate_email_format])
    contact_details = TextAreaField(_l("Contact Details"), validators=[Optional()])
    submit = SubmitField(_l("Update Profile"))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data.strip()).first()
        if user and user.id != current_user.id:
            raise ValidationError(_l("That username is taken. Please choose a different one."))

    def validate_email(self, email):
        user = User.query.filter(db.func.lower(User.email) == email.data.strip().lower()).first()
        if user and user.id != current_user.id:
            raise ValidationError(_l("That email is taken. Please choose a different one."))


class SearchFilterForm(FlaskForm):
    search_term = StringField(_l("Search Keywords"), validators=[Optional()])
    status = SelectField(
        _l("Status"),
        choices=[("", _l("Any")), ("Pending", _l("Pending")), ("In Progress", _l("In Progress")), ("Completed", _l("Completed"))],
        validators=[Optional()],
    )
    category = StringField(_l("Category"), validators=[Optional()])
    tracker_id = SelectField(_l("Project Tracker"), coerce=int, choices=[(0, _l("Any"))], validators=[Optional()])
    submit = SubmitField(_l("Apply Filters"))


class VolunteerForm(FlaskForm):
    name = StringField(_l("Name"), validators=[DataRequired(), Length(max=100)])
    additional_info = TextAreaField(_l("Additional Info"), validators=[Optional()])
    submit = SubmitField(_l("Volunteer"))


class StatusUpdateForm(FlaskForm):
    status = SelectField(
        _l("New Status"),
        choices=[("Pending", _l("Pending")), ("In Progress", _l("In Progress")), ("Completed", _l("Completed"))],
        validators=[DataRequired()],
    )
    submit = SubmitField(_l("Update Status"))


class CommentForm(FlaskForm):
    body = TextAreaField(_l("Add Comment"), validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField(_l("Add Comment"))


class SuggestionForm(FlaskForm):
    target_type = SelectField(
        _l("Send suggestion to"),
        choices=[
            ("council", _l("Council")),
            ("project_tracker", _l("Project tracker on a project")),
        ],
        default="council",
        validators=[DataRequired()],
    )
    project_id = SelectField(_l("Project"), coerce=int, choices=[(0, _l("Select a project"))], validators=[Optional()])
    name = StringField(_l("Your name"), validators=[Optional(), Length(max=120)])
    contact = StringField(_l("Contact information"), validators=[Optional(), Length(max=160)])
    title = StringField(_l("Suggestion title"), validators=[DataRequired(), Length(max=140)])
    body = TextAreaField(_l("Suggestion details"), validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField(_l("Submit Suggestion"))

    def validate_project_id(self, project_id):
        if self.target_type.data == "project_tracker" and project_id.data == 0:
            raise ValidationError(_l("Choose the project this suggestion belongs to."))


class HomePostForm(FlaskForm):
    post_type = SelectField(
        _l("Content Type"),
        choices=[("announcement", _l("Important announcement")), ("news", _l("News story"))],
        validators=[DataRequired()],
    )
    title = StringField(_l("Title"), validators=[DataRequired(), Length(max=160)])
    summary = StringField(_l("Short Summary"), validators=[Optional(), Length(max=260)])
    body = TextAreaField(_l("Body"), validators=[DataRequired(), Length(max=3000)])
    image_url = StringField(_l("Image URL"), validators=[Optional(), Length(max=500), validate_image_link])
    image_file = FileField(
        _l("Upload picture"),
        validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], _l("Upload a JPG, PNG, WebP, or GIF image."))],
    )
    is_published = BooleanField(_l("Published"), default=True)
    show_on_home = BooleanField(_l("Show on home page"), default=True)
    submit = SubmitField(_l("Save Home Content"))


class HomeContentSettingsForm(FlaskForm):
    news_enabled = BooleanField(_l("Show news section on the home page"), default=True)
    submit = SubmitField(_l("Save Home Page Settings"))


class SiteLinksForm(FlaskForm):
    instagram_enabled = BooleanField(_l("Show Instagram"), default=True)
    instagram_url = StringField(_l("Instagram URL"), validators=[Optional(), Length(max=500), validate_safe_link])
    instagram_description_en = TextAreaField(_l("English description"), validators=[Optional(), Length(max=500)])
    instagram_description_ar = TextAreaField(_l("Spanish description"), validators=[Optional(), Length(max=500)])
    whatsapp_enabled = BooleanField(_l("Show WhatsApp"), default=True)
    whatsapp_url = StringField(_l("WhatsApp URL"), validators=[Optional(), Length(max=500), validate_safe_link])
    whatsapp_description_en = TextAreaField(_l("English description"), validators=[Optional(), Length(max=500)])
    whatsapp_description_ar = TextAreaField(_l("Spanish description"), validators=[Optional(), Length(max=500)])
    facebook_enabled = BooleanField(_l("Show Facebook"), default=True)
    facebook_url = StringField(_l("Facebook URL"), validators=[Optional(), Length(max=500), validate_safe_link])
    facebook_description_en = TextAreaField(_l("English description"), validators=[Optional(), Length(max=500)])
    facebook_description_ar = TextAreaField(_l("Spanish description"), validators=[Optional(), Length(max=500)])
    twitter_enabled = BooleanField(_l("Show Twitter/X"), default=True)
    twitter_url = StringField(_l("Twitter/X URL"), validators=[Optional(), Length(max=500), validate_safe_link])
    twitter_description_en = TextAreaField(_l("English description"), validators=[Optional(), Length(max=500)])
    twitter_description_ar = TextAreaField(_l("Spanish description"), validators=[Optional(), Length(max=500)])
    telegram_enabled = BooleanField(_l("Show Telegram"), default=False)
    telegram_url = StringField(_l("Telegram URL"), validators=[Optional(), Length(max=500), validate_safe_link])
    telegram_description_en = TextAreaField(_l("English description"), validators=[Optional(), Length(max=500)])
    telegram_description_ar = TextAreaField(_l("Spanish description"), validators=[Optional(), Length(max=500)])
    submit = SubmitField(_l("Save Site Links"))


class DeleteUserForm(FlaskForm):
    submit = SubmitField(_l("Delete"))


class ActionForm(FlaskForm):
    pass


class DonationCampaignForm(FlaskForm):
    title = StringField(_l("Campaign Title"), validators=[DataRequired(), Length(max=140)])
    beneficiary = StringField(_l("Beneficiary or Purpose"), validators=[Optional(), Length(max=140)])
    description = TextAreaField(_l("Campaign Description"), validators=[DataRequired()])
    goal_amount = DecimalField(_l("Goal Amount"), places=2, validators=[DataRequired(), NumberRange(min=1)])
    currency = SelectField(
        _l("Currency"),
        choices=[("USD", "USD")],
        default="USD",
        validators=[DataRequired()],
    )
    status = SelectField(
        _l("Campaign Status"),
        choices=[("Active", _l("Active")), ("Paused", _l("Paused")), ("Closed", _l("Closed"))],
        default="Active",
        validators=[DataRequired()],
    )
    payment_instructions = TextAreaField(_l("Payment Instructions"), validators=[Optional()])
    submit = SubmitField(_l("Save Campaign"))


class DonationGroupForm(FlaskForm):
    name = StringField(_l("Group or Bloodline Name"), validators=[DataRequired(), Length(max=120)])
    description = TextAreaField(_l("Group Notes"), validators=[Optional(), Length(max=500)])
    submit = SubmitField(_l("Add Group"))


class DonationForm(FlaskForm):
    donor_name = StringField(_l("Donor Name"), validators=[DataRequired(), Length(max=120)])
    donor_email = StringField(_l("Email"), validators=[Optional(), Length(max=120), validate_email_format])
    donor_phone = StringField(_l("Phone"), validators=[Optional(), Length(max=50)])
    amount = DecimalField(_l("Donation Amount"), places=2, validators=[DataRequired(), NumberRange(min=1)])
    attribution_type = RadioField(
        _l("Donation Attribution"),
        choices=[("independent", _l("Independent donation")), ("group", _l("Under a group or bloodline"))],
        default="independent",
        validators=[DataRequired()],
    )
    group_id = SelectField(_l("Existing Group"), coerce=int, validators=[Optional()])
    new_group_name = StringField(_l("New Group or Bloodline"), validators=[Optional(), Length(max=120)])
    display_name = BooleanField(_l("Show my name publicly"), default=True)
    payment_method = SelectField(
        _l("Payment Method"),
        choices=[
            ("bank_transfer", _l("Bank transfer")),
            ("cash", _l("Cash payment")),
            ("online_gateway", _l("Online payment request")),
        ],
        default="bank_transfer",
        validators=[DataRequired()],
    )
    message = TextAreaField(_l("Optional Message"), validators=[Optional(), Length(max=500)])
    submit = SubmitField(_l("Create Donation Reference"))

    def validate_group_id(self, group_id):
        if self.attribution_type.data == "group" and group_id.data == 0 and not (self.new_group_name.data or "").strip():
            raise ValidationError(_l("Choose a group or enter a new group name."))


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != Role.ADMIN:
            flash(gettext("You do not have permission to access this page."), "danger")
            return redirect(url_for("dashboard", locale=get_locale()))
        return func(*args, **kwargs)

    return wrapper


def council_member_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.has_permission(Permission.VOTE_PROJECT):
            flash(gettext("You do not have permission to access this page."), "danger")
            return redirect(url_for("dashboard", locale=get_locale()))
        return func(*args, **kwargs)

    return wrapper


def proposal_creator_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.has_permission(Permission.CREATE_PROPOSAL):
            flash(gettext("You need proposal creation permission to create proposals."), "danger")
            return redirect(url_for("proposals_list", locale=get_locale()))
        return func(*args, **kwargs)

    return wrapper


def permission_required(permission):
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.has_permission(permission):
                flash(gettext("You do not have the required permission to access this page."), "danger")
                return redirect(url_for("dashboard", locale=get_locale()))
            return func(*args, **kwargs)

        return wrapper

    return decorator


def tracker_can_access(project):
    if current_user.role == Role.ADMIN:
        return True
    if current_user.has_permission(Permission.TRACK_ANY_PROJECT):
        return True
    return project.tracker_id == current_user.id and current_user.has_permission(Permission.TRACK_ASSIGNED_PROJECT)


def user_can_track_projects(user):
    return user.has_permission(Permission.TRACK_ANY_PROJECT) or user.has_permission(Permission.TRACK_ASSIGNED_PROJECT)


def can_edit_proposal(proposal):
    if not current_user.is_authenticated:
        return False
    if current_user.role == Role.ADMIN:
        return True
    return proposal.created_by_id == current_user.id and current_user.has_permission(Permission.CREATE_PROPOSAL)


def can_manage_home_content():
    return current_user.is_authenticated and (
        current_user.role == Role.ADMIN or current_user.has_permission(Permission.MANAGE_HOME_CONTENT)
    )


def can_use_home_post_type(post_type):
    if not can_manage_home_content():
        return False
    if current_user.role == Role.NEWS_EDITOR:
        return post_type == "news"
    return post_type in {"announcement", "news"}


def configure_home_post_form(form, post=None):
    if current_user.is_authenticated and current_user.role == Role.NEWS_EDITOR:
        form.post_type.choices = [("news", gettext("News story"))]
        form.post_type.data = "news"
    if post and current_user.role == Role.NEWS_EDITOR and post.post_type != "news":
        abort(403)
    return form


def save_home_post_image(file_storage):
    if not file_storage or not file_storage.filename:
        return ""
    upload_dir = os.path.join(BASE_DIR, "static", "uploads", "home_posts")
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file_storage.filename)
    if not filename:
        return ""
    unique_filename = f"{secrets.token_hex(10)}_{filename}"
    file_storage.save(os.path.join(upload_dir, unique_filename))
    return url_for("static", filename=f"uploads/home_posts/{unique_filename}")


def home_post_type_label(post_type):
    return {
        "announcement": gettext("Important announcement"),
        "news": gettext("News story"),
    }.get(post_type, post_type)


def news_section_enabled():
    return get_setting(HOME_NEWS_ENABLED_KEY, "1") == "1"


def suggestion_target_label(target_type):
    return {
        "council": gettext("Council"),
        "project_tracker": gettext("Project tracker"),
    }.get(target_type, target_type)


def suggestion_status_label(status):
    return {
        "New": gettext("New"),
        "Reviewed": gettext("Reviewed"),
        "Closed": gettext("Closed"),
    }.get(status, status)


def suggestion_inbox_query():
    query = PublicSuggestion.query.outerjoin(Project)
    if current_user.role == Role.ADMIN:
        return query

    filters = []
    if current_user.role == Role.COUNCIL_MEMBER or current_user.has_permission(Permission.CREATE_PROPOSAL):
        filters.append(PublicSuggestion.target_type == "council")
    if current_user.has_permission(Permission.TRACK_ANY_PROJECT):
        filters.append(PublicSuggestion.target_type == "project_tracker")
    elif current_user.has_permission(Permission.TRACK_ASSIGNED_PROJECT):
        filters.append(
            db.and_(
                PublicSuggestion.target_type == "project_tracker",
                Project.tracker_id == current_user.id,
            )
        )
    if not filters:
        return None
    return query.filter(db.or_(*filters))


def proposal_visibility_label(visibility):
    return {
        "council": gettext("Council members only"),
        "internal": gettext("Council members and trackers"),
        "public": gettext("Public page with internal voting"),
    }.get(visibility, visibility)


def proposal_vote_visibility_label(vote_visibility):
    return {
        "anonymous": gettext("Anonymous results"),
        "public": gettext("Public accountability"),
    }.get(vote_visibility, vote_visibility)


def proposal_eligible_roles(proposal):
    if proposal.visibility == "council":
        return [Role.ADMIN, Role.COUNCIL_MEMBER]
    return [Role.ADMIN, Role.COUNCIL_MEMBER, Role.TRACKER]


def can_view_proposal(proposal):
    if proposal.visibility == "public":
        return True
    if not current_user.is_authenticated:
        return False
    return current_user.role in proposal_eligible_roles(proposal)


def can_vote_on_proposal(proposal):
    return (
        current_user.is_authenticated
        and current_user.role in proposal_eligible_roles(proposal)
        and current_user.has_permission(Permission.VOTE_PROPOSAL)
    )


def proposal_eligible_voters(proposal):
    voters = User.query.filter(User.role.in_(proposal_eligible_roles(proposal))).order_by(User.role.asc(), User.username.asc()).all()
    return [user for user in voters if user.has_permission(Permission.VOTE_PROPOSAL)]


def proposal_visibility_filter(query):
    if not current_user.is_authenticated:
        return query.filter_by(visibility="public")
    if current_user.role in [Role.ADMIN, Role.COUNCIL_MEMBER]:
        return query
    if current_user.role == Role.TRACKER:
        return query.filter(CouncilProposal.visibility.in_(["internal", "public"]))
    return query.filter_by(visibility="public")


def display_user_name(user):
    if not user:
        return gettext("Unassigned")
    if get_locale() == "es":
        built_in_names = {
            "admin": gettext("Admin"),
            "tracker": gettext("Project Tracker"),
        }
        translated_name = built_in_names.get((user.username or "").lower())
        if translated_name:
            return translated_name
    return user.username


def require_tracker_access(project):
    if not current_user.is_authenticated:
        abort(401)
    if not tracker_can_access(project):
        flash(gettext("You do not have permission to track this project."), "danger")
        return False
    return True


def project_volunteer_count(project):
    members = ProjectMember.query.filter_by(project_id=project.id).all()
    member_names = {member.volunteer_name for member in members if member.volunteer_name}
    unmatched_public_volunteers = [
        volunteer
        for volunteer in Volunteer.query.filter_by(project_name=project.title).all()
        if volunteer.name not in member_names
    ]
    return len(members) + len(unmatched_public_volunteers)


def currency_label(currency):
    if get_locale() == "es":
        currency_names = {
            "USD": gettext("US dollars"),
        }
        return currency_names.get(currency, currency)
    return currency


def money(value, currency="USD"):
    amount = Decimal(value or 0)
    return f"{amount:,.2f} {currency_label(currency)}"


def donation_payment_status_label(status):
    return {
        "Pending": gettext("Pending"),
        "Confirmed": gettext("Confirmed"),
        "Rejected": gettext("Rejected"),
    }.get(status, gettext(status))


def generate_payment_reference():
    today = datetime.utcnow().strftime("%Y%m%d")
    for _ in range(12):
        reference = f"DON-{today}-{secrets.token_hex(4).upper()}"
        if not Donation.query.filter_by(payment_reference=reference).first():
            return reference
    return f"DON-{today}-{secrets.token_hex(8).upper()}"


def normalize_group_name(name):
    return " ".join((name or "").split())


def find_or_create_donation_group(campaign, name, description=""):
    cleaned_name = normalize_group_name(name)
    if not cleaned_name:
        return None, False
    existing_group = DonationGroup.query.filter(
        DonationGroup.campaign_id == campaign.id,
        db.func.lower(DonationGroup.name) == cleaned_name.lower(),
    ).first()
    if existing_group:
        if description and not existing_group.description:
            existing_group.description = description
        return existing_group, False
    group = DonationGroup(campaign_id=campaign.id, name=cleaned_name, description=description)
    db.session.add(group)
    db.session.flush()
    return group, True


class AuthModelView(ModelView):
    form_base_class = SecureForm

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        flash(gettext("You do not have permission to access this page."), "danger")
        if current_user.is_authenticated:
            return redirect(url_for("dashboard", locale=get_locale()))
        return redirect(url_for("login", locale=get_locale(), next=request.path))


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        flash(gettext("You do not have permission to access this page."), "danger")
        if current_user.is_authenticated:
            return redirect(url_for("dashboard", locale=get_locale()))
        return redirect(url_for("login", locale=get_locale(), next=request.path))


class UserModelView(AuthModelView):
    column_searchable_list = ["username", "email"]
    column_filters = ["role"]
    column_exclude_list = ["password"]
    form_columns = ["username", "email", "role", "contact_details", "permissions"]
    can_create = False


class ProjectModelView(AuthModelView):
    column_searchable_list = ["title", "description", "category"]
    column_filters = ["status", "category", "tracker_id"]
    column_list = ["id", "title", "status", "category", "voting_deadline", "start_date", "end_date", "tracker"]
    form_excluded_columns = ["votes", "volunteers", "comments"]

    def on_model_change(self, form, model, is_created):
        if is_created and current_user.is_authenticated:
            model.created_by_id = current_user.id
        super().on_model_change(form, model, is_created)


class CouncilProposalModelView(AuthModelView):
    column_searchable_list = ["title", "summary", "body"]
    column_filters = ["visibility", "vote_visibility", "status", "voting_deadline"]
    column_list = ["id", "title", "visibility", "vote_visibility", "status", "voting_deadline", "creator"]
    form_excluded_columns = ["votes"]

    def on_model_change(self, form, model, is_created):
        if is_created and current_user.is_authenticated:
            model.created_by_id = current_user.id
        super().on_model_change(form, model, is_created)


class VoteModelView(AuthModelView):
    column_list = ["id", "user", "project", "vote", "vote_timestamp"]
    column_filters = ["vote", "vote_timestamp", "user_id", "project_id"]
    can_create = False
    can_edit = False


class CouncilProposalVoteModelView(AuthModelView):
    column_list = ["id", "proposal", "user", "choice", "vote_timestamp"]
    column_filters = ["choice", "vote_timestamp", "proposal_id", "user_id"]
    can_create = False
    can_edit = False


class PublicSuggestionModelView(AuthModelView):
    column_searchable_list = ["title", "body", "name", "contact"]
    column_filters = ["target_type", "status", "created_at", "project_id"]
    column_list = ["id", "target_type", "project", "title", "status", "created_at"]
    form_columns = ["target_type", "project", "name", "contact", "title", "body", "status"]


class HomePostModelView(AuthModelView):
    column_searchable_list = ["title", "summary", "body"]
    column_filters = ["post_type", "is_published", "show_on_home", "created_at"]
    column_list = ["id", "post_type", "title", "is_published", "show_on_home", "creator", "created_at"]
    form_excluded_columns = ["creator", "created_by_id", "created_at", "updated_at"]

    def on_model_change(self, form, model, is_created):
        if is_created and current_user.is_authenticated:
            model.created_by_id = current_user.id
        model.updated_at = datetime.utcnow()
        super().on_model_change(form, model, is_created)


class AnalyticsView(BaseView):
    @expose("/")
    def index(self):
        stats = {
            "users": User.query.count(),
            "projects": Project.query.count(),
            "votes": Vote.query.count(),
            "volunteers": Volunteer.query.count(),
        }
        return self.render("admin/analytics.html", stats=stats)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN


admin = Admin(app, name="Arlington Civic Admin", template_mode="bootstrap4", index_view=SecureAdminIndexView())
admin.add_view(UserModelView(User, db.session))
admin.add_view(ProjectModelView(Project, db.session))
admin.add_view(VoteModelView(Vote, db.session))
admin.add_view(AuthModelView(Volunteer, db.session))
admin.add_view(AuthModelView(ProjectMember, db.session))
admin.add_view(AuthModelView(ProjectComment, db.session))
admin.add_view(CouncilProposalModelView(CouncilProposal, db.session))
admin.add_view(CouncilProposalVoteModelView(CouncilProposalVote, db.session))
admin.add_view(PublicSuggestionModelView(PublicSuggestion, db.session))
admin.add_view(HomePostModelView(HomePost, db.session))
admin.add_view(AuthModelView(DonationCampaign, db.session))
admin.add_view(AuthModelView(DonationGroup, db.session))
admin.add_view(AuthModelView(Donation, db.session))
admin.add_view(AnalyticsView(name="Analytics", endpoint="analytics"))


def bootstrap_database():
    db.create_all()
    admin_user = User.query.filter(db.func.lower(User.username) == "admin").first()
    if not admin_user:
        admin_user = User(username="admin", email="admin@arlington-civic.local", role=Role.ADMIN)
        admin_user.set_password(os.environ.get("DEFAULT_ADMIN_PASSWORD", "admin"))
        db.session.add(admin_user)
        db.session.commit()
    else:
        admin_user.role = Role.ADMIN
        if not admin_user.email:
            admin_user.email = "admin@arlington-civic.local"
    if not DonationCampaign.query.first():
        db.session.add(
            DonationCampaign(
                title="Arlington Neighborhood Support Fund",
                description="A transparent public campaign for neighborhood service gaps, emergency resident support, and community improvement work around Arlington and the UTA area.",
                beneficiary="Arlington residents and community partners",
                goal_amount=Decimal("25000.00"),
                currency="USD",
                payment_instructions="After submitting your pledge, use the reference number in your payment note or share it with the council office for confirmation. Connect a production payment provider before accepting real funds.",
                status="Active",
            )
        )
    if not Project.query.first() and admin_user:
        now = datetime.utcnow()
        db.session.add(
            Project(
                title="UTA District Walkability Review",
                description="Review crosswalks, lighting, bus stop access, and sidewalk trouble spots around the university district so residents, students, and visitors can move through the area more safely.",
                created_by_id=admin_user.id,
                tracker_id=admin_user.id,
                status="In Progress",
                category="Mobility",
                start_date=now - timedelta(days=10),
                end_date=now + timedelta(days=35),
                voting_deadline=now + timedelta(days=14),
                vote_type="simple_majority",
            )
        )
    if not CouncilProposal.query.first() and admin_user:
        db.session.add(
            CouncilProposal(
                title="Pilot weekend community shuttle coordination",
                summary="A short-term pilot to study weekend shuttle coordination between major Arlington activity zones and the UTA district.",
                body="The proposal asks council members to review ridership demand, community partners, and operating windows before approving a limited pilot plan.",
                created_by_id=admin_user.id,
                visibility="public",
                vote_visibility="public",
                status="Open",
                voting_deadline=datetime.utcnow() + timedelta(days=21),
            )
        )
    if not HomePost.query.first() and admin_user:
        now = datetime.utcnow()
        db.session.add_all(
            [
                HomePost(
                    post_type="announcement",
                    title="Public input window is open",
                    summary="Residents can submit suggestions for projects, safety concerns, and neighborhood service priorities from the Suggestions page.",
                    body="<p>The council portal is collecting resident ideas and project feedback. Submissions can be routed to the council or to a project tracker.</p>",
                    image_url="",
                    is_published=True,
                    show_on_home=True,
                    created_by_id=admin_user.id,
                    created_at=now - timedelta(days=1),
                ),
                HomePost(
                    post_type="news",
                    title="UTA-area mobility review begins",
                    summary="The first demo project focuses on walkability, lighting, and transit access around the university district.",
                    body="<p>Project trackers can post field updates, council members can vote on proposals, and residents can follow progress from the public project page.</p>",
                    image_url="https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80",
                    is_published=True,
                    show_on_home=True,
                    created_by_id=admin_user.id,
                    created_at=now - timedelta(hours=10),
                ),
            ]
        )
    if get_setting(HOME_NEWS_ENABLED_KEY, "") == "":
        set_setting(HOME_NEWS_ENABLED_KEY, "1")
    if get_setting(USEFUL_SITES_SETTING_KEY, "") == "":
        set_setting(
            USEFUL_SITES_SETTING_KEY,
            json.dumps(
                [
                    {
                        "enabled": True,
                        "title_en": "City of Arlington",
                        "title_ar": "Ciudad de Arlington",
                        "url": "https://www.arlingtontx.gov/",
                        "description_en": "Official city services, departments, notices, permits, and resident resources.",
                        "description_ar": "Servicios oficiales de la ciudad, departamentos, avisos, permisos y recursos para residentes.",
                    },
                    {
                        "enabled": True,
                        "title_en": "The University of Texas at Arlington",
                        "title_ar": "Universidad de Texas en Arlington",
                        "url": "https://www.uta.edu/",
                        "description_en": "Campus information, events, student resources, and university contacts.",
                        "description_ar": "Informacion del campus, eventos, recursos estudiantiles y contactos universitarios.",
                    },
                    {
                        "enabled": True,
                        "title_en": "Arlington Public Library",
                        "title_ar": "Biblioteca Publica de Arlington",
                        "url": "https://www.arlingtonlibrary.org/",
                        "description_en": "Library branches, learning programs, public computers, events, and research support.",
                        "description_ar": "Sucursales, programas de aprendizaje, computadoras publicas, eventos y apoyo de investigacion.",
                    },
                    {
                        "enabled": True,
                        "title_en": "Tarrant County",
                        "title_ar": "Condado de Tarrant",
                        "url": "https://www.tarrantcountytx.gov/",
                        "description_en": "County records, elections, public health, courts, and regional services.",
                        "description_ar": "Registros del condado, elecciones, salud publica, tribunales y servicios regionales.",
                    },
                ],
                ensure_ascii=False,
            ),
        )
    db.session.commit()


with app.app_context():
    bootstrap_database()


@app.before_request
def before_request():
    locale = (request.view_args or {}).get("locale")
    if locale:
        if locale not in app.config["BABEL_SUPPORTED_LANGUAGES"]:
            replacement_locale = choose_locale()
            path_parts = request.path.lstrip("/").split("/")
            path_parts[0] = replacement_locale
            new_path = "/" + "/".join(path_parts)
            return redirect(urlunparse(("", "", new_path, "", request.query_string.decode("utf-8"), "")))
        session["locale"] = locale
        refresh()
    g.locale = get_locale()
    g.delete_user_form = DeleteUserForm()
    g.action_form = ActionForm()
    g.search_filter_form = SearchFilterForm(request.args, meta={"csrf": False})
    g.search_filter_form.tracker_id.choices = [(0, gettext("Any"))] + [
        (user.id, display_user_name(user)) for user in tracker_assignable_users()
    ]
    if current_user.is_authenticated and current_user.has_permission(Permission.VOTE_PROJECT):
        voted_ids = [vote.project_id for vote in current_user.votes]
        g.projects_to_vote = (
            Project.query.filter(db.or_(Project.voting_deadline.is_(None), Project.voting_deadline > datetime.utcnow()), Project.id.notin_(voted_ids))
            .order_by(Project.voting_deadline.asc())
            .limit(8)
            .all()
        )
    else:
        g.projects_to_vote = []


@app.context_processor
def inject_helpers():
    def format_datetime(value, empty=None):
        if not value:
            return gettext(empty or "Not scheduled")
        return babel_format_datetime(value, format="medium")

    def status_class(status):
        return {
            "Pending": "status-pending",
            "In Progress": "status-progress",
            "Completed": "status-complete",
        }.get(status, "status-pending")

    return {
        "get_locale": get_locale,
        "format_datetime": format_datetime,
        "status_class": status_class,
        "role_label": role_label,
        "role_description": role_description,
        "permission_label": permission_label,
        "permission_description": permission_description,
        "display_user_name": display_user_name,
        "proposal_visibility_label": proposal_visibility_label,
        "proposal_vote_visibility_label": proposal_vote_visibility_label,
        "can_edit_proposal": can_edit_proposal,
        "can_manage_home_content": can_manage_home_content,
        "home_post_type_label": home_post_type_label,
        "news_section_enabled": news_section_enabled,
        "suggestion_target_label": suggestion_target_label,
        "suggestion_status_label": suggestion_status_label,
        "donation_payment_status_label": donation_payment_status_label,
        "currency_label": currency_label,
        "money": money,
        "current_year": datetime.utcnow().year,
        "Role": Role,
        "Permission": Permission,
        "role_workspace_label": role_workspace_label,
        "role_workspace_icon": role_workspace_icon,
        "role_workspace_url": role_workspace_url,
        "role_workspace_endpoints": role_workspace_endpoints,
        "tracker_can_access": tracker_can_access,
        "user_can_track_projects": user_can_track_projects,
        "site_links": get_site_links(),
        "useful_sites": get_useful_sites(),
    }


@app.route("/")
def home():
    return redirect(url_for("home_page", locale=choose_locale()))


def build_civic_home_context():
    now = datetime.utcnow()
    tracker_users = tracker_assignable_users()
    stats = {
        "projects": Project.query.count(),
        "active_projects": Project.query.filter(Project.status.in_(["Pending", "In Progress"])).count(),
        "open_votes": Project.query.filter(db.or_(Project.voting_deadline.is_(None), Project.voting_deadline > now)).count(),
        "council_members": User.query.filter_by(role=Role.COUNCIL_MEMBER).count(),
        "trackers": len(tracker_users),
        "volunteers": Volunteer.query.count(),
    }
    recent_projects = Project.query.order_by(Project.id.desc()).limit(6).all()
    pending_votes = (
        Project.query.filter(db.or_(Project.voting_deadline.is_(None), Project.voting_deadline > now))
        .order_by(Project.voting_deadline.asc())
        .limit(5)
        .all()
    )
    assigned_projects = []
    tracking_panel_title = gettext("Your assigned projects")
    if current_user.is_authenticated and current_user.has_permission(Permission.TRACK_ANY_PROJECT):
        assigned_projects = Project.query.order_by(Project.start_date.asc()).limit(6).all()
        tracking_panel_title = gettext("Projects you can track")
    elif current_user.is_authenticated and current_user.has_permission(Permission.TRACK_ASSIGNED_PROJECT):
        assigned_projects = Project.query.filter_by(tracker_id=current_user.id).order_by(Project.start_date.asc()).limit(6).all()
    latest_comments = ProjectComment.query.order_by(ProjectComment.created_at.desc()).limit(5).all()
    announcements = (
        HomePost.query.filter_by(post_type="announcement", is_published=True, show_on_home=True)
        .order_by(HomePost.created_at.desc())
        .limit(3)
        .all()
    )
    news_posts = []
    if news_section_enabled():
        news_posts = (
            HomePost.query.filter_by(post_type="news", is_published=True, show_on_home=True)
            .order_by(HomePost.created_at.desc())
            .limit(6)
            .all()
        )
    return {
        "stats": stats,
        "recent_projects": recent_projects,
        "pending_votes": pending_votes,
        "assigned_projects": assigned_projects,
        "tracking_panel_title": tracking_panel_title,
        "latest_comments": latest_comments,
        "announcements": announcements,
        "news_posts": news_posts,
        "show_news_section": news_section_enabled(),
    }


def role_workspace_label():
    if not current_user.is_authenticated:
        return gettext("Login")
    if current_user.role == Role.ADMIN:
        return gettext("Admin")
    if user_can_track_projects(current_user):
        return gettext("Tracker")
    if current_user.role == Role.COUNCIL_MEMBER or current_user.has_permission(Permission.VOTE_PROJECT) or current_user.has_permission(Permission.CREATE_PROPOSAL) or current_user.has_permission(Permission.VOTE_PROPOSAL):
        return gettext("Council")
    if can_manage_home_content():
        return gettext("News Desk")
    return gettext("Workspace")


def role_workspace_icon():
    if not current_user.is_authenticated:
        return "fa-solid fa-right-to-bracket"
    if current_user.role == Role.ADMIN:
        return "fa-solid fa-shield-halved"
    if user_can_track_projects(current_user):
        return "fa-solid fa-helmet-safety"
    if current_user.role == Role.COUNCIL_MEMBER or current_user.has_permission(Permission.VOTE_PROJECT) or current_user.has_permission(Permission.CREATE_PROPOSAL) or current_user.has_permission(Permission.VOTE_PROPOSAL):
        return "fa-solid fa-landmark"
    if can_manage_home_content():
        return "fa-solid fa-newspaper"
    return "fa-solid fa-briefcase"


def role_workspace_url(locale=None):
    locale = locale or get_locale()
    if not current_user.is_authenticated:
        return url_for("login", locale=locale)
    if current_user.role == Role.ADMIN:
        return url_for("admin_hub", locale=locale)
    if user_can_track_projects(current_user):
        return url_for("tracker_workspace", locale=locale)
    if current_user.role == Role.COUNCIL_MEMBER or current_user.has_permission(Permission.VOTE_PROJECT) or current_user.has_permission(Permission.CREATE_PROPOSAL) or current_user.has_permission(Permission.VOTE_PROPOSAL):
        return url_for("council_workspace", locale=locale)
    if can_manage_home_content():
        return url_for("news_workspace", locale=locale)
    return url_for("home_page", locale=locale)


def role_workspace_endpoints():
    if not current_user.is_authenticated:
        return ["login"]
    if current_user.role == Role.ADMIN:
        return [
            "admin_hub",
            "admin_donation_dashboard",
            "manage_users",
            "register",
            "edit_user",
            "admin_donations",
            "new_donation_campaign",
            "edit_donation_campaign",
            "manage_donation_campaign",
            "site_options",
            "home_content",
            "new_home_post",
            "edit_home_post",
            "suggestions_inbox",
        ]
    if user_can_track_projects(current_user):
        return ["tracker_workspace", "track_project", "update_project_status", "add_project_comment", "suggestions_inbox"]
    if current_user.role == Role.COUNCIL_MEMBER or current_user.has_permission(Permission.VOTE_PROJECT) or current_user.has_permission(Permission.CREATE_PROPOSAL) or current_user.has_permission(Permission.VOTE_PROPOSAL):
        return [
            "council_workspace",
            "proposals_list",
            "new_proposal",
            "proposal_detail",
            "edit_proposal",
            "proposal_vote",
            "project_vote",
            "results",
            "suggestions_inbox",
            "home_content",
            "new_home_post",
            "edit_home_post",
        ]
    if can_manage_home_content():
        return ["news_workspace", "home_content", "new_home_post", "edit_home_post"]
    return []


def api_datetime(value):
    if not value:
        return None
    return value.isoformat() + "Z"


def api_decimal(value):
    return float(Decimal(value or 0))


def api_absolute_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    parsed = urlparse(value)
    if parsed.scheme:
        return value
    if value.startswith("/"):
        return request.host_url.rstrip("/") + value
    return request.host_url.rstrip("/") + "/" + value.lstrip("/")


def api_project(project):
    yes_votes, no_votes = project.vote_counts()
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "status": project.status,
        "category": project.category or "",
        "tracker": display_user_name(project.tracker) if project.tracker else "",
        "progress": round(project.progress(), 1),
        "voting_progress": round(project.voting_progress(), 1),
        "is_open_for_voting": project.is_open_for_voting,
        "vote_counts": {"yes": yes_votes, "no": no_votes},
        "volunteer_count": project_volunteer_count(project),
        "start_date": api_datetime(project.start_date),
        "end_date": api_datetime(project.end_date),
        "voting_deadline": api_datetime(project.voting_deadline),
        "url": url_for("project", locale=get_locale(), project_id=project.id, _external=True),
    }


def api_proposal(proposal):
    return {
        "id": proposal.id,
        "title": proposal.title,
        "summary": proposal.summary or "",
        "body": proposal.body,
        "visibility": proposal.visibility,
        "vote_visibility": proposal.vote_visibility,
        "status": proposal.status,
        "is_open_for_voting": proposal.is_open_for_voting,
        "vote_counts": proposal.vote_counts(),
        "created_at": api_datetime(proposal.created_at),
        "voting_deadline": api_datetime(proposal.voting_deadline),
        "url": url_for("proposal_detail", locale=get_locale(), proposal_id=proposal.id, _external=True),
    }


def api_home_post(post):
    return {
        "id": post.id,
        "type": post.post_type,
        "title": post.title,
        "summary": post.summary or "",
        "body": post.body,
        "body_text": rich_text_to_plain_text(post.body),
        "image_url": api_absolute_url(post.image_url),
        "created_at": api_datetime(post.created_at),
        "updated_at": api_datetime(post.updated_at),
    }


def api_donation_group(group):
    return {
        "id": group.id,
        "name": group.name,
        "description": group.description or "",
        "confirmed_total": api_decimal(group.confirmed_total()),
    }


def api_donation(donation):
    return {
        "id": donation.id,
        "donor_name": donation.public_name(),
        "amount": api_decimal(donation.amount),
        "currency": donation.campaign.currency if donation.campaign else "USD",
        "group_name": donation.group.name if donation.group else "",
        "message": donation.message or "",
        "created_at": api_datetime(donation.created_at),
    }


def api_donation_campaign(campaign, include_details=False):
    payload = {
        "id": campaign.id,
        "title": campaign.title,
        "description": campaign.description,
        "goal_amount": api_decimal(campaign.goal_amount),
        "currency": campaign.currency,
        "beneficiary": campaign.beneficiary or "",
        "status": campaign.status,
        "confirmed_total": api_decimal(campaign.confirmed_total()),
        "pledged_total": api_decimal(campaign.pledged_total()),
        "progress": round(campaign.progress(), 1),
        "created_at": api_datetime(campaign.created_at),
        "url": url_for("donation_campaign", locale=get_locale(), campaign_id=campaign.id, _external=True),
    }
    if include_details:
        payload["payment_instructions"] = campaign.payment_instructions or ""
        payload["groups"] = [api_donation_group(group) for group in sorted(campaign.groups, key=lambda item: item.confirmed_total(), reverse=True)]
        payload["recent_donations"] = [
            api_donation(donation)
            for donation in Donation.query.filter_by(campaign_id=campaign.id, payment_status="Confirmed")
            .order_by(Donation.created_at.desc())
            .limit(10)
            .all()
        ]
    return payload


def api_link_item(item):
    return {
        "title": item.get("title", ""),
        "description": item.get("description", ""),
        "url": item.get("url", ""),
        "icon": item.get("icon", "fa-solid fa-globe"),
    }


def api_payload_error(message, status=400):
    return jsonify({"ok": False, "message": message}), status


@app.route("/<locale>/home")
def home_page(locale):
    return render_template("home.html", title=gettext("Home Page"), **build_civic_home_context())


def donation_dashboard_context():
    campaigns = DonationCampaign.query.order_by(DonationCampaign.created_at.desc()).limit(6).all()
    active_campaigns = [campaign for campaign in campaigns if campaign.status == "Active"]
    donations = Donation.query.order_by(Donation.created_at.desc()).limit(8).all()
    all_groups = DonationGroup.query.all()
    top_groups = sorted(all_groups, key=lambda group: group.confirmed_total(), reverse=True)[:5]
    confirmed_by_currency = (
        db.session.query(DonationCampaign.currency, db.func.coalesce(db.func.sum(Donation.amount), 0))
        .join(Donation, Donation.campaign_id == DonationCampaign.id)
        .filter(Donation.payment_status == "Confirmed")
        .group_by(DonationCampaign.currency)
        .all()
    )
    stats = {
        "campaigns": DonationCampaign.query.count(),
        "active_campaigns": DonationCampaign.query.filter_by(status="Active").count(),
        "pending_donations": Donation.query.filter_by(payment_status="Pending").count(),
        "confirmed_donations": Donation.query.filter_by(payment_status="Confirmed").count(),
        "groups": DonationGroup.query.count(),
    }
    totals = [(currency, Decimal(total or 0)) for currency, total in confirmed_by_currency]
    return {
        "stats": stats,
        "campaigns": campaigns,
        "active_campaigns": active_campaigns,
        "recent_donations": donations,
        "top_groups": top_groups,
        "confirmed_totals": totals,
    }


@app.route("/<locale>/dashboard")
def dashboard(locale):
    if not current_user.is_authenticated:
        return redirect(url_for("home_page", locale=locale))
    return redirect(role_workspace_url(locale))


@app.route("/<locale>/admin/donations/dashboard")
@admin_required
def admin_donation_dashboard(locale):
    return render_template(
        "dashboard.html",
        title=gettext("Donation Dashboard"),
        **donation_dashboard_context(),
    )


@app.route("/set_language/<locale>")
def set_language(locale):
    if locale not in app.config["BABEL_SUPPORTED_LANGUAGES"]:
        locale = app.config["BABEL_DEFAULT_LOCALE"]
    session["locale"] = locale
    if request.referrer:
        parsed = urlparse(request.referrer)
        path_parts = parsed.path.lstrip("/").split("/")
        if path_parts and path_parts[0] in app.config["BABEL_SUPPORTED_LANGUAGES"]:
            path_parts[0] = locale
            new_path = "/" + "/".join(path_parts)
            return redirect(urlunparse(("", "", new_path, "", parsed.query, "")))
    return redirect(url_for("dashboard", locale=locale))


@app.route("/<locale>/login", methods=["GET", "POST"])
def login(locale):
    if current_user.is_authenticated:
        return redirect(role_workspace_url(locale))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            remember_field = getattr(form, "remember_me", None)
            login_user(user, remember=bool(remember_field.data) if remember_field else False)
            flash(gettext("Welcome back, %(username)s.", username=user.username), "success")
            next_page = request.args.get("next")
            if is_safe_redirect(next_page):
                return redirect(next_page)
            return redirect(role_workspace_url(locale))
        flash(gettext("Login unsuccessful. Check the username and password, then try again."), "danger")
    return render_template("login.html", title=gettext("Login"), form=form)


@app.route("/<locale>/logout", methods=["POST"])
@login_required
def logout(locale):
    form = DeleteUserForm()
    is_async_logout = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    if not form.validate_on_submit():
        message = gettext("Could not sign you out. Please try again.")
        if is_async_logout:
            return jsonify({"ok": False, "message": message}), 400
        flash(message, "danger")
        return redirect(role_workspace_url(locale))
    logout_user()
    message = gettext("You have been logged out.")
    if is_async_logout:
        return jsonify({"ok": True, "message": message})
    flash(message, "info")
    return redirect(url_for("home_page", locale=locale))


@login_manager.unauthorized_handler
def unauthorized():
    flash(gettext("Please log in to access this page."), "warning")
    next_target = request.full_path if request.query_string else request.path
    return redirect(url_for("login", locale=get_locale(), next=next_target))


@app.route("/<locale>/projects/")
def projects_list(locale):
    page = request.args.get("page", 1, type=int)
    form = g.search_filter_form
    query = Project.query

    if form.search_term.data:
        term = f"%{form.search_term.data.strip()}%"
        query = query.filter((Project.title.ilike(term)) | (Project.description.ilike(term)))
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    if form.category.data:
        query = query.filter(Project.category.ilike(f"%{form.category.data.strip()}%"))
    if form.tracker_id.data and form.tracker_id.data != 0:
        query = query.filter_by(tracker_id=form.tracker_id.data)

    projects = query.order_by(Project.status.asc(), Project.start_date.is_(None), Project.start_date.asc()).paginate(
        page=page, per_page=6, error_out=False
    )
    return render_template("projects_list.html", title=gettext("Projects"), projects=projects)


@app.route("/<locale>/useful-sites")
def useful_sites_page(locale):
    social_sites = get_social_site_items()
    return render_template(
        "useful_sites.html",
        title=gettext("Useful Sites"),
        useful_site_items=social_sites + get_useful_sites(),
    )


@app.route("/<locale>/suggestions", methods=["GET", "POST"])
def suggestions_page(locale):
    form = SuggestionForm()
    form.project_id.choices = [(0, gettext("Select a project"))] + [
        (project.id, project.title) for project in Project.query.order_by(Project.title.asc()).all()
    ]
    if form.validate_on_submit():
        suggestion = PublicSuggestion(
            target_type=form.target_type.data,
            project_id=form.project_id.data if form.target_type.data == "project_tracker" else None,
            submitted_by_id=current_user.id if current_user.is_authenticated else None,
            name=(form.name.data or "").strip(),
            contact=(form.contact.data or "").strip(),
            title=form.title.data.strip(),
            body=form.body.data.strip(),
        )
        db.session.add(suggestion)
        db.session.commit()
        flash(gettext("Suggestion submitted successfully. Thank you for helping improve the city."), "success")
        return redirect(url_for("suggestions_page", locale=locale))
    return render_template("suggestions.html", title=gettext("Suggestions"), form=form)


@app.route("/<locale>/suggestions/inbox")
@login_required
def suggestions_inbox(locale):
    query = suggestion_inbox_query()
    if query is None:
        flash(gettext("You do not have permission to view suggestions."), "danger")
        return redirect(url_for("dashboard", locale=locale))
    suggestions = query.order_by(PublicSuggestion.created_at.desc()).all()
    return render_template("suggestions_inbox.html", title=gettext("Suggestion Inbox"), suggestions=suggestions)


@app.route("/<locale>/tracker")
@login_required
def tracker_workspace(locale):
    if not user_can_track_projects(current_user):
        flash(gettext("You do not have permission to access this page."), "danger")
        return redirect(role_workspace_url(locale))
    if current_user.has_permission(Permission.TRACK_ANY_PROJECT):
        projects = Project.query.order_by(Project.start_date.asc()).limit(8).all()
        project_title = gettext("Projects you can track")
    else:
        projects = Project.query.filter_by(tracker_id=current_user.id).order_by(Project.start_date.asc()).limit(8).all()
        project_title = gettext("Your assigned projects")
    query = suggestion_inbox_query()
    suggestions = query.order_by(PublicSuggestion.created_at.desc()).limit(5).all() if query else []
    workspace_links = [
        {
            "title": gettext("Projects"),
            "description": gettext("Open the public project list and jump into tracker pages when assigned."),
            "icon": "fa-solid fa-route",
            "href": url_for("projects_list", locale=locale),
        },
        {
            "title": gettext("Suggestion Inbox"),
            "description": gettext("Review ideas sent to the responsible project tracker."),
            "icon": "fa-solid fa-inbox",
            "href": url_for("suggestions_inbox", locale=locale),
        },
        {
            "title": gettext("Profile"),
            "description": gettext("Update your account contact information."),
            "icon": "fa-solid fa-user",
            "href": url_for("edit_profile", locale=locale),
        },
    ]
    return render_template(
        "role_workspace.html",
        title=gettext("Tracker Workspace"),
        workspace_title=gettext("Tracker Workspace"),
        workspace_kicker=gettext("Project operations"),
        workspace_description=gettext("A focused space for assigned projects, field updates, and project-specific public suggestions."),
        workspace_links=workspace_links,
        projects=projects,
        project_title=project_title,
        suggestions=suggestions,
    )


@app.route("/<locale>/council")
@login_required
def council_workspace(locale):
    has_council_access = (
        current_user.role == Role.COUNCIL_MEMBER
        or current_user.has_permission(Permission.VOTE_PROJECT)
        or current_user.has_permission(Permission.CREATE_PROPOSAL)
        or current_user.has_permission(Permission.VOTE_PROPOSAL)
    )
    if not has_council_access:
        flash(gettext("You do not have permission to access this page."), "danger")
        return redirect(role_workspace_url(locale))
    proposals = proposal_visibility_filter(CouncilProposal.query).order_by(CouncilProposal.created_at.desc()).limit(5).all()
    query = suggestion_inbox_query()
    suggestions = query.order_by(PublicSuggestion.created_at.desc()).limit(5).all() if query else []
    workspace_links = [
        {
            "title": gettext("Proposals"),
            "description": gettext("Review council proposals and vote when eligible."),
            "icon": "fa-solid fa-scale-balanced",
            "href": url_for("proposals_list", locale=locale),
        },
        {
            "title": gettext("Suggestion Inbox"),
            "description": gettext("Review public ideas sent to the council."),
            "icon": "fa-solid fa-inbox",
            "href": url_for("suggestions_inbox", locale=locale),
        },
        {
            "title": gettext("Profile"),
            "description": gettext("Update your account contact information."),
            "icon": "fa-solid fa-user",
            "href": url_for("edit_profile", locale=locale),
        },
    ]
    if current_user.has_permission(Permission.CREATE_PROPOSAL):
        workspace_links.insert(
            1,
            {
                "title": gettext("New Proposal"),
                "description": gettext("Create a proposal and choose voting visibility."),
                "icon": "fa-solid fa-circle-plus",
                "href": url_for("new_proposal", locale=locale),
            },
        )
    if can_manage_home_content():
        workspace_links.append(
            {
                "title": gettext("Home Content"),
                "description": gettext("Publish announcements and news for the public home page."),
                "icon": "fa-solid fa-newspaper",
                "href": url_for("home_content", locale=locale),
            }
        )
    return render_template(
        "role_workspace.html",
        title=gettext("Council Workspace"),
        workspace_title=gettext("Council Workspace"),
        workspace_kicker=gettext("Council decisions"),
        workspace_description=gettext("A focused space for votes, proposals, resident suggestions, and council-facing work."),
        workspace_links=workspace_links,
        pending_votes=g.projects_to_vote,
        proposals=proposals,
        suggestions=suggestions,
    )


@app.route("/<locale>/news-desk")
@login_required
def news_workspace(locale):
    if not can_manage_home_content():
        flash(gettext("You do not have permission to access this page."), "danger")
        return redirect(role_workspace_url(locale))
    posts = HomePost.query.order_by(HomePost.created_at.desc()).limit(6).all()
    workspace_links = [
        {
            "title": gettext("Home Content"),
            "description": gettext("Manage announcements and newspaper-style public updates."),
            "icon": "fa-solid fa-newspaper",
            "href": url_for("home_content", locale=locale),
        },
        {
            "title": gettext("New Home Content"),
            "description": gettext("Create an announcement or picture-led news story."),
            "icon": "fa-solid fa-circle-plus",
            "href": url_for("new_home_post", locale=locale),
        },
        {
            "title": gettext("Profile"),
            "description": gettext("Update your account contact information."),
            "icon": "fa-solid fa-user",
            "href": url_for("edit_profile", locale=locale),
        },
    ]
    return render_template(
        "role_workspace.html",
        title=gettext("News Desk"),
        workspace_title=gettext("News Desk"),
        workspace_kicker=gettext("Public updates"),
        workspace_description=gettext("A focused space for announcements, local news posts, and home page publishing."),
        workspace_links=workspace_links,
        posts=posts,
    )


@app.route("/<locale>/home-content", methods=["GET", "POST"])
@login_required
def home_content(locale):
    if not can_manage_home_content():
        flash(gettext("You do not have permission to manage home page content."), "danger")
        return redirect(url_for("home_page", locale=locale))
    settings_form = HomeContentSettingsForm(data={"news_enabled": news_section_enabled()})
    if request.method == "POST" and current_user.role != Role.ADMIN:
        flash(gettext("Only admins can change home page display settings."), "danger")
        return redirect(url_for("home_content", locale=locale))
    if settings_form.validate_on_submit():
        set_setting(HOME_NEWS_ENABLED_KEY, "1" if settings_form.news_enabled.data else "0")
        db.session.commit()
        flash(gettext("Home page settings updated."), "success")
        return redirect(url_for("home_content", locale=locale))
    post_query = HomePost.query
    if current_user.role == Role.NEWS_EDITOR:
        post_query = post_query.filter_by(post_type="news")
    posts = post_query.order_by(HomePost.created_at.desc()).all()
    return render_template("home_content.html", title=gettext("Home Content"), posts=posts, settings_form=settings_form)


@app.route("/<locale>/home-content/new", methods=["GET", "POST"])
@login_required
def new_home_post(locale):
    if not can_manage_home_content():
        flash(gettext("You do not have permission to manage home page content."), "danger")
        return redirect(url_for("home_page", locale=locale))
    form = configure_home_post_form(HomePostForm())
    if form.validate_on_submit():
        if not can_use_home_post_type(form.post_type.data):
            flash(gettext("This role can only create news stories."), "danger")
            return redirect(url_for("new_home_post", locale=locale))
        uploaded_image_url = save_home_post_image(form.image_file.data)
        clean_body = sanitize_rich_text(form.body.data.strip())
        post = HomePost(
            post_type=form.post_type.data,
            title=form.title.data.strip(),
            summary=(form.summary.data or "").strip(),
            body=clean_body,
            image_url=uploaded_image_url or (form.image_url.data or "").strip(),
            is_published=form.is_published.data,
            show_on_home=form.show_on_home.data,
            created_by_id=current_user.id,
        )
        db.session.add(post)
        db.session.commit()
        flash(gettext("Home page content created."), "success")
        return redirect(url_for("home_content", locale=locale))
    return render_template("home_post_form.html", title=gettext("New Home Content"), form=form)


@app.route("/<locale>/home-content/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit_home_post(locale, post_id):
    if not can_manage_home_content():
        flash(gettext("You do not have permission to manage home page content."), "danger")
        return redirect(url_for("home_page", locale=locale))
    post = HomePost.query.get_or_404(post_id)
    form = configure_home_post_form(HomePostForm(obj=post), post=post)
    if form.validate_on_submit():
        if not can_use_home_post_type(form.post_type.data):
            flash(gettext("This role can only create news stories."), "danger")
            return redirect(url_for("edit_home_post", locale=locale, post_id=post.id))
        uploaded_image_url = save_home_post_image(form.image_file.data)
        clean_body = sanitize_rich_text(form.body.data.strip())
        post.post_type = form.post_type.data
        post.title = form.title.data.strip()
        post.summary = (form.summary.data or "").strip()
        post.body = clean_body
        post.image_url = uploaded_image_url or (form.image_url.data or "").strip()
        post.is_published = form.is_published.data
        post.show_on_home = form.show_on_home.data
        post.updated_at = datetime.utcnow()
        db.session.commit()
        flash(gettext("Home page content updated."), "success")
        return redirect(url_for("home_content", locale=locale))
    return render_template("home_post_form.html", title=gettext("Edit Home Content"), form=form, post=post)


@app.route("/<locale>/home-content/<int:post_id>/toggle", methods=["POST"])
@login_required
def toggle_home_post(locale, post_id):
    if not can_manage_home_content():
        flash(gettext("You do not have permission to manage home page content."), "danger")
        return redirect(url_for("home_page", locale=locale))
    form = ActionForm()
    post = HomePost.query.get_or_404(post_id)
    if current_user.role == Role.NEWS_EDITOR and post.post_type != "news":
        abort(403)
    if not form.validate_on_submit():
        flash(gettext("Could not update this content. Please try again."), "danger")
        return redirect(url_for("home_content", locale=locale))
    post.is_published = not post.is_published
    post.updated_at = datetime.utcnow()
    db.session.commit()
    flash(gettext("Home page content visibility updated."), "success")
    return redirect(url_for("home_content", locale=locale))


@app.route("/<locale>/proposals")
def proposals_list(locale):
    page = request.args.get("page", 1, type=int)
    query = proposal_visibility_filter(CouncilProposal.query)
    proposals = query.order_by(CouncilProposal.status.asc(), CouncilProposal.created_at.desc()).paginate(page=page, per_page=8, error_out=False)
    return render_template("proposals_list.html", title=gettext("Council Proposals"), proposals=proposals)


@app.route("/<locale>/proposals/new", methods=["GET", "POST"])
@proposal_creator_required
def new_proposal(locale):
    form = ProposalForm()
    if form.validate_on_submit():
        proposal = CouncilProposal(
            title=form.title.data.strip(),
            summary=(form.summary.data or "").strip(),
            body=form.body.data.strip(),
            created_by_id=current_user.id,
            visibility=form.visibility.data,
            vote_visibility=form.vote_visibility.data,
            status=form.status.data,
            voting_deadline=form.voting_deadline.data,
        )
        db.session.add(proposal)
        db.session.commit()
        flash(gettext("Proposal created successfully."), "success")
        return redirect(url_for("proposal_detail", locale=locale, proposal_id=proposal.id))
    return render_template("proposal_form.html", title=gettext("New Proposal"), form=form)


@app.route("/<locale>/proposals/<int:proposal_id>")
def proposal_detail(locale, proposal_id):
    proposal = CouncilProposal.query.get_or_404(proposal_id)
    if not can_view_proposal(proposal):
        if not current_user.is_authenticated:
            flash(gettext("Please log in to view this proposal."), "warning")
            return redirect(url_for("login", locale=locale, next=request.path))
        flash(gettext("You do not have permission to view this proposal."), "danger")
        return redirect(url_for("proposals_list", locale=locale))

    vote_form = ProposalVoteForm()
    existing_vote = None
    if current_user.is_authenticated:
        existing_vote = CouncilProposalVote.query.filter_by(proposal_id=proposal.id, user_id=current_user.id).first()
        if existing_vote:
            vote_form.choice.data = existing_vote.choice
            vote_form.comment.data = existing_vote.comment
    votes = CouncilProposalVote.query.filter_by(proposal_id=proposal.id).all()
    votes_by_user = {vote.user_id: vote for vote in votes}
    eligible_voters = proposal_eligible_voters(proposal)
    non_voters = [user for user in eligible_voters if user.id not in votes_by_user]
    return render_template(
        "proposal_detail.html",
        title=proposal.title,
        proposal=proposal,
        vote_form=vote_form,
        existing_vote=existing_vote,
        can_vote=can_vote_on_proposal(proposal),
        counts=proposal.vote_counts(),
        eligible_voters=eligible_voters,
        votes_by_user=votes_by_user,
        non_voters=non_voters,
    )


@app.route("/<locale>/proposals/<int:proposal_id>/edit", methods=["GET", "POST"])
@login_required
def edit_proposal(locale, proposal_id):
    proposal = CouncilProposal.query.get_or_404(proposal_id)
    if not can_edit_proposal(proposal):
        flash(gettext("Only an admin or a proposal creator with proposal permission can edit this proposal."), "danger")
        return redirect(url_for("proposal_detail", locale=locale, proposal_id=proposal.id))
    form = ProposalForm(obj=proposal)
    form.submit.label.text = gettext("Update Proposal")
    if form.validate_on_submit():
        proposal.title = form.title.data.strip()
        proposal.summary = (form.summary.data or "").strip()
        proposal.body = form.body.data.strip()
        proposal.visibility = form.visibility.data
        proposal.vote_visibility = form.vote_visibility.data
        proposal.status = form.status.data
        proposal.voting_deadline = form.voting_deadline.data
        db.session.commit()
        flash(gettext("Proposal updated successfully."), "success")
        return redirect(url_for("proposal_detail", locale=locale, proposal_id=proposal.id))
    return render_template("proposal_form.html", title=gettext("Edit Proposal"), form=form, proposal=proposal)


@app.route("/<locale>/proposals/<int:proposal_id>/vote", methods=["POST"])
@login_required
def proposal_vote(locale, proposal_id):
    proposal = CouncilProposal.query.get_or_404(proposal_id)
    if not can_vote_on_proposal(proposal):
        flash(gettext("You are not eligible to vote on this proposal."), "danger")
        return redirect(url_for("proposal_detail", locale=locale, proposal_id=proposal.id))
    if not proposal.is_open_for_voting:
        flash(gettext("Voting is closed for this proposal."), "warning")
        return redirect(url_for("proposal_detail", locale=locale, proposal_id=proposal.id))

    form = ProposalVoteForm()
    if form.validate_on_submit():
        existing_vote = CouncilProposalVote.query.filter_by(proposal_id=proposal.id, user_id=current_user.id).first()
        if existing_vote:
            existing_vote.choice = form.choice.data
            existing_vote.comment = (form.comment.data or "").strip()
            existing_vote.vote_timestamp = datetime.utcnow()
            flash(gettext("Proposal vote updated."), "info")
        else:
            db.session.add(
                CouncilProposalVote(
                    proposal_id=proposal.id,
                    user_id=current_user.id,
                    choice=form.choice.data,
                    comment=(form.comment.data or "").strip(),
                )
            )
            flash(gettext("Proposal vote submitted."), "success")
        db.session.commit()
    else:
        flash(gettext("Could not submit your proposal vote. Please choose an option."), "danger")
    return redirect(url_for("proposal_detail", locale=locale, proposal_id=proposal.id))


@app.route("/<locale>/donations")
def donation_campaigns(locale):
    campaigns = DonationCampaign.query.filter_by(status="Active").order_by(DonationCampaign.created_at.desc()).all()
    return render_template("donation_campaigns.html", title=gettext("Donation Campaigns"), campaigns=campaigns)


@app.route("/<locale>/donations/<int:campaign_id>")
def donation_campaign(locale, campaign_id):
    campaign = DonationCampaign.query.get_or_404(campaign_id)
    groups = sorted(campaign.groups, key=lambda group: group.confirmed_total(), reverse=True)
    recent_donations = (
        Donation.query.filter_by(campaign_id=campaign.id, payment_status="Confirmed")
        .order_by(Donation.created_at.desc())
        .limit(12)
        .all()
    )
    return render_template(
        "donation_campaign.html",
        title=campaign.title,
        campaign=campaign,
        groups=groups,
        recent_donations=recent_donations,
    )


@app.route("/<locale>/donations/<int:campaign_id>/give", methods=["GET", "POST"])
def donate(locale, campaign_id):
    campaign = DonationCampaign.query.get_or_404(campaign_id)
    if campaign.status != "Active":
        flash(gettext("This donation campaign is not accepting payments right now."), "warning")
        return redirect(url_for("donation_campaign", locale=locale, campaign_id=campaign.id))

    form = DonationForm()
    form.group_id.choices = [(0, gettext("No group"))] + [(group.id, group.name) for group in campaign.groups]
    if current_user.is_authenticated and request.method == "GET":
        form.donor_name.data = current_user.username
        form.donor_email.data = current_user.email

    if form.validate_on_submit():
        group = None
        if form.attribution_type.data == "group":
            if form.group_id.data:
                group = DonationGroup.query.filter_by(id=form.group_id.data, campaign_id=campaign.id).first()
            elif form.new_group_name.data:
                group, _ = find_or_create_donation_group(campaign, form.new_group_name.data)
        donation = Donation(
            campaign_id=campaign.id,
            group_id=group.id if group else None,
            donor_name=form.donor_name.data.strip(),
            donor_email=(form.donor_email.data or "").strip().lower(),
            donor_phone=(form.donor_phone.data or "").strip(),
            amount=form.amount.data,
            attribution_type=form.attribution_type.data,
            display_name=form.display_name.data,
            payment_method=form.payment_method.data,
            payment_status="Pending",
            payment_reference=generate_payment_reference(),
            message=(form.message.data or "").strip(),
        )
        db.session.add(donation)
        db.session.commit()
        flash(gettext("Donation recorded. Please complete the payment using your reference number."), "success")
        return redirect(url_for("donation_receipt", locale=locale, payment_reference=donation.payment_reference))

    return render_template("donate.html", title=gettext("Donate"), campaign=campaign, form=form)


@app.route("/<locale>/donations/receipt/<payment_reference>")
def donation_receipt(locale, payment_reference):
    donation = Donation.query.filter_by(payment_reference=payment_reference).first_or_404()
    return render_template("donation_receipt.html", title=gettext("Donation Reference"), donation=donation)


@app.route("/<locale>/project/new", methods=["GET", "POST"])
@permission_required(Permission.CREATE_PROJECT)
def new_project(locale):
    form = ProjectForm()
    form.submit.label.text = gettext("Create Project")
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            voting_deadline=form.voting_deadline.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            status=form.status.data,
            created_by_id=current_user.id,
        )
        db.session.add(project)
        db.session.commit()
        flash(gettext("New project created successfully!"), "success")
        return redirect(url_for("project", project_id=project.id, locale=locale))
    return render_template("create_project.html", title=gettext("New Project"), form=form)


@app.route("/<locale>/project/<int:project_id>")
def project(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    vote_form = VoteForm()
    existing_vote = None
    if current_user.is_authenticated:
        existing_vote = Vote.query.filter_by(user_id=current_user.id, project_id=project_id).first()
        if existing_vote:
            vote_form.vote.data = "True" if existing_vote.vote else "False"
    yes_votes, no_votes = selected_project.vote_counts()
    volunteer_count = project_volunteer_count(selected_project)
    return render_template(
        "project.html",
        title=selected_project.title,
        project=selected_project,
        vote_form=vote_form,
        existing_vote=existing_vote,
        can_vote=current_user.is_authenticated
        and current_user.has_permission(Permission.VOTE_PROJECT)
        and selected_project.is_open_for_voting,
        can_view_results=current_user.is_authenticated and current_user.has_permission(Permission.VIEW_VOTE_RESULTS),
        yes_votes=yes_votes,
        no_votes=no_votes,
        volunteer_count=volunteer_count,
    )


@app.route("/<locale>/project/<int:project_id>/edit", methods=["GET", "POST"])
@permission_required(Permission.EDIT_PROJECT)
def edit_project(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=selected_project)
    form.submit.label.text = gettext("Update Project")
    if form.validate_on_submit():
        form.populate_obj(selected_project)
        db.session.commit()
        flash(gettext("Project updated successfully!"), "success")
        return redirect(url_for("project", project_id=selected_project.id, locale=locale))
    return render_template("edit_project.html", title=gettext("Edit Project"), form=form, project=selected_project)


@app.route("/<locale>/project/<int:project_id>/vote", methods=["POST"])
@council_member_required
def vote(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    if not selected_project.is_open_for_voting:
        flash(gettext("Voting deadline has passed for this project."), "warning")
        return redirect(url_for("project", project_id=selected_project.id, locale=locale))

    form = VoteForm()
    if form.validate_on_submit():
        vote_value = form.vote.data == "True"
        existing_vote = Vote.query.filter_by(user_id=current_user.id, project_id=project_id).first()
        if existing_vote:
            existing_vote.vote = vote_value
            existing_vote.vote_timestamp = datetime.utcnow()
            flash(gettext("Vote updated successfully!"), "info")
        else:
            db.session.add(Vote(user_id=current_user.id, project_id=project_id, vote=vote_value))
            flash(gettext("Vote submitted successfully!"), "success")
        db.session.commit()
    else:
        flash(gettext("Could not submit your vote. Please try again."), "danger")
    return redirect(url_for("project", project_id=selected_project.id, locale=locale))


@app.route("/<locale>/project/<int:project_id>/results")
@login_required
def view_results(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    if not current_user.has_permission(Permission.VIEW_VOTE_RESULTS):
        flash(gettext("You do not have permission to view voting results."), "danger")
        return redirect(url_for("project", project_id=selected_project.id, locale=locale))
    yes_votes, no_votes = selected_project.vote_counts()
    return render_template("results.html", title=gettext("Voting Results"), project=selected_project, yes_votes=yes_votes, no_votes=no_votes)


@app.route("/<locale>/project/<int:project_id>/assign", methods=["GET", "POST"])
@permission_required(Permission.ASSIGN_TRACKER)
def assign_tracker(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    form = AssignTrackerForm()
    trackers = tracker_assignable_users()
    form.tracker.choices = [(user.id, display_user_name(user)) for user in trackers]
    if not trackers:
        flash(gettext("Create a user with project tracking permission before assigning projects."), "warning")
        return redirect(url_for("project", project_id=selected_project.id, locale=locale))
    if form.validate_on_submit():
        tracker = User.query.get_or_404(form.tracker.data)
        selected_project.tracker = tracker
        db.session.commit()
        flash(gettext("Project assigned to %(tracker_name)s!", tracker_name=tracker.username), "success")
        return redirect(url_for("project", project_id=selected_project.id, locale=locale))
    return render_template("assign_tracker.html", title=gettext("Assign Project Tracker"), form=form, project=selected_project)


@app.route("/<locale>/project/<int:project_id>/track")
@login_required
def track_project(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    if not require_tracker_access(selected_project):
        return redirect(url_for("dashboard", locale=locale))
    status_form = StatusUpdateForm(obj=selected_project)
    comment_form = CommentForm()
    return render_template(
        "track_project.html",
        title=gettext("Track Project"),
        project=selected_project,
        status_form=status_form,
        comment_form=comment_form,
        comments=selected_project.comments,
        can_update_status=current_user.has_permission(Permission.UPDATE_PROJECT_STATUS),
        can_add_comment=current_user.has_permission(Permission.ADD_PROJECT_COMMENT),
    )


@app.route("/<locale>/project/<int:project_id>/status", methods=["POST"])
@login_required
def update_project_status(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    if not require_tracker_access(selected_project):
        return redirect(url_for("dashboard", locale=locale))
    if not current_user.has_permission(Permission.UPDATE_PROJECT_STATUS):
        flash(gettext("You do not have permission to update project status."), "danger")
        return redirect(url_for("track_project", project_id=selected_project.id, locale=locale))
    form = StatusUpdateForm()
    if form.validate_on_submit():
        selected_project.status = form.status.data
        db.session.add(
            ProjectComment(
                project_id=selected_project.id,
                user_id=current_user.id,
                body=gettext("Status changed to %(status)s.", status=selected_project.status),
            )
        )
        db.session.commit()
        flash(gettext("Project status updated."), "success")
    else:
        flash(gettext("Could not update project status."), "danger")
    return redirect(url_for("track_project", project_id=selected_project.id, locale=locale))


@app.route("/<locale>/project/<int:project_id>/comment", methods=["POST"])
@login_required
def add_comment(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    if not require_tracker_access(selected_project):
        return redirect(url_for("dashboard", locale=locale))
    if not current_user.has_permission(Permission.ADD_PROJECT_COMMENT):
        flash(gettext("You do not have permission to add project updates."), "danger")
        return redirect(url_for("track_project", project_id=selected_project.id, locale=locale))
    form = CommentForm()
    if form.validate_on_submit():
        db.session.add(ProjectComment(project_id=selected_project.id, user_id=current_user.id, body=form.body.data.strip()))
        db.session.commit()
        flash(gettext("Comment added."), "success")
    else:
        flash(gettext("Comment cannot be empty."), "danger")
    return redirect(url_for("track_project", project_id=selected_project.id, locale=locale))


@app.route("/<locale>/project/<int:project_id>/volunteer", methods=["GET", "POST"])
def volunteer_for_project(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    form = VolunteerForm()
    if current_user.is_authenticated and request.method == "GET" and not form.name.data:
        form.name.data = current_user.username
    if form.validate_on_submit():
        db.session.add(
            Volunteer(
                name=form.name.data.strip(),
                project_name=selected_project.title,
                additional_info=(form.additional_info.data or "").strip(),
            )
        )
        if current_user.is_authenticated:
            existing = ProjectMember.query.filter_by(user_id=current_user.id, project_id=selected_project.id).first()
            if not existing:
                db.session.add(ProjectMember(user_id=current_user.id, project_id=selected_project.id, volunteer_name=form.name.data.strip()))
        db.session.commit()
        flash(gettext("Thank you for volunteering for %(project_title)s!", project_title=selected_project.title), "success")
        return redirect(url_for("project", project_id=selected_project.id, locale=locale))
    return render_template("volunteer_form.html", title=gettext("Volunteer for Project"), form=form, project=selected_project)


@app.route("/<locale>/calendar")
def calendar(locale):
    projects = Project.query.order_by(Project.start_date.asc()).all()
    return render_template("calendar.html", title=gettext("Project Calendar"), projects=projects)


@app.route("/<locale>/api/mobile/bootstrap")
def mobile_bootstrap(locale):
    context = build_civic_home_context()
    active_campaigns = DonationCampaign.query.filter_by(status="Active").order_by(DonationCampaign.created_at.desc()).limit(4).all()
    public_proposals = (
        CouncilProposal.query.filter_by(visibility="public")
        .order_by(CouncilProposal.status.asc(), CouncilProposal.created_at.desc())
        .limit(5)
        .all()
    )
    return jsonify(
        {
            "ok": True,
            "locale": locale,
            "generated_at": api_datetime(datetime.utcnow()),
            "stats": context["stats"],
            "announcements": [api_home_post(post) for post in context["announcements"]],
            "news": [api_home_post(post) for post in context["news_posts"]],
            "recent_projects": [api_project(project) for project in context["recent_projects"]],
            "pending_votes": [api_project(project) for project in context["pending_votes"]],
            "donation_campaigns": [api_donation_campaign(campaign) for campaign in active_campaigns],
            "public_proposals": [api_proposal(proposal) for proposal in public_proposals],
            "useful_sites": [api_link_item(item) for item in get_social_site_items() + get_useful_sites()],
        }
    )


@app.route("/<locale>/api/mobile/projects")
def mobile_projects(locale):
    projects = Project.query.order_by(Project.status.asc(), Project.start_date.is_(None), Project.start_date.asc()).all()
    return jsonify({"ok": True, "projects": [api_project(project) for project in projects]})


@app.route("/<locale>/api/mobile/projects/<int:project_id>")
def mobile_project_detail(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    payload = api_project(selected_project)
    payload["comments"] = [
        {
            "id": comment.id,
            "author": display_user_name(comment.author) if comment.author else "",
            "body": comment.body,
            "created_at": api_datetime(comment.created_at),
        }
        for comment in selected_project.comments[-8:]
    ]
    return jsonify({"ok": True, "project": payload})


@app.route("/<locale>/api/mobile/projects/<int:project_id>/volunteer", methods=["POST"])
def mobile_project_volunteer(locale, project_id):
    selected_project = Project.query.get_or_404(project_id)
    data = request.get_json(silent=True) or {}
    name = str(data.get("name") or "").strip()[:100]
    additional_info = str(data.get("additional_info") or "").strip()[:1000]
    if len(name) < 2:
        return api_payload_error(gettext("Please enter your name."))
    volunteer = Volunteer(name=name, project_name=selected_project.title, additional_info=additional_info)
    db.session.add(volunteer)
    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "message": gettext("Thank you for volunteering for %(project_title)s!", project_title=selected_project.title),
            "volunteer": {"id": volunteer.id, "name": volunteer.name, "project_name": volunteer.project_name},
        }
    ), 201


@app.route("/<locale>/api/mobile/proposals")
def mobile_proposals(locale):
    proposals = (
        CouncilProposal.query.filter_by(visibility="public")
        .order_by(CouncilProposal.status.asc(), CouncilProposal.created_at.desc())
        .all()
    )
    return jsonify({"ok": True, "proposals": [api_proposal(proposal) for proposal in proposals]})


@app.route("/<locale>/api/mobile/donations")
def mobile_donation_campaigns(locale):
    campaigns = DonationCampaign.query.filter_by(status="Active").order_by(DonationCampaign.created_at.desc()).all()
    return jsonify({"ok": True, "campaigns": [api_donation_campaign(campaign, include_details=True) for campaign in campaigns]})


@app.route("/<locale>/api/mobile/donations/<int:campaign_id>")
def mobile_donation_campaign_detail(locale, campaign_id):
    campaign = DonationCampaign.query.get_or_404(campaign_id)
    return jsonify({"ok": True, "campaign": api_donation_campaign(campaign, include_details=True)})


@app.route("/<locale>/api/mobile/donations/<int:campaign_id>/pledge", methods=["POST"])
def mobile_donation_pledge(locale, campaign_id):
    campaign = DonationCampaign.query.get_or_404(campaign_id)
    if campaign.status != "Active":
        return api_payload_error(gettext("This donation campaign is not accepting payments right now."), 409)
    data = request.get_json(silent=True) or {}
    donor_name = str(data.get("donor_name") or "").strip()[:120]
    donor_email = str(data.get("donor_email") or "").strip().lower()[:120]
    donor_phone = str(data.get("donor_phone") or "").strip()[:50]
    attribution_type = str(data.get("attribution_type") or "independent").strip()
    new_group_name = str(data.get("new_group_name") or "").strip()[:120]
    message = str(data.get("message") or "").strip()[:1000]
    display_name = bool(data.get("display_name", True))
    try:
        amount = Decimal(str(data.get("amount", "0")))
    except Exception:
        amount = Decimal("0")
    if len(donor_name) < 2:
        return api_payload_error(gettext("Please enter your name."))
    if amount <= 0:
        return api_payload_error(gettext("Amount must be greater than zero."))
    group = None
    if attribution_type == "group":
        group_id = data.get("group_id")
        if group_id:
            group = DonationGroup.query.filter_by(id=group_id, campaign_id=campaign.id).first()
        if not group and new_group_name:
            group, _ = find_or_create_donation_group(campaign, new_group_name)
        if not group:
            return api_payload_error(gettext("Choose a group or enter a new group name."))
    else:
        attribution_type = "independent"
    donation = Donation(
        campaign_id=campaign.id,
        group_id=group.id if group else None,
        donor_name=donor_name,
        donor_email=donor_email,
        donor_phone=donor_phone,
        amount=amount,
        attribution_type=attribution_type,
        display_name=display_name,
        payment_method=str(data.get("payment_method") or "bank_transfer")[:30],
        payment_status="Pending",
        payment_reference=generate_payment_reference(),
        message=message,
    )
    db.session.add(donation)
    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "message": gettext("Donation recorded. Please complete the payment using your reference number."),
            "payment_reference": donation.payment_reference,
            "receipt_url": url_for("donation_receipt", locale=locale, payment_reference=donation.payment_reference, _external=True),
            "donation": {
                "id": donation.id,
                "amount": api_decimal(donation.amount),
                "currency": campaign.currency,
                "campaign_title": campaign.title,
            },
        }
    ), 201


@app.route("/<locale>/api/mobile/suggestions", methods=["POST"])
def mobile_suggestion(locale):
    data = request.get_json(silent=True) or {}
    target_type = str(data.get("target_type") or "council").strip()
    project_id = data.get("project_id")
    name = str(data.get("name") or "").strip()[:120]
    contact = str(data.get("contact") or "").strip()[:160]
    title = str(data.get("title") or "").strip()[:140]
    body = str(data.get("body") or "").strip()[:4000]
    if target_type not in {"council", "project_tracker"}:
        target_type = "council"
    selected_project = None
    if target_type == "project_tracker":
        try:
            selected_project = Project.query.get(int(project_id))
        except (TypeError, ValueError):
            selected_project = None
        if not selected_project:
            return api_payload_error(gettext("Select a project."))
    if len(title) < 3:
        return api_payload_error(gettext("Title is required."))
    if len(body) < 10:
        return api_payload_error(gettext("Please add a few details so the council can understand the suggestion."))
    suggestion = PublicSuggestion(
        target_type=target_type,
        project_id=selected_project.id if selected_project else None,
        submitted_by_id=current_user.id if current_user.is_authenticated else None,
        name=name,
        contact=contact,
        title=title,
        body=body,
    )
    db.session.add(suggestion)
    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "message": gettext("Suggestion submitted successfully. Thank you for helping improve the city."),
            "suggestion": {
                "id": suggestion.id,
                "title": suggestion.title,
                "target_type": suggestion.target_type,
                "status": suggestion.status,
                "created_at": api_datetime(suggestion.created_at),
            },
        }
    ), 201


@app.route("/<locale>/admin")
@admin_required
def admin_hub(locale):
    admin_links = [
        {
            "title": gettext("Manage Users"),
            "description": gettext("Create users, edit roles, and adjust permissions."),
            "icon": "fa-solid fa-users-gear",
            "href": url_for("manage_users", locale=locale),
        },
        {
            "title": gettext("Register User"),
            "description": gettext("Add a new admin, council member, tracker, or news editor."),
            "icon": "fa-solid fa-user-plus",
            "href": url_for("register", locale=locale),
        },
        {
            "title": gettext("Donation Admin"),
            "description": gettext("Manage donation campaigns, giving groups, and payment confirmations."),
            "icon": "fa-solid fa-hand-holding-heart",
            "href": url_for("admin_donations", locale=locale),
        },
        {
            "title": gettext("Donation Dashboard"),
            "description": gettext("Review donation totals, pending payments, giving groups, and recent references."),
            "icon": "fa-solid fa-chart-pie",
            "href": url_for("admin_donation_dashboard", locale=locale),
        },
        {
            "title": gettext("New Donation Campaign"),
            "description": gettext("Create a new donation request with groups, goals, and payment instructions."),
            "icon": "fa-solid fa-circle-plus",
            "href": url_for("new_donation_campaign", locale=locale),
        },
        {
            "title": gettext("Site Links"),
            "description": gettext("Edit footer social links, useful sites, and public link descriptions."),
            "icon": "fa-solid fa-link",
            "href": url_for("site_options", locale=locale),
        },
        {
            "title": gettext("Home Content"),
            "description": gettext("Publish home page announcements and newspaper-style news posts."),
            "icon": "fa-solid fa-newspaper",
            "href": url_for("home_content", locale=locale),
        },
        {
            "title": gettext("Suggestion Inbox"),
            "description": gettext("Review ideas sent to the council or to project trackers."),
            "icon": "fa-solid fa-inbox",
            "href": url_for("suggestions_inbox", locale=locale),
        },
        {
            "title": gettext("Profile"),
            "description": gettext("Update your account contact information."),
            "icon": "fa-solid fa-user",
            "href": url_for("edit_profile", locale=locale),
        },
        {
            "title": gettext("Technical Admin"),
            "description": gettext("Open the protected database administration panel."),
            "icon": "fa-solid fa-screwdriver-wrench",
            "href": "/admin/",
        },
    ]
    return render_template("admin_hub.html", title=gettext("Admin"), admin_links=admin_links)


@app.route("/<locale>/manage_users")
@admin_required
def manage_users(locale):
    users = User.query.order_by(User.role.asc(), User.username.asc()).all()
    return render_template("manage_users.html", title=gettext("Manage Users"), users=users)


@app.route("/<locale>/admin/donations")
@admin_required
def admin_donations(locale):
    campaigns = DonationCampaign.query.order_by(DonationCampaign.created_at.desc()).all()
    return render_template("admin_donations.html", title=gettext("Donation Campaigns"), campaigns=campaigns)


@app.route("/<locale>/admin/donations/new", methods=["GET", "POST"])
@admin_required
def new_donation_campaign(locale):
    form = DonationCampaignForm()
    if form.validate_on_submit():
        campaign = DonationCampaign(
            title=form.title.data.strip(),
            beneficiary=(form.beneficiary.data or "").strip(),
            description=form.description.data.strip(),
            goal_amount=form.goal_amount.data,
            currency=form.currency.data,
            status=form.status.data,
            payment_instructions=(form.payment_instructions.data or "").strip(),
        )
        db.session.add(campaign)
        db.session.commit()
        flash(gettext("Donation campaign created."), "success")
        return redirect(url_for("manage_donation_campaign", locale=locale, campaign_id=campaign.id))
    return render_template("donation_campaign_form.html", title=gettext("New Donation Campaign"), form=form)


@app.route("/<locale>/admin/donations/<int:campaign_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_donation_campaign(locale, campaign_id):
    campaign = DonationCampaign.query.get_or_404(campaign_id)
    form = DonationCampaignForm(obj=campaign)
    if form.validate_on_submit():
        campaign.title = form.title.data.strip()
        campaign.beneficiary = (form.beneficiary.data or "").strip()
        campaign.description = form.description.data.strip()
        campaign.goal_amount = form.goal_amount.data
        campaign.currency = form.currency.data
        campaign.status = form.status.data
        campaign.payment_instructions = (form.payment_instructions.data or "").strip()
        db.session.commit()
        flash(gettext("Donation campaign updated."), "success")
        return redirect(url_for("manage_donation_campaign", locale=locale, campaign_id=campaign.id))
    return render_template("donation_campaign_form.html", title=gettext("Edit Donation Campaign"), form=form, campaign=campaign)


@app.route("/<locale>/admin/donations/<int:campaign_id>", methods=["GET", "POST"])
@admin_required
def manage_donation_campaign(locale, campaign_id):
    campaign = DonationCampaign.query.get_or_404(campaign_id)
    group_form = DonationGroupForm()
    if group_form.validate_on_submit():
        group, created = find_or_create_donation_group(
            campaign,
            group_form.name.data,
            (group_form.description.data or "").strip(),
        )
        db.session.commit()
        if created:
            flash(gettext("Donation group added."), "success")
        else:
            flash(gettext("Donation group already exists."), "info")
        return redirect(url_for("manage_donation_campaign", locale=locale, campaign_id=campaign.id))
    donations = Donation.query.filter_by(campaign_id=campaign.id).order_by(Donation.created_at.desc()).all()
    groups = sorted(campaign.groups, key=lambda group: group.confirmed_total(), reverse=True)
    return render_template(
        "manage_donation_campaign.html",
        title=campaign.title,
        campaign=campaign,
        group_form=group_form,
        groups=groups,
        donations=donations,
    )


@app.route("/<locale>/admin/donations/<int:campaign_id>/donations/<int:donation_id>/<status>", methods=["POST"])
@admin_required
def update_donation_status(locale, campaign_id, donation_id, status):
    form = ActionForm()
    donation = Donation.query.filter_by(id=donation_id, campaign_id=campaign_id).first_or_404()
    if status not in {"Pending", "Confirmed", "Rejected"}:
        abort(404)
    if not form.validate_on_submit():
        flash(gettext("Could not update donation status. Please try again."), "danger")
        return redirect(url_for("manage_donation_campaign", locale=locale, campaign_id=campaign_id))
    donation.payment_status = status
    db.session.commit()
    flash(gettext("Donation status updated."), "success")
    return redirect(url_for("manage_donation_campaign", locale=locale, campaign_id=campaign_id))


@app.route("/<locale>/admin/site-links", methods=["GET", "POST"])
@admin_required
def site_options(locale):
    form = SiteLinksForm(data=get_site_links())
    useful_site_rows = get_useful_sites(include_disabled=True)
    custom_site_errors = []
    if request.method == "POST":
        useful_site_rows, custom_site_errors = parse_useful_sites_form(request.form)
    if form.validate_on_submit():
        if custom_site_errors:
            for error in custom_site_errors:
                flash(error, "danger")
            return render_template(
                "site_options.html",
                title=gettext("Site Links"),
                form=form,
                social_platforms=SOCIAL_LINK_PLATFORMS,
                useful_site_rows=useful_site_rows or [empty_useful_site()],
                custom_site_errors=custom_site_errors,
            )
        for key in DEFAULT_SITE_LINKS:
            value = getattr(form, key).data or ""
            set_setting(key, value.strip())
        for key in DEFAULT_SITE_LINK_VISIBILITY:
            set_setting(key, "1" if getattr(form, key).data else "0")
        for key in DEFAULT_SITE_LINK_DESCRIPTIONS:
            set_setting(key, (getattr(form, key).data or "").strip())
        set_setting(USEFUL_SITES_SETTING_KEY, json.dumps(useful_site_rows, ensure_ascii=False))
        db.session.commit()
        flash(gettext("Site links updated successfully."), "success")
        return redirect(url_for("site_options", locale=locale))
    return render_template(
        "site_options.html",
        title=gettext("Site Links"),
        form=form,
        social_platforms=SOCIAL_LINK_PLATFORMS,
        useful_site_rows=useful_site_rows or [empty_useful_site()],
        custom_site_errors=custom_site_errors,
    )


@app.route("/<locale>/register", methods=["GET", "POST"])
@admin_required
def register(locale):
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.strip(), email=form.email.data.strip().lower(), role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(gettext("Account created successfully!"), "success")
        return redirect(url_for("manage_users", locale=locale))
    return render_template("register.html", title=gettext("Register User"), form=form, role_descriptions=role_description_items())


@app.route("/<locale>/user/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(locale, user_id):
    user = User.query.get_or_404(user_id)
    form = UserEditForm(user, obj=user)
    if form.validate_on_submit():
        if user.id == current_user.id and user.role == Role.ADMIN and form.role.data != Role.ADMIN:
            flash(gettext("You cannot remove your own admin role while you are logged in."), "warning")
            return redirect(url_for("edit_user", locale=locale, user_id=user.id))
        if user.role == Role.ADMIN and form.role.data != Role.ADMIN and User.query.filter_by(role=Role.ADMIN).count() <= 1:
            flash(gettext("Keep at least one admin account before changing this role."), "warning")
            return redirect(url_for("edit_user", locale=locale, user_id=user.id))
        user.username = form.username.data.strip()
        user.email = form.email.data.strip().lower()
        user.role = form.role.data
        user.contact_details = form.contact_details.data
        use_defaults = request.form.get("use_default_permissions") == "1"
        overrides = {
            permission: request.form.get(f"permission_state_{permission}", "default")
            for permission in permission_keys()
        }
        user.permissions = serialize_permission_config(use_defaults, overrides)
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash(gettext("User updated successfully."), "success")
        return redirect(url_for("manage_users", locale=locale))
    return render_template(
        "edit_user.html",
        title=gettext("Edit User"),
        form=form,
        user=user,
        permission_config=parse_permission_config(user.permissions),
        permission_rows=permission_editor_rows(user),
        role_descriptions=role_description_items(),
    )


@app.route("/<locale>/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(locale, user_id):
    form = DeleteUserForm()
    if not form.validate_on_submit():
        flash(gettext("Could not delete user. Please try again."), "danger")
        return redirect(url_for("manage_users", locale=locale))
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash(gettext("You cannot delete your own account while logged in."), "warning")
        return redirect(url_for("manage_users", locale=locale))
    db.session.delete(user)
    db.session.commit()
    flash(gettext("User deleted successfully."), "success")
    return redirect(url_for("manage_users", locale=locale))


@app.route("/<locale>/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile(locale):
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data.strip()
        current_user.email = form.email.data.strip().lower()
        current_user.contact_details = form.contact_details.data
        db.session.commit()
        flash(gettext("Your profile has been updated!"), "success")
        return redirect(url_for("dashboard", locale=locale))
    return render_template("edit_profile.html", title=gettext("Edit Profile"), form=form)


@app.errorhandler(404)
def not_found(error):
    return render_template("dashboard.html", title=gettext("Not Found"), stats={}, recent_projects=[], pending_votes=[], assigned_projects=[], latest_comments=[]), 404


if __name__ == "__main__":
    app.run(debug=True)
