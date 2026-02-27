from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.extensions import db
from app.models.availability import AvailabilityWindow

admin_availability_bp = Blueprint("admin_availability", __name__)


@admin_availability_bp.route("/")
@login_required
def manage_availability():
    # Show current and future availability
    windows = (
        AvailabilityWindow.query.filter(AvailabilityWindow.date >= date.today())
        .order_by(AvailabilityWindow.date, AvailabilityWindow.start_time)
        .all()
    )
    return render_template("admin/availability.html", windows=windows)


@admin_availability_bp.route("/add", methods=["POST"])
@login_required
def add_window():
    window_date = request.form.get("date")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time")

    if not all([window_date, start_time, end_time]):
        flash("All fields are required.", "error")
        return redirect(url_for("admin_availability.manage_availability"))

    existing = AvailabilityWindow.query.filter_by(
        date=window_date, start_time=start_time, end_time=end_time
    ).first()
    if existing:
        flash("This availability window already exists.", "error")
        return redirect(url_for("admin_availability.manage_availability"))

    window = AvailabilityWindow(
        date=datetime.strptime(window_date, "%Y-%m-%d").date(),
        start_time=datetime.strptime(start_time, "%H:%M").time(),
        end_time=datetime.strptime(end_time, "%H:%M").time(),
    )
    db.session.add(window)
    db.session.commit()
    flash("Availability window added.", "success")
    return redirect(url_for("admin_availability.manage_availability"))


@admin_availability_bp.route("/<int:window_id>/delete", methods=["POST"])
@login_required
def delete_window(window_id):
    window = AvailabilityWindow.query.get_or_404(window_id)
    db.session.delete(window)
    db.session.commit()
    flash("Availability window removed.", "success")
    return redirect(url_for("admin_availability.manage_availability"))


@admin_availability_bp.route("/copy-week", methods=["POST"])
@login_required
def copy_week():
    source_date = request.form.get("source_week")
    target_date = request.form.get("target_week")

    if not source_date or not target_date:
        flash("Both source and target weeks are required.", "error")
        return redirect(url_for("admin_availability.manage_availability"))

    source_start = datetime.strptime(source_date, "%Y-%m-%d").date()
    target_start = datetime.strptime(target_date, "%Y-%m-%d").date()
    day_offset = (target_start - source_start).days

    source_windows = AvailabilityWindow.query.filter(
        AvailabilityWindow.date.between(source_start, source_start + timedelta(days=6))
    ).all()

    count = 0
    for window in source_windows:
        new_date = window.date + timedelta(days=day_offset)
        existing = AvailabilityWindow.query.filter_by(
            date=new_date, start_time=window.start_time, end_time=window.end_time
        ).first()
        if not existing:
            new_window = AvailabilityWindow(
                date=new_date,
                start_time=window.start_time,
                end_time=window.end_time,
            )
            db.session.add(new_window)
            count += 1

    db.session.commit()
    flash(f"Copied {count} availability windows.", "success")
    return redirect(url_for("admin_availability.manage_availability"))
