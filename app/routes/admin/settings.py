from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.settings import Setting

admin_settings_bp = Blueprint("admin_settings", __name__)

DEFAULT_SETTINGS = {
    "reminder_hours_before": "24",
    "buffer_minutes": "30",
    "sms_enabled": "true",
    "email_enabled": "true",
}


@admin_settings_bp.route("/")
@login_required
def view_settings():
    settings = {}
    for key, default in DEFAULT_SETTINGS.items():
        setting = db.session.get(Setting, key)
        settings[key] = setting.value if setting else default
    return render_template("admin/settings.html", settings=settings)


@admin_settings_bp.route("/", methods=["POST"])
@login_required
def update_settings():
    for key in DEFAULT_SETTINGS:
        value = request.form.get(key, "").strip()
        if value:
            setting = db.session.get(Setting, key)
            if setting:
                setting.value = value
            else:
                setting = Setting(key=key, value=value)
                db.session.add(setting)

    db.session.commit()
    flash("Settings updated.", "success")
    return redirect(url_for("admin_settings.view_settings"))
