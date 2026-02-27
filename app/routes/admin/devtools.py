from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import limiter

admin_devtools_bp = Blueprint("admin_devtools", __name__)

DEVTOOLS_PASSWORD_HASH = generate_password_hash("2212002g")


def devtools_required(f):
    from functools import wraps

    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not session.get("devtools_unlocked"):
            return redirect(url_for("admin_devtools.devtools_login"))
        return f(*args, **kwargs)

    return decorated


@admin_devtools_bp.route("/login", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per minute", methods=["POST"])
def devtools_login():
    if session.get("devtools_unlocked"):
        return redirect(url_for("admin_devtools.devtools_page"))

    if request.method == "POST":
        password = request.form.get("password", "")
        if check_password_hash(DEVTOOLS_PASSWORD_HASH, password):
            session["devtools_unlocked"] = True
            return redirect(url_for("admin_devtools.devtools_page"))
        flash("Invalid developer password.", "error")

    return render_template("admin/devtools_login.html")


@admin_devtools_bp.route("/")
@devtools_required
def devtools_page():
    return render_template("admin/devtools.html")
