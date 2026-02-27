import time
import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from sqlalchemy import func
from werkzeug.security import check_password_hash
from app.models.user import AdminUser
from app.extensions import limiter

logger = logging.getLogger(__name__)

admin_auth_bp = Blueprint("admin_auth", __name__)

_failed_attempts = {}
LOCKOUT_THRESHOLD = 5
LOCKOUT_WINDOW = 900


def _check_lockout(ip):
    if ip not in _failed_attempts:
        return False
    attempts, first_attempt_time = _failed_attempts[ip]
    if time.time() - first_attempt_time > LOCKOUT_WINDOW:
        del _failed_attempts[ip]
        return False
    return attempts >= LOCKOUT_THRESHOLD


def _record_failure(ip):
    now = time.time()
    if ip in _failed_attempts:
        attempts, first_time = _failed_attempts[ip]
        if now - first_time > LOCKOUT_WINDOW:
            _failed_attempts[ip] = (1, now)
        else:
            _failed_attempts[ip] = (attempts + 1, first_time)
    else:
        _failed_attempts[ip] = (1, now)


def _clear_failures(ip):
    _failed_attempts.pop(ip, None)


@admin_auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute;20 per hour", methods=["POST"])
def login():
    if request.method == "POST":
        ip = request.remote_addr
        if _check_lockout(ip):
            remaining = int(LOCKOUT_WINDOW - (time.time() - _failed_attempts[ip][1]))
            minutes = max(1, remaining // 60)
            logger.warning("Locked out IP %s attempted login", ip)
            flash(f"Too many failed attempts. Please try again in {minutes} minute{'s' if minutes != 1 else ''}.", "error")
            return render_template("admin/login.html")

        username = request.form.get("username", "").strip()
        password = request.form.get("password")
        user = AdminUser.query.filter(func.lower(AdminUser.username) == username.lower()).first()
        if user and check_password_hash(user.password_hash, password):
            _clear_failures(ip)
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("admin_dashboard.dashboard"))

        _record_failure(ip)
        logger.warning("Failed login attempt for username '%s' from IP %s", username, ip)
        flash("Invalid username or password.", "error")
    return render_template("admin/login.html")


@admin_auth_bp.route("/logout")
@login_required
def logout():
    session.pop("devtools_unlocked", None)
    logout_user()
    return redirect(url_for("public.home"))
