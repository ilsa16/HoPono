import calendar
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from app.extensions import db
from app.models.availability import AvailabilityWindow

admin_availability_bp = Blueprint("admin_availability", __name__)


def _monday_of(d):
    return d - timedelta(days=d.weekday())


@admin_availability_bp.route("/")
@login_required
def manage_availability():
    windows = (
        AvailabilityWindow.query.filter(AvailabilityWindow.date >= date.today())
        .order_by(AvailabilityWindow.date, AvailabilityWindow.start_time)
        .all()
    )
    return render_template("admin/availability.html", windows=windows)


@admin_availability_bp.route("/api/week")
@login_required
def api_week():
    start_str = request.args.get("start")
    if not start_str:
        start_date = _monday_of(date.today())
    else:
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date()

    end_date = start_date + timedelta(days=6)

    windows = (
        AvailabilityWindow.query
        .filter(AvailabilityWindow.date.between(start_date, end_date))
        .order_by(AvailabilityWindow.date, AvailabilityWindow.start_time)
        .all()
    )

    result = {}
    for d in range(7):
        day = start_date + timedelta(days=d)
        result[day.isoformat()] = []

    for w in windows:
        result[w.date.isoformat()].append({
            "id": w.id,
            "start_time": w.start_time.strftime("%H:%M"),
            "end_time": w.end_time.strftime("%H:%M"),
        })

    return jsonify({"week_start": start_date.isoformat(), "days": result})


@admin_availability_bp.route("/api/add", methods=["POST"])
@login_required
def api_add():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    window_date = data.get("date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if not all([window_date, start_time, end_time]):
        return jsonify({"error": "date, start_time, and end_time are required"}), 400

    parsed_date = datetime.strptime(window_date, "%Y-%m-%d").date()
    parsed_start = datetime.strptime(start_time, "%H:%M").time()
    parsed_end = datetime.strptime(end_time, "%H:%M").time()

    if parsed_start >= parsed_end:
        return jsonify({"error": "Start time must be before end time"}), 400

    existing = AvailabilityWindow.query.filter_by(
        date=parsed_date, start_time=parsed_start, end_time=parsed_end
    ).first()
    if existing:
        return jsonify({"error": "This window already exists", "id": existing.id}), 409

    window = AvailabilityWindow(
        date=parsed_date,
        start_time=parsed_start,
        end_time=parsed_end,
    )
    db.session.add(window)
    db.session.commit()

    return jsonify({
        "id": window.id,
        "date": window.date.isoformat(),
        "start_time": window.start_time.strftime("%H:%M"),
        "end_time": window.end_time.strftime("%H:%M"),
    }), 201


@admin_availability_bp.route("/api/delete", methods=["POST"])
@login_required
def api_delete():
    data = request.get_json()
    if not data or not data.get("id"):
        return jsonify({"error": "id is required"}), 400

    window = db.session.get(AvailabilityWindow, data["id"])
    if not window:
        return jsonify({"error": "Window not found"}), 404

    db.session.delete(window)
    db.session.commit()
    return jsonify({"deleted": True})


@admin_availability_bp.route("/api/clear-day", methods=["POST"])
@login_required
def api_clear_day():
    data = request.get_json()
    if not data or not data.get("date"):
        return jsonify({"error": "date is required"}), 400

    parsed_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
    count = AvailabilityWindow.query.filter_by(date=parsed_date).delete()
    db.session.commit()
    return jsonify({"deleted_count": count})


@admin_availability_bp.route("/api/copy-week", methods=["POST"])
@login_required
def api_copy_week():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    source_str = data.get("source_start")
    target_str = data.get("target_start")

    if not source_str or not target_str:
        return jsonify({"error": "source_start and target_start are required"}), 400

    source_start = datetime.strptime(source_str, "%Y-%m-%d").date()
    target_start = datetime.strptime(target_str, "%Y-%m-%d").date()
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
    return jsonify({"copied": count})


@admin_availability_bp.route("/api/month")
@login_required
def api_month():
    try:
        year = int(request.args.get("year", date.today().year))
        month = int(request.args.get("month", date.today().month))
    except ValueError:
        return jsonify({"error": "Invalid year or month"}), 400

    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])

    windows = (
        AvailabilityWindow.query
        .filter(AvailabilityWindow.date.between(first_day, last_day))
        .order_by(AvailabilityWindow.date, AvailabilityWindow.start_time)
        .all()
    )

    result = {}
    for w in windows:
        key = w.date.isoformat()
        if key not in result:
            result[key] = {"count": 0, "windows": []}
        result[key]["count"] += 1
        result[key]["windows"].append({
            "id": w.id,
            "start_time": w.start_time.strftime("%H:%M"),
            "end_time": w.end_time.strftime("%H:%M"),
        })

    return jsonify({"year": year, "month": month, "days": result})


@admin_availability_bp.route("/api/copy-month", methods=["POST"])
@login_required
def api_copy_month():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    source_year = data.get("source_year")
    source_month = data.get("source_month")
    target_year = data.get("target_year")
    target_month = data.get("target_month")

    if not all([source_year, source_month, target_year, target_month]):
        return jsonify({"error": "source_year, source_month, target_year, target_month required"}), 400

    source_start = date(source_year, source_month, 1)
    source_end = date(source_year, source_month, calendar.monthrange(source_year, source_month)[1])
    target_last_day = calendar.monthrange(target_year, target_month)[1]

    source_windows = AvailabilityWindow.query.filter(
        AvailabilityWindow.date.between(source_start, source_end)
    ).all()

    count = 0
    for window in source_windows:
        target_day = min(window.date.day, target_last_day)
        new_date = date(target_year, target_month, target_day)

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
    return jsonify({"copied": count})


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
