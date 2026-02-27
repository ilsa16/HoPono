from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from sqlalchemy import func
from werkzeug.security import check_password_hash
from app.models.user import AdminUser

admin_auth_bp = Blueprint("admin_auth", __name__)


@admin_auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password")
        user = AdminUser.query.filter(func.lower(AdminUser.username) == username.lower()).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin_dashboard.dashboard"))
        flash("Invalid username or password.", "error")
    return render_template("admin/login.html")


@admin_auth_bp.route("/logout")
@login_required
def logout():
    session.pop("devtools_unlocked", None)
    logout_user()
    return redirect(url_for("public.home"))
