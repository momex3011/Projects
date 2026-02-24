from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.user import User
from app import db
from flask_login import login_user, logout_user, login_required

auth_bp = Blueprint("auth", __name__, template_folder="templates")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.check_password(request.form["password"]):
            login_user(user)
            return redirect(request.args.get("next") or url_for("admin.dashboard"))
        flash("Invalid login", "danger")
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))
